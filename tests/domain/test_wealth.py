"""Unit tests for wealth analytics helpers and census."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Government,
    Health,
    Institution,
    InstitutionKind,
    SimulationConfig,
    World,
    census_wealth,
    gini_bps,
    median_int,
    share_bps,
    society_money_total,
    top_share_bps,
    wealth_alive_total,
)


def _world(
    *agents: Agent,
    treasury: int = 0,
    governments: tuple[Government, ...] = (),
    institutions: tuple[Institution, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        institutions=institutions,
        agents=agents,
        treasury=treasury,
    )


def test_share_bps_and_median_int() -> None:
    """Basis-point shares and integer medians are deterministic."""
    assert share_bps(1, 4) == 2500
    assert share_bps(1, 0) == 0
    assert median_int((1, 3, 8)) == 3
    assert median_int((2, 4)) == 3
    with pytest.raises(ValueError):
        median_int(())


def test_gini_bps_equal_and_concentrated() -> None:
    """Equal balances yield 0; one holder of all money is highly unequal."""
    assert gini_bps((5, 5, 5, 5)) == 0
    assert gini_bps((0, 0)) == 0
    assert gini_bps((10,)) == 0
    concentrated = gini_bps((0, 0, 0, 10))
    assert concentrated > 7000
    assert concentrated <= 10000


def test_top_share_bps_decile() -> None:
    """Top-decile helper always includes at least the richest agent."""
    assert (
        top_share_bps((1, 1, 1, 1, 1, 1, 1, 1, 1, 11), fraction_numer=1)
        == (11 * 10000) // 20
    )
    assert top_share_bps((0, 0, 10)) == 10000


def test_census_wealth_includes_treasury_and_inequality() -> None:
    """Census reports society totals and living-only inequality metrics."""
    living_a = Agent.create(agent_id=0, name="A", money=0)
    living_b = Agent.create(agent_id=1, name="B", money=10)
    dead = Agent.create(agent_id=2, name="C", money=4).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(
        living_a,
        living_b,
        dead,
        treasury=6,
        governments=(Government.create(0, "Camp", 0, (0,), treasury=4),),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL, budget=2),
        ),
    )
    snap = census_wealth(world)
    assert snap.total == 14
    assert snap.alive_total == 10
    assert snap.dead_total == 4
    assert snap.treasury == 6
    assert snap.government_treasury == 4
    assert snap.institution_budget == 2
    assert snap.society_total == 26
    assert snap.treasury_share_bps == 4615
    assert snap.median_alive == 5
    assert snap.min_alive == 0
    assert snap.max_alive == 10
    assert snap.zero_count == 1
    assert snap.top1_share_bps == 10000
    assert snap.gini_bps == gini_bps((0, 10))
    assert wealth_alive_total(world) == 10
    assert society_money_total(world) == 26


def test_census_wealth_empty_living() -> None:
    """No living agents yields zero inequality metrics and null medians."""
    dead = Agent.create(agent_id=0, name="A", money=3).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = _world(dead, treasury=2)
    snap = census_wealth(world)
    assert snap.alive_count == 0
    assert snap.government_treasury == 0
    assert snap.institution_budget == 0
    assert snap.median_alive is None
    assert snap.gini_bps == 0
    assert snap.top1_share_bps == 0
    assert snap.top10_share_bps == 0
    assert snap.zero_count == 0
    assert snap.society_total == 5


def test_census_wealth_is_deterministic() -> None:
    """Identical worlds produce identical censuses."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=2),
        Agent.create(agent_id=1, name="B", money=8),
        treasury=1,
    )
    assert census_wealth(world) == census_wealth(world)
