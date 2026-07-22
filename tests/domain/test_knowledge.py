"""Unit tests for knowledge diffusion helpers."""

from __future__ import annotations

from civitas.domain import (
    AGRICULTURE_FACT,
    ANATOMY_FACT,
    ARCHITECTURE_FACT,
    ASTRONOMY_FACT,
    CAMP_AGRICULTURE,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASTRONOMY,
    CAMP_CARTOGRAPHY,
    CAMP_CROP_ROTATION,
    CAMP_DIALECTIC,
    CAMP_DYEING,
    CAMP_ENGINEERING,
    CAMP_FORESTRY,
    CAMP_HYGIENE,
    CAMP_IRRIGATION,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_MINING,
    CAMP_NAVIGATION,
    CAMP_PHILOSOPHY,
    CAMP_POTTERY,
    CAMP_RHETORIC,
    CAMP_SCRIBE,
    CAMP_SEAFARING,
    CAMP_SURVEYING,
    CAMP_TANNING,
    CAMP_TEXTILES,
    CAMP_WRITING,
    CARTOGRAPHY_FACT,
    CROP_ROTATION_FACT,
    DEFAULT_TEACHINGS_PER_KNOWER,
    DYEING_FACT,
    ENGINEERING_FACT,
    FIRE_FACT,
    FORESTRY_FACT,
    HYGIENE_FACT,
    IRRIGATION_FACT,
    LOGIC_FACT,
    MATHEMATICS_FACT,
    MEDICINE_FACT,
    METALLURGY_FACT,
    MINING_FACT,
    NAVIGATION_FACT,
    PHILOSOPHY_FACT,
    POTTERY_FACT,
    RHETORIC_FACT,
    SEAFARING_FACT,
    SURVEYING_FACT,
    TANNING_FACT,
    TEXTILES_FACT,
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


def test_bootstrap_uses_medicine_technology_fact() -> None:
    """Discovered medicine bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
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
    with_medicine = discover_technology(with_rhetoric, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    world, gains = bootstrap_discovered_knowledge(with_medicine)
    assert len(gains) == 1
    assert gains[0].fact == MEDICINE_FACT
    assert world.agents[0].knowledge.knows(MEDICINE_FACT)


def test_bootstrap_uses_anatomy_technology_fact() -> None:
    """Discovered anatomy bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
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
    with_medicine = discover_technology(with_rhetoric, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    with_anatomy = discover_technology(with_medicine, CAMP_ANATOMY.technology_id)
    assert with_anatomy is not None
    world, gains = bootstrap_discovered_knowledge(with_anatomy)
    assert len(gains) == 1
    assert gains[0].fact == ANATOMY_FACT
    assert world.agents[0].knowledge.knows(ANATOMY_FACT)


def test_bootstrap_uses_hygiene_technology_fact() -> None:
    """Discovered hygiene bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
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
    with_medicine = discover_technology(with_rhetoric, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    with_anatomy = discover_technology(with_medicine, CAMP_ANATOMY.technology_id)
    assert with_anatomy is not None
    with_hygiene = discover_technology(with_anatomy, CAMP_HYGIENE.technology_id)
    assert with_hygiene is not None
    world, gains = bootstrap_discovered_knowledge(with_hygiene)
    assert len(gains) == 1
    assert gains[0].fact == HYGIENE_FACT
    assert world.agents[0].knowledge.knows(HYGIENE_FACT)


def test_bootstrap_uses_engineering_technology_fact() -> None:
    """Discovered engineering bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_engineering = discover_technology(current, CAMP_ENGINEERING.technology_id)
    assert with_engineering is not None
    world, gains = bootstrap_discovered_knowledge(with_engineering)
    assert len(gains) == 1
    assert gains[0].fact == ENGINEERING_FACT
    assert world.agents[0].knowledge.knows(ENGINEERING_FACT)


def test_bootstrap_uses_architecture_technology_fact() -> None:
    """Discovered architecture bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_architecture = discover_technology(current, CAMP_ARCHITECTURE.technology_id)
    assert with_architecture is not None
    world, gains = bootstrap_discovered_knowledge(with_architecture)
    assert len(gains) == 1
    assert gains[0].fact == ARCHITECTURE_FACT
    assert world.agents[0].knowledge.knows(ARCHITECTURE_FACT)


def test_bootstrap_uses_surveying_technology_fact() -> None:
    """Discovered surveying bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_surveying = discover_technology(current, CAMP_SURVEYING.technology_id)
    assert with_surveying is not None
    world, gains = bootstrap_discovered_knowledge(with_surveying)
    assert len(gains) == 1
    assert gains[0].fact == SURVEYING_FACT
    assert world.agents[0].knowledge.knows(SURVEYING_FACT)


def test_bootstrap_uses_navigation_technology_fact() -> None:
    """Discovered navigation bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_navigation = discover_technology(current, CAMP_NAVIGATION.technology_id)
    assert with_navigation is not None
    world, gains = bootstrap_discovered_knowledge(with_navigation)
    assert len(gains) == 1
    assert gains[0].fact == NAVIGATION_FACT
    assert world.agents[0].knowledge.knows(NAVIGATION_FACT)


def test_bootstrap_uses_cartography_technology_fact() -> None:
    """Discovered cartography bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_cartography = discover_technology(current, CAMP_CARTOGRAPHY.technology_id)
    assert with_cartography is not None
    world, gains = bootstrap_discovered_knowledge(with_cartography)
    assert len(gains) == 1
    assert gains[0].fact == CARTOGRAPHY_FACT
    assert world.agents[0].knowledge.knows(CARTOGRAPHY_FACT)


def test_bootstrap_uses_seafaring_technology_fact() -> None:
    """Discovered seafaring bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_seafaring = discover_technology(current, CAMP_SEAFARING.technology_id)
    assert with_seafaring is not None
    world, gains = bootstrap_discovered_knowledge(with_seafaring)
    assert len(gains) == 1
    assert gains[0].fact == SEAFARING_FACT
    assert world.agents[0].knowledge.knows(SEAFARING_FACT)


def test_bootstrap_uses_agriculture_technology_fact() -> None:
    """Discovered agriculture bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_agriculture = discover_technology(current, CAMP_AGRICULTURE.technology_id)
    assert with_agriculture is not None
    world, gains = bootstrap_discovered_knowledge(with_agriculture)
    assert len(gains) == 1
    assert gains[0].fact == AGRICULTURE_FACT
    assert world.agents[0].knowledge.knows(AGRICULTURE_FACT)


def test_bootstrap_uses_crop_rotation_technology_fact() -> None:
    """Discovered crop rotation bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
                AGRICULTURE_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_crop_rotation = discover_technology(current, CAMP_CROP_ROTATION.technology_id)
    assert with_crop_rotation is not None
    world, gains = bootstrap_discovered_knowledge(with_crop_rotation)
    assert len(gains) == 1
    assert gains[0].fact == CROP_ROTATION_FACT
    assert world.agents[0].knowledge.knows(CROP_ROTATION_FACT)


def test_bootstrap_uses_forestry_technology_fact() -> None:
    """Discovered forestry bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
                AGRICULTURE_FACT,
                CROP_ROTATION_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_forestry = discover_technology(current, CAMP_FORESTRY.technology_id)
    assert with_forestry is not None
    world, gains = bootstrap_discovered_knowledge(with_forestry)
    assert len(gains) == 1
    assert gains[0].fact == FORESTRY_FACT
    assert world.agents[0].knowledge.knows(FORESTRY_FACT)


def test_bootstrap_uses_textiles_technology_fact() -> None:
    """Discovered textiles bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
                AGRICULTURE_FACT,
                CROP_ROTATION_FACT,
                FORESTRY_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_textiles = discover_technology(current, CAMP_TEXTILES.technology_id)
    assert with_textiles is not None
    world, gains = bootstrap_discovered_knowledge(with_textiles)
    assert len(gains) == 1
    assert gains[0].fact == TEXTILES_FACT
    assert world.agents[0].knowledge.knows(TEXTILES_FACT)


def test_bootstrap_uses_dyeing_technology_fact() -> None:
    """Discovered dyeing bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
                AGRICULTURE_FACT,
                CROP_ROTATION_FACT,
                FORESTRY_FACT,
                TEXTILES_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_dyeing = discover_technology(current, CAMP_DYEING.technology_id)
    assert with_dyeing is not None
    world, gains = bootstrap_discovered_knowledge(with_dyeing)
    assert len(gains) == 1
    assert gains[0].fact == DYEING_FACT
    assert world.agents[0].knowledge.knows(DYEING_FACT)


def test_bootstrap_uses_tanning_technology_fact() -> None:
    """Discovered tanning bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
                AGRICULTURE_FACT,
                CROP_ROTATION_FACT,
                FORESTRY_FACT,
                TEXTILES_FACT,
                DYEING_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_tanning = discover_technology(current, CAMP_TANNING.technology_id)
    assert with_tanning is not None
    world, gains = bootstrap_discovered_knowledge(with_tanning)
    assert len(gains) == 1
    assert gains[0].fact == TANNING_FACT
    assert world.agents[0].knowledge.knows(TANNING_FACT)


def test_bootstrap_uses_mining_technology_fact() -> None:
    """Discovered mining bootstraps through the generic tech fact mapping."""
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
                RHETORIC_FACT,
                MEDICINE_FACT,
                ANATOMY_FACT,
                HYGIENE_FACT,
                ENGINEERING_FACT,
                ARCHITECTURE_FACT,
                SURVEYING_FACT,
                NAVIGATION_FACT,
                CARTOGRAPHY_FACT,
                SEAFARING_FACT,
                AGRICULTURE_FACT,
                CROP_ROTATION_FACT,
                FORESTRY_FACT,
                TEXTILES_FACT,
                DYEING_FACT,
                TANNING_FACT,
            }
        )
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=prior),
        Agent.create(agent_id=1, name="B", knowledge=prior),
    )
    current = world
    for technology in (
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
        CAMP_TANNING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    with_mining = discover_technology(current, CAMP_MINING.technology_id)
    assert with_mining is not None
    world, gains = bootstrap_discovered_knowledge(with_mining)
    assert len(gains) == 1
    assert gains[0].fact == MINING_FACT
    assert world.agents[0].knowledge.knows(MINING_FACT)


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


def test_collegium_stacks_with_teaching_sources_in_diffusion() -> None:
    """Collegium seat bonus contributes to actual peer teaching capacity."""
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    active_dialectic = CAMP_DIALECTIC.model_copy(update={"active": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    technologies = tuple(
        discovered_writing
        if item.technology_id == CAMP_WRITING.technology_id
        else discovered_philosophy
        if item.technology_id == CAMP_PHILOSOPHY.technology_id
        else item
        for item in default_technologies()
    )
    research_progress = tuple(
        item
        for item in default_research_progress()
        if item.technology_id
        not in {CAMP_WRITING.technology_id, CAMP_PHILOSOPHY.technology_id}
    )
    innovations = tuple(
        active_scribe
        if item.innovation_id == CAMP_SCRIBE.innovation_id
        else active_dialectic
        if item.innovation_id == CAMP_DIALECTIC.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=10, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        technologies=technologies,
        research_progress=research_progress,
        innovations=innovations,
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Forum Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
            Infrastructure.create(1, 0, 1, 1, "Forum Stoa", InfrastructureKind.STOA),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Forum Academy", InstitutionKind.ACADEMY),
            Institution.create(1, 0, 1, "Forum School", InstitutionKind.SCHOOL),
            Institution.create(2, 0, 1, "Forum Collegium", InstitutionKind.COLLEGIUM),
        ),
        agents=(
            Agent.create(
                agent_id=0, name="A", location_id=1, knowledge=_FIRE_AND_POTTERY
            ),
            *(
                Agent.create(
                    agent_id=agent_id,
                    name=f"L{agent_id}",
                    location_id=1,
                    knowledge=_FIRE,
                )
                for agent_id in range(1, 10)
            ),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    stacked, gains = diffuse_knowledge(with_pottery, teachings_per_knower=0)
    # Scribe + dialectic + scriptorium + stoa + academy + forum + school
    # + curriculum + collegium = nine learners taught from a zero base.
    assert len(gains) == 9
    assert all(
        stacked.agents[agent_id].knowledge.knows(POTTERY_FACT)
        for agent_id in range(1, 10)
    )


def test_architect_stacks_with_teaching_sources_in_diffusion() -> None:
    """Architect seat bonus contributes to actual peer teaching capacity."""
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    active_dialectic = CAMP_DIALECTIC.model_copy(update={"active": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    technologies = tuple(
        discovered_writing
        if item.technology_id == CAMP_WRITING.technology_id
        else discovered_philosophy
        if item.technology_id == CAMP_PHILOSOPHY.technology_id
        else item
        for item in default_technologies()
    )
    research_progress = tuple(
        item
        for item in default_research_progress()
        if item.technology_id
        not in {CAMP_WRITING.technology_id, CAMP_PHILOSOPHY.technology_id}
    )
    innovations = tuple(
        active_scribe
        if item.innovation_id == CAMP_SCRIBE.innovation_id
        else active_dialectic
        if item.innovation_id == CAMP_DIALECTIC.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=11, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        technologies=technologies,
        research_progress=research_progress,
        innovations=innovations,
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Forum Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
            Infrastructure.create(1, 0, 1, 1, "Forum Stoa", InfrastructureKind.STOA),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Forum Academy", InstitutionKind.ACADEMY),
            Institution.create(1, 0, 1, "Forum School", InstitutionKind.SCHOOL),
            Institution.create(2, 0, 1, "Forum Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 1, "Forum Architect", InstitutionKind.ARCHITECT),
        ),
        agents=(
            Agent.create(
                agent_id=0, name="A", location_id=1, knowledge=_FIRE_AND_POTTERY
            ),
            *(
                Agent.create(
                    agent_id=agent_id,
                    name=f"L{agent_id}",
                    location_id=1,
                    knowledge=_FIRE,
                )
                for agent_id in range(1, 11)
            ),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    stacked, gains = diffuse_knowledge(with_pottery, teachings_per_knower=0)
    # Prior nine teaching sources + architect = ten learners from a zero base.
    assert len(gains) == 10
    assert all(
        stacked.agents[agent_id].knowledge.knows(POTTERY_FACT)
        for agent_id in range(1, 11)
    )


def test_cartographer_stacks_with_teaching_sources_in_diffusion() -> None:
    """Cartographer seat bonus contributes to actual peer teaching capacity."""
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    active_dialectic = CAMP_DIALECTIC.model_copy(update={"active": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    technologies = tuple(
        discovered_writing
        if item.technology_id == CAMP_WRITING.technology_id
        else discovered_philosophy
        if item.technology_id == CAMP_PHILOSOPHY.technology_id
        else item
        for item in default_technologies()
    )
    research_progress = tuple(
        item
        for item in default_research_progress()
        if item.technology_id
        not in {CAMP_WRITING.technology_id, CAMP_PHILOSOPHY.technology_id}
    )
    innovations = tuple(
        active_scribe
        if item.innovation_id == CAMP_SCRIBE.innovation_id
        else active_dialectic
        if item.innovation_id == CAMP_DIALECTIC.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=12, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        technologies=technologies,
        research_progress=research_progress,
        innovations=innovations,
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Forum Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
            Infrastructure.create(1, 0, 1, 1, "Forum Stoa", InfrastructureKind.STOA),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Forum Academy", InstitutionKind.ACADEMY),
            Institution.create(1, 0, 1, "Forum School", InstitutionKind.SCHOOL),
            Institution.create(2, 0, 1, "Forum Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 1, "Forum Architect", InstitutionKind.ARCHITECT),
            Institution.create(
                4, 0, 1, "Forum Cartographer", InstitutionKind.CARTOGRAPHER
            ),
        ),
        agents=(
            Agent.create(
                agent_id=0, name="A", location_id=1, knowledge=_FIRE_AND_POTTERY
            ),
            *(
                Agent.create(
                    agent_id=agent_id,
                    name=f"L{agent_id}",
                    location_id=1,
                    knowledge=_FIRE,
                )
                for agent_id in range(1, 12)
            ),
        ),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    stacked, gains = diffuse_knowledge(with_pottery, teachings_per_knower=0)
    # Prior ten teaching sources + cartographer = eleven learners from a zero base.
    assert len(gains) == 11
    assert all(
        stacked.agents[agent_id].knowledge.knows(POTTERY_FACT)
        for agent_id in range(1, 12)
    )


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
    assert snap.medicine_knower_count == 0
    assert snap.anatomy_knower_count == 0
    assert snap.hygiene_knower_count == 0
    assert snap.engineering_knower_count == 0
    assert snap.architecture_knower_count == 0
    assert snap.surveying_knower_count == 0
    assert snap.navigation_knower_count == 0
    assert snap.cartography_knower_count == 0
    assert snap.seafaring_knower_count == 0
    assert snap.agriculture_knower_count == 0
    assert snap.crop_rotation_knower_count == 0
    assert snap.forestry_knower_count == 0
    assert snap.textiles_knower_count == 0
    assert snap.dyeing_knower_count == 0
    assert snap.tanning_knower_count == 0
    assert snap.mining_knower_count == 0
    assert snap.total_fact_instances == 2
    assert snap.coverage_bps == 10_000
    assert agents_knowing(world, FIRE_FACT)[0].agent_id.value == 0
    assert grant_knowledge(world, 0, FIRE_FACT) == world
