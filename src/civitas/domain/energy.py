"""Energy helpers for REST recovery and activity costs.

Restoring energy does not consume inventory. Domain helpers keep the
energy system, action executor, and geography relocation aligned without
systems calling each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.numeric import clamp_unit

if TYPE_CHECKING:
    from civitas.domain.agent import Agent

DEFAULT_REST_RESTORE: float = 0.20


def can_rest(agent: Agent) -> bool:
    """Return True when ``agent`` is alive and energy is below full."""
    if not agent.is_alive():
        return False
    return agent.needs.energy < 1.0


def apply_rest(
    agent: Agent,
    *,
    restore: float = DEFAULT_REST_RESTORE,
) -> Agent | None:
    """Restore the energy need for a resting agent.

    Returns the updated agent, or ``None`` when resting is illegal
    (dead, already at full energy, or negative ``restore``).
    """
    if restore < 0.0:
        return None
    if not can_rest(agent):
        return None

    previous = agent.needs.energy
    current = clamp_unit(previous + restore)
    if current == previous:
        return None
    new_needs = agent.needs.model_copy(update={"energy": current})
    return agent.model_copy(update={"needs": new_needs})


def spend_energy(agent: Agent, amount: float) -> Agent | None:
    """Deduct ``amount`` energy from a living agent.

    Returns the updated agent, or ``None`` when the agent is dead,
    ``amount`` is negative, or energy is insufficient.
    """
    if amount < 0.0:
        msg = f"energy amount must be >= 0, got {amount}"
        raise ValueError(msg)
    if not agent.is_alive():
        return None
    if agent.needs.energy < amount:
        return None
    if amount == 0.0:
        return agent
    new_energy = clamp_unit(agent.needs.energy - amount)
    new_needs = agent.needs.model_copy(update={"energy": new_energy})
    return agent.model_copy(update={"needs": new_needs})
