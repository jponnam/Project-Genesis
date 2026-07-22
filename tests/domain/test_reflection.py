"""Unit tests for reflection helpers."""

from __future__ import annotations

from civitas.domain import (
    AGRICULTURE_FACT,
    ANATOMY_FACT,
    ARCHITECTURE_FACT,
    ASTRONOMY_FACT,
    CAMP_LOCATION,
    CARTOGRAPHY_FACT,
    CROP_ROTATION_FACT,
    ENGINEERING_FACT,
    FIRE_FACT,
    FORESTRY_FACT,
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
    SEAFARING_FACT,
    SURVEYING_FACT,
    WRITING_FACT,
    Agent,
    Knowledge,
    Needs,
    SimulationConfig,
    Tick,
    World,
    apply_memory_encoding,
    apply_reflections,
    belief_from_reflection,
    build_reflection_prompt,
    default_innovations,
    default_research_progress,
    default_technologies,
    dominant_need_name,
)
from civitas.llm import SeededMockLanguageModel
from civitas.llm.protocol import LanguageModelRequest


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=42),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        agents=agents,
    )


def test_dominant_need_picks_lowest_vital() -> None:
    """Lowest vital need wins; ties break alphabetically."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.2, water=0.4, energy=0.2),
    )
    assert dominant_need_name(agent) == "energy"


def test_belief_from_reflection_sets_priority_proposition() -> None:
    """Reflection belief encodes the dominant need and a bounded confidence."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.1, water=0.9, energy=0.9),
    )
    belief = belief_from_reflection(agent, "mock:abcd")
    assert belief.proposition == "priority:food"
    assert 0.0 < belief.confidence <= 0.99


def test_apply_reflections_updates_beliefs_and_memory() -> None:
    """Reflection upserts a belief and appends a reflection memory."""
    world = _world(Agent.create(agent_id=0, name="A")).with_tick(Tick(value=1))
    world, _ = apply_memory_encoding(world)
    prompt = build_reflection_prompt(world.agents[0])
    assert "agent=0" in prompt
    world, outcomes = apply_reflections(world, SeededMockLanguageModel(), seed=42)
    assert len(outcomes) == 1
    assert world.agents[0].beliefs.entries
    assert world.agents[0].beliefs.entries[0].proposition.startswith("priority:")
    assert any(record.kind == "reflection" for record in world.agents[0].memory.records)


def test_reflection_prompt_accepts_full_technology_fact_content() -> None:
    """Reflection prompt length still fits with every canonical tech fact."""
    all_facts = frozenset(
        {
            ARCHITECTURE_FACT,
            ASTRONOMY_FACT,
            ANATOMY_FACT,
            CARTOGRAPHY_FACT,
            CROP_ROTATION_FACT,
            ENGINEERING_FACT,
            AGRICULTURE_FACT,
            FIRE_FACT,
            FORESTRY_FACT,
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
            SEAFARING_FACT,
            SURVEYING_FACT,
            WRITING_FACT,
        }
    )
    world = _world(
        Agent.create(agent_id=0, name="A", knowledge=Knowledge(facts=all_facts))
    ).with_tick(Tick(value=1))
    world, _ = apply_memory_encoding(world)
    prompt = build_reflection_prompt(world.agents[0])
    assert len(prompt) == 294
    assert "forestry" in prompt
    LanguageModelRequest(prompt=prompt, seed=42)
