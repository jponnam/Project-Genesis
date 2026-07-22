"""Unit tests for the BirthSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    FIRE_FACT,
    Agent,
    AgentBorn,
    Knowledge,
    KnowledgeLearned,
    Needs,
    SimulationConfig,
    Tick,
    World,
)
from civitas.engine import EventBus
from civitas.systems import BirthConfig, BirthSystem


def _eligible_parent(agent_id: int = 0, *, birth_tick: int = 0) -> Agent:
    return Agent.create(
        agent_id=agent_id,
        name=f"P-{agent_id}",
        birth_tick=birth_tick,
        needs=Needs(food=0.9, water=0.9, energy=0.9),
        knowledge=Knowledge(facts=frozenset({FIRE_FACT})),
    )


def _world(*agents: Agent, tick: int = 10) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        tick=Tick(value=tick),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_apply_births_emits_agent_born_and_grows_roster() -> None:
    """One eligible parent produces one child and one AgentBorn event."""
    world = _world(_eligible_parent())
    bus = EventBus()
    system = BirthSystem(BirthConfig(min_parent_age_ticks=0, max_births_per_tick=1))
    updated = system.apply_births(world, bus=bus)
    assert updated.population_size == 2
    events = [event for event in bus.history if isinstance(event, AgentBorn)]
    assert len(events) == 1
    assert events[0].parent_id.value == 0
    assert events[0].agent_id.value == 1
    assert events[0].name == "Agent-1"
    assert events[0].location_id.value == 0
    assert updated.agents[1].knowledge.knows(FIRE_FACT)
    learned = [event for event in bus.history if isinstance(event, KnowledgeLearned)]
    assert len(learned) == 1
    assert learned[0].fact == FIRE_FACT
    assert learned[0].source == "birth"
    assert learned[0].teacher_id is not None
    assert learned[0].teacher_id.value == 0


def test_apply_births_respects_max_births_and_parent_order() -> None:
    """Lowest parent ids birth first up to the per-tick cap."""
    world = _world(_eligible_parent(0), _eligible_parent(1), _eligible_parent(2))
    bus = EventBus()
    updated = BirthSystem(
        BirthConfig(min_parent_age_ticks=0, max_births_per_tick=2)
    ).apply_births(world, bus=bus)
    assert updated.population_size == 5
    parents = [
        event.parent_id.value for event in bus.history if isinstance(event, AgentBorn)
    ]
    assert parents == [0, 1]


def test_apply_births_can_be_disabled() -> None:
    """BirthConfig.enabled=False skips all births."""
    world = _world(_eligible_parent())
    bus = EventBus()
    updated = BirthSystem(
        BirthConfig(enabled=False, min_parent_age_ticks=0)
    ).apply_births(world, bus=bus)
    assert updated == world
    assert bus.history == ()


def test_apply_births_respects_max_population() -> None:
    """Population ceiling stops further births."""
    world = _world(_eligible_parent(0), _eligible_parent(1))
    updated = BirthSystem(
        BirthConfig(
            min_parent_age_ticks=0,
            max_births_per_tick=5,
            max_population=3,
        )
    ).apply_births(world)
    assert updated.population_size == 3


def test_can_birth_delegates_to_domain_rules() -> None:
    """System.can_birth mirrors domain eligibility for an agent id."""
    world = _world(_eligible_parent(), tick=10)
    system = BirthSystem(BirthConfig(min_parent_age_ticks=10))
    assert system.can_birth(world, 0) is True
    assert system.can_birth(world, 99) is False
