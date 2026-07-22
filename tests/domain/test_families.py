"""Unit tests for kinship helpers and family census."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Health,
    SimulationConfig,
    World,
    census_families,
    children_of,
    generation_of,
    parent_of,
    root_of,
    siblings_of,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_parent_children_siblings_and_root() -> None:
    """Parentage helpers walk recorded birth links."""
    founder = Agent.create(agent_id=0, name="A")
    child_a = Agent.create(agent_id=1, name="B", parent_id=0)
    child_b = Agent.create(agent_id=2, name="C", parent_id=0)
    grand = Agent.create(agent_id=3, name="D", parent_id=1)
    world = _world(founder, child_a, child_b, grand)

    assert parent_of(world, 1) is not None
    assert parent_of(world, 1).agent_id.value == 0  # type: ignore[union-attr]
    assert [agent.agent_id.value for agent in children_of(world, 0)] == [1, 2]
    assert [agent.agent_id.value for agent in siblings_of(world, 1)] == [2]
    assert root_of(world, 3) is not None
    assert root_of(world, 3).value == 0  # type: ignore[union-attr]
    assert generation_of(world, 0) == 0
    assert generation_of(world, 1) == 1
    assert generation_of(world, 3) == 2


def test_census_families_lineages_and_orphans() -> None:
    """Census reports founders, orphans, and lineage sizes."""
    founder = Agent.create(agent_id=0, name="A")
    other = Agent.create(agent_id=1, name="B")
    child = Agent.create(agent_id=2, name="C", parent_id=0)
    orphan = Agent.create(agent_id=3, name="D", parent_id=9)
    dead_parent = Agent.create(agent_id=4, name="E").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    orphan_of_dead = Agent.create(agent_id=5, name="F", parent_id=4)
    world = _world(founder, other, child, orphan, dead_parent, orphan_of_dead)

    snap = census_families(world)
    assert snap.living_agent_count == 5
    assert snap.founder_count == 2  # 0 and 1
    assert snap.parented_count == 3  # 2, 3, 5
    assert snap.orphan_count == 2  # 3 (missing) and 5 (dead parent)
    assert snap.living_with_living_parent == 1
    assert snap.lineage_count == 4  # roots 0,1,3,5 (broken/orphan roots)
    assert snap.max_generation_depth == 1
    assert snap.parents_with_living_children == 1
    assert snap.mean_living_children == 1.0
    assert snap.max_living_children == 1
    assert census_families(world) == snap


def test_children_of_can_include_dead() -> None:
    """living_only=False includes dead children."""
    parent = Agent.create(agent_id=0, name="A")
    living = Agent.create(agent_id=1, name="B", parent_id=0)
    dead = Agent.create(agent_id=2, name="C", parent_id=0).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(parent, living, dead)
    assert len(children_of(world, 0, living_only=True)) == 1
    assert len(children_of(world, 0, living_only=False)) == 2
