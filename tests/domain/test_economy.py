"""Unit tests for domain economy helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Health,
    SimulationConfig,
    World,
    can_afford,
    census_wealth,
    credit_money,
    debit_money,
    transfer_money,
    wealth_alive_total,
    wealth_total,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_can_afford_and_debit_credit() -> None:
    """Living agents can debit/credit integer balances."""
    agent = Agent.create(agent_id=0, name="A", money=10)
    assert can_afford(agent, 10) is True
    assert can_afford(agent, 11) is False

    richer = credit_money(agent, 5)
    assert richer is not None
    assert richer.money == 15

    poorer = debit_money(agent, 4)
    assert poorer is not None
    assert poorer.money == 6
    assert debit_money(agent, 11) is None


def test_dead_agents_cannot_transact() -> None:
    """Dead agents reject afford/credit/debit."""
    dead = Agent.create(agent_id=0, name="A", money=10).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_afford(dead, 1) is False
    assert credit_money(dead, 1) is None
    assert debit_money(dead, 1) is None


def test_transfer_money_moves_balances() -> None:
    """Legal transfers debit the payer and credit the payee."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=8),
        Agent.create(agent_id=1, name="B", money=1),
    )
    updated = transfer_money(world, 0, 1, 3)
    assert updated is not None
    payer = updated.agent_by_id(0)
    payee = updated.agent_by_id(1)
    assert payer is not None and payee is not None
    assert payer.money == 5
    assert payee.money == 4
    assert wealth_total(updated) == wealth_total(world)


def test_transfer_money_rejects_illegal_cases() -> None:
    """Self-pay, missing agents, poor payers, and dead parties fail."""
    living = Agent.create(agent_id=0, name="A", money=2)
    other = Agent.create(agent_id=1, name="B", money=0)
    dead = Agent.create(agent_id=2, name="C", money=9).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(living, other, dead)
    assert transfer_money(world, 0, 0, 1) is None
    assert transfer_money(world, 0, 1, 5) is None
    assert transfer_money(world, 0, 9, 1) is None
    assert transfer_money(world, 0, 2, 1) is None
    assert transfer_money(world, 2, 1, 1) is None


def test_negative_amounts_raise() -> None:
    """Negative money amounts are rejected."""
    agent = Agent.create(agent_id=0, name="A", money=5)
    with pytest.raises(ValueError, match="money amount"):
        can_afford(agent, -1)
    with pytest.raises(ValueError, match="money amount"):
        credit_money(agent, -1)


def test_census_wealth_splits_alive_and_dead() -> None:
    """Wealth census reports totals and living-agent stats."""
    living = Agent.create(agent_id=0, name="A", money=10)
    dead = Agent.create(agent_id=1, name="B", money=4).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(living, dead)
    snap = census_wealth(world)
    assert snap.total == 14
    assert snap.alive_total == 10
    assert snap.dead_total == 4
    assert snap.alive_count == 1
    assert snap.mean_alive == pytest.approx(10.0)
    assert snap.min_alive == 10
    assert snap.max_alive == 10
    assert wealth_alive_total(world) == 10
