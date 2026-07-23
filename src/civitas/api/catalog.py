"""Read-only discovery and loading of local JSONL simulation runs."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from civitas.api.models import AgentSummary, RunDetail, RunListItem
from civitas.domain import (
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentMoved,
    AgentSpawned,
    DomainEvent,
)
from civitas.storage.replay import (
    ReplayError,
    agent_ids_in_event,
    extract_metadata,
    filter_events,
    load_events,
    verify_metadata,
)
from civitas.storage.summary import build_inspection


class RunNotFoundError(LookupError):
    """Raised when a run_id does not resolve to a JSONL file."""


def default_runs_dir() -> Path:
    """Return the configured runs directory (env ``CIVITAS_RUNS_DIR`` or ``runs``)."""
    configured = os.environ.get("CIVITAS_RUNS_DIR", "runs")
    return Path(configured)


def list_run_paths(runs_dir: Path | None = None) -> tuple[Path, ...]:
    """List JSONL files in ``runs_dir`` sorted by name."""
    root = default_runs_dir() if runs_dir is None else runs_dir
    if not root.is_dir():
        return ()
    return tuple(sorted(path for path in root.glob("*.jsonl") if path.is_file()))


def resolve_run_path(run_id: str, runs_dir: Path | None = None) -> Path:
    """Resolve ``run_id`` to a JSONL path under the runs directory.

    ``run_id`` may be a bare stem (``demo_seed42``) or include ``.jsonl``.
    Path traversal outside the runs directory is rejected.
    """
    root = (default_runs_dir() if runs_dir is None else runs_dir).resolve()
    stem = run_id.removesuffix(".jsonl")
    if not stem or "/" in stem or "\\" in stem or stem in {".", ".."}:
        raise RunNotFoundError(f"invalid run_id: {run_id}")
    candidate = (root / f"{stem}.jsonl").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RunNotFoundError(f"run_id escapes runs directory: {run_id}") from exc
    if not candidate.is_file():
        raise RunNotFoundError(f"run not found: {run_id}")
    return candidate


def run_id_for_path(path: Path) -> str:
    """Return the stable run identifier for a JSONL path."""
    return path.stem


def describe_run(path: Path) -> RunListItem:
    """Build list metadata for one run file (loads events once)."""
    events = load_events(path)
    metadata = extract_metadata(events)
    return RunListItem(
        run_id=run_id_for_path(path),
        path=str(path),
        size_bytes=path.stat().st_size,
        seed=metadata.seed,
        run_name=metadata.run_name,
        ticks_configured=metadata.ticks_configured,
        ticks_executed=metadata.ticks_executed,
        agent_count=metadata.agent_count,
        event_count=metadata.event_count,
    )


def detail_run(path: Path) -> RunDetail:
    """Build detailed metadata including verification notes."""
    events = load_events(path)
    metadata = extract_metadata(events)
    notes = verify_metadata(metadata)
    base = describe_run(path)
    return RunDetail(
        **base.model_dump(),
        has_started=metadata.has_started,
        has_completed=metadata.has_completed,
        verification_notes=list(notes),
    )


def load_run_events(
    run_id: str,
    runs_dir: Path | None = None,
) -> tuple[Path, tuple[DomainEvent, ...]]:
    """Resolve and load events for ``run_id``."""
    path = resolve_run_path(run_id, runs_dir=runs_dir)
    return path, load_events(path)


def paginate_events(
    events: tuple[DomainEvent, ...],
    *,
    offset: int,
    limit: int,
    from_tick: int | None = None,
    to_tick: int | None = None,
    agent_id: int | None = None,
    event_type: str | None = None,
) -> tuple[int, list[dict[str, object]]]:
    """Filter and paginate events into JSON-ready records."""
    filtered = filter_events(
        events,
        from_tick=from_tick,
        to_tick=to_tick,
        agent_ids=None if agent_id is None else frozenset({agent_id}),
        event_types=None if event_type is None else frozenset({event_type}),
    )
    total = len(filtered)
    page = filtered[offset : offset + limit]
    records = [event.to_record() for event in page]
    return total, records


def build_agent_summaries(events: tuple[DomainEvent, ...]) -> list[AgentSummary]:
    """Derive per-agent summaries from lifecycle and action events."""
    names: dict[int, str] = {}
    spawned: set[int] = set()
    born: set[int] = set()
    died: dict[int, str] = {}
    actions: dict[int, Counter[str]] = {}
    locations: dict[int, int] = {}
    seen: set[int] = set()

    for event in events:
        if isinstance(event, AgentSpawned):
            agent_id = int(event.agent_id.value)
            spawned.add(agent_id)
            names[agent_id] = str(event.name)
            locations[agent_id] = int(event.location_id.value)
            seen.add(agent_id)
        elif isinstance(event, AgentBorn):
            agent_id = int(event.agent_id.value)
            born.add(agent_id)
            names[agent_id] = str(event.name)
            locations[agent_id] = int(event.location_id.value)
            seen.add(agent_id)
        elif isinstance(event, AgentDied):
            agent_id = int(event.agent_id.value)
            died[agent_id] = str(event.cause)
            names.setdefault(agent_id, str(event.name))
            seen.add(agent_id)
        elif isinstance(event, AgentMoved):
            agent_id = int(event.agent_id.value)
            locations[agent_id] = int(event.to_location_id.value)
            seen.add(agent_id)
        elif isinstance(event, ActionSelected):
            agent_id = int(event.agent_id.value)
            actions.setdefault(agent_id, Counter())[str(event.action)] += 1
            seen.add(agent_id)
        else:
            for agent_id in agent_ids_in_event(event):
                seen.add(agent_id)

    summaries: list[AgentSummary] = []
    for agent_id in sorted(seen):
        summaries.append(
            AgentSummary(
                agent_id=agent_id,
                name=names.get(agent_id),
                spawned=agent_id in spawned,
                born=agent_id in born,
                died=agent_id in died,
                death_cause=died.get(agent_id),
                action_counts=dict(sorted(actions.get(agent_id, Counter()).items())),
                last_location_id=locations.get(agent_id),
            )
        )
    return summaries


def summary_dict(path: Path) -> dict[str, object]:
    """Return inspection summary mapping for API responses."""
    return build_inspection(path).to_dict()


__all__ = [
    "ReplayError",
    "RunNotFoundError",
    "build_agent_summaries",
    "default_runs_dir",
    "describe_run",
    "detail_run",
    "list_run_paths",
    "load_run_events",
    "paginate_events",
    "resolve_run_path",
    "run_id_for_path",
    "summary_dict",
]
