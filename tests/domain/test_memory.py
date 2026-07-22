"""Unit tests for episodic memory encoding helpers."""

from __future__ import annotations

from civitas.domain import (
    ANATOMY_FACT,
    ARCHITECTURE_FACT,
    ASTRONOMY_FACT,
    CAMP_LOCATION,
    CARTOGRAPHY_FACT,
    ENGINEERING_FACT,
    FIRE_FACT,
    HYGIENE_FACT,
    IRRIGATION_FACT,
    LOGIC_FACT,
    MATHEMATICS_FACT,
    MEDICINE_FACT,
    METALLURGY_FACT,
    NAVIGATION_FACT,
    PHILOSOPHY_FACT,
    POTTERY_FACT,
    RHETORIC_FACT,
    SURVEYING_FACT,
    WRITING_FACT,
    Agent,
    Knowledge,
    MemoryKind,
    SimulationConfig,
    Tick,
    World,
    apply_memory_encoding,
    census_memory,
    default_innovations,
    default_research_progress,
    default_technologies,
    encode_agent_episode,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        agents=agents,
    )


def test_encode_agent_episode_is_deterministic() -> None:
    """Episode content is a stable function of agent state and tick."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        knowledge=Knowledge(facts=frozenset({FIRE_FACT})),
    )
    record = encode_agent_episode(agent, Tick(value=3))
    assert record.kind == MemoryKind.EPISODE.value
    assert record.tick.value == 3
    assert "loc=0" in record.content
    assert "facts=fire" in record.content
    assert encode_agent_episode(agent, Tick(value=3)) == record


def test_encode_agent_episode_accepts_full_technology_fact_content() -> None:
    """Episode content can fit every canonical technology fact."""
    all_facts = frozenset(
        {
            ARCHITECTURE_FACT,
            ASTRONOMY_FACT,
            ANATOMY_FACT,
            CARTOGRAPHY_FACT,
            ENGINEERING_FACT,
            FIRE_FACT,
            HYGIENE_FACT,
            IRRIGATION_FACT,
            LOGIC_FACT,
            MATHEMATICS_FACT,
            MEDICINE_FACT,
            METALLURGY_FACT,
            NAVIGATION_FACT,
            PHILOSOPHY_FACT,
            POTTERY_FACT,
            RHETORIC_FACT,
            SURVEYING_FACT,
            WRITING_FACT,
        }
    )
    record = encode_agent_episode(
        Agent.create(agent_id=0, name="A", knowledge=Knowledge(facts=all_facts)),
        Tick(value=3),
    )
    assert len(record.content) == 221
    assert (
        "facts=anatomy,architecture,astronomy,cartography,engineering,fire"
        in record.content
    )


def test_apply_memory_encoding_writes_one_record_per_living_agent() -> None:
    """Encoding appends one episode per living agent in id order."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    ).with_tick(Tick(value=2))
    world, writes = apply_memory_encoding(world)
    assert len(writes) == 2
    assert writes[0].agent_id.value == 0
    assert writes[1].agent_id.value == 1
    assert len(world.agents[0].memory.records) == 1
    assert world.agents[0].memory.records[0].kind == "episode"


def test_census_memory_counts_records() -> None:
    """Census reports aggregate memory coverage after encoding."""
    world = _world(Agent.create(agent_id=0, name="A")).with_tick(Tick(value=1))
    world, _ = apply_memory_encoding(world)
    snap = census_memory(world)
    assert snap.living_count == 1
    assert snap.total_records == 1
    assert snap.agents_with_memory == 1
    assert snap.episode_records == 1
    assert snap.reflection_records == 0
    assert snap.belief_count == 0
    assert snap.mean_records_bps == 10_000
