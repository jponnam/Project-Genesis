"""Production recipes and crafting helpers.

Agents convert inventory inputs into crafted outputs by paying an energy
cost. Recipes are a fixed deterministic catalog — no RNG. Domain helpers
keep the production system and action executor aligned without systems
calling each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

from civitas.domain.attributes import ResourceStack
from civitas.domain.energy import spend_energy
from civitas.domain.types import NonEmptyStr, UnitInterval

if TYPE_CHECKING:
    from collections.abc import Callable

    from civitas.domain.agent import Agent

DEFAULT_PRODUCE_ENERGY_COST: float = 0.10

TOOLS_RESOURCE: str = "tools"
RATIONS_RESOURCE: str = "rations"


class Recipe(BaseModel):
    """Immutable crafting recipe with sorted input/output stacks."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    recipe_id: NonEmptyStr
    inputs: tuple[ResourceStack, ...]
    outputs: tuple[ResourceStack, ...]
    energy_cost: UnitInterval = DEFAULT_PRODUCE_ENERGY_COST

    @model_validator(mode="after")
    def stacks_must_be_sorted_and_positive(self) -> Self:
        """Reject empty, unsorted, or non-positive recipe stacks."""
        if not self.inputs:
            msg = "recipe inputs must be non-empty"
            raise ValueError(msg)
        if not self.outputs:
            msg = "recipe outputs must be non-empty"
            raise ValueError(msg)
        for label, stacks in (("inputs", self.inputs), ("outputs", self.outputs)):
            names = [stack.resource for stack in stacks]
            if len(names) != len(set(names)):
                msg = f"recipe {label} resources must be unique"
                raise ValueError(msg)
            if names != sorted(names):
                msg = f"recipe {label} must be ordered by resource name"
                raise ValueError(msg)
            if any(stack.quantity < 1 for stack in stacks):
                msg = f"recipe {label} quantities must be >= 1"
                raise ValueError(msg)
        return self


def _stack(resource: str, quantity: int) -> ResourceStack:
    return ResourceStack(resource=resource, quantity=quantity)


# Stable catalog keyed by recipe_id; iteration order is recipe_id ascending.
PRODUCTION_RECIPES: dict[str, Recipe] = {
    "rations": Recipe(
        recipe_id="rations",
        inputs=(_stack("food", 2), _stack("water", 1)),
        outputs=(_stack(RATIONS_RESOURCE, 1),),
        energy_cost=0.05,
    ),
    "tools": Recipe(
        recipe_id="tools",
        inputs=(_stack("stone", 1), _stack("wood", 2)),
        outputs=(_stack(TOOLS_RESOURCE, 1),),
        energy_cost=DEFAULT_PRODUCE_ENERGY_COST,
    ),
}

RECIPE_CATALOG: tuple[Recipe, ...] = tuple(
    PRODUCTION_RECIPES[key] for key in sorted(PRODUCTION_RECIPES)
)


def recipe_by_id(recipe_id: str) -> Recipe | None:
    """Return the recipe for ``recipe_id``, or ``None`` if unknown."""
    return PRODUCTION_RECIPES.get(recipe_id)


def can_produce(
    agent: Agent,
    recipe_id: str,
    *,
    energy_cost: float | None = None,
) -> bool:
    """Return True when a living agent can craft ``recipe_id`` right now."""
    recipe = recipe_by_id(recipe_id)
    if recipe is None:
        return False
    if not agent.is_alive():
        return False
    cost = recipe.energy_cost if energy_cost is None else energy_cost
    if agent.needs.energy < cost:
        return False
    return all(
        agent.inventory.quantity(stack.resource) >= stack.quantity
        for stack in recipe.inputs
    )


def apply_produce(
    agent: Agent,
    recipe_id: str,
    *,
    energy_cost: float | None = None,
) -> Agent | None:
    """Craft ``recipe_id`` for ``agent`` when legal.

    Consumes inputs, adds outputs, and spends the effective energy cost.
    Returns the updated agent, or ``None`` when crafting is illegal.
    """
    recipe = recipe_by_id(recipe_id)
    if recipe is None:
        return None
    cost = recipe.energy_cost if energy_cost is None else energy_cost
    if not can_produce(agent, recipe_id, energy_cost=cost):
        return None

    inventory = agent.inventory
    for stack in recipe.inputs:
        try:
            inventory = inventory.remove(stack.resource, stack.quantity)
        except ValueError:
            return None
    for stack in recipe.outputs:
        inventory = inventory.add(stack.resource, stack.quantity)

    crafted = agent.model_copy(update={"inventory": inventory})
    return spend_energy(crafted, cost)


def producible_recipes(
    agent: Agent,
    *,
    energy_cost_fn: Callable[[Recipe], float] | None = None,
) -> tuple[Recipe, ...]:
    """Return recipes ``agent`` can craft, in catalog order."""
    result: list[Recipe] = []
    for recipe in RECIPE_CATALOG:
        cost = None if energy_cost_fn is None else energy_cost_fn(recipe)
        if can_produce(agent, recipe.recipe_id, energy_cost=cost):
            result.append(recipe)
    return tuple(result)
