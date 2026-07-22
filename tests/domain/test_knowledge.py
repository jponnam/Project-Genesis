"""Unit tests for knowledge diffusion helpers."""

from __future__ import annotations

from civitas.domain import (
    ASTRONOMY_FACT,
    CAMP_ASTRONOMY,
    CAMP_IRRIGATION,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_MATHEMATICS,
    CAMP_METALLURGY,
    CAMP_PHILOSOPHY,
    CAMP_POTTERY,
    CAMP_RHETORIC,
    CAMP_SCRIBE,
    CAMP_WRITING,
    DEFAULT_TEACHINGS_PER_KNOWER,
    FIRE_FACT,
    IRRIGATION_FACT,
    LOGIC_FACT,
    MATHEMATICS_FACT,
    METALLURGY_FACT,
    PHILOSOPHY_FACT,
    POTTERY_FACT,
    RHETORIC_FACT,
    WRITING_FACT,
    Agent,
    City,
    CityKind,
    Government,
    Infrastructure,
    InfrastructureKind,
    Institution,
    InstitutionKind,
    Knowledge,
    KnowledgeSource,
    Law,
    LawKind,
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
    default_world_map,
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


def test_ethics_lowers_min_teach_trust_for_subject_learners() -> None:
    """Active ETHICS lets subject learners learn at trust just below the base floor."""
    bare = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        agents=(
            Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
            Agent.create(agent_id=1, name="B", knowledge=_FIRE),
        ),
    )
    discovered = discover_technology(bare, CAMP_POTTERY.technology_id)
    assert discovered is not None
    bonded = set_relationship(discovered, 1, 0, affinity=0.0, trust=0.46)
    assert bonded is not None
    without, blocked = diffuse_knowledge(bonded, teachings_per_knower=1, min_trust=0.5)
    assert blocked == ()
    assert not without.agents[1].knowledge.knows(POTTERY_FACT)

    with_ethics = bonded.model_copy(
        update={"laws": (Law.create(0, 0, "Camp Ethics", LawKind.ETHICS),)}
    )
    taught, gains = diffuse_knowledge(
        with_ethics, teachings_per_knower=1, min_trust=0.5
    )
    assert len(gains) == 1
    assert gains[0].agent_id.value == 1
    assert taught.agents[1].knowledge.knows(POTTERY_FACT)


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


