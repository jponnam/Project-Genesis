"""Unit tests for the GovernmentSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Government,
    GovernmentsObserved,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import GovernmentConfig, GovernmentSystem


def test_observe_emits_governments_observed_without_mutating_world() -> None:
    """observe publishes one government census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=4))
    bus = EventBus()
    updated = GovernmentSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, GovernmentsObserved)]
    assert len(events) == 1
    assert events[0].government_count == 1
    assert events[0].covered_location_count == 9
    assert events[0].uncovered_location_count == 0
    assert events[0].living_subject_count == 4
    assert events[0].vacant_leader_count == 1


def test_observe_can_suppress_events() -> None:
    """GovernmentConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    GovernmentSystem(GovernmentConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_system_wrappers_appoint_and_treasury() -> None:
    """System mutation wrappers apply legal changes and ignore illegal ones."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=1),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = GovernmentSystem()
    appointed = system.appoint_leader(world, 0, 0)
    assert appointed.government_by_id(0).leader_id.value == 0  # type: ignore[union-attr]
    credited = system.credit_treasury(appointed, 0, 4)
    assert credited.government_by_id(0).treasury == 5  # type: ignore[union-attr]
    unchanged = system.debit_treasury(credited, 0, 99)
    assert unchanged == credited
