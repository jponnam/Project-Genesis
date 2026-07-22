"""Domain events for event-sourced simulation.

Everything important becomes a ``DomainEvent``. Events are immutable,
JSON-serializable, and totally ordered by ``sequence`` within a run.
Systems communicate exclusively through these events.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import (
    AgentId,
    GovernmentId,
    LawId,
    ListingId,
    LocationId,
    MarketId,
)
from civitas.domain.time import Tick
from civitas.domain.types import (
    AffinityScore,
    NonEmptyStr,
    NonNegativeInt,
    UnitInterval,
)


class DomainEvent(BaseModel):
    """Base class for all domain events.

    Attributes:
        sequence: Total order index within a run (stamped by the event bus).
        tick: Simulation tick at which the event occurred.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    sequence: NonNegativeInt = Field(
        default=0,
        description="Total order index; assigned by EventBus on publish.",
    )
    tick: Tick = Field(description="Tick at which this event occurred.")

    @property
    def event_type(self) -> str:
        """Stable type name used for serialization and dispatch."""
        return type(self).__name__

    def to_record(self) -> dict[str, Any]:
        """Serialize to a JSON-ready mapping including ``event_type``."""
        payload = self.model_dump(mode="json")
        payload["event_type"] = self.event_type
        return payload


class SimulationStarted(DomainEvent):
    """Emitted once when a simulation run begins."""

    seed: NonNegativeInt
    ticks: NonNegativeInt
    agent_count: NonNegativeInt
    run_name: NonEmptyStr


class SimulationCompleted(DomainEvent):
    """Emitted once when a simulation run finishes."""

    ticks_executed: NonNegativeInt


class TickStarted(DomainEvent):
    """Emitted at the beginning of a tick's agent-update cycle."""


class TickCompleted(DomainEvent):
    """Emitted after all agents have been updated for a tick."""


class LocationCreated(DomainEvent):
    """Emitted when a location is added to the world map."""

    location_id: LocationId
    name: NonEmptyStr
    x: int
    y: int
    kind: NonEmptyStr


class AgentSpawned(DomainEvent):
    """Emitted when an agent is created in the world."""

    agent_id: AgentId
    name: NonEmptyStr
    location_id: LocationId


class AgentMoved(DomainEvent):
    """Emitted when an agent relocates from one location to another."""

    agent_id: AgentId
    from_location_id: LocationId
    to_location_id: LocationId


class ActionSelected(DomainEvent):
    """Emitted when a policy selects an action for an agent."""

    agent_id: AgentId
    action: NonEmptyStr
    utility: float
    target_location_id: LocationId | None = None
    target_resource: NonEmptyStr | None = None
    target_agent_id: AgentId | None = None


class ActionCompleted(DomainEvent):
    """Emitted when an action has been applied to world state."""

    agent_id: AgentId
    action: NonEmptyStr
    success: bool


class ResourceConsumed(DomainEvent):
    """Emitted when an agent consumes a resource from inventory."""

    agent_id: AgentId
    resource: NonEmptyStr
    amount: NonNegativeInt


class ResourceGathered(DomainEvent):
    """Emitted when an agent gathers a resource from a location deposit."""

    agent_id: AgentId
    location_id: LocationId
    resource: NonEmptyStr
    amount: NonNegativeInt


class NeedDecayed(DomainEvent):
    """Emitted when a homeostatic need changes due to decay or recovery."""

    agent_id: AgentId
    need: NonEmptyStr
    previous: UnitInterval
    current: UnitInterval


class PopulationObserved(DomainEvent):
    """Emitted when a population census is taken."""

    initial_count: NonNegativeInt
    total: NonNegativeInt
    alive: NonNegativeInt
    dead: NonNegativeInt
    # (location_id, agent_count) pairs in ascending location_id order.
    location_counts: tuple[tuple[int, int], ...] = ()


class AgentBorn(DomainEvent):
    """Emitted when a living parent produces a new agent."""

    agent_id: AgentId
    parent_id: AgentId
    location_id: LocationId
    name: NonEmptyStr


class AgentDied(DomainEvent):
    """Emitted when a living agent transitions to dead."""

    agent_id: AgentId
    location_id: LocationId
    cause: NonEmptyStr
    name: NonEmptyStr


class MoneyTransferred(DomainEvent):
    """Emitted when money moves from one living agent to another."""

    from_agent_id: AgentId
    to_agent_id: AgentId
    amount: NonNegativeInt


