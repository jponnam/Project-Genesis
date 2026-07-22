"""Unit tests for the InstitutionSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Government,
    Institution,
    InstitutionKind,
    InstitutionsObserved,
    SimulationConfig,
    World,
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
    assert events[0].vacant_officer_count == 1


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
