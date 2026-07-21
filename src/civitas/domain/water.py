"""Water consumption helpers for the DRINK action.

Drinking requires inventory water. Domain helpers keep the water system
and action executor aligned without either calling the other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.numeric import clamp_unit

if TYPE_CHECKING:
    from civitas.domain.agent import Agent

# Keep as a plain string to avoid importing resources (circular with location).
WATER_RESOURCE: str = "water"
DEFAULT_DRINK_CONSUME_AMOUNT: int = 1
DEFAULT_DRINK_RESTORE: float = 0.30


def can_drink(agent: Agent, *, amount: int = DEFAULT_DRINK_CONSUME_AMOUNT) -> bool:
    """Return True when ``agent`` can consume ``amount`` water."""
    if amount <= 0:
        return False
    if not agent.is_alive():
        return False
    return agent.inventory.quantity(WATER_RESOURCE) >= amount


def apply_drink(
    agent: Agent,
    *,
    restore: float = DEFAULT_DRINK_RESTORE,
    amount: int = DEFAULT_DRINK_CONSUME_AMOUNT,
) -> Agent | None:
    """Consume inventory water and restore the water need.

    Returns the updated agent, or ``None`` when drinking is illegal
    (dead, insufficient water, or non-positive ``amount`` / ``restore``).
    """
    if amount <= 0 or restore < 0.0:
        return None
    if not can_drink(agent, amount=amount):
        return None

    previous = agent.needs.water
    current = clamp_unit(previous + restore)
    new_inventory = agent.inventory.remove(WATER_RESOURCE, amount)
    new_needs = agent.needs.model_copy(update={"water": current})
    return agent.model_copy(update={"inventory": new_inventory, "needs": new_needs})
