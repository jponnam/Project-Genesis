"""Domain events for event-sourced simulation.

Everything important becomes a ``DomainEvent``. Events are immutable,
JSON-serializable, and totally ordered by ``sequence`` within a run.
Systems communicate exclusively through these events.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import AgentId, LocationId
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


class AgentSpawned(DomainEvent):
    """Emitted when an agent is created in the world."""

    agent_id: AgentId
    name: NonEmptyStr
    location_id: LocationId


class ActionSelected(DomainEvent):
    """Emitted when a policy selects an action for an agent."""

    agent_id: AgentId
    action: NonEmptyStr
    utility: float


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


class NeedDecayed(DomainEvent):
    """Emitted when a homeostatic need changes due to decay or recovery."""

    agent_id: AgentId
    need: NonEmptyStr
    previous: UnitInterval
    current: UnitInterval


CONCRETE_EVENT_TYPES: tuple[type[DomainEvent], ...] = (
    SimulationStarted,
    SimulationCompleted,
    TickStarted,
    TickCompleted,
    AgentSpawned,
    ActionSelected,
    ActionCompleted,
    ResourceConsumed,
    NeedDecayed,
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