def test_bootstrap_uses_irrigation_technology_fact() -> None:
    """Discovered irrigation bootstraps through the generic tech fact mapping."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE_AND_POTTERY),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    world, gains = bootstrap_discovered_knowledge(with_irrigation)
    assert len(gains) == 1
    assert gains[0].fact == IRRIGATION_FACT
    assert world.agents[0].knowledge.knows(IRRIGATION_FACT)


def test_bootstrap_uses_metallurgy_technology_fact() -> None:
    """Discovered metallurgy bootstraps through the generic tech fact mapping."""
    prior = Knowledge(facts=frozenset({FIRE_FACT, POTTERY_FACT, IRRIGATION_FACT}))
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    world, gains = bootstrap_discovered_knowledge(with_metallurgy)
    assert len(gains) == 1
    assert gains[0].fact == METALLURGY_FACT
    assert world.agents[0].knowledge.knows(METALLURGY_FACT)


def test_bootstrap_uses_writing_technology_fact() -> None:
    """Discovered writing bootstraps through the generic tech fact mapping."""
    prior = Knowledge(
        facts=frozenset({FIRE_FACT, POTTERY_FACT, IRRIGATION_FACT, METALLURGY_FACT})
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    world, gains = bootstrap_discovered_knowledge(with_writing)
    assert len(gains) == 1
    assert gains[0].fact == WRITING_FACT
    assert world.agents[0].knowledge.knows(WRITING_FACT)


def test_bootstrap_uses_mathematics_technology_fact() -> None:
    """Discovered mathematics bootstraps through the generic tech fact mapping."""
    prior = Knowledge(
        facts=frozenset(
            {FIRE_FACT, POTTERY_FACT, IRRIGATION_FACT, METALLURGY_FACT, WRITING_FACT}
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    world, gains = bootstrap_discovered_knowledge(with_math)
    assert len(gains) == 1
    assert gains[0].fact == MATHEMATICS_FACT
    assert world.agents[0].knowledge.knows(MATHEMATICS_FACT)


def test_bootstrap_uses_astronomy_technology_fact() -> None:
    """Discovered astronomy bootstraps through the generic tech fact mapping."""
    prior = Knowledge(
        facts=frozenset(
            {
                FIRE_FACT,
                POTTERY_FACT,
                IRRIGATION_FACT,
                METALLURGY_FACT,
                WRITING_FACT,
                MATHEMATICS_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    world, gains = bootstrap_discovered_knowledge(with_astronomy)
    assert len(gains) == 1
    assert gains[0].fact == ASTRONOMY_FACT
    assert world.agents[0].knowledge.knows(ASTRONOMY_FACT)


def test_bootstrap_uses_philosophy_technology_fact() -> None:
    """Discovered philosophy bootstraps through the generic tech fact mapping."""
    prior = Knowledge(
        facts=frozenset(
            {
                FIRE_FACT,
                POTTERY_FACT,
                IRRIGATION_FACT,
                METALLURGY_FACT,
                WRITING_FACT,
                MATHEMATICS_FACT,
                ASTRONOMY_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    world, gains = bootstrap_discovered_knowledge(with_philosophy)
    assert len(gains) == 1
    assert gains[0].fact == PHILOSOPHY_FACT
    assert world.agents[0].knowledge.knows(PHILOSOPHY_FACT)


def test_bootstrap_uses_logic_technology_fact() -> None:
    """Discovered logic bootstraps through the generic tech fact mapping."""
    prior = Knowledge(
        facts=frozenset(
            {
                FIRE_FACT,
                POTTERY_FACT,
                IRRIGATION_FACT,
                METALLURGY_FACT,
                WRITING_FACT,
                MATHEMATICS_FACT,
                ASTRONOMY_FACT,
                PHILOSOPHY_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    world, gains = bootstrap_discovered_knowledge(with_logic)
    assert len(gains) == 1
    assert gains[0].fact == LOGIC_FACT
    assert world.agents[0].knowledge.knows(LOGIC_FACT)


def test_bootstrap_uses_rhetoric_technology_fact() -> None:
    """Discovered rhetoric bootstraps through the generic tech fact mapping."""
    prior = Knowledge(
        facts=frozenset(
            {
                FIRE_FACT,
                POTTERY_FACT,
                IRRIGATION_FACT,
                METALLURGY_FACT,
                WRITING_FACT,
                MATHEMATICS_FACT,
                ASTRONOMY_FACT,
                PHILOSOPHY_FACT,
                LOGIC_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    with_rhetoric = discover_technology(with_logic, CAMP_RHETORIC.technology_id)
    assert with_rhetoric is not None
    world, gains = bootstrap_discovered_knowledge(with_rhetoric)
    assert len(gains) == 1
    assert gains[0].fact == RHETORIC_FACT
    assert world.agents[0].knowledge.knows(RHETORIC_FACT)


def test_active_scribe_raises_teachings_per_knower() -> None:
    """Active scribe lets each knower teach one extra peer per diffusion pass."""
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
        Agent.create(agent_id=1, name="B", knowledge=_FIRE),
        Agent.create(agent_id=2, name="C", knowledge=_FIRE),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    without_scribe, gains = diffuse_knowledge(
        with_pottery, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    assert len(gains) == 1
    assert without_scribe.agents[1].knowledge.knows(POTTERY_FACT)
    assert not without_scribe.agents[2].knowledge.knows(POTTERY_FACT)

    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    innovations = tuple(
        active_scribe if item.innovation_id == CAMP_SCRIBE.innovation_id else item
        for item in with_writing.innovations
    )
    with_scribe_world = with_writing.model_copy(update={"innovations": innovations})
    with_scribe, gains = diffuse_knowledge(
        with_scribe_world, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    assert len(gains) == 2
    assert with_scribe.agents[1].knowledge.knows(POTTERY_FACT)
    assert with_scribe.agents[2].knowledge.knows(POTTERY_FACT)


def test_scriptorium_stacks_with_scribe_in_diffusion() -> None:
    """Scriptorium seat bonus stacks with scribe for peer teaching capacity."""
    world = World(
        config=SimulationConfig(agent_count=4, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        agents=(
            Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
            Agent.create(agent_id=1, name="B", knowledge=_FIRE),
            Agent.create(agent_id=2, name="C", knowledge=_FIRE),
            Agent.create(agent_id=3, name="D", knowledge=_FIRE),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_scriptorium, gains = diffuse_knowledge(
        with_pottery, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    # Base 1 + scriptorium 1 = two learners taught.
    assert len(gains) == 2
    assert with_scriptorium.agents[1].knowledge.knows(POTTERY_FACT)
    assert with_scriptorium.agents[2].knowledge.knows(POTTERY_FACT)
    assert not with_scriptorium.agents[3].knowledge.knows(POTTERY_FACT)

    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    innovations = tuple(
        active_scribe if item.innovation_id == CAMP_SCRIBE.innovation_id else item
        for item in with_writing.innovations
    )
    stacked_world = with_writing.model_copy(update={"innovations": innovations})
    stacked, gains = diffuse_knowledge(
        stacked_world, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    # Base 1 + scribe 1 + scriptorium 1 = three learners taught.
    assert len(gains) == 3
    assert stacked.agents[1].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[2].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[3].knowledge.knows(POTTERY_FACT)


def test_curriculum_stacks_with_scribe_and_scriptorium_in_diffusion() -> None:
    """Curriculum subject bonus stacks with scribe and scriptorium capacity."""
    world = World(
        config=SimulationConfig(agent_count=5, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        agents=(
            Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
            Agent.create(agent_id=1, name="B", knowledge=_FIRE),
            Agent.create(agent_id=2, name="C", knowledge=_FIRE),
            Agent.create(agent_id=3, name="D", knowledge=_FIRE),
            Agent.create(agent_id=4, name="E", knowledge=_FIRE),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    innovations = tuple(
        active_scribe if item.innovation_id == CAMP_SCRIBE.innovation_id else item
        for item in with_writing.innovations
    )
    stacked_world = with_writing.model_copy(update={"innovations": innovations})
    stacked, gains = diffuse_knowledge(
        stacked_world, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    # Base 1 + scribe 1 + scriptorium 1 + curriculum 1 = four learners taught.
    assert len(gains) == 4
    assert stacked.agents[1].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[2].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[3].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[4].knowledge.knows(POTTERY_FACT)


def test_academy_stacks_with_scribe_scriptorium_curriculum_in_diffusion() -> None:
    """Academy seat bonus stacks with scribe, scriptorium, and curriculum capacity."""
    world = World(
        config=SimulationConfig(agent_count=6, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        institutions=(
            Institution.create(0, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
        ),
        agents=(
            Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
            Agent.create(agent_id=1, name="B", knowledge=_FIRE),
            Agent.create(agent_id=2, name="C", knowledge=_FIRE),
            Agent.create(agent_id=3, name="D", knowledge=_FIRE),
            Agent.create(agent_id=4, name="E", knowledge=_FIRE),
            Agent.create(agent_id=5, name="F", knowledge=_FIRE),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    innovations = tuple(
        active_scribe if item.innovation_id == CAMP_SCRIBE.innovation_id else item
        for item in with_writing.innovations
    )
    stacked_world = with_writing.model_copy(update={"innovations": innovations})
    stacked, gains = diffuse_knowledge(
        stacked_world, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    # Base 1 + scribe 1 + scriptorium 1 + curriculum 1 + academy 1 = five learners.
    assert len(gains) == 5
    assert stacked.agents[1].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[2].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[3].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[4].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[5].knowledge.knows(POTTERY_FACT)


def test_school_stacks_with_academy_in_diffusion() -> None:
    """School seat bonus stacks with academy, scribe, scriptorium, and curriculum."""
    world = World(
        config=SimulationConfig(agent_count=7, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        institutions=(
            Institution.create(0, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(1, 0, 0, "Camp School", InstitutionKind.SCHOOL),
        ),
        agents=(
            Agent.create(agent_id=0, name="A", knowledge=_FIRE_AND_POTTERY),
            Agent.create(agent_id=1, name="B", knowledge=_FIRE),
            Agent.create(agent_id=2, name="C", knowledge=_FIRE),
            Agent.create(agent_id=3, name="D", knowledge=_FIRE),
            Agent.create(agent_id=4, name="E", knowledge=_FIRE),
            Agent.create(agent_id=5, name="F", knowledge=_FIRE),
            Agent.create(agent_id=6, name="G", knowledge=_FIRE),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    innovations = tuple(
        active_scribe if item.innovation_id == CAMP_SCRIBE.innovation_id else item
        for item in with_writing.innovations
    )
    stacked_world = with_writing.model_copy(update={"innovations": innovations})
    stacked, gains = diffuse_knowledge(
        stacked_world, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    # Base 1 + scribe 1 + scriptorium 1 + curriculum 1 + academy 1 + school 1 = 6.
    assert len(gains) == 6
    assert stacked.agents[1].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[2].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[3].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[4].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[5].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[6].knowledge.knows(POTTERY_FACT)


def test_forum_stacks_with_academy_scriptorium_in_diffusion() -> None:
    """Forum seat bonus stacks with academy, scriptorium, curriculum, and scribe."""
    world = World(
        config=SimulationConfig(agent_count=7, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Forum Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Forum Academy", InstitutionKind.ACADEMY),
        ),
        agents=(
            Agent.create(
                agent_id=0, name="A", location_id=1, knowledge=_FIRE_AND_POTTERY
            ),
            Agent.create(agent_id=1, name="B", location_id=1, knowledge=_FIRE),
            Agent.create(agent_id=2, name="C", location_id=1, knowledge=_FIRE),
            Agent.create(agent_id=3, name="D", location_id=1, knowledge=_FIRE),
            Agent.create(agent_id=4, name="E", location_id=1, knowledge=_FIRE),
            Agent.create(agent_id=5, name="F", location_id=1, knowledge=_FIRE),
            Agent.create(agent_id=6, name="G", location_id=1, knowledge=_FIRE),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    innovations = tuple(
        active_scribe if item.innovation_id == CAMP_SCRIBE.innovation_id else item
        for item in with_writing.innovations
    )
    stacked_world = with_writing.model_copy(update={"innovations": innovations})
    stacked, gains = diffuse_knowledge(
        stacked_world, teachings_per_knower=DEFAULT_TEACHINGS_PER_KNOWER
    )
    # Base 1 + scribe 1 + scriptorium 1 + curriculum 1 + academy 1 + forum 1 = 6.
    assert len(gains) == 6
    assert stacked.agents[1].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[2].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[3].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[4].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[5].knowledge.knows(POTTERY_FACT)
    assert stacked.agents[6].knowledge.knows(POTTERY_FACT)


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
    assert snap.irrigation_knower_count == 0
    assert snap.metallurgy_knower_count == 0
    assert snap.writing_knower_count == 0
    assert snap.mathematics_knower_count == 0
    assert snap.astronomy_knower_count == 0
    assert snap.philosophy_knower_count == 0
    assert snap.logic_knower_count == 0
    assert snap.rhetoric_knower_count == 0
    assert snap.total_fact_instances == 2
    assert snap.coverage_bps == 10_000
    assert agents_knowing(world, FIRE_FACT)[0].agent_id.value == 0
    assert grant_knowledge(world, 0, FIRE_FACT) == world
