"""Unit tests for domain relationship helpers and census."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentId,
    AgentStatus,
    Health,
    Location,
    LocationKind,
    Needs,
    Relationship,
    RelationshipMap,
    SimulationConfig,
    World,
    adjust_affinity,
    adjust_relationship,
    adjust_relationship_trust,
    adjust_trust,
    apply_socialize,
    bond_count,
    can_socialize,
    census_relationships,
    clamp_affinity,
    clear_bond,
    clear_relationship,
    get_bond,
    set_bond,
    set_relationship,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_clamp_affinity_bounds() -> None:
    """Affinity clamps to [-1, 1] with stable rounding."""
    assert clamp_affinity(2.0) == 1.0
    assert clamp_affinity(-3.0) == -1.0
    assert clamp_affinity(0.1234567) == 0.123457


def test_relationship_map_upsert_and_without() -> None:
    """Upsert replaces by target id and keeps ascending other_id order."""
    first = Relationship(other_id=AgentId(value=2), affinity=0.1)
    second = Relationship(other_id=AgentId(value=1), affinity=0.2)
    rel_map = RelationshipMap().upsert(first).upsert(second)
    assert [bond.other_id.value for bond in rel_map.bonds] == [1, 2]
    replaced = rel_map.upsert(
        Relationship(other_id=AgentId(value=2), affinity=0.9, trust=0.8)
    )
    assert replaced.toward(2) is not None
    assert replaced.toward(2).affinity == 0.9
    assert replaced.toward(2).trust == 0.8
    cleared = replaced.without(1)
    assert cleared.toward(1) is None
    assert cleared.toward(2) is not None


def test_set_and_adjust_bond_on_agent() -> None:
    """Living agents can create and adjust directed bonds."""
    agent = Agent.create(agent_id=0, name="A")
    bonded = set_bond(agent, 1, affinity=0.25, trust=0.7)
    assert bonded is not None
    bond = get_bond(bonded, 1)
    assert bond is not None
    assert bond.affinity == 0.25
    assert bond.trust == 0.7

    warmer = adjust_affinity(bonded, 1, 0.5)
    assert warmer is not None
    assert get_bond(warmer, 1).affinity == 0.75  # type: ignore[union-attr]
    assert get_bond(warmer, 1).trust == 0.7  # type: ignore[union-attr]

    created = adjust_affinity(agent, 2, -0.4)
    assert created is not None
    assert get_bond(created, 2).affinity == -0.4  # type: ignore[union-attr]


def test_set_bond_rejects_self_and_dead() -> None:
    """Self-bonds and dead sources are illegal."""
    living = Agent.create(agent_id=0, name="A")
    dead = living.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert set_bond(living, 0, affinity=0.1) is None
    assert set_bond(dead, 1, affinity=0.1) is None
    assert clear_bond(dead, 1) is None


def test_world_relationship_helpers() -> None:
    """World helpers mutate only legal living-to-living directed bonds."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    updated = set_relationship(world, 0, 1, affinity=0.5)
    assert updated is not None
    assert get_bond(updated.agent_by_id(0), 1).affinity == 0.5  # type: ignore[union-attr]
    warmer = adjust_relationship(updated, 0, 1, 0.2)
    assert warmer is not None
    assert get_bond(warmer.agent_by_id(0), 1).affinity == 0.7  # type: ignore[union-attr]
    cleared = clear_relationship(warmer, 0, 1)
    assert cleared is not None
    assert get_bond(cleared.agent_by_id(0), 1) is None  # type: ignore[arg-type]


def test_world_relationship_rejects_illegal_cases() -> None:
    """Missing, self, and dead endpoints block mutations."""
    dead = Agent.create(agent_id=1, name="B").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(Agent.create(agent_id=0, name="A"), dead)
    assert set_relationship(world, 0, 0, affinity=0.1) is None
    assert set_relationship(world, 0, 1, affinity=0.1) is None
    assert set_relationship(world, 0, 9, affinity=0.1) is None
    assert adjust_relationship(world, 0, 1, 0.1) is None


def test_census_relationships_counts_and_affinity_stats() -> None:
    """Census reports bond counts and living-only living_bond_count."""
    a = set_bond(Agent.create(agent_id=0, name="A"), 1, affinity=0.2, trust=0.4)
    b = set_bond(Agent.create(agent_id=1, name="B"), 0, affinity=-0.4, trust=0.6)
    assert a is not None and b is not None
    dead = set_bond(Agent.create(agent_id=2, name="C"), 0, affinity=1.0, trust=0.9)
    assert dead is not None
    dead = dead.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(a, b, dead)
    snap = census_relationships(world)
    assert snap.bond_count == 3
    assert snap.agents_with_bonds == 3
    assert snap.living_bond_count == 2
    assert snap.mean_affinity == pytest.approx(round((0.2 - 0.4 + 1.0) / 3, 6))
    assert snap.min_affinity == -0.4
    assert snap.max_affinity == 1.0
    assert snap.mean_trust == pytest.approx(round((0.4 + 0.6 + 0.9) / 3, 6))
    assert snap.min_trust == 0.4
    assert snap.max_trust == 0.9
    assert bond_count(world) == 3


def test_adjust_trust_preserves_affinity() -> None:
    """Trust adjustments keep affinity and create bonds when missing."""
    agent = Agent.create(agent_id=0, name="A")
    bonded = set_bond(agent, 1, affinity=0.3, trust=0.5)
    assert bonded is not None
    warmer = adjust_trust(bonded, 1, 0.2)
    assert warmer is not None
    bond = get_bond(warmer, 1)
    assert bond is not None
    assert bond.affinity == 0.3
    assert bond.trust == 0.7
    created = adjust_trust(agent, 2, 0.1)
    assert created is not None
    new_bond = get_bond(created, 2)
    assert new_bond is not None
    assert new_bond.affinity == 0.0
    assert new_bond.trust == 0.6


def test_can_socialize_and_apply_socialize() -> None:
    """Legal SOCIALIZE restores social need and raises mutual bonds."""
    actor = Agent.create(agent_id=0, name="A").model_copy(
        update={
            "needs": Needs(food=1.0, water=1.0, energy=1.0, social=0.4, safety=1.0),
        }
    )
    partner = Agent.create(agent_id=1, name="B")
    world = _world(actor, partner)
    assert can_socialize(world, 0, 1) is True
    updated = apply_socialize(world, 0, 1)
    assert updated is not None
    new_actor = updated.agent_by_id(0)
    new_partner = updated.agent_by_id(1)
    assert new_actor is not None and new_partner is not None
    assert new_actor.needs.social == pytest.approx(0.55)
    actor_bond = get_bond(new_actor, 1)
    partner_bond = get_bond(new_partner, 0)
    assert actor_bond is not None and partner_bond is not None
    assert actor_bond.affinity == 0.05
    assert actor_bond.trust == 0.55
    assert partner_bond.affinity == 0.05
    assert partner_bond.trust == 0.55


def test_can_socialize_rejects_illegal_partners() -> None:
    """Distant, dead, missing, and self partners are illegal."""
    plain = Agent.create(agent_id=1, name="B", location_id=1)
    elsewhere = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION, elsewhere),
        agents=(Agent.create(agent_id=0, name="A"), plain),
    )
    assert can_socialize(world, 0, 1) is False
    assert apply_socialize(world, 0, 1) is None
    assert can_socialize(world, 0, 0) is False
    dead = plain.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    dead_world = world.with_agent(dead)
    assert adjust_relationship_trust(dead_world, 0, 1, 0.1) is None
