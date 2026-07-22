"""Unit tests for the FoodSystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    DEFAULT_EAT_RESTORE,
    ZONING_EAT_RESTORE_BONUS,
    Agent,
    Government,
    Inventory,
    Law,
    LawKind,
    NeedDecayed,
    Needs,
    ResourceConsumed,
    ResourceStack,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus
from civitas.systems import FoodConfig, FoodSystem


def _world_with_food(quantity: int = 2) -> World:
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.5, water=1.0, energy=1.0, social=1.0, safety=1.0),
    ).model_copy(
        update={
            "inventory": Inventory(
                stacks=(ResourceStack(resource="food", quantity=quantity),)
            )
        }
    )
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )


def test_eat_emits_consume_and_need_events() -> None:
    """Successful eat publishes ResourceConsumed and food NeedDecayed."""
    world = _world_with_food()
    bus = EventBus()
    updated = FoodSystem().eat(world, 0, bus=bus)
    assert updated.agents[0].inventory.quantity("food") == 1
    assert updated.agents[0].needs.food == pytest.approx(0.75)
    assert any(
        isinstance(event, ResourceConsumed) and event.resource == "food"
        for event in bus.history
    )
    assert any(
        isinstance(event, NeedDecayed) and event.need == "food" for event in bus.history
    )


def test_eat_without_food_is_noop() -> None:
    """Eating with an empty inventory leaves the world unchanged."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    system = FoodSystem()
    assert system.can_eat(world, 0) is False
    assert system.eat(world, 0, bus=bus) == world
    assert bus.history == ()


def test_food_config_controls_restore_and_amount() -> None:
    """FoodConfig restore and consume_amount are applied."""
    world = _world_with_food(quantity=3)
    updated = FoodSystem(FoodConfig(restore=0.4, consume_amount=2)).eat(world, 0)
    assert updated.agents[0].inventory.quantity("food") == 1
    assert updated.agents[0].needs.food == pytest.approx(0.9)


def test_eat_uses_active_zoning_restore_bonus() -> None:
    """FoodSystem.eat includes subject-scoped zoning eat restore bonus."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.4, water=1.0, energy=1.0, social=1.0, safety=1.0),
    ).model_copy(
        update={
            "inventory": Inventory(stacks=(ResourceStack(resource="food", quantity=2),))
        }
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Zoning", LawKind.ZONING),),
        agents=(agent,),
    )
    updated = FoodSystem().eat(world, 0)
    assert updated.agents[0].needs.food == pytest.approx(
        0.4 + DEFAULT_EAT_RESTORE + ZONING_EAT_RESTORE_BONUS
    )


def test_missing_agent_raises() -> None:
    """eat raises when the agent id is absent."""
    world = _world_with_food()
    with pytest.raises(ValueError, match="not found"):
        FoodSystem().eat(world, 9)
