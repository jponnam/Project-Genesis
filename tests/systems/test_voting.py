"""Unit tests for the VoteSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    ElectionResolved,
    ElectionsObserved,
    Government,
    SimulationConfig,
    World,
    set_relationship,
)
from civitas.domain.ids import AgentId
from civitas.engine import EventBus, WorldFactory
from civitas.systems import VoteConfig, VoteSystem


def test_observe_emits_elections_observed_without_mutating_world() -> None:
    """observe publishes one election census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = VoteSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, ElectionsObserved)]
    assert len(events) == 1
    assert events[0].election_count == 0
    assert events[0].closed_count == 0
    assert events[0].governments_with_elections == 0


def test_observe_can_suppress_events() -> None:
    """VoteConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    VoteSystem(VoteConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_conduct_emits_election_resolved_and_sets_leader() -> None:
    """conduct archives an election, appoints a leader, and emits resolve."""
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(
            Agent.create(agent_id=0, name="A"),
            Agent.create(agent_id=1, name="B"),
        ),
    )
    world = set_relationship(world, 0, 1, affinity=1.0, trust=1.0)
    assert world is not None
    bus = EventBus()
    updated = VoteSystem().conduct(world, 0, bus=bus)
    assert updated.governments[0].leader_id == AgentId(value=1)
    assert len(updated.elections) == 1
    resolved = [event for event in bus.history if isinstance(event, ElectionResolved)]
    assert len(resolved) == 1
    assert resolved[0].winner_id == AgentId(value=1)
    assert resolved[0].franchise_count == 2
    assert resolved[0].ballot_count == 2


def test_conduct_unknown_government_is_noop() -> None:
    """Unknown governments leave the world and bus unchanged."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = VoteSystem().conduct(world, 99, bus=bus)
    assert updated == world
    assert bus.history == ()
