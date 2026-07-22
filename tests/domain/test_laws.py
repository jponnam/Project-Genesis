"""Unit tests for law models, helpers, and tax-schedule override."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    CAMP_POLL_TAX_LAW,
    ETHICS_MIN_TEACH_TRUST_DELTA,
    Agent,
    AgentStatus,
    Government,
    Law,
    LawKind,
    SimulationConfig,
    World,
    active_calendar_law,
    active_curriculum_law,
    active_ethics_law,
    active_market_fee_law,
    calendar_retrieval_bonus_for,
    census_laws,
    curriculum_teachings_bonus_for,
    default_laws,
    default_world_map,
    enact_law,
    ethics_min_teach_trust_delta_for,
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


def test_world_rejects_duplicate_active_curriculum() -> None:
    """At most one active CURRICULUM law per government."""
    left = Law.create(0, 0, "Schools A", LawKind.CURRICULUM)
    right = Law.create(1, 0, "Schools B", LawKind.CURRICULUM)
    with pytest.raises(ValidationError, match="CURRICULUM"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_calendar() -> None:
    """At most one active CALENDAR law per government."""
    left = Law.create(0, 0, "Calendar A", LawKind.CALENDAR)
    right = Law.create(1, 0, "Calendar B", LawKind.CALENDAR)
    with pytest.raises(ValidationError, match="CALENDAR"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_ethics() -> None:
    """At most one active ETHICS law per government."""
    left = Law.create(0, 0, "Ethics A", LawKind.ETHICS)
    right = Law.create(1, 0, "Ethics B", LawKind.ETHICS)
    with pytest.raises(ValidationError, match="ETHICS"):
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


def test_enact_curriculum_and_uniqueness() -> None:
    """CURRICULUM enacts once per government; kind alone enables the bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    curriculum = Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM)
    enacted = enact_law(world, curriculum)
    assert enacted is not None
    assert active_curriculum_law(enacted, 0) == curriculum
    assert curriculum_teachings_bonus_for(enacted, enacted.agents[0]) == 1
    duplicate = Law.create(1, 0, "Other Schools", LawKind.CURRICULUM)
    assert enact_law(enacted, duplicate) is None
    # TAX_SCHEDULE and MARKET_FEE may coexist with CURRICULUM.
    tax = Law.create(1, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=1)
    with_tax = enact_law(enacted, tax)
    assert with_tax is not None
    fee = Law.create(2, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1)
    with_fee = enact_law(with_tax, fee)
    assert with_fee is not None
    assert active_curriculum_law(with_fee, 0) == curriculum


def test_curriculum_bonus_requires_living_subject() -> None:
    """Only living agents under a CURRICULUM polity receive the teaching bonus."""
    curriculum = Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(curriculum,))
    assert curriculum_teachings_bonus_for(world, world.agents[0]) == 1
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert curriculum_teachings_bonus_for(world, dead) == 0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert curriculum_teachings_bonus_for(ungoverned, ungoverned.agents[0]) == 0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert curriculum_teachings_bonus_for(bare, bare.agents[0]) == 0


