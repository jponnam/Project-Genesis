"""Unit tests for domain tax helpers and world treasury."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentId,
    AgentStatus,
    Health,
    SimulationConfig,
    World,
    apply_tax,
    collectable_tax,
    levy_taxes,
    tax_due,
    wealth_total,
)


def _world(*agents: Agent, treasury: int = 0) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
        treasury=treasury,
    )


def test_tax_due_flat_and_basis_points() -> None:
    """Flat tax plus integer basis-point wealth component."""
    agent = Agent.create(agent_id=0, name="A", money=250)
    assert tax_due(agent, flat_amount=1, rate_bps=0) == 1
    assert tax_due(agent, flat_amount=1, rate_bps=100) == 3  # 1 + floor(2.5)
    assert tax_due(agent, flat_amount=0, rate_bps=1000) == 25


def test_tax_due_rejects_negatives_and_skips_dead() -> None:
    """Negative config raises; dead agents owe nothing."""
    agent = Agent.create(agent_id=0, name="A", money=10)
    with pytest.raises(ValueError):
        tax_due(agent, flat_amount=-1)
    with pytest.raises(ValueError):
        tax_due(agent, rate_bps=-1)
    dead = agent.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert tax_due(dead, flat_amount=5) == 0


def test_collectable_tax_caps_at_balance() -> None:
    """Poor agents pay only what they hold."""
    agent = Agent.create(agent_id=0, name="A", money=1)
    assert collectable_tax(agent, flat_amount=5, rate_bps=0) == 1
    broke = Agent.create(agent_id=1, name="B", money=0)
    assert collectable_tax(broke, flat_amount=1) == 0


def test_apply_tax_moves_money_to_treasury() -> None:
    """Successful levies debit the agent and credit the treasury."""
    world = _world(Agent.create(agent_id=0, name="A", money=5), treasury=2)
    updated = apply_tax(world, 0, 3)
    assert updated is not None
    agent = updated.agent_by_id(0)
    assert agent is not None
    assert agent.money == 2
    assert updated.treasury == 5
    before = wealth_total(world) + world.treasury
    after = wealth_total(updated) + updated.treasury
    assert after == before


def test_apply_tax_illegal_cases() -> None:
    """Missing, dead, or unaffordable payments return None."""
    alive = Agent.create(agent_id=0, name="A", money=1)
    dead = Agent.create(agent_id=1, name="B", money=5).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(alive, dead)
    assert apply_tax(world, 9, 1) is None
    assert apply_tax(world, 1, 1) is None
    assert apply_tax(world, 0, 2) is None
    assert apply_tax(world, 0, 0) == world


def test_levy_taxes_collects_in_id_order() -> None:
    """Levy walks living agents ascending by id and reports treasury marks."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=2),
        Agent.create(agent_id=1, name="B", money=0),
        Agent.create(agent_id=2, name="C", money=4),
    )
    updated, collections = levy_taxes(world, flat_amount=1, rate_bps=0)
    assert collections == (
        (AgentId(value=0), 1, 1),
        (AgentId(value=2), 1, 2),
    )
    assert updated.treasury == 2
    assert updated.agent_by_id(0).money == 1  # type: ignore[union-attr]
    assert updated.agent_by_id(1).money == 0  # type: ignore[union-attr]
    assert updated.agent_by_id(2).money == 3  # type: ignore[union-attr]


def test_world_treasury_helpers() -> None:
    """World starts at treasury 0 and with_treasury updates immutably."""
    world = _world(Agent.create(agent_id=0, name="A"))
    assert world.treasury == 0
    richer = world.with_treasury(7)
    assert richer.treasury == 7
    assert world.treasury == 0
    with pytest.raises(ValueError):
        world.with_treasury(-1)
