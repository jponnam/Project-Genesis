"""Unit tests for the ActionExecutor."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    ActionChoice,
    ActionCompleted,
    ActionKind,
    Agent,
    AgentId,
    AgentMoved,
    AgentStatus,
    Health,
    Inventory,
    Location,
    LocationId,
    LocationKind,
    NeedDecayed,
    Needs,
    ResourceConsumed,
    ResourceGathered,
    ResourceStack,
    SimulationConfig,
    World,
    location_stock,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import ActionConfig, ActionExecutor, NeedsSystem, UtilityPolicy


def _choice(agent_id: int, action: ActionKind, utility: float = 1.0) -> ActionChoice:
    return ActionChoice(
        agent_id=AgentId(value=agent_id),
        action=action,
        utility=utility,
    )


def _with_food(
    agent_id: int,
    *,
    food_need: float,
    quantity: int = 1,
    water_need: float = 1.0,
) -> Agent:
    return Agent.create(
        agent_id=agent_id,
        name=f"A{agent_id}",
        needs=Needs(
            food=food_need,
            water=water_need,
            energy=1.0,
            social=1.0,
            safety=1.0,
        ),
    ).model_copy(
        update={
            "inventory": Inventory(
                stacks=(ResourceStack(resource="food", quantity=quantity),)
            )
        }
    )


def test_eat_restores_food_need() -> None:
    """Eating increases food satisfaction by the configured amount."""
    agent = _with_food(0, food_need=0.4, quantity=1)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.EAT), bus=bus)
    assert updated.agents[0].needs.food == pytest.approx(0.65)
    assert updated.agents[0].inventory.quantity("food") == 0
    assert any(isinstance(event, NeedDecayed) for event in bus.history)
    assert any(isinstance(event, ResourceConsumed) for event in bus.history)
    assert any(
        isinstance(event, ActionCompleted) and event.success for event in bus.history
    )


def test_eat_fails_without_inventory_food() -> None:
    """Eating without food fails and does not restore the food need."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.4, water=1.0, energy=1.0, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.EAT), bus=bus)
    assert updated.agents[0].needs.food == pytest.approx(0.4)
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is False
    assert not any(isinstance(event, ResourceConsumed) for event in bus.history)


def test_idle_succeeds_without_state_change() -> None:
    """Idle completes successfully and leaves needs unchanged."""
    agent = Agent.create(agent_id=0, name="A")
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )
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
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(dead,),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.EAT), bus=bus)
    assert updated.agents[0] == dead
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is False


def test_execute_all_applies_in_agent_id_order() -> None:
    """execute_all sorts choices by agent id before applying."""
    agents = (
        _with_food(0, food_need=0.5, quantity=1),
        Agent.create(
            agent_id=1,
            name="B",
            needs=Needs(food=1.0, water=0.5, energy=1.0, social=1.0, safety=1.0),
        ).model_copy(
            update={
                "inventory": Inventory(
                    stacks=(ResourceStack(resource="water", quantity=1),)
                )
            }
        ),
    )
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )
    choices = (
        _choice(1, ActionKind.DRINK),
        _choice(0, ActionKind.EAT),
    )
    bus = EventBus()
    updated = ActionExecutor().execute_all(world, choices, bus=bus)
    assert updated.agents[0].needs.food == pytest.approx(0.75)
    assert updated.agents[1].needs.water == pytest.approx(0.80)
    assert updated.agents[1].inventory.quantity("water") == 0
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert [event.agent_id.value for event in completed] == [0, 1]


def test_drink_fails_without_inventory_water() -> None:
    """Drinking without water fails and does not restore the water need."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=0.4, energy=1.0, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.DRINK), bus=bus)
    assert updated.agents[0].needs.water == pytest.approx(0.4)
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is False
    assert not any(isinstance(event, ResourceConsumed) for event in bus.history)


def test_drink_consumes_water_and_restores_need() -> None:
    """DRINK consumes inventory water and restores the water need."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=0.4, energy=1.0, social=1.0, safety=1.0),
    ).model_copy(
        update={
            "inventory": Inventory(
                stacks=(ResourceStack(resource="water", quantity=2),)
            )
        }
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, _choice(0, ActionKind.DRINK), bus=bus)
    assert updated.agents[0].needs.water == pytest.approx(0.70)
    assert updated.agents[0].inventory.quantity("water") == 1
    assert any(
        isinstance(event, ResourceConsumed) and event.resource == "water"
        for event in bus.history
    )


def test_restore_clamps_at_one() -> None:
    """Need restoration cannot exceed 1.0."""
    agent = _with_food(0, food_need=0.9, quantity=1)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )
    updated = ActionExecutor(ActionConfig(eat=0.5)).execute(
        world, _choice(0, ActionKind.EAT)
    )
    assert updated.agents[0].needs.food == 1.0


def test_missing_agent_raises() -> None:
    """Executing a choice for an absent agent is an error."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
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


def test_move_relocates_agent_and_emits_agent_moved() -> None:
    """MOVE updates location, spends energy, and emits AgentMoved."""
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    agent = Agent.create(agent_id=0, name="A", location_id=0)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(agent,),
    )
    choice = ActionChoice(
        agent_id=AgentId(value=0),
        action=ActionKind.MOVE,
        utility=1.0,
        target_location_id=LocationId(value=1),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, choice, bus=bus)
    assert updated.agents[0].location_id.value == 1
    assert updated.agents[0].needs.energy == pytest.approx(0.95)
    assert any(isinstance(event, AgentMoved) for event in bus.history)
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is True


def test_move_fails_when_destination_full() -> None:
    """MOVE fails cleanly when the destination is at capacity."""
    plain = Location.create(1, "Plain", 1, 0, capacity=1)
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(
            Agent.create(agent_id=0, name="A", location_id=1),
            Agent.create(agent_id=1, name="B", location_id=0),
        ),
    )
    choice = ActionChoice(
        agent_id=AgentId(value=1),
        action=ActionKind.MOVE,
        utility=1.0,
        target_location_id=LocationId(value=1),
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, choice, bus=bus)
    assert updated.agents[1].location_id.value == 0
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is False


def test_gather_transfers_deposit_into_inventory() -> None:
    """GATHER depletes location stock and emits ResourceGathered."""
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, forest),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    choice = ActionChoice(
        agent_id=AgentId(value=0),
        action=ActionKind.GATHER,
        utility=1.0,
        target_resource="wood",
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, choice, bus=bus)
    assert updated.agents[0].inventory.quantity("wood") == 1
    assert location_stock(updated.locations[1], "wood") == 15
    assert any(isinstance(event, ResourceGathered) for event in bus.history)
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is True


def test_gather_fails_when_stock_missing() -> None:
    """GATHER fails when the current location lacks the resource."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    choice = ActionChoice(
        agent_id=AgentId(value=0),
        action=ActionKind.GATHER,
        utility=1.0,
        target_resource="food",
    )
    bus = EventBus()
    updated = ActionExecutor().execute(world, choice, bus=bus)
    assert updated.agents[0].inventory.quantity("food") == 0
    completed = [event for event in bus.history if isinstance(event, ActionCompleted)]
    assert completed[0].success is False
