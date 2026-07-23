"""Human- and machine-readable inspection summaries for JSONL runs.

Summaries are derived only from persisted ``DomainEvent`` records.
Fields that cannot be reconstructed from the log are omitted or set
to ``None`` / empty rather than invented.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from civitas.domain import (
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentSpawned,
    CityCreated,
    DomainEvent,
    InstitutionCreated,
    KnowledgeLearned,
    MoneyTransferred,
    PopulationObserved,
    RelationshipUpdated,
    ResourceConsumed,
    ResourceGathered,
    ResourceProduced,
    ResourceTraded,
    TechnologyDiscovered,
    WealthObserved,
)
from civitas.storage.replay import (
    ReplayError,
    extract_metadata,
    load_events,
    verify_metadata,
)


@dataclass(frozen=True, slots=True)
class WealthSnapshot:
    """Last ``WealthObserved`` census values, when present."""

    total: int
    alive_total: int
    alive_count: int
    mean_alive: float
    min_alive: int | None
    max_alive: int | None
    median_alive: int | None
    gini_bps: int
    top1_share_bps: int
    treasury: int
    zero_count: int


@dataclass(frozen=True, slots=True)
class PopulationSnapshot:
    """Last ``PopulationObserved`` census values, when present."""

    total: int
    alive: int
    dead: int
    location_counts: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class SocialSnapshot:
    """Social-change counters derivable from the event stream."""

    relationship_updates: int
    relationships_created: int
    money_transfers: int
    knowledge_learned: int
    last_bond_count: int | None
    last_network_density_bps: int | None
    last_mean_standing: float | None


@dataclass(frozen=True, slots=True)
class RunInspection:
    """Event-derived inspection report for one JSONL simulation run."""

    path: str
    run_name: str | None
    seed: int | None
    ticks_configured: int | None
    ticks_executed: int | None
    agent_count_configured: int | None
    event_count: int
    event_types: dict[str, int]
    verification_notes: tuple[str, ...]
    agents_spawned: int
    births: int
    deaths: int
    estimated_living: int
    actions: dict[str, int]
    trades: int
    resources_gathered: dict[str, int]
    resources_consumed: dict[str, int]
    resources_produced: dict[str, int]
    resources_traded: dict[str, int]
    final_resource_holdings_available: bool
    wealth: WealthSnapshot | None
    population: PopulationSnapshot | None
    institutions: tuple[str, ...]
    cities: tuple[str, ...]
    technologies_discovered: tuple[str, ...]
    social: SocialSnapshot
    notable_events: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


def _resource_totals(
    events: tuple[DomainEvent, ...],
    event_cls: type[DomainEvent],
    resource_attr: str = "resource",
    amount_attr: str = "amount",
) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for event in events:
        if not isinstance(event, event_cls):
            continue
        if event_cls is ResourceProduced:
            produced = event
            assert isinstance(produced, ResourceProduced)
            for resource, amount in produced.outputs:
                totals[str(resource)] += int(amount)
            continue
        resource = str(getattr(event, resource_attr))
        amount = int(getattr(event, amount_attr))
        totals[resource] += amount
    return dict(sorted(totals.items()))


def _last_of_type(
    events: tuple[DomainEvent, ...],
    event_cls: type[DomainEvent],
) -> DomainEvent | None:
    for event in reversed(events):
        if isinstance(event, event_cls):
            return event
    return None


def _notable_events(events: tuple[DomainEvent, ...]) -> tuple[str, ...]:
    """Return a short deterministic list of notable lifecycle milestones."""
    notables: list[str] = []
    for event in events:
        tick = int(event.tick.value)
        if isinstance(event, TechnologyDiscovered):
            notables.append(f"t{tick}: discovered {event.name} ({event.kind})")
        elif isinstance(event, AgentBorn):
            notables.append(
                f"t{tick}: birth {event.name} "
                f"(id={event.agent_id.value}, parent={event.parent_id.value})"
            )
        elif isinstance(event, AgentDied):
            notables.append(
                f"t{tick}: death {event.name} "
                f"(id={event.agent_id.value}, cause={event.cause})"
            )
        elif isinstance(event, InstitutionCreated):
            notables.append(f"t{tick}: institution {event.name} ({event.kind})")
        elif isinstance(event, CityCreated):
            notables.append(f"t{tick}: city {event.name} ({event.kind})")
        elif isinstance(event, ResourceTraded):
            notables.append(
                f"t{tick}: trade {event.resource} x{event.quantity} "
                f"@ {event.price} "
                f"(buyer={event.buyer_id.value}, seller={event.seller_id.value})"
            )
    # Keep the report bounded and deterministic.
    return tuple(notables[:50])


def build_inspection(path: Path | str) -> RunInspection:
    """Load ``path`` and build an inspection report.

    Raises:
        ReplayError: When the JSONL log cannot be loaded.
    """
    resolved = Path(path)
    events = load_events(resolved)
    metadata = extract_metadata(events)
    notes = verify_metadata(metadata)
    type_counts = dict(Counter(e.event_type for e in events).most_common())

    spawned = sum(1 for e in events if isinstance(e, AgentSpawned))
    births = sum(1 for e in events if isinstance(e, AgentBorn))
    deaths = sum(1 for e in events if isinstance(e, AgentDied))
    actions = Counter(
        str(event.action) for event in events if isinstance(event, ActionSelected)
    )
    trades = sum(1 for e in events if isinstance(e, ResourceTraded))

    wealth_event = _last_of_type(events, WealthObserved)
    wealth: WealthSnapshot | None = None
    if isinstance(wealth_event, WealthObserved):
        wealth = WealthSnapshot(
            total=int(wealth_event.total),
            alive_total=int(wealth_event.alive_total),
            alive_count=int(wealth_event.alive_count),
            mean_alive=float(wealth_event.mean_alive),
            min_alive=wealth_event.min_alive,
            max_alive=wealth_event.max_alive,
            median_alive=wealth_event.median_alive,
            gini_bps=int(wealth_event.gini_bps),
            top1_share_bps=int(wealth_event.top1_share_bps),
            treasury=int(wealth_event.treasury),
            zero_count=int(wealth_event.zero_count),
        )

    pop_event = _last_of_type(events, PopulationObserved)
    population: PopulationSnapshot | None = None
    if isinstance(pop_event, PopulationObserved):
        population = PopulationSnapshot(
            total=int(pop_event.total),
            alive=int(pop_event.alive),
            dead=int(pop_event.dead),
            location_counts=tuple(
                (int(loc), int(count)) for loc, count in pop_event.location_counts
            ),
        )

    last_rel = None
    last_net = None
    last_rep = None
    for event in reversed(events):
        if last_rel is None and event.event_type == "RelationshipsObserved":
            last_rel = event.model_dump(mode="json")
        elif last_net is None and event.event_type == "NetworksObserved":
            last_net = event.model_dump(mode="json")
        elif last_rep is None and event.event_type == "ReputationObserved":
            last_rep = event.model_dump(mode="json")
        if last_rel is not None and last_net is not None and last_rep is not None:
            break

    social = SocialSnapshot(
        relationship_updates=sum(
            1 for e in events if isinstance(e, RelationshipUpdated)
        ),
        relationships_created=sum(
            1 for e in events if isinstance(e, RelationshipUpdated) and e.created
        ),
        money_transfers=sum(1 for e in events if isinstance(e, MoneyTransferred)),
        knowledge_learned=sum(1 for e in events if isinstance(e, KnowledgeLearned)),
        last_bond_count=None if last_rel is None else int(last_rel["bond_count"]),
        last_network_density_bps=(
            None if last_net is None else int(last_net["density_bps"])
        ),
        last_mean_standing=(
            None if last_rep is None else float(last_rep["mean_standing"])
        ),
    )

    institutions = tuple(
        f"{event.kind}:{event.name}"
        for event in events
        if isinstance(event, InstitutionCreated)
    )
    cities = tuple(
        f"{event.kind}:{event.name}"
        for event in events
        if isinstance(event, CityCreated)
    )
    techs = tuple(
        f"{event.kind}:{event.name}"
        for event in events
        if isinstance(event, TechnologyDiscovered)
    )

    return RunInspection(
        path=str(resolved),
        run_name=metadata.run_name,
        seed=metadata.seed,
        ticks_configured=metadata.ticks_configured,
        ticks_executed=metadata.ticks_executed,
        agent_count_configured=metadata.agent_count,
        event_count=metadata.event_count,
        event_types=type_counts,
        verification_notes=notes,
        agents_spawned=spawned,
        births=births,
        deaths=deaths,
        estimated_living=max(0, spawned + births - deaths),
        actions=dict(sorted(actions.items())),
        trades=trades,
        resources_gathered=_resource_totals(events, ResourceGathered),
        resources_consumed=_resource_totals(events, ResourceConsumed),
        resources_produced=_resource_totals(events, ResourceProduced),
        resources_traded=_resource_totals(
            events,
            ResourceTraded,
            amount_attr="quantity",
        ),
        final_resource_holdings_available=False,
        wealth=wealth,
        population=population,
        institutions=institutions,
        cities=cities,
        technologies_discovered=techs,
        social=social,
        notable_events=_notable_events(events),
    )


__all__ = [
    "PopulationSnapshot",
    "ReplayError",
    "RunInspection",
    "SocialSnapshot",
    "WealthSnapshot",
    "build_inspection",
]
