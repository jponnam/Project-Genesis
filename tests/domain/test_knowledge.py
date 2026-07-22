"""Unit tests for knowledge diffusion helpers."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_POTTERY,
    FIRE_FACT,
    POTTERY_FACT,
    Agent,
    Knowledge,
    KnowledgeSource,
    SimulationConfig,
    World,
    agents_knowing,
    apply_knowledge_diffusion,
    bootstrap_discovered_knowledge,
    can_learn_from_teacher,
    census_knowledge,
    default_innovations,
    default_research_progress,
    default_technologies,
    diffuse_knowledge,
    discover_technology,
    grant_knowledge,
    set_relationship,
)

_FIRE = Knowledge(facts=frozenset({FIRE_FACT}))
_FIRE_AND_POTTERY = Knowledge(facts=frozenset({FIRE_FACT, POTTERY_FACT}))


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        agents=agents,
    )


def test_knowledge_learn_is_idempotent() -> None:
    """Learning an already-known fact returns the same knowledge object."""
    base = Knowledge(facts=frozenset({FIRE_FACT}))
    assert base.learn(FIRE_FACT) is base
    learned = Knowledge().learn(FIRE_FACT)
    assert learned.knows(FIRE_FACT)


def test_bootstrap_grants_pottery_to_lowest_living_id() -> None:
    """Bootstrap grants missing discovered facts to the lowest living agent."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE),
    )
    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    world, gains = bootstrap_discovered_knowledge(discovered)
    assert len(gains) == 1
    assert gains[0].source is KnowledgeSource.BOOTSTRAP
    assert gains[0].agent_id.value == 0
    assert gains[0].fact == POTTERY_FACT
    assert world.agents[0].knowledge.knows(POTTERY_FACT)
    assert not world.agents[1].knowledge.knows(POTTERY_FACT)


def test_diffuse_knowledge_teaches_co_located_peers() -> None:
    """Peer diffusion teaches one learner per knower by default."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE),
        Agent.create(agent_id=2, name="C", knowledge=_FIRE),
    )
    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    world, gains = diffuse_knowledge(discovered, teachings_per_knower=1)
    assert len(gains) == 1
    assert gains[0].source is KnowledgeSource.PEER
    assert gains[0].teacher_id is not None
    assert gains[0].teacher_id.value == 0
    assert gains[0].agent_id.value == 1
    assert world.agents[1].knowledge.knows(POTTERY_FACT)
    assert not world.agents[2].knowledge.knows(POTTERY_FACT)


def test_diffuse_knowledge_requires_learner_trust() -> None:
    """Low learner→teacher trust blocks peer teaching."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE),
    )
    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    bonded = set_relationship(discovered, 1, 0, affinity=0.0, trust=0.1)
    assert bonded is not None
    teacher = bonded.agents[0]
    learner = bonded.agents[1]
    assert can_learn_from_teacher(learner, teacher, min_trust=0.5) is False
    world, gains = diffuse_knowledge(bonded, teachings_per_knower=1, min_trust=0.5)
    assert gains == ()
    assert not world.agents[1].knowledge.knows(POTTERY_FACT)


def test_apply_knowledge_diffusion_bootstraps_then_diffuses() -> None:
    """Full apply bootstraps pottery then spreads one peer hop."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE),
    )
    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    world, gains = apply_knowledge_diffusion(discovered)
    assert [gain.source for gain in gains] == [
        KnowledgeSource.BOOTSTRAP,
        KnowledgeSource.PEER,
    ]
    assert all(agent.knowledge.knows(POTTERY_FACT) for agent in world.agents)


def test_census_knowledge_counts_coverage() -> None:
    """Census reports fire coverage and zero pottery before discovery."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE),
    )
    snap = census_knowledge(world)
    assert snap.living_count == 2
    assert snap.discovered_technology_count == 1
    assert snap.fire_knower_count == 2
    assert snap.pottery_knower_count == 0
    assert snap.total_fact_instances == 2
    assert snap.coverage_bps == 10_000
    assert agents_knowing(world, FIRE_FACT)[0].agent_id.value == 0
    assert grant_knowledge(world, 0, FIRE_FACT) == world
