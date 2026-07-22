"""Unit tests for law models, helpers, and tax-schedule override."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    ASSEMBLY_SOCIALIZE_RESTORE_BONUS,
    BUILDING_CODES_MOVE_ENERGY_DISCOUNT,
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    CAMP_POLL_TAX_LAW,
    CONSERVATION_WOOD_GATHER_BONUS,
    CUSTOMS_PRODUCE_ENERGY_DISCOUNT,
    ETHICS_MIN_TEACH_TRUST_DELTA,
    LABOR_PRODUCE_ENERGY_DISCOUNT,
    LAND_TENURE_EAT_RESTORE_BONUS,
    PASSAGE_MOVE_ENERGY_DISCOUNT,
    QUARANTINE_REST_RESTORE_BONUS,
    SANITATION_DRINK_RESTORE_BONUS,
    ZONING_EAT_RESTORE_BONUS,
    Agent,
    AgentStatus,
    Government,
    Law,
    LawKind,
    SimulationConfig,
    World,
    active_assembly_law,
    active_building_codes_law,
    active_calendar_law,
    active_conservation_law,
    active_curriculum_law,
    active_customs_law,
    active_ethics_law,
    active_labor_law,
    active_land_tenure_law,
    active_market_fee_law,
    active_passage_law,
    active_quarantine_law,
    active_sanitation_law,
    active_zoning_law,
    assembly_socialize_bonus_for,
    building_codes_move_discount_for,
    calendar_retrieval_bonus_for,
    census_laws,
    conservation_wood_bonus_for,
    curriculum_teachings_bonus_for,
    customs_produce_discount_for,
    default_laws,
    default_world_map,
    enact_law,
    ethics_min_teach_trust_delta_for,
    labor_produce_discount_for,
    land_tenure_eat_bonus_for,
    levy_taxes,
    market_fee_for,
    passage_move_discount_for,
    quarantine_rest_bonus_for,
    repeal_law,
    sanitation_drink_bonus_for,
    set_law_active,
    tax_schedule_for_agent,
    zoning_eat_bonus_for,
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
    assert all(law.kind is not LawKind.SANITATION for law in default_laws())
    assert all(law.kind is not LawKind.QUARANTINE for law in default_laws())
    assert all(law.kind is not LawKind.BUILDING_CODES for law in default_laws())
    assert all(law.kind is not LawKind.ZONING for law in default_laws())
    assert all(law.kind is not LawKind.PASSAGE for law in default_laws())
    assert all(law.kind is not LawKind.CUSTOMS for law in default_laws())
    assert all(law.kind is not LawKind.LAND_TENURE for law in default_laws())
    assert all(law.kind is not LawKind.LABOR for law in default_laws())


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


def test_world_rejects_duplicate_active_assembly() -> None:
    """At most one active ASSEMBLY law per government."""
    left = Law.create(0, 0, "Assembly A", LawKind.ASSEMBLY)
    right = Law.create(1, 0, "Assembly B", LawKind.ASSEMBLY)
    with pytest.raises(ValidationError, match="ASSEMBLY"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_sanitation() -> None:
    """At most one active SANITATION law per government."""
    left = Law.create(0, 0, "Sanitation A", LawKind.SANITATION)
    right = Law.create(1, 0, "Sanitation B", LawKind.SANITATION)
    with pytest.raises(ValidationError, match="SANITATION"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_quarantine() -> None:
    """At most one active QUARANTINE law per government."""
    left = Law.create(0, 0, "Quarantine A", LawKind.QUARANTINE)
    right = Law.create(1, 0, "Quarantine B", LawKind.QUARANTINE)
    with pytest.raises(ValidationError, match="QUARANTINE"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_building_codes() -> None:
    """At most one active BUILDING_CODES law per government."""
    left = Law.create(0, 0, "Building Codes A", LawKind.BUILDING_CODES)
    right = Law.create(1, 0, "Building Codes B", LawKind.BUILDING_CODES)
    with pytest.raises(ValidationError, match="BUILDING_CODES"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_zoning() -> None:
    """At most one active ZONING law per government."""
    left = Law.create(0, 0, "Zoning A", LawKind.ZONING)
    right = Law.create(1, 0, "Zoning B", LawKind.ZONING)
    with pytest.raises(ValidationError, match="ZONING"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_passage() -> None:
    """At most one active PASSAGE law per government."""
    left = Law.create(0, 0, "Passage A", LawKind.PASSAGE)
    right = Law.create(1, 0, "Passage B", LawKind.PASSAGE)
    with pytest.raises(ValidationError, match="PASSAGE"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_customs() -> None:
    """At most one active CUSTOMS law per government."""
    left = Law.create(0, 0, "Customs A", LawKind.CUSTOMS)
    right = Law.create(1, 0, "Customs B", LawKind.CUSTOMS)
    with pytest.raises(ValidationError, match="CUSTOMS"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_land_tenure() -> None:
    """At most one active LAND_TENURE law per government."""
    left = Law.create(0, 0, "Land Tenure A", LawKind.LAND_TENURE)
    right = Law.create(1, 0, "Land Tenure B", LawKind.LAND_TENURE)
    with pytest.raises(ValidationError, match="LAND_TENURE"):
        _world(Agent.create(agent_id=0, name="A"), laws=(left, right))


def test_world_rejects_duplicate_active_labor() -> None:
    """At most one active LABOR law per government."""
    left = Law.create(0, 0, "Labor A", LawKind.LABOR)
    right = Law.create(1, 0, "Labor B", LawKind.LABOR)
    with pytest.raises(ValidationError, match="LABOR"):
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


def test_enact_assembly_and_uniqueness() -> None:
    """ASSEMBLY enacts once per government; kind alone enables the bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    assembly = Law.create(0, 0, "Camp Assembly", LawKind.ASSEMBLY, flat_amount=9)
    enacted = enact_law(world, assembly)
    assert enacted is not None
    assert active_assembly_law(enacted, 0) == assembly
    assert assembly_socialize_bonus_for(enacted, enacted.agents[0]) == (
        ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    assert ASSEMBLY_SOCIALIZE_RESTORE_BONUS == 0.05
    duplicate = Law.create(1, 0, "Other Assembly", LawKind.ASSEMBLY)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with ASSEMBLY.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assert active_assembly_law(with_ethics, 0) == assembly
    assert assembly_socialize_bonus_for(with_ethics, with_ethics.agents[0]) == (
        ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )


def test_assembly_bonus_requires_living_subject() -> None:
    """Only living agents under an ASSEMBLY polity receive the socialize bonus."""
    assembly = Law.create(0, 0, "Camp Assembly", LawKind.ASSEMBLY)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(assembly,))
    assert assembly_socialize_bonus_for(world, world.agents[0]) == (
        ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert assembly_socialize_bonus_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert assembly_socialize_bonus_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert assembly_socialize_bonus_for(bare, bare.agents[0]) == 0.0


def test_enact_sanitation_and_uniqueness() -> None:
    """SANITATION enacts once per government; kind alone enables the bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    sanitation = Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION)
    enacted = enact_law(world, sanitation)
    assert enacted is not None
    assert active_sanitation_law(enacted, 0) == sanitation
    assert sanitation_drink_bonus_for(enacted, enacted.agents[0]) == (
        SANITATION_DRINK_RESTORE_BONUS
    )
    assert SANITATION_DRINK_RESTORE_BONUS == 0.05
    duplicate = Law.create(1, 0, "Other Sanitation", LawKind.SANITATION)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with SANITATION.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    assert active_sanitation_law(with_assembly, 0) == sanitation
    assert sanitation_drink_bonus_for(with_assembly, with_assembly.agents[0]) == (
        SANITATION_DRINK_RESTORE_BONUS
    )


def test_enact_quarantine_and_uniqueness() -> None:
    """QUARANTINE enacts once per government; kind alone enables the bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    quarantine = Law.create(0, 0, "Camp Quarantine", LawKind.QUARANTINE)
    enacted = enact_law(world, quarantine)
    assert enacted is not None
    assert active_quarantine_law(enacted, 0) == quarantine
    assert quarantine_rest_bonus_for(enacted, enacted.agents[0]) == (
        QUARANTINE_REST_RESTORE_BONUS
    )
    assert QUARANTINE_REST_RESTORE_BONUS == 0.05
    duplicate = Law.create(1, 0, "Other Quarantine", LawKind.QUARANTINE)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with QUARANTINE.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    sanitation = Law.create(7, 0, "Camp Sanitation", LawKind.SANITATION)
    with_sanitation = enact_law(with_assembly, sanitation)
    assert with_sanitation is not None
    assert active_quarantine_law(with_sanitation, 0) == quarantine
    assert quarantine_rest_bonus_for(with_sanitation, with_sanitation.agents[0]) == (
        QUARANTINE_REST_RESTORE_BONUS
    )


def test_enact_building_codes_and_uniqueness() -> None:
    """BUILDING_CODES enacts once per government; kind alone enables discount."""
    world = _world(Agent.create(agent_id=0, name="A"))
    building_codes = Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    enacted = enact_law(world, building_codes)
    assert enacted is not None
    assert active_building_codes_law(enacted, 0) == building_codes
    assert building_codes_move_discount_for(enacted, enacted.agents[0]) == (
        BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    )
    assert BUILDING_CODES_MOVE_ENERGY_DISCOUNT == 0.02
    duplicate = Law.create(1, 0, "Other Building Codes", LawKind.BUILDING_CODES)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with BUILDING_CODES.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    sanitation = Law.create(7, 0, "Camp Sanitation", LawKind.SANITATION)
    with_sanitation = enact_law(with_assembly, sanitation)
    assert with_sanitation is not None
    quarantine = Law.create(8, 0, "Camp Quarantine", LawKind.QUARANTINE)
    with_quarantine = enact_law(with_sanitation, quarantine)
    assert with_quarantine is not None
    assert active_building_codes_law(with_quarantine, 0) == building_codes
    assert (
        building_codes_move_discount_for(
            with_quarantine,
            with_quarantine.agents[0],
        )
        == BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    )


def test_enact_zoning_and_uniqueness() -> None:
    """ZONING enacts once per government; kind alone enables the eat bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    zoning = Law.create(0, 0, "Camp Zoning", LawKind.ZONING)
    enacted = enact_law(world, zoning)
    assert enacted is not None
    assert active_zoning_law(enacted, 0) == zoning
    assert zoning_eat_bonus_for(enacted, enacted.agents[0]) == ZONING_EAT_RESTORE_BONUS
    assert ZONING_EAT_RESTORE_BONUS == 0.05
    duplicate = Law.create(1, 0, "Other Zoning", LawKind.ZONING)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with ZONING.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    sanitation = Law.create(7, 0, "Camp Sanitation", LawKind.SANITATION)
    with_sanitation = enact_law(with_assembly, sanitation)
    assert with_sanitation is not None
    quarantine = Law.create(8, 0, "Camp Quarantine", LawKind.QUARANTINE)
    with_quarantine = enact_law(with_sanitation, quarantine)
    assert with_quarantine is not None
    building_codes = Law.create(9, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    with_codes = enact_law(with_quarantine, building_codes)
    assert with_codes is not None
    passage = Law.create(10, 0, "Camp Passage", LawKind.PASSAGE)
    with_passage = enact_law(with_codes, passage)
    assert with_passage is not None
    customs = Law.create(11, 0, "Camp Customs", LawKind.CUSTOMS)
    with_customs = enact_law(with_passage, customs)
    assert with_customs is not None
    land_tenure = Law.create(12, 0, "Camp Land Tenure", LawKind.LAND_TENURE)
    with_tenure = enact_law(with_customs, land_tenure)
    assert with_tenure is not None
    assert active_zoning_law(with_tenure, 0) == zoning
    assert zoning_eat_bonus_for(with_tenure, with_tenure.agents[0]) == (
        ZONING_EAT_RESTORE_BONUS
    )


def test_enact_passage_and_uniqueness() -> None:
    """PASSAGE enacts once per government; kind alone enables discount."""
    world = _world(Agent.create(agent_id=0, name="A"))
    passage = Law.create(0, 0, "Camp Passage", LawKind.PASSAGE)
    enacted = enact_law(world, passage)
    assert enacted is not None
    assert active_passage_law(enacted, 0) == passage
    assert passage_move_discount_for(enacted, enacted.agents[0]) == (
        PASSAGE_MOVE_ENERGY_DISCOUNT
    )
    assert PASSAGE_MOVE_ENERGY_DISCOUNT == 0.02
    duplicate = Law.create(1, 0, "Other Passage", LawKind.PASSAGE)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with PASSAGE.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    sanitation = Law.create(7, 0, "Camp Sanitation", LawKind.SANITATION)
    with_sanitation = enact_law(with_assembly, sanitation)
    assert with_sanitation is not None
    quarantine = Law.create(8, 0, "Camp Quarantine", LawKind.QUARANTINE)
    with_quarantine = enact_law(with_sanitation, quarantine)
    assert with_quarantine is not None
    building_codes = Law.create(9, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    with_codes = enact_law(with_quarantine, building_codes)
    assert with_codes is not None
    zoning = Law.create(10, 0, "Camp Zoning", LawKind.ZONING)
    with_zoning = enact_law(with_codes, zoning)
    assert with_zoning is not None
    customs = Law.create(11, 0, "Camp Customs", LawKind.CUSTOMS)
    with_customs = enact_law(with_zoning, customs)
    assert with_customs is not None
    land_tenure = Law.create(12, 0, "Camp Land Tenure", LawKind.LAND_TENURE)
    with_tenure = enact_law(with_customs, land_tenure)
    assert with_tenure is not None
    assert active_passage_law(with_tenure, 0) == passage
    assert (
        passage_move_discount_for(
            with_tenure,
            with_tenure.agents[0],
        )
        == PASSAGE_MOVE_ENERGY_DISCOUNT
    )


def test_enact_customs_and_uniqueness() -> None:
    """CUSTOMS enacts once per government; kind alone enables discount."""
    world = _world(Agent.create(agent_id=0, name="A"))
    customs = Law.create(0, 0, "Camp Customs", LawKind.CUSTOMS)
    enacted = enact_law(world, customs)
    assert enacted is not None
    assert active_customs_law(enacted, 0) == customs
    assert customs_produce_discount_for(enacted, enacted.agents[0]) == (
        CUSTOMS_PRODUCE_ENERGY_DISCOUNT
    )
    assert CUSTOMS_PRODUCE_ENERGY_DISCOUNT == 0.02
    duplicate = Law.create(1, 0, "Other Customs", LawKind.CUSTOMS)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with CUSTOMS.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    sanitation = Law.create(7, 0, "Camp Sanitation", LawKind.SANITATION)
    with_sanitation = enact_law(with_assembly, sanitation)
    assert with_sanitation is not None
    quarantine = Law.create(8, 0, "Camp Quarantine", LawKind.QUARANTINE)
    with_quarantine = enact_law(with_sanitation, quarantine)
    assert with_quarantine is not None
    building_codes = Law.create(9, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    with_codes = enact_law(with_quarantine, building_codes)
    assert with_codes is not None
    zoning = Law.create(10, 0, "Camp Zoning", LawKind.ZONING)
    with_zoning = enact_law(with_codes, zoning)
    assert with_zoning is not None
    passage = Law.create(11, 0, "Camp Passage", LawKind.PASSAGE)
    with_passage = enact_law(with_zoning, passage)
    assert with_passage is not None
    land_tenure = Law.create(12, 0, "Camp Land Tenure", LawKind.LAND_TENURE)
    with_tenure = enact_law(with_passage, land_tenure)
    assert with_tenure is not None
    assert active_customs_law(with_tenure, 0) == customs
    assert (
        customs_produce_discount_for(
            with_tenure,
            with_tenure.agents[0],
        )
        == CUSTOMS_PRODUCE_ENERGY_DISCOUNT
    )


def test_enact_land_tenure_and_uniqueness() -> None:
    """LAND_TENURE enacts once per government; kind alone enables eat bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    land_tenure = Law.create(0, 0, "Camp Land Tenure", LawKind.LAND_TENURE)
    enacted = enact_law(world, land_tenure)
    assert enacted is not None
    assert active_land_tenure_law(enacted, 0) == land_tenure
    assert land_tenure_eat_bonus_for(enacted, enacted.agents[0]) == (
        LAND_TENURE_EAT_RESTORE_BONUS
    )
    assert LAND_TENURE_EAT_RESTORE_BONUS == 0.05
    duplicate = Law.create(1, 0, "Other Land Tenure", LawKind.LAND_TENURE)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with LAND_TENURE.
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
    ethics = Law.create(5, 0, "Camp Ethics", LawKind.ETHICS)
    with_ethics = enact_law(with_calendar, ethics)
    assert with_ethics is not None
    assembly = Law.create(6, 0, "Camp Assembly", LawKind.ASSEMBLY)
    with_assembly = enact_law(with_ethics, assembly)
    assert with_assembly is not None
    sanitation = Law.create(7, 0, "Camp Sanitation", LawKind.SANITATION)
    with_sanitation = enact_law(with_assembly, sanitation)
    assert with_sanitation is not None
    quarantine = Law.create(8, 0, "Camp Quarantine", LawKind.QUARANTINE)
    with_quarantine = enact_law(with_sanitation, quarantine)
    assert with_quarantine is not None
    building_codes = Law.create(9, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    with_codes = enact_law(with_quarantine, building_codes)
    assert with_codes is not None
    zoning = Law.create(10, 0, "Camp Zoning", LawKind.ZONING)
    with_zoning = enact_law(with_codes, zoning)
    assert with_zoning is not None
    passage = Law.create(11, 0, "Camp Passage", LawKind.PASSAGE)
    with_passage = enact_law(with_zoning, passage)
    assert with_passage is not None
    customs = Law.create(12, 0, "Camp Customs", LawKind.CUSTOMS)
    with_customs = enact_law(with_passage, customs)
    assert with_customs is not None
    assert active_land_tenure_law(with_customs, 0) == land_tenure
    assert (
        land_tenure_eat_bonus_for(
            with_customs,
            with_customs.agents[0],
        )
        == LAND_TENURE_EAT_RESTORE_BONUS
    )


def test_sanitation_bonus_requires_living_subject() -> None:
    """Only living agents under a SANITATION polity receive the drink bonus."""
    sanitation = Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(sanitation,))
    assert sanitation_drink_bonus_for(world, world.agents[0]) == (
        SANITATION_DRINK_RESTORE_BONUS
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert sanitation_drink_bonus_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert sanitation_drink_bonus_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert sanitation_drink_bonus_for(bare, bare.agents[0]) == 0.0


def test_quarantine_bonus_requires_living_subject() -> None:
    """Only living agents under a QUARANTINE polity receive the rest bonus."""
    quarantine = Law.create(0, 0, "Camp Quarantine", LawKind.QUARANTINE)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(quarantine,))
    assert quarantine_rest_bonus_for(world, world.agents[0]) == (
        QUARANTINE_REST_RESTORE_BONUS
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert quarantine_rest_bonus_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert quarantine_rest_bonus_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert quarantine_rest_bonus_for(bare, bare.agents[0]) == 0.0


def test_building_codes_discount_requires_living_subject() -> None:
    """Only living agents under BUILDING_CODES receive the move discount."""
    building_codes = Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(building_codes,))
    assert building_codes_move_discount_for(world, world.agents[0]) == (
        BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert building_codes_move_discount_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert building_codes_move_discount_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert building_codes_move_discount_for(bare, bare.agents[0]) == 0.0


def test_zoning_bonus_requires_living_subject() -> None:
    """Only living agents under a ZONING polity receive the eat bonus."""
    zoning = Law.create(0, 0, "Camp Zoning", LawKind.ZONING)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(zoning,))
    assert zoning_eat_bonus_for(world, world.agents[0]) == ZONING_EAT_RESTORE_BONUS
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert zoning_eat_bonus_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert zoning_eat_bonus_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert zoning_eat_bonus_for(bare, bare.agents[0]) == 0.0


def test_passage_discount_requires_living_subject() -> None:
    """Only living agents under PASSAGE receive the move discount."""
    passage = Law.create(0, 0, "Camp Passage", LawKind.PASSAGE)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(passage,))
    assert passage_move_discount_for(world, world.agents[0]) == (
        PASSAGE_MOVE_ENERGY_DISCOUNT
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert passage_move_discount_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert passage_move_discount_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert passage_move_discount_for(bare, bare.agents[0]) == 0.0


def test_customs_discount_requires_living_subject() -> None:
    """Only living agents under CUSTOMS receive the produce discount."""
    customs = Law.create(0, 0, "Camp Customs", LawKind.CUSTOMS)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(customs,))
    assert customs_produce_discount_for(world, world.agents[0]) == (
        CUSTOMS_PRODUCE_ENERGY_DISCOUNT
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert customs_produce_discount_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert customs_produce_discount_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert customs_produce_discount_for(bare, bare.agents[0]) == 0.0


def test_land_tenure_bonus_requires_living_subject() -> None:
    """Only living agents under LAND_TENURE receive the eat bonus."""
    land_tenure = Law.create(0, 0, "Camp Land Tenure", LawKind.LAND_TENURE)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(land_tenure,))
    assert land_tenure_eat_bonus_for(world, world.agents[0]) == (
        LAND_TENURE_EAT_RESTORE_BONUS
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert land_tenure_eat_bonus_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert land_tenure_eat_bonus_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert land_tenure_eat_bonus_for(bare, bare.agents[0]) == 0.0


def test_enact_conservation_and_uniqueness() -> None:
    """CONSERVATION enacts once per government; kind alone enables wood bonus."""
    world = _world(Agent.create(agent_id=0, name="A"))
    conservation = Law.create(0, 0, "Camp Conservation", LawKind.CONSERVATION)
    enacted = enact_law(world, conservation)
    assert enacted is not None
    assert active_conservation_law(enacted, 0) == conservation
    assert conservation_wood_bonus_for(enacted, enacted.agents[0]) == (
        CONSERVATION_WOOD_GATHER_BONUS
    )
    assert CONSERVATION_WOOD_GATHER_BONUS == 1
    duplicate = Law.create(1, 0, "Other Conservation", LawKind.CONSERVATION)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with CONSERVATION.
    land_tenure = Law.create(1, 0, "Camp Land Tenure", LawKind.LAND_TENURE)
    with_tenure = enact_law(enacted, land_tenure)
    assert with_tenure is not None
    assert active_conservation_law(with_tenure, 0) == conservation


def test_conservation_bonus_requires_living_subject() -> None:
    """Only living agents under CONSERVATION receive the wood gather bonus."""
    conservation = Law.create(0, 0, "Camp Conservation", LawKind.CONSERVATION)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(conservation,))
    assert conservation_wood_bonus_for(world, world.agents[0]) == (
        CONSERVATION_WOOD_GATHER_BONUS
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert conservation_wood_bonus_for(world, dead) == 0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert conservation_wood_bonus_for(ungoverned, ungoverned.agents[0]) == 0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert conservation_wood_bonus_for(bare, bare.agents[0]) == 0


def test_enact_labor_and_uniqueness() -> None:
    """LABOR enacts once per government; kind alone enables discount."""
    world = _world(Agent.create(agent_id=0, name="A"))
    labor = Law.create(0, 0, "Camp Labor", LawKind.LABOR)
    enacted = enact_law(world, labor)
    assert enacted is not None
    assert active_labor_law(enacted, 0) == labor
    assert labor_produce_discount_for(enacted, enacted.agents[0]) == (
        LABOR_PRODUCE_ENERGY_DISCOUNT
    )
    assert LABOR_PRODUCE_ENERGY_DISCOUNT == 0.02
    duplicate = Law.create(1, 0, "Other Labor", LawKind.LABOR)
    assert enact_law(enacted, duplicate) is None
    # Other unique kinds may coexist with LABOR.
    customs = Law.create(1, 0, "Camp Customs", LawKind.CUSTOMS)
    with_customs = enact_law(enacted, customs)
    assert with_customs is not None
    assert active_labor_law(with_customs, 0) == labor
    assert (
        labor_produce_discount_for(
            with_customs,
            with_customs.agents[0],
        )
        == LABOR_PRODUCE_ENERGY_DISCOUNT
    )


def test_labor_discount_requires_living_subject() -> None:
    """Only living agents under LABOR receive the produce discount."""
    labor = Law.create(0, 0, "Camp Labor", LawKind.LABOR)
    world = _world(Agent.create(agent_id=0, name="A"), laws=(labor,))
    assert labor_produce_discount_for(world, world.agents[0]) == (
        LABOR_PRODUCE_ENERGY_DISCOUNT
    )
    dead = world.agents[0].model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": world.agents[0].health.model_copy(update={"vitality": 0.0}),
        }
    )
    assert labor_produce_discount_for(world, dead) == 0.0
    ungoverned = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(),
        laws=(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert labor_produce_discount_for(ungoverned, ungoverned.agents[0]) == 0.0
    bare = _world(Agent.create(agent_id=0, name="A"))
    assert labor_produce_discount_for(bare, bare.agents[0]) == 0.0


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
    """Census reports active/inactive and per-kind tallies."""
    active = Law.create(0, 0, "A", LawKind.TAX_SCHEDULE, flat_amount=1, active=True)
    inactive = Law.create(1, 0, "B", LawKind.TAX_SCHEDULE, flat_amount=1, active=False)
    fee = Law.create(2, 0, "Fee", LawKind.MARKET_FEE, flat_amount=1, active=True)
    curriculum = Law.create(3, 0, "Schools", LawKind.CURRICULUM, active=True)
    calendar = Law.create(4, 0, "Calendar", LawKind.CALENDAR, active=True)
    ethics = Law.create(5, 0, "Ethics", LawKind.ETHICS, active=True)
    assembly = Law.create(6, 0, "Assembly", LawKind.ASSEMBLY, active=True)
    sanitation = Law.create(7, 0, "Sanitation", LawKind.SANITATION, active=True)
    quarantine = Law.create(8, 0, "Quarantine", LawKind.QUARANTINE, active=True)
    building_codes = Law.create(
        9,
        0,
        "Building Codes",
        LawKind.BUILDING_CODES,
        active=True,
    )
    zoning = Law.create(10, 0, "Zoning", LawKind.ZONING, active=True)
    passage = Law.create(11, 0, "Passage", LawKind.PASSAGE, active=True)
    customs = Law.create(12, 0, "Customs", LawKind.CUSTOMS, active=True)
    land_tenure = Law.create(13, 0, "Land Tenure", LawKind.LAND_TENURE, active=True)
    conservation = Law.create(14, 0, "Conservation", LawKind.CONSERVATION, active=True)
    labor = Law.create(15, 0, "Labor", LawKind.LABOR, active=True)
    world = _world(
        Agent.create(agent_id=0, name="A"),
        laws=(
            active,
            inactive,
            fee,
            curriculum,
            calendar,
            ethics,
            assembly,
            sanitation,
            quarantine,
            building_codes,
            zoning,
            passage,
            customs,
            land_tenure,
            conservation,
            labor,
        ),
    )
    snap = census_laws(world)
    assert snap.law_count == 16
    assert snap.active_count == 15
    assert snap.inactive_count == 1
    assert snap.governments_with_active_laws == 1
    assert snap.active_tax_schedule_count == 1
    assert snap.active_market_fee_count == 1
    assert snap.active_curriculum_count == 1
    assert snap.active_calendar_count == 1
    assert snap.active_ethics_count == 1
    assert snap.active_assembly_count == 1
    assert snap.active_sanitation_count == 1
    assert snap.active_quarantine_count == 1
    assert snap.active_building_codes_count == 1
    assert snap.active_zoning_count == 1
    assert snap.active_passage_count == 1
    assert snap.active_customs_count == 1
    assert snap.active_land_tenure_count == 1
    assert snap.active_conservation_count == 1
    assert snap.active_labor_count == 1
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