class TaxCollected(DomainEvent):
    """Emitted when an agent pays tax into the world treasury."""

    agent_id: AgentId
    amount: NonNegativeInt
    treasury_after: NonNegativeInt


class ResourceTraded(DomainEvent):
    """Emitted when a buyer purchases inventory from a seller."""

    buyer_id: AgentId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt
    price: NonNegativeInt


class ResourceProduced(DomainEvent):
    """Emitted when an agent crafts outputs from a production recipe."""

    agent_id: AgentId
    recipe_id: NonEmptyStr
    # (resource, quantity) pairs in ascending resource name order.
    outputs: tuple[tuple[str, int], ...] = ()


class MarketCreated(DomainEvent):
    """Emitted when a market venue is added to the world."""

    market_id: MarketId
    location_id: LocationId
    name: NonEmptyStr


class GovernmentCreated(DomainEvent):
    """Emitted when a government / polity is added to the world."""

    government_id: GovernmentId
    name: NonEmptyStr
    seat_location_id: LocationId
    # Location ids in ascending order.
    jurisdiction: tuple[int, ...] = ()
    leader_id: AgentId | None = None


class LawCreated(DomainEvent):
    """Emitted when a statute is added to the world."""

    law_id: LawId
    government_id: GovernmentId
    name: NonEmptyStr
    kind: NonEmptyStr
    active: bool = True
    flat_amount: NonNegativeInt = 0
    rate_bps: NonNegativeInt = 0


class ListingPosted(DomainEvent):
    """Emitted when a seller escrows goods onto a market listing."""

    market_id: MarketId
    listing_id: ListingId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt
    unit_price: NonNegativeInt


class ListingFilled(DomainEvent):
    """Emitted when a buyer purchases units from a market listing."""

    market_id: MarketId
    listing_id: ListingId
    buyer_id: AgentId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt
    unit_price: NonNegativeInt
    total_price: NonNegativeInt


class ListingCancelled(DomainEvent):
    """Emitted when a seller cancels an open listing and recovers escrow."""

    market_id: MarketId
    listing_id: ListingId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt


class MarketObserved(DomainEvent):
    """Emitted when an open-book market census is taken."""

    market_count: NonNegativeInt
    listing_count: NonNegativeInt
    total_units: NonNegativeInt
    # (market_id, listing_count) pairs in ascending market_id order.
    market_listings: tuple[tuple[int, int], ...] = ()


class PriceObserved(DomainEvent):
    """Emitted when a market price census is taken.

    Each quote tuple is:
    ``(market_id, resource, best_ask, ask_quantity, last_trade,
    listing_count, total_units, suggested_unit_price)`` with ``None``
    allowed for missing best ask / last trade.
    """

    quote_count: NonNegativeInt
    quotes: tuple[
        tuple[int, str, int | None, int, int | None, int, int, int],
        ...,
    ] = ()


class WealthObserved(DomainEvent):
    """Emitted when a wealth census is taken."""

    total: NonNegativeInt
    alive_total: NonNegativeInt
    dead_total: NonNegativeInt
    alive_count: NonNegativeInt
    mean_alive: float
    min_alive: NonNegativeInt | None = None
    max_alive: NonNegativeInt | None = None
    treasury: NonNegativeInt = 0
    society_total: NonNegativeInt = 0
    treasury_share_bps: NonNegativeInt = 0
    median_alive: NonNegativeInt | None = None
    gini_bps: NonNegativeInt = 0
    top1_share_bps: NonNegativeInt = 0
    top10_share_bps: NonNegativeInt = 0
    zero_count: NonNegativeInt = 0


class RelationshipUpdated(DomainEvent):
    """Emitted when a directed relationship bond is created or updated."""

    from_agent_id: AgentId
    to_agent_id: AgentId
    affinity: AffinityScore
    trust: UnitInterval
    created: bool = False


class RelationshipsObserved(DomainEvent):
    """Emitted when a relationship census is taken."""

    bond_count: NonNegativeInt
    agents_with_bonds: NonNegativeInt
    living_bond_count: NonNegativeInt
    mean_affinity: float
    min_affinity: AffinityScore | None = None
    max_affinity: AffinityScore | None = None
    mean_trust: float = 0.0
    min_trust: UnitInterval | None = None
    max_trust: UnitInterval | None = None


