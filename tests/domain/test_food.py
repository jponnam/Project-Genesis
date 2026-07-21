"""Unit tests for domain food consumption helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    Agent,
    AgentStatus,
    Health,
    Inventory,
    Needs,
    ResourceStack,
    apply_eat,
    can_eat,
)


def _with_food(quantity: int = 1, *, food_need: float = 0.4) -> Agent:
    return Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(
            food=food_need,
            water=1.0,
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


def test_can_eat_requires_inventory_food() -> None:
    """Agents without food cannot eat."""
    assert can_eat(Agent.create(agent_id=0, name="A")) is False
    assert can_eat(_with_food(1)) is True


def test_apply_eat_consumes_food_and_restores_need() -> None:
    """Eating decrements inventory and raises food satisfaction."""
    agent = _with_food(2, food_need=0.4)
    updated = apply_eat(agent, restore=0.25, amount=1)
    assert updated is not None
    assert updated.inventory.quantity("food") == 1
    assert updated.needs.food == pytest.approx(0.65)


def test_apply_eat_rejects_empty_inventory() -> None:
    """Eating without food returns None."""
    assert apply_eat(Agent.create(agent_id=0, name="A")) is None


def test_apply_eat_rejects_dead_agent() -> None:
    """Dead agents cannot eat even with food on hand."""
    dead = _with_food(1).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_eat(dead) is False
    assert apply_eat(dead) is None


def test_apply_eat_clamps_food_need() -> None:
    """Food restoration cannot exceed 1.0."""
    updated = apply_eat(_with_food(1, food_need=0.9), restore=0.5)
    assert updated is not None
    assert updated.needs.food == 1.0
