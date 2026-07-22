"""Unit tests for memory retrieval helpers."""

from __future__ import annotations

from civitas.domain import (
    ARCHIVE_RETRIEVAL_LIMIT_BONUS,
    CAMP_LOCATION,
    DEFAULT_RETRIEVAL_LIMIT,
    Agent,
    Goal,
    GoalSet,
    Government,
    Institution,
    InstitutionKind,
    Memory,
    MemoryKind,
    MemoryRecord,
    Needs,
    SimulationConfig,
    Tick,
    World,
    apply_retrieval,
    census_retrieval,
    default_innovations,
    default_research_progress,
    default_technologies,
    relevance_score,
    retrieval_query_for_agent,
    retrieve_memories,
)


def _world(
    *agents: Agent,
    institutions: tuple[Institution, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=institutions,
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        agents=agents,
    )


def test_retrieval_query_prefers_goal_target() -> None:
    """Planned satisfy-need goals become the retrieval query."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.2, water=0.9, energy=0.9),
    )
    agent = agent.model_copy(
        update={
            "goals": GoalSet(
                goals=(Goal(kind="satisfy_food", priority=0.7, target="food"),)
            )
        }
    )
    assert retrieval_query_for_agent(agent) == "food"


def test_retrieve_memories_ranks_relevant_then_recent() -> None:
    """Retrieval prefers query matches, then more recent ticks."""
    records = (
        MemoryRecord(
            tick=Tick(value=1),
            kind=MemoryKind.EPISODE.value,
            content="food=0.2",
        ),
        MemoryRecord(
            tick=Tick(value=2),
            kind=MemoryKind.REFLECTION.value,
            content="priority water",
        ),
        MemoryRecord(
            tick=Tick(value=3),
            kind=MemoryKind.EPISODE.value,
            content="food=0.1",
        ),
    )
    agent = Agent.create(agent_id=0, name="A").model_copy(
        update={
            "goals": GoalSet(
                goals=(Goal(kind="satisfy_food", priority=0.8, target="food"),)
            ),
            "memory": Memory(records=records),
        }
    )
    retrieved = retrieve_memories(agent, limit=2)
    assert len(retrieved) == 2
    assert retrieved[0].tick.value == 3
    assert retrieved[1].tick.value == 1
    assert relevance_score(retrieved[0], "food") > relevance_score(retrieved[1], "food")


def test_apply_retrieval_writes_working_memory() -> None:
    """Apply pass stores query + top memories on each living agent."""
    agent = Agent.create(agent_id=0, name="A").model_copy(
        update={
            "goals": GoalSet(
                goals=(Goal(kind="satisfy_energy", priority=0.6, target="energy"),)
            ),
            "memory": Memory(
                records=(
                    MemoryRecord(
                        tick=Tick(value=1),
                        kind=MemoryKind.EPISODE.value,
                        content="energy=0.4",
                    ),
                )
            ),
        }
    )
    world, hits = apply_retrieval(_world(agent).with_tick(Tick(value=2)))
    assert len(hits) == 1
    assert hits[0].query == "energy"
    assert hits[0].retrieved_count == 1
    assert world.agents[0].working_memory.query == "energy"
    assert len(world.agents[0].working_memory.records) == 1
    snap = census_retrieval(world)
    assert snap.agents_with_context == 1
    assert snap.total_retrieved == 1
    assert snap.mean_retrieved_bps == 10_000


def test_apply_retrieval_uses_archive_limit_bonus() -> None:
    """Colocated archives raise how many memories the apply path retrieves."""
    records = tuple(
        MemoryRecord(
            tick=Tick(value=tick),
            kind=MemoryKind.EPISODE.value,
            content=f"food=0.{tick}",
        )
        for tick in range(
            1, DEFAULT_RETRIEVAL_LIMIT + ARCHIVE_RETRIEVAL_LIMIT_BONUS + 2
        )
    )
    agent = Agent.create(agent_id=0, name="A").model_copy(
        update={
            "goals": GoalSet(
                goals=(Goal(kind="satisfy_food", priority=0.8, target="food"),)
            ),
            "memory": Memory(records=records),
        }
    )
    bare, bare_hits = apply_retrieval(_world(agent))
    assert bare_hits[0].retrieved_count == DEFAULT_RETRIEVAL_LIMIT
    assert len(bare.agents[0].working_memory.records) == DEFAULT_RETRIEVAL_LIMIT

    boosted, boosted_hits = apply_retrieval(
        _world(
            agent,
            institutions=(
                Institution.create(0, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            ),
        )
    )
    expected = DEFAULT_RETRIEVAL_LIMIT + ARCHIVE_RETRIEVAL_LIMIT_BONUS
    assert boosted_hits[0].retrieved_count == expected
    assert len(boosted.agents[0].working_memory.records) == expected
