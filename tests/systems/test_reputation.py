"""Unit tests for the ReputationSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    ReputationObserved,
    SimulationConfig,
    World,
    set_relationship,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import ReputationConfig, ReputationSystem


def test_observe_emits_reputation_observed_without_mutating_world() -> None:
    """observe publishes one reputation census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=4))
    bus = EventBus()
    updated = ReputationSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, ReputationObserved)]
    assert len(events) == 1
    assert events[0].living_agent_count == 4
    assert events[0].mean_standing == 0.0
    assert events[0].agents_with_inbound_bonds == 0
    assert events[0].top_agent_id is not None
    assert events[0].top_standing == 0.0


def test_observe_can_suppress_events() -> None:
    """ReputationConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    ReputationSystem(ReputationConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_observe_reports_top_agent_from_inbound_bonds() -> None:
    """Census event surfaces the highest-standing agent id."""
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(
            Agent.create(agent_id=0, name="A"),
            Agent.create(agent_id=1, name="B"),
        ),
    )
    world = set_relationship(world, 1, 0, affinity=1.0, trust=1.0)
    assert world is not None
    bus = EventBus()
    ReputationSystem().observe(world, bus=bus)
    events = [
        event for event in bus.history if isinstance(event, ReputationObserved)
    ]
    event = events[0]
    assert event.top_agent_id is not None
    assert event.top_agent_id.value == 0
    assert event.top_standing == 0.75
    assert event.agents_with_inbound_bonds == 1
