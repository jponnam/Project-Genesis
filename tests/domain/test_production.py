"""Unit tests for domain production recipes and crafting helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    RECIPE_CATALOG,
    Agent,
    AgentStatus,
    Health,
    Inventory,
    Needs,
    Recipe,
    ResourceStack,
    apply_produce,
    can_produce,
    producible_recipes,
    recipe_by_id,
)


def _crafter(
    *,
    food: int = 0,
    water: int = 0,
    wood: int = 0,
    stone: int = 0,
    energy: float = 1.0,
) -> Agent:
    stacks = [
        ResourceStack(resource=name, quantity=qty)
        for name, qty in (
            ("food", food),
            ("stone", stone),
            ("water", water),
            ("wood", wood),
        )
        if qty > 0
    ]
    stacks.sort(key=lambda stack: stack.resource)
    return Agent.create(agent_id=0, name="Crafter").model_copy(
        update={
            "inventory": Inventory(stacks=tuple(stacks)),
            "needs": Needs(
                food=1.0,
                water=1.0,
                energy=energy,
                social=1.0,
                safety=1.0,
            ),
        }
    )


def test_recipe_catalog_is_stable_and_sorted() -> None:
    """Catalog contains rations and tools in ascending recipe_id order."""
    assert tuple(recipe.recipe_id for recipe in RECIPE_CATALOG) == ("rations", "tools")
    assert recipe_by_id("rations") is not None
    assert recipe_by_id("tools") is not None
    assert recipe_by_id("missing") is None


def test_recipe_rejects_unsorted_inputs() -> None:
    """Recipe inputs must be unique and sorted by resource name."""
    with pytest.raises(ValidationError):
        Recipe(
            recipe_id="bad",
            inputs=(
                ResourceStack(resource="wood", quantity=1),
                ResourceStack(resource="stone", quantity=1),
            ),
            outputs=(ResourceStack(resource="tools", quantity=1),),
        )


def test_can_produce_and_apply_rations() -> None:
    """Rations consume food+water, add output, and spend energy."""
    agent = _crafter(food=2, water=1, energy=0.5)
    assert can_produce(agent, "rations") is True
    updated = apply_produce(agent, "rations")
    assert updated is not None
    assert updated.inventory.quantity("food") == 0
    assert updated.inventory.quantity("water") == 0
    assert updated.inventory.quantity("rations") == 1
    assert updated.needs.energy == pytest.approx(0.45)


def test_can_produce_and_apply_tools() -> None:
    """Tools consume stone+wood and spend the default energy cost."""
    agent = _crafter(stone=1, wood=2, energy=1.0)
    assert can_produce(agent, "tools") is True
    updated = apply_produce(agent, "tools")
    assert updated is not None
    assert updated.inventory.quantity("stone") == 0
    assert updated.inventory.quantity("wood") == 0
    assert updated.inventory.quantity("tools") == 1
    assert updated.needs.energy == pytest.approx(0.9)


def test_can_produce_rejects_illegal_cases() -> None:
    """Missing inputs, energy, unknown recipes, and death block crafting."""
    poor = _crafter(food=1, water=1)
    assert can_produce(poor, "rations") is False
    assert apply_produce(poor, "rations") is None

    tired = _crafter(food=2, water=1, energy=0.01)
    assert can_produce(tired, "rations") is False

    dead = _crafter(food=2, water=1).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_produce(dead, "rations") is False
    assert can_produce(_crafter(food=2, water=1), "alchemy") is False


def test_producible_recipes_returns_catalog_order() -> None:
    """Only affordable recipes appear, preserving catalog order."""
    agent = _crafter(food=2, water=1, stone=1, wood=2)
    assert tuple(recipe.recipe_id for recipe in producible_recipes(agent)) == (
        "rations",
        "tools",
    )
    rations_only = _crafter(food=2, water=1)
    assert tuple(recipe.recipe_id for recipe in producible_recipes(rations_only)) == (
        "rations",
    )


def test_energy_cost_override_enables_and_spends_discounted_cost() -> None:
    """Optional energy_cost overrides recipe cost for legality and spending."""
    tired = _crafter(food=2, water=1, energy=0.03)
    assert can_produce(tired, "rations") is False
    assert can_produce(tired, "rations", energy_cost=0.02) is True
    updated = apply_produce(tired, "rations", energy_cost=0.02)
    assert updated is not None
    assert updated.needs.energy == pytest.approx(0.01)
    assert updated.inventory.quantity("rations") == 1

    agent = _crafter(food=2, water=1, stone=1, wood=2, energy=0.04)
    recipes = producible_recipes(agent, energy_cost_fn=lambda recipe: 0.02)
    assert tuple(recipe.recipe_id for recipe in recipes) == ("rations", "tools")