class ReputationObserved(DomainEvent):
    """Emitted when a public-standing (reputation) census is taken."""

    living_agent_count: NonNegativeInt
    mean_standing: UnitInterval
    median_standing_bps: NonNegativeInt
    gini_standing_bps: NonNegativeInt
    top_standing_share_bps: NonNegativeInt
    agents_with_inbound_bonds: NonNegativeInt
    top_agent_id: AgentId | None = None
    top_standing: UnitInterval | None = None


class FamiliesObserved(DomainEvent):
    """Emitted when a kinship / family-lineage census is taken."""

    living_agent_count: NonNegativeInt
    founder_count: NonNegativeInt
    parented_count: NonNegativeInt
    orphan_count: NonNegativeInt
    living_with_living_parent: NonNegativeInt
    lineage_count: NonNegativeInt
    mean_lineage_size: float
    max_lineage_size: NonNegativeInt
    max_generation_depth: NonNegativeInt
    parents_with_living_children: NonNegativeInt
    mean_living_children: float
    max_living_children: NonNegativeInt


class NetworksObserved(DomainEvent):
    """Emitted when a social-network census is taken."""

    living_agent_count: NonNegativeInt
    directed_edge_count: NonNegativeInt
    undirected_edge_count: NonNegativeInt
    reciprocal_pair_count: NonNegativeInt
    reciprocity_rate: float
    reciprocity_bps: NonNegativeInt
    mean_degree: float
    max_degree: NonNegativeInt
    max_degree_agent_id: AgentId | None = None
    isolated_count: NonNegativeInt
    component_count: NonNegativeInt
    largest_component_size: NonNegativeInt
    mean_component_size: float
    density: float
    density_bps: NonNegativeInt
    strongest_from_id: AgentId | None = None
    strongest_to_id: AgentId | None = None
    strongest_strength: UnitInterval | None = None


class GovernmentsObserved(DomainEvent):
    """Emitted when a government census is taken."""

    government_count: NonNegativeInt
    covered_location_count: NonNegativeInt
    uncovered_location_count: NonNegativeInt
    total_treasury: NonNegativeInt
    led_count: NonNegativeInt
    vacant_leader_count: NonNegativeInt
    living_subject_count: NonNegativeInt
    mean_subjects: float
    max_subjects: NonNegativeInt
    max_subjects_government_id: GovernmentId | None = None


class LawsObserved(DomainEvent):
    """Emitted when a statute census is taken."""

    law_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_active_laws: NonNegativeInt
    active_tax_schedule_count: NonNegativeInt


CONCRETE_EVENT_TYPES: tuple[type[DomainEvent], ...] = (
    SimulationStarted,
    SimulationCompleted,
    TickStarted,
    TickCompleted,
    LocationCreated,
    MarketCreated,
    GovernmentCreated,
    LawCreated,
    AgentSpawned,
    AgentMoved,
    AgentBorn,
    AgentDied,
    ActionSelected,
    ActionCompleted,
    ResourceConsumed,
    ResourceGathered,
    ResourceTraded,
    ResourceProduced,
    ListingPosted,
    ListingFilled,
    ListingCancelled,
    NeedDecayed,
    PopulationObserved,
    MoneyTransferred,
    TaxCollected,
    MarketObserved,
    PriceObserved,
    WealthObserved,
    RelationshipUpdated,
    RelationshipsObserved,
    ReputationObserved,
    FamiliesObserved,
    NetworksObserved,
    GovernmentsObserved,
    LawsObserved,
)

EVENT_TYPE_REGISTRY: dict[str, type[DomainEvent]] = {
    cls.__name__: cls for cls in CONCRETE_EVENT_TYPES
}


def event_from_record(record: dict[str, Any]) -> DomainEvent:
    """Deserialize a JSONL/JSON record into a concrete ``DomainEvent``.

    Raises:
        ValueError: If ``event_type`` is missing or unknown.
        ValidationError: If the payload fails model validation.
    """
    if "event_type" not in record:
        msg = "event record missing required key 'event_type'"
        raise ValueError(msg)
    event_type = record["event_type"]
    if not isinstance(event_type, str):
        msg = f"event_type must be a string, got {type(event_type).__name__}"
        raise ValueError(msg)
    try:
        event_cls = EVENT_TYPE_REGISTRY[event_type]
    except KeyError as exc:
        msg = f"unknown event_type: {event_type}"
        raise ValueError(msg) from exc
    payload = {key: value for key, value in record.items() if key != "event_type"}
    return event_cls.model_validate(payload)
