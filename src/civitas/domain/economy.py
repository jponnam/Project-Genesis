"""Economy helpers for integer money and wealth observation.

Money is a non-negative integer on each agent. Domain helpers credit,
debit, and transfer balances without floating-point arithmetic so runs
stay deterministic. Wealth census helpers are read-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import AgentId
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class WealthCensus(BaseModel):
    """Immutable money snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    total: NonNegativeInt = Field(description="Sum of money across the full roster.")
    alive_total: NonNegativeInt = Field(description="Sum of money among living agents.")
    dead_total: NonNegativeInt = Field(description="Sum of money among dead agents.")
    alive_count: NonNegativeInt
    mean_alive: float = Field(
        description="Mean money among living agents, or 0.0 when none are alive."
    )
    min_alive: NonNegativeInt | None = Field(
        default=None,
        description="Minimum living-agent money, or None when none are alive.",
    )
    max_alive: NonNegativeInt | None = Field(
        default=None,
        description="Maximum living-agent money, or None when none are alive.",
    )


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


def census_wealth(world: World) -> WealthCensus:
    """Build a deterministic wealth census for ``world``."""
    alive = world.alive_agents()
    total = wealth_total(world)
    alive_total = wealth_alive_total(world)
    alive_count = len(alive)
    if alive_count == 0:
        mean_alive = 0.0
        min_alive: int | None = None
        max_alive: int | None = None
    else:
        balances = tuple(agent.money for agent in alive)
        mean_alive = round(alive_total / alive_count, 6)
        min_alive = min(balances)
        max_alive = max(balances)
    return WealthCensus(
        tick=world.tick,
        total=total,
        alive_total=alive_total,
        dead_total=total - alive_total,
        alive_count=alive_count,
        mean_alive=mean_alive,
        min_alive=min_alive,
        max_alive=max_alive,
    )
