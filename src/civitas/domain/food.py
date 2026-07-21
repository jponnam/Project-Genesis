"""Food consumption helpers for the EAT action.

Eating requires inventory food. Domain helpers keep the food system and
action executor aligned without either calling the other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.numeric import clamp_unit

if TYPE_CHECKING:
    from civitas.domain.agent import Agent

# Keep as a plain string to avoid importing resources (circular with location).
FOOD_RESOURCE: str = "food"
DEFAULT_EAT_CONSUME_AMOUNT: int = 1
DEFAULT_EAT_RESTORE: float = 0.25


def can_eat(agent: Agent, *, amount: int = DEFAULT_EAT_CONSUME_AMOUNT) -> bool:
    """Return True when ``agent`` can consume ``amount`` food."""
    if amount <= 0:
        return False
    if not agent.is_alive():
        return False
    return agent.inventory.quantity(FOOD_RESOURCE) >= amount


def apply_eat(
    agent: Agent,
    *,
    restore: float = DEFAULT_EAT_RESTORE,
    amount: int = DEFAULT_EAT_CONSUME_AMOUNT,
) -> Agent | None:
    """Consume inventory food and restore the food need.

    Returns the updated agent, or ``None`` when eating is illegal
    (dead, insufficient food, or non-positive ``amount`` / ``restore``).
    """
    if amount <= 0 or restore < 0.0:
        return None
    if not can_eat(agent, amount=amount):
        return None

    previous = agent.needs.food
    current = clamp_unit(previous + restore)
    new_inventory = agent.inventory.remove(FOOD_RESOURCE, amount)
    new_needs = agent.needs.model_copy(update={"food": current})
    return agent.model_copy(update={"inventory": new_inventory, "needs": new_needs})
