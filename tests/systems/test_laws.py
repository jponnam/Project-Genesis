"""Unit tests for the LawSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Government,
    Law,
    LawKind,
    LawsObserved,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import LawConfig, LawSystem


def test_observe_emits_laws_observed_without_mutating_world() -> None:
    """observe publishes one law census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = LawSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].law_count == 1
    assert events[0].active_count == 1
    assert events[0].active_tax_schedule_count == 1
    assert events[0].active_market_fee_count == 0
    assert events[0].active_curriculum_count == 0
    assert events[0].active_calendar_count == 0
    assert events[0].active_ethics_count == 0
    assert events[0].active_assembly_count == 0
    assert events[0].active_sanitation_count == 0
    assert events[0].active_quarantine_count == 0
    assert events[0].active_building_codes_count == 0
    assert events[0].active_zoning_count == 0
    assert events[0].active_passage_count == 0
    assert events[0].active_customs_count == 0
    assert events[0].active_land_tenure_count == 0
    assert events[0].active_conservation_count == 0
    assert events[0].active_labor_count == 0
    assert events[0].active_sumptuary_count == 0
    assert events[0].active_mineral_rights_count == 0
    assert events[0].active_safety_codes_count == 0
    assert events[0].active_timber_rights_count == 0
    assert events[0].active_forest_management_count == 0
    assert events[0].active_firing_codes_count == 0
    assert events[0].active_clay_codes_count == 0


def test_observe_emits_active_assembly_count() -> None:
    """observe reports active ASSEMBLY laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Assembly", LawKind.ASSEMBLY),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_assembly_count == 1


def test_observe_emits_active_sanitation_count() -> None:
    """observe reports active SANITATION laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_sanitation_count == 1


def test_observe_emits_active_quarantine_count() -> None:
    """observe reports active QUARANTINE laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Quarantine", LawKind.QUARANTINE),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_quarantine_count == 1


def test_observe_emits_active_building_codes_count() -> None:
    """observe reports active BUILDING_CODES laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_building_codes_count == 1


def test_observe_emits_active_zoning_count() -> None:
    """observe reports active ZONING laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Zoning", LawKind.ZONING),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_zoning_count == 1


def test_observe_emits_active_passage_count() -> None:
    """observe reports active PASSAGE laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Passage", LawKind.PASSAGE),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_passage_count == 1


def test_observe_emits_active_customs_count() -> None:
    """observe reports active CUSTOMS laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Customs", LawKind.CUSTOMS),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_customs_count == 1


def test_observe_emits_active_land_tenure_count() -> None:
    """observe reports active LAND_TENURE laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Land Tenure", LawKind.LAND_TENURE),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_land_tenure_count == 1


def test_observe_emits_active_conservation_count() -> None:
    """observe reports active CONSERVATION laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Conservation", LawKind.CONSERVATION),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_conservation_count == 1


def test_observe_emits_active_labor_count() -> None:
    """observe reports active LABOR laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Labor", LawKind.LABOR),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_labor_count == 1


def test_observe_emits_active_mineral_rights_count() -> None:
    """observe reports active MINERAL_RIGHTS laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Mineral Rights", LawKind.MINERAL_RIGHTS),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_mineral_rights_count == 1


def test_observe_emits_active_safety_codes_count() -> None:
    """observe reports active SAFETY_CODES laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Safety Codes", LawKind.SAFETY_CODES),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_safety_codes_count == 1


def test_observe_emits_active_timber_rights_count() -> None:
    """observe reports active TIMBER_RIGHTS laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Timber Rights", LawKind.TIMBER_RIGHTS),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_timber_rights_count == 1


def test_observe_emits_active_forest_management_count() -> None:
    """observe reports active FOREST_MANAGEMENT laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(
            Law.create(
                0, 0, "Camp Forest Management", LawKind.FOREST_MANAGEMENT
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_forest_management_count == 1




def test_observe_emits_active_firing_codes_count() -> None:
    """observe reports active FIRING_CODES laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Firing Codes", LawKind.FIRING_CODES),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_firing_codes_count == 1


def test_observe_emits_active_clay_codes_count() -> None:
    """observe reports active CLAY_CODES laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Clay Codes", LawKind.CLAY_CODES),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_clay_codes_count == 1

def test_observe_emits_active_sumptuary_count() -> None:
    """observe reports active SUMPTUARY laws in LawsObserved."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Sumptuary", LawKind.SUMPTUARY),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].active_sumptuary_count == 1


def test_observe_can_suppress_events() -> None:
    """LawConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=1),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem(LawConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_system_wrappers_enact_and_repeal() -> None:
    """System wrappers apply legal statute mutations."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = LawSystem()
    enacted = system.enact(
        world,
        Law.create(0, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=2),
    )
    assert enacted.law_by_id(0) is not None
    repealed = system.repeal(enacted, 0)
    assert repealed.law_by_id(0).active is False  # type: ignore[union-attr]
