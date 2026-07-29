"""Deterministic partial world projector over JSONL event streams.

Projects event-derivable state into a labeled summary. This is **not** a
full ``World`` rebuild: fields that cannot be proven from the log are
omitted or marked unavailable rather than invented.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from civitas.domain import (
    AgentBorn,
    AgentDied,
    AgentSpawned,
    CityCreated,
    DomainEvent,
    InstitutionCreated,
    PopulationObserved,
    ResourcesObserved,
    TechnologyDiscovered,
    WealthObserved,
)
from civitas.storage.replay import ReplayError, extract_metadata, load_events


@dataclass(frozen=True, slots=True)
class ProjectedState:
    """Partial projected state derived only from persisted events."""

    path: str | None
    seed: int | None
    ticks_configured: int | None
    ticks_executed: int | None
    run_name: str | None
    agent_count_configured: int | None
    event_count: int
    agents_spawned: tuple[int, ...]
    agents_born: tuple[int, ...]
    agents_died: tuple[int, ...]
    estimated_living_ids: tuple[int, ...]
    institutions: tuple[str, ...]
    cities: tuple[str, ...]
    technologies_discovered: tuple[str, ...]
    last_wealth_alive_total: int | None
    last_wealth_gini_bps: int | None
    last_population_alive: int | None
    resource_holdings_available: bool
    resource_alive_totals: tuple[tuple[str, int], ...]
    resource_agent_holdings: tuple[tuple[int, str, int], ...]
    resource_escrow_totals: tuple[tuple[str, int], ...]
    unavailable: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


_DEFAULT_UNAVAILABLE = (
    "full_world_identity",
    "per_agent_money_vector",
    "agent_needs",
    "agent_personality",
    "location_deposits",
    "open_research_progress_rows",
)


def project_events(
    events: tuple[DomainEvent, ...] | list[DomainEvent],
    *,
    path: str | None = None,
) -> ProjectedState:
    """Project a deterministic partial state from ``events``."""
    ordered = tuple(events)
    metadata = extract_metadata(ordered)

    spawned: list[int] = []
    born: list[int] = []
    died: set[int] = set()
    living: set[int] = set()
    institutions: list[str] = []
    cities: list[str] = []
    techs: list[str] = []

    last_wealth: WealthObserved | None = None
    last_population: PopulationObserved | None = None
    last_resources: ResourcesObserved | None = None

    for event in ordered:
        if isinstance(event, AgentSpawned):
            agent_id = int(event.agent_id.value)
            spawned.append(agent_id)
            living.add(agent_id)
        elif isinstance(event, AgentBorn):
            agent_id = int(event.agent_id.value)
            born.append(agent_id)
            living.add(agent_id)
        elif isinstance(event, AgentDied):
            agent_id = int(event.agent_id.value)
            died.add(agent_id)
            living.discard(agent_id)
        elif isinstance(event, InstitutionCreated):
            institutions.append(f"{event.kind}:{event.name}")
        elif isinstance(event, CityCreated):
            cities.append(f"{event.kind}:{event.name}")
        elif isinstance(event, TechnologyDiscovered):
            techs.append(f"{event.kind}:{event.name}")
        elif isinstance(event, WealthObserved):
            last_wealth = event
        elif isinstance(event, PopulationObserved):
            last_population = event
        elif isinstance(event, ResourcesObserved):
            last_resources = event

    unavailable = list(_DEFAULT_UNAVAILABLE)
    if last_resources is None:
        unavailable.append("resource_holdings")

    return ProjectedState(
        path=path,
        seed=metadata.seed,
        ticks_configured=metadata.ticks_configured,
        ticks_executed=metadata.ticks_executed,
        run_name=metadata.run_name,
        agent_count_configured=metadata.agent_count,
        event_count=len(ordered),
        agents_spawned=tuple(spawned),
        agents_born=tuple(born),
        agents_died=tuple(sorted(died)),
        estimated_living_ids=tuple(sorted(living)),
        institutions=tuple(institutions),
        cities=tuple(cities),
        technologies_discovered=tuple(techs),
        last_wealth_alive_total=(
            None if last_wealth is None else int(last_wealth.alive_total)
        ),
        last_wealth_gini_bps=(
            None if last_wealth is None else int(last_wealth.gini_bps)
        ),
        last_population_alive=(
            None if last_population is None else int(last_population.alive)
        ),
        resource_holdings_available=last_resources is not None,
        resource_alive_totals=(
            ()
            if last_resources is None
            else tuple(
                (str(resource), int(amount))
                for resource, amount in last_resources.alive_totals
            )
        ),
        resource_agent_holdings=(
            ()
            if last_resources is None
            else tuple(
                (int(agent_id), str(resource), int(amount))
                for agent_id, resource, amount in last_resources.agent_holdings
            )
        ),
        resource_escrow_totals=(
            ()
            if last_resources is None
            else tuple(
                (str(resource), int(amount))
                for resource, amount in last_resources.escrow_totals
            )
        ),
        unavailable=tuple(unavailable),
    )


def project_run(path: Path | str) -> ProjectedState:
    """Load a JSONL run and project its partial state."""
    resolved = Path(path)
    events = load_events(resolved)
    return project_events(events, path=str(resolved))


__all__ = [
    "ProjectedState",
    "ReplayError",
    "project_events",
    "project_run",
]
