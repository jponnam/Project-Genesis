"""Unit tests for the NetworkSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    NetworksObserved,
    SimulationConfig,
    World,
    set_relationship,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import NetworkConfig, NetworkSystem


def test_observe_emits_networks_observed_without_mutating_world() -> None:
    """observe publishes one network census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=4))
    bus = EventBus()
    updated = NetworkSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, NetworksObserved)]
    assert len(events) == 1
    assert events[0].living_agent_count == 4
    assert events[0].directed_edge_count == 0
    assert events[0].component_count == 4
    assert events[0].isolated_count == 4
    assert events[0].strongest_from_id is None


def test_observe_can_suppress_events() -> None:
    """NetworkConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    NetworkSystem(NetworkConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_observe_reports_reciprocal_component() -> None:
    """Census event reflects mutual living bonds."""
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(
            Agent.create(agent_id=0, name="A"),
            Agent.create(agent_id=1, name="B"),
        ),
    )
    world = set_relationship(world, 0, 1, affinity=1.0, trust=1.0)
    assert world is not None
    world = set_relationship(world, 1, 0, affinity=1.0, trust=1.0)
    assert world is not None
    bus = EventBus()
    NetworkSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, NetworksObserved)]
    event = events[0]
    assert event.directed_edge_count == 2
    assert event.undirected_edge_count == 1
    assert event.reciprocal_pair_count == 1
    assert event.reciprocity_bps == 10_000
    assert event.component_count == 1
    assert event.largest_component_size == 2
    assert event.strongest_from_id is not None
    assert event.strongest_from_id.value == 0
    assert event.strongest_to_id is not None
    assert event.strongest_to_id.value == 1
    assert event.strongest_strength == 1.0
