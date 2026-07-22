"""Tax levy helpers for integer money collection into public treasuries.

Living agents pay a flat poll tax plus an optional basis-point wealth
component each levy. Collection is capped at the agent's balance so poor
agents pay what they can. Money math stays integer-only.

When an agent lives under a government with an active ``TAX_SCHEDULE`` law,
that statute's ``flat_amount`` / ``rate_bps`` override the fallback levy
parameters for that agent.

Collected money is redirected to the governing polity's treasury when the
payer lives inside a government jurisdiction; otherwise it remains in the
legacy ``World.treasury`` pool.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.economy import debit_money
from civitas.domain.governments import credit_government_treasury, government_at
from civitas.domain.ids import AgentId, GovernmentId
from civitas.domain.laws import tax_schedule_for_agent

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


def resolve_tax_params(
    world: World,
    agent: Agent,
    *,
    flat_amount: int = DEFAULT_FLAT_AMOUNT,
    rate_bps: int = DEFAULT_RATE_BPS,
) -> tuple[int, int]:
    """Return effective ``(flat_amount, rate_bps)`` for ``agent``.

    Active government tax schedules override the fallback parameters.
    """
    schedule = tax_schedule_for_agent(world, agent)
    if schedule is None:
        return (flat_amount, rate_bps)
    return schedule


def apply_tax(world: World, agent_id: AgentId | int, amount: int) -> World | None:
    """Debit ``amount`` from ``agent_id`` into the applicable treasury.

    Returns the updated world, or ``None`` when the agent is missing, dead,
    or cannot afford ``amount``. ``amount`` of 0 is a no-op success for
    living agents. Tax paid inside a government jurisdiction is credited to
    that government's treasury; otherwise it is credited to ``world.treasury``.
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
    government = government_at(world, agent.location_id)
    if government is not None:
        return credit_government_treasury(world, government.government_id, amount)
    return world.with_treasury(world.treasury + amount)


def levy_taxes(
    world: World,
    *,
    flat_amount: int = DEFAULT_FLAT_AMOUNT,
    rate_bps: int = DEFAULT_RATE_BPS,
) -> tuple[World, tuple[tuple[AgentId, int, int, GovernmentId | None], ...]]:
    """Collect taxes from every living agent in ascending id order.

    Per-agent schedules come from active ``TAX_SCHEDULE`` laws when present;
    otherwise ``flat_amount`` / ``rate_bps`` are used. Returns the updated
    world and ``(agent_id, amount, treasury_after, government_id)`` tuples
    for each non-zero collection. ``treasury_after`` is the credited
    destination balance and ``government_id`` is ``None`` for world treasury
    collections.
    """
    collections: list[tuple[AgentId, int, int, GovernmentId | None]] = []
    for agent in world.alive_agents():
        government = government_at(world, agent.location_id)
        effective_flat, effective_rate = resolve_tax_params(
            world,
            agent,
            flat_amount=flat_amount,
            rate_bps=rate_bps,
        )
        amount = collectable_tax(
            agent,
            flat_amount=effective_flat,
            rate_bps=effective_rate,
        )
        if amount == 0:
            continue
        updated = apply_tax(world, agent.agent_id, amount)
        if updated is None:
            continue
        world = updated
        if government is None:
            treasury_after = world.treasury
            government_id = None
        else:
            updated_government = world.government_by_id(government.government_id)
            if updated_government is None:
                continue
            treasury_after = updated_government.treasury
            government_id = updated_government.government_id
        collections.append((agent.agent_id, amount, treasury_after, government_id))
    return world, tuple(collections)
