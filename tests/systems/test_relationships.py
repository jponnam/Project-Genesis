"""Unit tests for the RelationshipSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    RelationshipsObserved,
    RelationshipUpdated,
    SimulationConfig,
    World,
    get_bond,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import RelationshipConfig, RelationshipSystem


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_observe_emits_relationships_observed_without_mutating() -> None:
    """observe publishes one census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = RelationshipSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, RelationshipsObserved)
    ]
    assert len(events) == 1
    assert events[0].bond_count == 0
    assert events[0].agents_with_bonds == 0
    assert events[0].living_bond_count == 0
    assert events[0].mean_affinity == 0.0
    assert events[0].min_affinity is None


def test_observe_can_suppress_events() -> None:
    """RelationshipConfig.emit_events=False skips publishing."""
    world = _world(Agent.create(agent_id=0, name="A"))
    bus = EventBus()
    RelationshipSystem(RelationshipConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_set_bond_emits_relationship_updated() -> None:
    """Successful set_bond mutates affinity and emits RelationshipUpdated."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    bus = EventBus()
    system = RelationshipSystem()
    updated = system.set_bond(world, 0, 1, affinity=0.4, trust=0.8, bus=bus)
    source = updated.agent_by_id(0)
    assert source is not None
    bond = get_bond(source, 1)
    assert bond is not None
    assert bond.affinity == 0.4
    assert bond.trust == 0.8
    events = [event for event in bus.history if isinstance(event, RelationshipUpdated)]
    assert len(events) == 1
    assert events[0].created is True
    assert events[0].from_agent_id.value == 0
    assert events[0].to_agent_id.value == 1

    bus2 = EventBus()
    again = system.set_bond(updated, 0, 1, affinity=0.6, bus=bus2)
    source_again = again.agent_by_id(0)
    assert source_again is not None
    updated_bond = get_bond(source_again, 1)
    assert updated_bond is not None
    assert updated_bond.affinity == 0.6
    events2 = [
        event for event in bus2.history if isinstance(event, RelationshipUpdated)
    ]
    assert events2[0].created is False


def test_adjust_affinity_creates_when_missing() -> None:
    """adjust_affinity creates a bond and reports created=True."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    bus = EventBus()
    updated = RelationshipSystem().adjust_affinity(world, 0, 1, 0.3, bus=bus)
    source = updated.agent_by_id(0)
    assert source is not None
    bond = get_bond(source, 1)
    assert bond is not None
    assert bond.affinity == 0.3
    events = [event for event in bus.history if isinstance(event, RelationshipUpdated)]
    assert events[0].created is True


def test_illegal_set_bond_is_noop() -> None:
    """Illegal updates leave the world and bus unchanged."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    bus = EventBus()
    updated = RelationshipSystem().set_bond(world, 0, 0, affinity=0.5, bus=bus)
    assert updated == world
    assert bus.history == ()


def test_clear_bond_removes_directed_edge() -> None:
    """clear_bond removes an existing outgoing bond."""
    system = RelationshipSystem()
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    world = system.set_bond(world, 0, 1, affinity=0.5)
    cleared = system.clear_bond(world, 0, 1)
    source = cleared.agent_by_id(0)
    assert source is not None
    assert get_bond(source, 1) is None


def test_adjust_trust_emits_relationship_updated() -> None:
    """adjust_trust mutates trust and emits RelationshipUpdated."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    bus = EventBus()
    updated = RelationshipSystem().adjust_trust(world, 0, 1, 0.2, bus=bus)
    source = updated.agent_by_id(0)
    assert source is not None
    bond = get_bond(source, 1)
    assert bond is not None
    assert bond.trust == 0.7
    assert bond.affinity == 0.0
    events = [event for event in bus.history if isinstance(event, RelationshipUpdated)]
    assert len(events) == 1
    assert events[0].created is True
    assert events[0].trust == 0.7
