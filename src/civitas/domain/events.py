"""Domain events for event-sourced simulation.

Everything important becomes a ``DomainEvent``. Events are immutable,
JSON-serializable, and totally ordered by ``sequence`` within a run.
Systems communicate exclusively through these events.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import AgentId, ListingId, LocationId, MarketId
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt, UnitInterval


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


CONCRETE_EVENT_TYPES: tuple[type[DomainEvent], ...] = (
    SimulationStarted,
    SimulationCompleted,
    TickStarted,
    TickCompleted,
    LocationCreated,
    MarketCreated,
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
    MarketObserved,
    PriceObserved,
    WealthObserved,
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
