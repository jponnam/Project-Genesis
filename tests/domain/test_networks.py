"""Unit tests for social-network helpers and census."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentId,
    AgentStatus,
    Health,
    Relationship,
    SimulationConfig,
    World,
    census_networks,
    degrees,
    directed_strength,
    set_bond,
    set_relationship,
    strongest_tie,
    weak_components,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_directed_strength_extremes() -> None:
    """Bond strength maps max affinity/trust to 1 and min to 0."""
    other = AgentId(value=1)
    assert (
        directed_strength(Relationship(other_id=other, affinity=1.0, trust=1.0)) == 1.0
    )
    assert (
        directed_strength(Relationship(other_id=other, affinity=-1.0, trust=0.0)) == 0.0
    )


def test_census_no_bonds_all_isolated() -> None:
    """Living agents without bonds form one isolate component each."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    snap = census_networks(world)
    assert snap.living_agent_count == 3
    assert snap.directed_edge_count == 0
    assert snap.undirected_edge_count == 0
    assert snap.reciprocal_pair_count == 0
    assert snap.reciprocity_rate == 0.0
    assert snap.mean_degree == 0.0
    assert snap.isolated_count == 3
    assert snap.component_count == 3
    assert snap.largest_component_size == 1
    assert snap.density == 0.0
    assert snap.strongest_tie is None
    assert census_networks(world) == snap


def test_one_directed_edge_counts() -> None:
    """A single directed bond creates one undirected edge without reciprocity."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    world = set_relationship(world, 0, 1, affinity=1.0, trust=1.0)
    assert world is not None
    snap = census_networks(world)
    assert snap.directed_edge_count == 1
    assert snap.undirected_edge_count == 1
    assert snap.reciprocal_pair_count == 0
    assert snap.reciprocity_bps == 0
    rows = {row.agent_id.value: row for row in degrees(world)}
    assert rows[0].out_degree == 1
    assert rows[0].in_degree == 0
    assert rows[0].undirected_degree == 1
    assert rows[1].in_degree == 1
    assert snap.component_count == 1
    assert snap.largest_component_size == 2
    assert snap.density == 1.0
    assert snap.density_bps == 10_000
    tie = strongest_tie(world)
    assert tie is not None
    assert tie.from_id.value == 0
    assert tie.to_id.value == 1
    assert tie.strength == 1.0
    assert tie.reciprocal is False


def test_mutual_bond_is_reciprocal() -> None:
    """Mutual directed bonds yield full reciprocity on one undirected edge."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    world = set_relationship(world, 0, 1, affinity=0.0, trust=0.5)
    assert world is not None
    world = set_relationship(world, 1, 0, affinity=0.0, trust=0.5)
    assert world is not None
    snap = census_networks(world)
    assert snap.directed_edge_count == 2
    assert snap.undirected_edge_count == 1
    assert snap.reciprocal_pair_count == 1
    assert snap.reciprocity_rate == 1.0
    assert snap.reciprocity_bps == 10_000
    assert snap.mean_degree == 1.0
    tie = snap.strongest_tie
    assert tie is not None
    assert tie.reciprocal is True


def test_disjoint_pairs_form_two_components() -> None:
    """Two disjoint edges yield two components of size 2."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
        Agent.create(agent_id=3, name="D"),
    )
    world = set_relationship(world, 0, 1, affinity=0.2, trust=0.5)
    assert world is not None
    world = set_relationship(world, 2, 3, affinity=0.2, trust=0.5)
    assert world is not None
    components = weak_components(world)
    assert len(components) == 2
    assert components[0].member_ids[0].value == 0
    assert components[1].member_ids[0].value == 2
    snap = census_networks(world)
    assert snap.component_count == 2
    assert snap.largest_component_size == 2
    assert snap.mean_component_size == 2.0


def test_triangle_has_full_density() -> None:
    """An undirected triangle among three agents has density 1."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 0, 1, affinity=0.0, trust=0.5)
    assert world is not None
    world = set_relationship(world, 1, 2, affinity=0.0, trust=0.5)
    assert world is not None
    world = set_relationship(world, 2, 0, affinity=0.0, trust=0.5)
    assert world is not None
    snap = census_networks(world)
    assert snap.undirected_edge_count == 3
    assert snap.density == 1.0
    assert snap.density_bps == 10_000
    assert snap.component_count == 1
    assert snap.isolated_count == 0


def test_dead_peer_bonds_are_ignored() -> None:
    """Bonds involving dead agents do not count as living network edges."""
    living = Agent.create(agent_id=0, name="A")
    peer = set_bond(Agent.create(agent_id=1, name="B"), 0, affinity=1.0, trust=1.0)
    assert peer is not None
    dead = peer.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    living = set_bond(living, 1, affinity=1.0, trust=1.0)
    assert living is not None
    world = _world(living, dead)
    snap = census_networks(world)
    assert snap.living_agent_count == 1
    assert snap.directed_edge_count == 0
    assert snap.undirected_edge_count == 0
    assert snap.isolated_count == 1


def test_strongest_tie_prefers_higher_strength_then_smaller_ids() -> None:
    """Strongest-tie selection uses strength first, then smaller pair ids."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 0, 1, affinity=0.0, trust=0.5)
    assert world is not None
    world = set_relationship(world, 1, 2, affinity=1.0, trust=1.0)
    assert world is not None
    tie = strongest_tie(world)
    assert tie is not None
    assert tie.from_id.value == 1
    assert tie.to_id.value == 2
    assert tie.strength == 1.0

    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 0, 1, affinity=1.0, trust=1.0)
    assert world is not None
    world = set_relationship(world, 1, 2, affinity=1.0, trust=1.0)
    assert world is not None
    tie = strongest_tie(world)
    assert tie is not None
    assert tie.from_id.value == 0
    assert tie.to_id.value == 1
