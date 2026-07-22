"""Unit tests for the InfrastructureSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    DEFAULT_WELL_BUILD_COST,
    Agent,
    City,
    CityKind,
    Government,
    Infrastructure,
    InfrastructureBuilt,
    InfrastructureKind,
    InfrastructuresObserved,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import InfrastructureConfig, InfrastructureSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one infrastructure census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].infrastructure_count == 1
    assert events[0].active_well_count == 1
    assert events[0].active_storehouse_count == 0


def test_observe_can_suppress_events() -> None:
    """InfrastructureConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    InfrastructureSystem(InfrastructureConfig(emit_events=False)).observe(
        world, bus=bus
    )
    assert bus.history == ()


def test_system_wrappers_create_and_dissolve() -> None:
    """System wrappers apply legal infrastructure mutations."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = InfrastructureSystem()
    created = system.create(
        world,
        Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
    )
    assert created.infrastructure_by_id(0) is not None
    dissolved = system.dissolve(created, 0)
    assert dissolved.infrastructure[0].active is False


def test_system_build_emits_infrastructure_built() -> None:
    """build pays the catalog cost and emits InfrastructureBuilt."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(
            Government.create(0, "Camp", 0, (0,), treasury=DEFAULT_WELL_BUILD_COST + 2),
        ),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    system = InfrastructureSystem()
    built = system.build(
        world,
        Infrastructure.create(0, 0, 0, 0, "Paid Well", InfrastructureKind.WELL),
        bus=bus,
    )
    assert built.infrastructure_by_id(0) is not None
    assert built.governments[0].treasury == 2
    events = [event for event in bus.history if isinstance(event, InfrastructureBuilt)]
    assert len(events) == 1
    assert events[0].cost == DEFAULT_WELL_BUILD_COST
    assert events[0].treasury_after == 2
    assert events[0].name == "Paid Well"

    unchanged = system.build(
        built,
        Infrastructure.create(1, 0, 0, 0, "Dup", InfrastructureKind.WELL),
        bus=bus,
    )
    assert unchanged == built
    assert len([e for e in bus.history if isinstance(e, InfrastructureBuilt)]) == 1