def test_enact_calendar_and_uniqueness() -> None:
    """CALENDAR enacts once per government; kind alone enables the bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    calendar = Law.create(0, 0, "Camp Calendar", LawKind.CALENDAR, flat_amount=9)
    enacted = enact_law(world, calendar)
    assert enacted is not None
    assert active_calendar_law(enacted, 0) == calendar
    assert calendar_retrieval_bonus_for(enacted, enacted.agents[0]) == 1
    duplicate = Law.create(1, 0, "Other Calendar", LawKind.CALENDAR)
    assert enact_law(enacted, duplicate) is None
    # TAX_SCHEDULE, MARKET_FEE, and CURRICULUM may coexist with CALENDAR.
    tax = Law.create(1, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=1)
    with_tax = enact_law(enacted, tax)
    assert with_tax is not None
    fee = Law.create(2, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1)
    with_fee = enact_law(with_tax, fee)
    assert with_fee is not None
    curriculum = Law.create(3, 0, "Camp Schools", LawKind.CURRICULUM)
    with_curriculum = enact_law(with_fee, curriculum)
    assert with_curriculum is not None
    assert active_calendar_law(with_curriculum, 0) == calendar
    assert calendar_retrieval_bonus_for(with_curriculum, with_curriculum.agents[0]) == 1


def test_calendar_bonus_requires_living_subject() -> None:
    """Only living agents under a CALENDAR polity receive the retrieval bonus."""
    calendar = Law.create(0, 0, "Camp Calendar", LawKind.CALENDAR)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(calendar,))
    assert calendar_retrieval_bonus_for(world, world.agents[0]) == 1
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert calendar_retrieval_bonus_for(world, dead) == 0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert calendar_retrieval_bonus_for(ungoverned, ungoverned.agents[0]) == 0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert calendar_retrieval_bonus_for(bare, bare.agents[0]) == 0


def test_enact_ethics_and_uniqueness() -> None:
    """ETHICS enacts once per government; kind alone enables the trust delta."""
    world = _world(Agent.create(agent_id=0, name="A"))
    ethics = Law.create(0, 0, "Camp Ethics", LawKind.ETHICS, flat_amount=9)
    enacted = enact_law(world, ethics)
    assert enacted is not None
    assert active_ethics_law(enacted, 0) == ethics
    assert ethics_min_teach_trust_delta_for(enacted, enacted.agents[0]) == (
        ETHICS_MIN_TEACH_TRUST_DELTA
    )
    assert ETHICS_MIN_TEACH_TRUST_DELTA == -0.05
    duplicate = Law.create(1, 0, "Other Ethics", LawKind.ETHICS)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with ETHICS.
    tax = Law.create(1, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=1)
    with_tax = enact_law(enacted, tax)
    assert with_tax is not None
    fee = Law.create(2, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1)
    with_fee = enact_law(with_tax, fee)
    assert with_fee is not None
    curriculum = Law.create(3, 0, "Camp Schools", LawKind.CURRICULUM)
    with_curriculum = enact_law(with_fee, curriculum)
    assert with_curriculum is not None
    calendar = Law.create(4, 0, "Camp Calendar", LawKind.CALENDAR)
    with_calendar = enact_law(with_curriculum, calendar)
    assert with_calendar is not None
    assert active_ethics_law(with_calendar, 0) == ethics
    assert (
        ethics_min_teach_trust_delta_for(with_calendar, with_calendar.agents[0])
        == ETHICS_MIN_TEACH_TRUST_DELTA
    )


def test_ethics_delta_requires_living_subject() -> None:
    """Only living agents under an ETHICS polity receive the teach-trust delta."""
    ethics = Law.create(0, 0, "Camp Ethics", LawKind.ETHICS)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(ethics,))
    assert ethics_min_teach_trust_delta_for(world, world.agents[0]) == (
        ETHICS_MIN_TEACH_TRUST_DELTA
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert ethics_min_teach_trust_delta_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert ethics_min_teach_trust_delta_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert ethics_min_teach_trust_delta_for(bare, bare.agents[0]) == 0.0


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
    curriculum = Law.create(3, 0, "Schools", LawKind.CURRICULUM, active=True)
    calendar = Law.create(4, 0, "Calendar", LawKind.CALENDAR, active=True)
    ethics = Law.create(5, 0, "Ethics", LawKind.ETHICS, active=True)
    world = _world(
        Agent.create(agent_id=0, name="A"),
        laws=(active, inactive, fee, curriculum, calendar, ethics),
    )
    snap = census_laws(world)
    assert snap.law_count == 6
    assert snap.active_count == 5
    assert snap.inactive_count == 1
    assert snap.governments_with_active_laws == 1
    assert snap.active_tax_schedule_count == 1
    assert snap.active_market_fee_count == 1
    assert snap.active_curriculum_count == 1
    assert snap.active_calendar_count == 1
    assert snap.active_ethics_count == 1
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
