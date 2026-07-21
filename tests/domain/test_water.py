"""Unit tests for domain water consumption helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    Agent,
    AgentStatus,
    Health,
    Inventory,
    Needs,
    ResourceStack,
    apply_drink,
    can_drink,
)


def _with_water(quantity: int = 1, *, water_need: float = 0.4) -> Agent:
    return Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(
            food=1.0,
            water=water_need,
            energy=1.0,
            social=1.0,
            safety=1.0,
        ),
    ).model_copy(
        update={
            "inventory": Inventory(
                stacks=(ResourceStack(resource="water", quantity=quantity),)
            )
        }
    )


def test_can_drink_requires_inventory_water() -> None:
    """Agents without water cannot drink."""
    assert can_drink(Agent.create(agent_id=0, name="A")) is False
    assert can_drink(_with_water(1)) is True


def test_apply_drink_consumes_water_and_restores_need() -> None:
    """Drinking decrements inventory and raises water satisfaction."""
    agent = _with_water(2, water_need=0.4)
    updated = apply_drink(agent, restore=0.30, amount=1)
    assert updated is not None
    assert updated.inventory.quantity("water") == 1
    assert updated.needs.water == pytest.approx(0.70)


def test_apply_drink_rejects_empty_inventory() -> None:
    """Drinking without water returns None."""
    assert apply_drink(Agent.create(agent_id=0, name="A")) is None


def test_apply_drink_rejects_dead_agent() -> None:
    """Dead agents cannot drink even with water on hand."""
    dead = _with_water(1).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_drink(dead) is False
    assert apply_drink(dead) is None


def test_apply_drink_clamps_water_need() -> None:
    """Water restoration cannot exceed 1.0."""
    updated = apply_drink(_with_water(1, water_need=0.9), restore=0.5)
    assert updated is not None
    assert updated.needs.water == 1.0
