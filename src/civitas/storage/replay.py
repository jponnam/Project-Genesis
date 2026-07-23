"""Event-stream replay helpers for JSONL simulation runs.

Replay reads persisted ``DomainEvent`` records via ``JsonlEventStore``.
It does not re-execute the tick loop or reconstruct a full ``World``
aggregate (that projector does not exist). Final summaries are derived
only from event fields that are present in the log.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from civitas.domain import (
    ActionSelected,
    DomainEvent,
    SimulationCompleted,
    SimulationStarted,
)
from civitas.domain.events import EVENT_TYPE_REGISTRY
from civitas.storage.jsonl import JsonlEventStore


class ReplayError(Exception):
    """Raised when a JSONL run cannot be loaded or verified for replay."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Deterministic metadata extracted from lifecycle events."""

    seed: int | None
    ticks_configured: int | None
    agent_count: int | None
    run_name: str | None
    ticks_executed: int | None
    has_started: bool
    has_completed: bool
    first_sequence: int | None
    last_sequence: int | None
    event_count: int


@dataclass(frozen=True, slots=True)
class FinalStateSummary:
    """Partial end-of-run picture derived from the event stream.

    This is not a full ``World`` reconstruction. Fields are populated
    only when corresponding events exist.
    """

    agents_spawned: int
    agents_born: int
    agents_died: int
    estimated_living: int
    actions: dict[str, int]
    technologies_discovered: tuple[str, ...]
    institutions_created: tuple[str, ...]
    cities_created: tuple[str, ...]
    last_wealth_total_money: int | None
    last_population_alive: int | None


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Filtered replay view over a JSONL event store."""

    path: Path
    metadata: RunMetadata
    events: tuple[DomainEvent, ...]
    type_counts: dict[str, int]
    verification_notes: tuple[str, ...] = field(default_factory=tuple)
    final_state: FinalStateSummary | None = None


def _tick_value(event: DomainEvent) -> int:
    return int(event.tick.value)


def agent_ids_in_event(event: DomainEvent) -> frozenset[int]:
    """Return numeric agent ids referenced by common event fields."""
    found: set[int] = set()
    data = event.model_dump(mode="python")
    for key, value in data.items():
        if key.endswith("agent_id") or key in {
            "agent_id",
            "parent_id",
            "from_agent_id",
            "to_agent_id",
            "buyer_id",
            "seller_id",
            "teacher_id",
            "leader_id",
            "officer_id",
            "winner_id",
            "top_agent_id",
            "max_degree_agent_id",
            "strongest_from_id",
            "strongest_to_id",
            "target_agent_id",
        }:
            if isinstance(value, dict) and "value" in value:
                found.add(int(value["value"]))
            elif value is None:
                continue
    return frozenset(found)


def load_events(path: Path | str) -> tuple[DomainEvent, ...]:
    """Load and validate a JSONL event store.

    Raises:
        ReplayError: For missing files, malformed JSONL, unknown event
            types, validation failures, or broken sequence continuity.
    """
    store = JsonlEventStore(path)
    try:
        return store.read_all(validate_sequence=True)
    except FileNotFoundError as exc:
        raise ReplayError(f"event store not found: {store.path}") from exc
    except ValidationError as exc:
        raise ReplayError(f"malformed event payload: {exc}") from exc
    except ValueError as exc:
        message = str(exc)
        lowered = message.lower()
        if "unknown event_type" in lowered:
            raise ReplayError(
                f"unsupported or unknown event type in log: {message}"
            ) from exc
        if "invalid json" in lowered or "invalid event" in lowered:
            raise ReplayError(f"malformed JSONL: {message}") from exc
        if "non-contiguous sequence" in lowered:
            raise ReplayError(f"incomplete or corrupt log: {message}") from exc
        raise ReplayError(message) from exc


def extract_metadata(events: tuple[DomainEvent, ...]) -> RunMetadata:
    """Extract run metadata from lifecycle events."""
    started = next((e for e in events if isinstance(e, SimulationStarted)), None)
    completed = next(
        (e for e in events if isinstance(e, SimulationCompleted)),
        None,
    )
    return RunMetadata(
        seed=None if started is None else int(started.seed),
        ticks_configured=None if started is None else int(started.ticks),
        agent_count=None if started is None else int(started.agent_count),
        run_name=None if started is None else str(started.run_name),
        ticks_executed=None if completed is None else int(completed.ticks_executed),
        has_started=started is not None,
        has_completed=completed is not None,
        first_sequence=None if not events else int(events[0].sequence),
        last_sequence=None if not events else int(events[-1].sequence),
        event_count=len(events),
    )


def verify_metadata(metadata: RunMetadata) -> tuple[str, ...]:
    """Return human-readable verification notes (empty when fully healthy)."""
    notes: list[str] = []
    if not metadata.has_started:
        notes.append("missing SimulationStarted event")
    if not metadata.has_completed:
        notes.append("incomplete log: missing SimulationCompleted event")
    if (
        metadata.has_started
        and metadata.has_completed
        and metadata.ticks_configured is not None
        and metadata.ticks_executed is not None
        and metadata.ticks_executed != metadata.ticks_configured
    ):
        notes.append(
            "ticks_executed "
            f"({metadata.ticks_executed}) differs from configured ticks "
            f"({metadata.ticks_configured})"
        )
    if metadata.first_sequence is not None and metadata.first_sequence != 0:
        notes.append(
            f"log does not start at sequence 0 (got {metadata.first_sequence})"
        )
    if (
        metadata.last_sequence is not None
        and metadata.event_count > 0
        and metadata.last_sequence != metadata.event_count - 1
    ):
        notes.append(
            "last sequence "
            f"({metadata.last_sequence}) is inconsistent with event_count "
            f"({metadata.event_count})"
        )
    return tuple(notes)


def filter_events(
    events: tuple[DomainEvent, ...],
    *,
    from_tick: int | None = None,
    to_tick: int | None = None,
    agent_ids: frozenset[int] | None = None,
    event_types: frozenset[str] | None = None,
) -> tuple[DomainEvent, ...]:
    """Filter events by tick range, agent id, and/or event type name."""
    if from_tick is not None and to_tick is not None and from_tick > to_tick:
        raise ReplayError(
            f"invalid tick range: from_tick {from_tick} > to_tick {to_tick}"
        )
    if event_types:
        unknown = sorted(event_types - frozenset(EVENT_TYPE_REGISTRY))
        if unknown:
            joined = ", ".join(unknown)
            raise ReplayError(f"unknown event type filter value(s): {joined}")

    selected: list[DomainEvent] = []
    for event in events:
        tick = _tick_value(event)
        if from_tick is not None and tick < from_tick:
            continue
        if to_tick is not None and tick > to_tick:
            continue
        if event_types is not None and event.event_type not in event_types:
            continue
        if agent_ids is not None and agent_ids.isdisjoint(agent_ids_in_event(event)):
            continue
        selected.append(event)
    return tuple(selected)


def build_final_state_summary(events: tuple[DomainEvent, ...]) -> FinalStateSummary:
    """Derive a partial final-state summary from lifecycle and action events."""
    spawned = sum(1 for e in events if e.event_type == "AgentSpawned")
    born = sum(1 for e in events if e.event_type == "AgentBorn")
    died = sum(1 for e in events if e.event_type == "AgentDied")
    actions = Counter(
        str(event.action) for event in events if isinstance(event, ActionSelected)
    )
    tech_names = tuple(
        str(event.model_dump(mode="json")["name"])
        for event in events
        if event.event_type == "TechnologyDiscovered"
    )
    institutions = tuple(
        str(event.model_dump(mode="json")["kind"])
        for event in events
        if event.event_type == "InstitutionCreated"
    )
    cities = tuple(
        str(event.model_dump(mode="json")["kind"])
        for event in events
        if event.event_type == "CityCreated"
    )
    last_wealth_total: int | None = None
    for event in reversed(events):
        if event.event_type == "WealthObserved":
            last_wealth_total = int(event.model_dump(mode="json")["total"])
            break
    last_pop_alive: int | None = None
    for event in reversed(events):
        if event.event_type == "PopulationObserved":
            last_pop_alive = int(event.model_dump(mode="json")["alive"])
            break
    return FinalStateSummary(
        agents_spawned=spawned,
        agents_born=born,
        agents_died=died,
        estimated_living=max(0, spawned + born - died),
        actions=dict(sorted(actions.items())),
        technologies_discovered=tech_names,
        institutions_created=institutions,
        cities_created=cities,
        last_wealth_total_money=last_wealth_total,
        last_population_alive=last_pop_alive,
    )


def replay_run(
    path: Path | str,
    *,
    from_tick: int | None = None,
    to_tick: int | None = None,
    agent_ids: frozenset[int] | None = None,
    event_types: frozenset[str] | None = None,
    include_final_state: bool = False,
    verify: bool = True,
) -> ReplayResult:
    """Load, optionally verify, filter, and summarize a JSONL run."""
    resolved = Path(path)
    events = load_events(resolved)
    metadata = extract_metadata(events)
    notes = verify_metadata(metadata) if verify else ()
    filtered = filter_events(
        events,
        from_tick=from_tick,
        to_tick=to_tick,
        agent_ids=agent_ids,
        event_types=event_types,
    )
    counts = dict(Counter(event.event_type for event in filtered).most_common())
    final_state = build_final_state_summary(events) if include_final_state else None
    return ReplayResult(
        path=resolved,
        metadata=metadata,
        events=filtered,
        type_counts=counts,
        verification_notes=notes,
        final_state=final_state,
    )


def event_to_brief(event: DomainEvent) -> dict[str, Any]:
    """Return a compact JSON-ready view of one event for CLI listing."""
    dump = event.model_dump(mode="json")
    brief: dict[str, Any] = {
        "sequence": dump["sequence"],
        "tick": dump["tick"]["value"]
        if isinstance(dump.get("tick"), dict)
        else dump.get("tick"),
        "event_type": event.event_type,
    }
    for key in (
        "agent_id",
        "action",
        "run_name",
        "seed",
        "name",
        "kind",
        "utility",
    ):
        if key in dump and dump[key] is not None:
            value = dump[key]
            if isinstance(value, dict) and "value" in value:
                brief[key] = value["value"]
            else:
                brief[key] = value
    return brief
