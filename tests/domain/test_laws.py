"""Unit tests for law models, helpers, and tax-schedule override."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    CAMP_POLL_TAX_LAW,
    Agent,
    Government,
    Law,
    LawKind,
    SimulationConfig,
    World,
    active_market_fee_law,
    census_laws,
    default_laws,
    default_world_map,
    enact_law,
    levy_taxes,
    market_fee_for,
    repeal_law,
    set_law_active,
    tax_schedule_for_agent,
)


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (Government.create(0, "Camp", 0, (0,)),),
    laws: tuple[Law, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        laws=laws,
        agents=agents,
    )


def test_default_laws_seed_camp_poll_tax() -> None:
    """Canonical law is an active unit poll tax for Camp Authority."""
    assert default_laws() == (CAMP_POLL_TAX_LAW,)
    assert CAMP_POLL_TAX_LAW.kind == LawKind.TAX_SCHEDULE
    assert CAMP_POLL_TAX_LAW.flat_amount == 1
    assert CAMP_POLL_TAX_LAW.active is True
    assert CAMP_POLL_TAX_LAW.government_id.value == CAMP_GOVERNMENT.government_id.value


def test_world_rejects_unknown_government_and_duplicate_active_tax() -> None:
    """Laws must reference known governments; one active tax schedule each."""
    with pytest.raises(ValidationError, match="unknown government"):
        _world(
            Agent.create(agent_id=0, name="A"),
            governments=(),
            laws=(Law.create(0, 0, "X", LawKind.TAX_SCHEDULE, flat_amount=1),),
        )
    left = Law.create(0, 0, "A", LawKind.TAX_SCHEDULE, flat_amount=1)
    right = Law.create(1, 0, "B", LawKind.TAX_SCHEDULE, flat_amount=2)
    with pytest.raises(ValidationError, match="TAX_SCHEDULE"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_market_fee() -> None:
    """At most one active MARKET_FEE law per government."""
    left = Law.create(0, 0, "Fee A", LawKind.MARKET_FEE, flat_amount=1)
    right = Law.create(1, 0, "Fee B", LawKind.MARKET_FEE, flat_amount=2)
    with pytest.raises(ValidationError, match="MARKET_FEE"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_enact_repeal_and_set_active() -> None:
    """Enactment and soft repeal follow legality rules."""
    world = _world(Agent.create(agent_id=0, name="A"))
    law = Law.create(0, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=2)
    enacted = enact_law(world, law)
    assert enacted is not None
    assert enacted.law_by_id(0) is not None
    assert enact_law(enacted, law) is None
    second = Law.create(1, 0, "Other", LawKind.TAX_SCHEDULE, flat_amount=3)
    assert enact_law(enacted, second) is None
    repealed = repeal_law(enacted, 0)
    assert repealed is not None
    assert repealed.law_by_id(0).active is False  # type: ignore[union-attr]
    reactivated = set_law_active(repealed, 0, True)
    assert reactivated is not None
    assert reactivated.law_by_id(0).active is True  # type: ignore[union-attr]


def test_enact_market_fee_and_uniqueness() -> None:
    """MARKET_FEE enacts once per government; lookup uses flat_amount."""
    world = _world(Agent.create(agent_id=0, name="A"))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2)
    enacted = enact_law(world, fee)
    assert enacted is not None
    assert market_fee_for(enacted, 0) == 2
    assert active_market_fee_law(enacted, 0) == fee
    duplicate = Law.create(1, 0, "Other Fee", LawKind.MARKET_FEE, flat_amount=3)
    assert enact_law(enacted, duplicate) is None
    # TAX_SCHEDULE may coexist with MARKET_FEE for the same government.
    tax = Law.create(1, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=1)
    with_tax = enact_law(enacted, tax)
    assert with_tax is not None
    assert market_fee_for(with_tax, 0) == 2


def test_tax_schedule_overrides_levy_fallback() -> None:
    """Active TAX_SCHEDULE beats levy_taxes fallback parameters."""
    law = Law.create(0, 0, "Heavy", LawKind.TAX_SCHEDULE, flat_amount=2)
    world = _world(Agent.create(agent_id=0, name="A", money=5), laws=(law,))
    assert tax_schedule_for_agent(world, world.agents[0]) == (2, 0)
    updated, collections = levy_taxes(world, flat_amount=1, rate_bps=0)
    assert collections == (
        (world.agents[0].agent_id, 2, 2, world.governments[0].government_id),
    )
    assert updated.agent_by_id(0).money == 3  # type: ignore[union-attr]
    assert updated.government_by_id(0).treasury == 2  # type: ignore[union-attr]

    repealed = repeal_law(world, 0)
    assert repealed is not None
    _, after = levy_taxes(repealed, flat_amount=1, rate_bps=0)
    assert after == (
        (world.agents[0].agent_id, 1, 1, world.governments[0].government_id),
    )


def test_census_laws_counts() -> None:
    """Census reports active/inactive and tax-schedule tallies."""
    active = Law.create(0, 0, "A", LawKind.TAX_SCHEDULE, flat_amount=1, active=True)
    inactive = Law.create(1, 0, "B", LawKind.TAX_SCHEDULE, flat_amount=1, active=False)
    fee = Law.create(2, 0, "Fee", LawKind.MARKET_FEE, flat_amount=1, active=True)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(active, inactive, fee))
    snap = census_laws(world)
    assert snap.law_count == 3
    assert snap.active_count == 2
    assert snap.inactive_count == 1
    assert snap.governments_with_active_laws == 1
    assert snap.active_tax_schedule_count == 1
    assert snap.active_market_fee_count == 1
    assert census_laws(world) == snap


def test_market_fee_for_without_government_is_zero() -> None:
    """Ungoverned locations have no market fee."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert market_fee_for(world, 0) == 0
    assert active_market_fee_law(world, 0) is None


def test_full_map_default_law_compatible_with_camp_government() -> None:
    """Factory-shaped governments and laws validate together."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        laws=default_laws(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert world.laws[0].name == "Camp Poll Tax"
