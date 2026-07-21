"""Unit tests for the ActionExecutor."""

from __future__ import annotations

import pytest

from civitas.domain import (
    ActionChoice,
    ActionCompleted,
    ActionKind,
    Agent,
    AgentId,
    AgentStatus,
    Health,
    Inventory,
    NeedDecayed,
    Needs,
    ResourceConsumed,
    ResourceStack,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import ActionConfig, ActionExecutor, NeedsSystem, UtilityPolicy


def _choice(agent_id: int, action: ActionKind, utility: float = 1.0) -> ActionChoice:
    return ActionChoice(
        agent_id=AgentId(value=agent_id),
        action=action,
        utility=utility,
    )


def test_eat_restores_food_need() -> None:
    """Eating increases food satisfaction by the configured amount."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.4, water=1.0, energy=1.0, social=1.0, safety=1.0),
    )
    world = World(config=SimulationConfig(agent_count=1, seed=1), agents=(agent,))
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.EAT), bus=bus)
    assert updated.agents[0].needs.food == pytest.approx(0.65)
    assert any(isinstance(event, NeedDecayed) for event in bus.history)
    assert any(
        isinstance(event, ActionCompleted) and event.success for event in bus.history
    )


def test_eat_consumes_inventory_food_when_present() -> None:
    """Eating with food in inventory emits ResourceConsumed and decrements stock."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.5, water=1.0, energy=1.0, social=1.0, safety=1.0),
    ).model_copy(
        update={
            "inventory": Inventory(stacks=(ResourceStack(resource="food", quantity=2),))
        }
    )
    world = World(config=SimulationConfig(agent_count=1, seed=1), agents=(agent,))
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.EAT), bus=bus)
    assert updated.agents[0].inventory.quantity("food") == 1
    assert any(isinstance(event, ResourceConsumed) for event in bus.history)


def test_idle_succeeds_without_state_change() -> None:
    """Idle completes successfully and leaves needs unchanged."""
    agent = Agent.create(agent_id=0, name="A")
    world = World(config=SimulationConfig(agent_count=1, seed=1), agents=(agent,))
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.IDLE), bus=bus)
    assert updated.agents[0].needs == agent.needs
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert len(completed) == 1
    assert completed[0].success is True


def test_dead_agent_action_fails() -> None:
    """Actions on dead agents fail and do not alter state."""
    dead = Agent.create(agent_id=0, name="D").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = World(config=SimulationConfig(agent_count=1, seed=1), agents=(dead,))
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.EAT), bus=bus)
    assert updated.agents[0] == dead
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is False


def test_execute_all_applies_in_agent_id_order() -> None:
    """execute_all sorts choices by agent id before applying."""
    agents = (
        Agent.create(
            agent_id=0,
            name="A",
            needs=Needs(food=0.5, water=1.0, energy=1.0, social=1.0, safety=1.0),
        ),
        Agent.create(
            agent_id=1,
            name="B",
            needs=Needs(food=1.0, water=0.5, energy=1.0, social=1.0, safety=1.0),
        ),
    )
    world = World(config=SimulationConfig(agent_count=2, seed=1), agents=agents)
    choices = (
        _choice(1, ActionKind.DRINK),
        _choice(0, ActionKind.EAT),
    )
    bus = EventBus()
    updated = ActionExecutor().execute_all(world, choices, bus=bus)
    assert updated.agents[0].needs.food == pytest.approx(0.75)
    assert updated.agents[1].needs.water == pytest.approx(0.80)
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert [event.agent_id.value for event in completed] == [0, 1]


def test_restore_clamps_at_one() -> None:
    """Need restoration cannot exceed 1.0."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.9, water=1.0, energy=1.0, social=1.0, safety=1.0),
    )
    world = World(config=SimulationConfig(agent_count=1, seed=1), agents=(agent,))
    updated = ActionExecutor(ActionConfig(eat=0.5)).execute(
        world, _choice(0, ActionKind.EAT)
    )
    assert updated.agents[0].needs.food == 1.0


def test_missing_agent_raises() -> None:
    """Executing a choice for an absent agent is an error."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    with pytest.raises(ValueError, match="not found"):
        ActionExecutor().execute(world, _choice(9, ActionKind.IDLE))


def test_policy_to_executor_pipeline_is_deterministic() -> None:
    """Engine-style select-then-execute orchestration is reproducible."""
    config = SimulationConfig(seed=42, agent_count=5, ticks=10)
    policy = UtilityPolicy()
    executor = ActionExecutor()
    needs = NeedsSystem()

    def run() -> World:
        world = WorldFactory().create(config)
        world = needs.apply_decay(world)
        choices = policy.select_all(world)
        return executor.execute_all(world, choices)

    assert run() == run()
