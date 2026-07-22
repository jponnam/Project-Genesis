"""Unit tests for reputation standing helpers and census."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    REPUTATION_RECIPROCITY_WEIGHT,
    REPUTATION_TRUST_WEIGHT,
    Agent,
    AgentStatus,
    Health,
    SimulationConfig,
    World,
    census_reputation,
    inbound_bonds,
    set_bond,
    set_relationship,
    standing_of,
    standings,
    top_standing,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_standing_zero_without_inbound_bonds() -> None:
    """Living agents with no inbound peers score standing 0."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    row = standing_of(world, 0)
    assert row is not None
    assert row.standing == 0.0
    assert row.standing_bps == 0
    assert row.inbound_bond_count == 0


def test_standing_from_inbound_bond_without_reciprocity() -> None:
    """One inbound max bond without reciprocity yields 0.75 standing."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    updated = set_relationship(world, 1, 0, affinity=1.0, trust=1.0)
    assert updated is not None
    row = standing_of(updated, 0)
    assert row is not None
    assert row.standing == 0.75
    assert row.standing_bps == 7500
    assert row.inbound_bond_count == 1
    assert len(inbound_bonds(updated, 0)) == 1


def test_standing_reciprocity_bonus() -> None:
    """Reciprocal outbound bond adds the reciprocity weight."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    world = set_relationship(world, 1, 0, affinity=1.0, trust=1.0)
    assert world is not None
    world = set_relationship(world, 0, 1, affinity=0.0, trust=0.5)
    assert world is not None
    row = standing_of(world, 0)
    assert row is not None
    assert row.standing == 1.0
    assert row.standing_bps == 10_000
    assert REPUTATION_TRUST_WEIGHT + REPUTATION_RECIPROCITY_WEIGHT == 1.0


def test_standing_ignores_dead_peer_bonds() -> None:
    """Inbound bonds from dead peers do not count."""
    peer = set_bond(Agent.create(agent_id=1, name="B"), 0, affinity=1.0, trust=1.0)
    assert peer is not None
    dead = peer.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(Agent.create(agent_id=0, name="A"), dead)
    row = standing_of(world, 0)
    assert row is not None
    assert row.standing == 0.0
    assert row.inbound_bond_count == 0
    assert standing_of(world, 1) is None


def test_standing_means_multiple_inbound() -> None:
    """Multiple inbound contributions are averaged."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 1, 0, affinity=1.0, trust=1.0)
    assert world is not None
    world = set_relationship(world, 2, 0, affinity=-1.0, trust=0.0)
    assert world is not None
    row = standing_of(world, 0)
    assert row is not None
    # 0.75 from B, 0.0 from C → mean 0.375
    assert row.standing == 0.375
    assert row.standing_bps == 3750
    assert row.inbound_bond_count == 2


def test_census_reputation_and_top_standing() -> None:
    """Census aggregates inequality metrics; top prefers higher standing."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 1, 0, affinity=1.0, trust=1.0)
    assert world is not None
    world = set_relationship(world, 2, 1, affinity=0.0, trust=0.5)
    assert world is not None
    snap = census_reputation(world)
    assert snap.living_agent_count == 3
    assert snap.agents_with_inbound_bonds == 2
    rows = standings(world)
    assert len(rows) == 3
    top = top_standing(rows)
    assert top is not None
    assert top.agent_id.value == 0
    assert snap.top_standing_share_bps > 0
    assert snap.gini_standing_bps >= 0
    assert census_reputation(world) == snap


def test_top_standing_tie_breaks_by_smaller_agent_id() -> None:
    """Equal standing prefers the smaller agent id."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 2, 0, affinity=1.0, trust=1.0)
    assert world is not None
    world = set_relationship(world, 2, 1, affinity=1.0, trust=1.0)
    assert world is not None
    top = top_standing(standings(world))
    assert top is not None
    assert top.agent_id.value == 0
