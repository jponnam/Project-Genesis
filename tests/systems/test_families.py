"""Unit tests for the FamilySystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    FamiliesObserved,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import FamilyConfig, FamilySystem


def test_observe_emits_families_observed_without_mutating_world() -> None:
    """observe publishes one family census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=4))
    bus = EventBus()
    updated = FamilySystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, FamiliesObserved)]
    assert len(events) == 1
    assert events[0].living_agent_count == 4
    assert events[0].founder_count == 4
    assert events[0].parented_count == 0
    assert events[0].lineage_count == 4


def test_observe_can_suppress_events() -> None:
    """FamilyConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    FamilySystem(FamilyConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_observe_reports_parented_lineage() -> None:
    """Census event reflects recorded parent_id links."""
    world = World(
        config=SimulationConfig(agent_count=3, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(
            Agent.create(agent_id=0, name="A"),
            Agent.create(agent_id=1, name="B", parent_id=0),
            Agent.create(agent_id=2, name="C", parent_id=0),
        ),
    )
    bus = EventBus()
    FamilySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, FamiliesObserved)]
    event = events[0]
    assert event.founder_count == 1
    assert event.parented_count == 2
    assert event.living_with_living_parent == 2
    assert event.lineage_count == 1
    assert event.max_lineage_size == 3
    assert event.parents_with_living_children == 1
    assert event.max_living_children == 2
