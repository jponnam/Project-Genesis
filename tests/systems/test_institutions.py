"""Unit tests for the InstitutionSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Government,
    Institution,
    InstitutionFunded,
    InstitutionKind,
    InstitutionsObserved,
    SimulationConfig,
    World,
    society_money_total,
)
from civitas.domain.ids import AgentId
from civitas.engine import EventBus, WorldFactory
from civitas.systems import InstitutionConfig, InstitutionSystem


def test_observe_emits_institutions_observed_without_mutating_world() -> None:
    """observe publishes one institution census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = InstitutionSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, InstitutionsObserved)]
    assert len(events) == 1
    assert events[0].institution_count == 1
    assert events[0].active_count == 1
    assert events[0].active_council_count == 1
    assert events[0].active_guild_count == 0
    assert events[0].active_archive_count == 0
    assert events[0].active_bureaucracy_count == 0
    assert events[0].active_academy_count == 0
    assert events[0].active_temple_count == 0
    assert events[0].active_school_count == 0
    assert events[0].active_lyceum_count == 0
    assert events[0].active_hospital_count == 0
    assert events[0].active_apothecary_count == 0
    assert events[0].active_collegium_count == 0
    assert events[0].active_workshop_count == 0
    assert events[0].active_mason_count == 0
    assert events[0].active_architect_count == 0
    assert events[0].active_caravan_count == 0
    assert events[0].active_merchant_count == 0
    assert events[0].active_cartographer_count == 0
    assert events[0].active_granary_count == 0
    assert events[0].active_husbandman_count == 0
    assert events[0].active_agronomist_count == 0
    assert events[0].active_weaver_count == 0
    assert events[0].active_dyer_count == 0
    assert events[0].active_tailor_count == 0
    assert events[0].active_miner_count == 0
    assert events[0].active_smelter_count == 0
    assert events[0].active_smith_count == 0
    assert events[0].vacant_officer_count == 1
    assert events[0].total_budget == 0
    assert events[0].funded_count == 0


def test_observe_emits_active_health_institution_counts() -> None:
    """observe maps active health institution counts into the observed event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(2, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(3, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(4, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(5, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(6, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(7, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(8, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(9, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                10, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(11, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(12, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN),
            Institution.create(
                13, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(14, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
            Institution.create(15, 0, 0, "Camp Dyer", InstitutionKind.DYER),
            Institution.create(16, 0, 0, "Camp Tailor", InstitutionKind.TAILOR),
            Institution.create(17, 0, 0, "Camp Miner", InstitutionKind.MINER),
            Institution.create(18, 0, 0, "Camp Smelter", InstitutionKind.SMELTER),
            Institution.create(19, 0, 0, "Camp Smith", InstitutionKind.SMITH),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InstitutionSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, InstitutionsObserved)]
    assert len(events) == 1
    assert events[0].active_council_count == 1
    assert events[0].active_lyceum_count == 1
    assert events[0].active_hospital_count == 1
    assert events[0].active_apothecary_count == 1
    assert events[0].active_collegium_count == 1
    assert events[0].active_workshop_count == 1
    assert events[0].active_mason_count == 1
    assert events[0].active_architect_count == 1
    assert events[0].active_caravan_count == 1
    assert events[0].active_merchant_count == 1
    assert events[0].active_cartographer_count == 1
    assert events[0].active_granary_count == 1
    assert events[0].active_husbandman_count == 1
    assert events[0].active_agronomist_count == 1
    assert events[0].active_weaver_count == 1
    assert events[0].active_dyer_count == 1
    assert events[0].active_tailor_count == 1
    assert events[0].active_miner_count == 1
    assert events[0].active_smelter_count == 1
    assert events[0].active_smith_count == 1


def test_observe_can_suppress_events() -> None:
    """InstitutionConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    InstitutionSystem(InstitutionConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_system_wrappers_create_dissolve_and_appoint() -> None:
    """System wrappers apply legal institution mutations."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = InstitutionSystem()
    created = system.create(
        world,
        Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
    )
    assert created.institution_by_id(0) is not None
    staffed = system.appoint_officer(created, 0, 0)
    assert staffed.institutions[0].officer_id == AgentId(value=0)
    dissolved = system.dissolve(staffed, 0)
    assert dissolved.institutions[0].active is False


def test_system_fund_emits_institution_funded() -> None:
    """fund moves treasury money into the budget and emits InstitutionFunded."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=8),),
        institutions=(Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),),
        agents=(Agent.create(agent_id=0, name="A", money=2),),
    )
    bus = EventBus()
    system = InstitutionSystem()
    initial = society_money_total(world)
    funded = system.fund(world, 0, 5, bus=bus)
    assert funded.governments[0].treasury == 3
    assert funded.institutions[0].budget == 5
    assert society_money_total(funded) == initial
    events = [event for event in bus.history if isinstance(event, InstitutionFunded)]
    assert len(events) == 1
    assert events[0].amount == 5
    assert events[0].budget_after == 5
    assert events[0].treasury_after == 3

    unchanged = system.fund(funded, 0, 9, bus=bus)
    assert unchanged == funded
    assert len([e for e in bus.history if isinstance(e, InstitutionFunded)]) == 1
