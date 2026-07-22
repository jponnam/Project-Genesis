"""Economy helpers for integer money balances.

Money is a non-negative integer on each agent. Domain helpers credit,
debit, and transfer balances without floating-point arithmetic so runs
stay deterministic. Wealth analytics live in ``civitas.domain.wealth``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.ids import AgentId

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


def can_afford(agent: Agent, amount: int) -> bool:
    """Return True when a living ``agent`` can pay ``amount``."""
    if amount < 0:
        msg = f"money amount must be >= 0, got {amount}"
        raise ValueError(msg)
    if not agent.is_alive():
        return False
    return agent.money >= amount


def credit_money(agent: Agent, amount: int) -> Agent | None:
    """Add ``amount`` to a living agent's money balance.

    Returns the updated agent, or ``None`` when the agent is dead.
    ``amount`` of 0 is a no-op success for living agents.
    """
    if amount < 0:
        msg = f"money amount must be >= 0, got {amount}"
        raise ValueError(msg)
    if not agent.is_alive():
        return None
    if amount == 0:
        return agent
    return agent.model_copy(update={"money": agent.money + amount})


def debit_money(agent: Agent, amount: int) -> Agent | None:
    """Remove ``amount`` from a living agent's money balance.

    Returns the updated agent, or ``None`` when the agent is dead or
    cannot afford ``amount``.
    """
    if not can_afford(agent, amount):
        return None
    if amount == 0:
        return agent
    return agent.model_copy(update={"money": agent.money - amount})


def transfer_money(
    world: World,
    payer_id: AgentId | int,
    payee_id: AgentId | int,
    amount: int,
) -> World | None:
    """Move ``amount`` from ``payer_id`` to ``payee_id`` when legal.

    Both agents must exist, be distinct, and be alive. The payer must
    afford ``amount``. Returns the updated world, or ``None`` if illegal.
    """
    if amount < 0:
        msg = f"money amount must be >= 0, got {amount}"
        raise ValueError(msg)

    payer = world.agent_by_id(payer_id)
    payee = world.agent_by_id(payee_id)
    if payer is None or payee is None:
        return None
    if payer.agent_id == payee.agent_id:
        return None
    if not payer.is_alive() or not payee.is_alive():
        return None

    debited = debit_money(payer, amount)
    if debited is None:
        return None
    credited = credit_money(payee, amount)
    if credited is None:
        return None

    world = world.with_agent(debited)
    return world.with_agent(credited)


def wealth_total(world: World) -> int:
    """Return the sum of money across the full roster."""
    return sum(agent.money for agent in world.agents)


def wealth_alive_total(world: World) -> int:
    """Return the sum of money among living agents."""
    return sum(agent.money for agent in world.alive_agents())
