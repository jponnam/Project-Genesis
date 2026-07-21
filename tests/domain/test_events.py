"""Unit tests for domain event models and serialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentId,
    AgentSpawned,
    DomainEvent,
    LocationId,
    NeedDecayed,
    ResourceConsumed,
    SimulationCompleted,
    SimulationStarted,
    Tick,
    TickCompleted,
    TickStarted,
    event_from_record,
)
from civitas.domain.events import CONCRETE_EVENT_TYPES, EVENT_TYPE_REGISTRY


def test_domain_event_exposes_event_type_name() -> None:
    """event_type matches the concrete class name."""
    event = TickStarted(tick=Tick(value=1))
    assert event.event_type == "TickStarted"
    assert isinstance(event, DomainEvent)


def test_events_are_frozen() -> None:
    """Domain events cannot be mutated in place."""
    event = TickCompleted(sequence=0, tick=Tick(value=2))
    with pytest.raises(ValidationError):
        event.sequence = 9  # type: ignore[misc]


def test_to_record_includes_event_type_and_round_trips() -> None:
    """Serialization includes event_type and deserializes losslessly."""
    original = ActionSelected(
        sequence=3,
        tick=Tick(value=4),
        agent_id=AgentId(value=1),
        action="eat",
        utility=0.75,
    )
    record = original.to_record()
    assert record["event_type"] == "ActionSelected"
    assert record["action"] == "eat"
    restored = event_from_record(record)
    assert restored == original
    assert isinstance(restored, ActionSelected)


def test_event_from_record_rejects_unknown_type() -> None:
    """Unknown event_type values are hard errors."""
    with pytest.raises(ValueError, match="unknown event_type"):
        event_from_record(
            {
                "event_type": "NotARealEvent",
                "sequence": 0,
                "tick": {"value": 0},
            }
        )


def test_event_from_record_requires_event_type() -> None:
    """Records without event_type are rejected."""
    with pytest.raises(ValueError, match="missing required key"):
        event_from_record({"sequence": 0, "tick": {"value": 0}})


def test_all_concrete_events_are_registered() -> None:
    """Every concrete event type is present in the registry."""
    assert len(CONCRETE_EVENT_TYPES) == len(EVENT_TYPE_REGISTRY)
    for event_cls in CONCRETE_EVENT_TYPES:
        assert EVENT_TYPE_REGISTRY[event_cls.__name__] is event_cls


def test_phase1_events_validate_payloads() -> None:
    """Representative Phase 1 events accept well-formed payloads."""
    tick = Tick(value=1)
    started = SimulationStarted(
        tick=Tick(value=0),
        seed=42,
        ticks=100,
        agent_count=10,
        run_name="default",
    )
    spawned = AgentSpawned(
        tick=tick,
        agent_id=AgentId(value=0),
        name="Ada",
        location_id=LocationId(value=0),
    )
    completed = ActionCompleted(
        tick=tick,
        agent_id=AgentId(value=0),
        action="rest",
        success=True,
    )
    consumed = ResourceConsumed(
        tick=tick,
        agent_id=AgentId(value=0),
        resource="food",
        amount=1,
    )
    decayed = NeedDecayed(
        tick=tick,
        agent_id=AgentId(value=0),
        need="food",
        previous=1.0,
        current=0.9,
    )
    finished = SimulationCompleted(tick=Tick(value=100), ticks_executed=100)
    assert started.run_name == "default"
    assert spawned.name == "Ada"
    assert completed.success is True
    assert consumed.amount == 1
    assert decayed.current == 0.9
    assert finished.ticks_executed == 100


def test_nested_ids_round_trip_through_record() -> None:
    """Nested AgentId/LocationId survive JSON record round-trips."""
    event = AgentSpawned(
        sequence=5,
        tick=Tick(value=0),
        agent_id=AgentId(value=9),
        name="Bea",
        location_id=LocationId(value=2),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentSpawned)
    assert restored.agent_id == AgentId(value=9)
    assert restored.location_id == LocationId(value=2)
