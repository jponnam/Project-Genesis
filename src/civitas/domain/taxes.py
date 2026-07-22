"""Tax levy helpers for integer money collection into the treasury.

Living agents pay a flat poll tax plus an optional basis-point wealth
component each levy. Collection is capped at the agent's balance so poor
agents pay what they can. Money math stays integer-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.economy import debit_money
from civitas.domain.ids import AgentId

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

DEFAULT_FLAT_AMOUNT: int = 1
DEFAULT_RATE_BPS: int = 0
BPS_DENOMINATOR: int = 10_000


def tax_due(
    agent: Agent,
    *,
    flat_amount: int = DEFAULT_FLAT_AMOUNT,
    rate_bps: int = DEFAULT_RATE_BPS,
) -> int:
    """Return the nominal tax owed by ``agent`` (0 when not living)."""
    if flat_amount < 0:
        msg = f"flat_amount must be >= 0, got {flat_amount}"
        raise ValueError(msg)
    if rate_bps < 0:
        msg = f"rate_bps must be >= 0, got {rate_bps}"
        raise ValueError(msg)
    if not agent.is_alive():
        return 0
    percentage = (agent.money * rate_bps) // BPS_DENOMINATOR
    return flat_amount + percentage


def collectable_tax(
    agent: Agent,
    *,
    flat_amount: int = DEFAULT_FLAT_AMOUNT,
    rate_bps: int = DEFAULT_RATE_BPS,
) -> int:
    """Return how much tax can actually be collected from ``agent``."""
    due = tax_due(agent, flat_amount=flat_amount, rate_bps=rate_bps)
    if due == 0 or not agent.is_alive():
        return 0
    return min(due, agent.money)


def apply_tax(world: World, agent_id: AgentId | int, amount: int) -> World | None:
    """Debit ``amount`` from ``agent_id`` into ``world.treasury``.

    Returns the updated world, or ``None`` when the agent is missing, dead,
    or cannot afford ``amount``. ``amount`` of 0 is a no-op success for
    living agents.
    """
    if amount < 0:
        msg = f"tax amount must be >= 0, got {amount}"
        raise ValueError(msg)

    agent = world.agent_by_id(agent_id)
    if agent is None or not agent.is_alive():
        return None
    if amount == 0:
        return world

    debited = debit_money(agent, amount)
    if debited is None:
        return None
    world = world.with_agent(debited)
    return world.with_treasury(world.treasury + amount)


def levy_taxes(
    world: World,
    *,
    flat_amount: int = DEFAULT_FLAT_AMOUNT,
    rate_bps: int = DEFAULT_RATE_BPS,
) -> tuple[World, tuple[tuple[AgentId, int, int], ...]]:
    """Collect taxes from every living agent in ascending id order.

    Returns the updated world and
    ``(agent_id, amount, treasury_after)`` triples for each non-zero
    collection.
    """
    collections: list[tuple[AgentId, int, int]] = []
    for agent in world.alive_agents():
        amount = collectable_tax(
            agent,
            flat_amount=flat_amount,
            rate_bps=rate_bps,
        )
        if amount == 0:
            continue
        updated = apply_tax(world, agent.agent_id, amount)
        if updated is None:
            continue
        world = updated
        collections.append((agent.agent_id, amount, world.treasury))
    return world, tuple(collections)
