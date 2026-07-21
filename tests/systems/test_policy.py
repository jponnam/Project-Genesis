"""Unit tests for the utility-based action policy."""

from __future__ import annotations

import pytest

from civitas.domain import (
    ACTION_CATALOG,
    CAMP_LOCATION,
    ActionKind,
    ActionSelected,
    Agent,
    AgentStatus,
    Goal,
    GoalSet,
    Health,
    Needs,
    Personality,
    SimulationConfig,
    World,
    default_world_map,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import PolicyConfig, UtilityPolicy


def test_hungry_agent_selects_eat() -> None:
    """Low food satisfaction yields eat as the top action."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.1, water=0.9, energy=0.9, social=0.9, safety=0.9),
    )
    choice = UtilityPolicy().select(agent)
    assert choice.action is ActionKind.EAT
    assert choice.utility > 0.0


def test_thirsty_agent_selects_drink() -> None:
    """Low water satisfaction yields drink as the top action."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.9, water=0.05, energy=0.9, social=0.9, safety=0.9),
    )
    assert UtilityPolicy().select(agent).action is ActionKind.DRINK


def test_satisfied_agent_prefers_idle() -> None:
    """When all needs are high, idle outranks restorative actions."""
    agent = Agent.create(agent_id=0, name="A", needs=Needs())
    scores = UtilityPolicy().score_all(agent)
    assert max(scores, key=scores.get) == ActionKind.IDLE.value
    assert UtilityPolicy().select(agent).action is ActionKind.IDLE


def test_extraversion_raises_socialize_utility() -> None:
    """Higher extraversion increases socialize utility."""
    needs = Needs(food=0.8, water=0.8, energy=0.8, social=0.4, safety=0.8)
    introvert = Agent.create(
        agent_id=0,
        name="I",
        needs=needs,
        personality=Personality(extraversion=0.1),
    )
    extrovert = Agent.create(
        agent_id=1,
        name="E",
        needs=needs,
        personality=Personality(extraversion=0.9),
    )
    policy = UtilityPolicy()
    assert policy.score(extrovert, ActionKind.SOCIALIZE) > policy.score(
        introvert, ActionKind.SOCIALIZE
    )


def test_goal_bonus_can_tip_selection() -> None:
    """A matching high-priority goal can override raw need urgency."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.55, water=0.5, energy=0.9, social=0.9, safety=0.9),
        personality=Personality(),
    )
    # Without goals, water is slightly more urgent than food.
    policy = UtilityPolicy(PolicyConfig(goal_weight=0.5))
    assert policy.select(agent).action is ActionKind.DRINK

    driven = agent.model_copy(
        update={
            "goals": GoalSet(goals=(Goal(kind="satisfy_food", priority=1.0),)),
        }
    )
    assert policy.select(driven).action is ActionKind.EAT


def test_tie_breaks_by_action_name() -> None:
    """Equal utilities resolve to the lexicographically earlier action."""
    policy = UtilityPolicy(
        PolicyConfig(goal_weight=0.0, idle_weight=0.0, personality_floor=1.0)
    )
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.5, water=0.5, energy=1.0, social=1.0, safety=1.0),
        personality=Personality(
            openness=0.0,
            conscientiousness=0.0,
            extraversion=0.0,
            agreeableness=0.0,
            neuroticism=0.0,
        ),
    )
    # Food and water urgency are both 0.5; tie-break prefers 'drink' < 'eat'.
    assert policy.select(agent).action is ActionKind.DRINK


def test_select_rejects_dead_agent() -> None:
    """Dead agents cannot receive an action selection."""
    dead = Agent.create(agent_id=0, name="D").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    with pytest.raises(ValueError, match="non-living"):
        UtilityPolicy().select(dead)


def test_select_all_skips_dead_and_publishes_events() -> None:
    """select_all covers living agents only and emits ActionSelected."""
    living = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.1, water=0.9, energy=0.9, social=0.9, safety=0.9),
    )
    dead = Agent.create(agent_id=1, name="B").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(living, dead),
    )
    bus = EventBus()
    choices = UtilityPolicy().select_all(world, bus=bus)
    assert len(choices) == 1
    assert choices[0].action is ActionKind.EAT
    assert len(bus.history) == 1
    assert isinstance(bus.history[0], ActionSelected)
    assert bus.history[0].action == "eat"


def test_policy_is_deterministic_for_seed_forty_two_world() -> None:
    """Seed 42 worlds produce identical action choice sequences."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=8))
    policy = UtilityPolicy()
    first = policy.select_all(world)
    second = policy.select_all(world)
    assert first == second
    assert len(first) == 8


def test_action_catalog_is_complete_and_stable() -> None:
    """Catalog order is fixed and covers every ActionKind exactly once."""
    assert ACTION_CATALOG == (
        ActionKind.EAT,
        ActionKind.DRINK,
        ActionKind.REST,
        ActionKind.SOCIALIZE,
        ActionKind.SEEK_SAFETY,
        ActionKind.MOVE,
        ActionKind.IDLE,
    )
    assert len(ACTION_CATALOG) == len(set(ACTION_CATALOG))
    assert set(ACTION_CATALOG) == set(ActionKind)


def test_open_satisfied_agent_selects_move_on_map() -> None:
    """High openness with satisfied needs prefers MOVE when neighbors exist."""
    agent = Agent.create(
        agent_id=0,
        name="Explorer",
        needs=Needs(),
        personality=Personality(openness=1.0, agreeableness=0.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(agent,),
    )
    choice = UtilityPolicy().select(agent, world=world)
    assert choice.action is ActionKind.MOVE
    assert choice.target_location_id is not None
    assert choice.target_location_id.value in {1, 3}


def test_move_unavailable_without_world_or_energy() -> None:
    """MOVE is skipped when no world is provided or energy is insufficient."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(),
        personality=Personality(openness=1.0),
    )
    choice = UtilityPolicy().select(agent)
    assert choice.action is not ActionKind.MOVE
    assert choice.target_location_id is None

    tired = agent.model_copy(
        update={
            "needs": Needs(food=1.0, water=1.0, energy=0.01, social=1.0, safety=1.0),
            "personality": Personality(openness=1.0, agreeableness=0.0),
        }
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(tired,),
    )
    assert UtilityPolicy().select(tired, world=world).action is not ActionKind.MOVE
