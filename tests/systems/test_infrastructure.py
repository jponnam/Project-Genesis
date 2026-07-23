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
    InfrastructureCommissioned,
    InfrastructureKind,
    InfrastructuresObserved,
    Institution,
    InstitutionKind,
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
    assert events[0].active_road_count == 0
    assert events[0].active_scriptorium_count == 0
    assert events[0].active_stoa_count == 0
    assert events[0].active_observatory_count == 0
    assert events[0].active_shrine_count == 0
    assert events[0].active_clinic_count == 0
    assert events[0].active_bathhouse_count == 0
    assert events[0].active_bridge_count == 0
    assert events[0].active_scaffold_count == 0
    assert events[0].active_waystation_count == 0
    assert events[0].active_beacon_count == 0
    assert events[0].active_ditch_count == 0
    assert events[0].active_terrace_count == 0
    assert events[0].active_fulling_mill_count == 0
    assert events[0].active_warehouse_count == 0
    assert events[0].active_mineshaft_count == 0
    assert events[0].active_forge_works_count == 0
    assert events[0].active_lumber_yard_count == 0
    assert events[0].active_sawpit_count == 0
    assert events[0].active_kiln_yard_count == 0
    assert events[0].active_clay_pit_count == 0
    assert events[0].active_glasshouse_count == 0


def test_observe_emits_active_stoa_count() -> None:
    """observe includes active stoa counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Stoa", InfrastructureKind.STOA),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_stoa_count == 1
    assert events[0].active_scriptorium_count == 0


def test_observe_emits_active_clinic_count() -> None:
    """observe includes active clinic counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Clinic", InfrastructureKind.CLINIC),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_clinic_count == 1
    assert events[0].active_shrine_count == 0


def test_observe_emits_active_bathhouse_count() -> None:
    """observe includes active bathhouse counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Bathhouse", InfrastructureKind.BATHHOUSE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_bathhouse_count == 1
    assert events[0].active_clinic_count == 0


def test_observe_emits_active_bridge_count() -> None:
    """observe includes active bridge counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Bridge", InfrastructureKind.BRIDGE),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_bridge_count == 1
    assert events[0].active_road_count == 0


def test_observe_emits_active_scaffold_count() -> None:
    """observe includes active scaffold counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scaffold", InfrastructureKind.SCAFFOLD
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_scaffold_count == 1
    assert events[0].active_bridge_count == 0


def test_observe_emits_active_waystation_count() -> None:
    """observe includes active waystation counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Waystation", InfrastructureKind.WAYSTATION
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_waystation_count == 1
    assert events[0].active_scaffold_count == 0


def test_observe_emits_active_beacon_count() -> None:
    """observe includes active beacon counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Beacon", InfrastructureKind.BEACON),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_beacon_count == 1
    assert events[0].active_waystation_count == 0


def test_observe_emits_active_ditch_count() -> None:
    """observe includes active ditch counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Ditch", InfrastructureKind.DITCH),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_ditch_count == 1
    assert events[0].active_beacon_count == 0


def test_observe_emits_active_terrace_count() -> None:
    """observe includes active terrace counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Terrace", InfrastructureKind.TERRACE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_terrace_count == 1
    assert events[0].active_ditch_count == 0


def test_observe_emits_active_fulling_mill_count() -> None:
    """observe includes active fulling mill counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Fulling Mill", InfrastructureKind.FULLING_MILL
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_fulling_mill_count == 1
    assert events[0].active_terrace_count == 0


def test_observe_emits_active_warehouse_count() -> None:
    """observe includes active warehouse counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Warehouse", InfrastructureKind.WAREHOUSE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_warehouse_count == 1
    assert events[0].active_fulling_mill_count == 0


def test_observe_emits_active_mineshaft_count() -> None:
    """observe includes active mineshaft counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Mineshaft", InfrastructureKind.MINESHAFT
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_mineshaft_count == 1
    assert events[0].active_warehouse_count == 0


def test_observe_emits_active_forge_works_count() -> None:
    """observe includes active forge works counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Forge Works", InfrastructureKind.FORGE_WORKS
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_forge_works_count == 1
    assert events[0].active_mineshaft_count == 0


def test_observe_emits_active_lumber_yard_count() -> None:
    """observe includes active lumber yard counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Lumber Yard", InfrastructureKind.LUMBER_YARD
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_lumber_yard_count == 1
    assert events[0].active_forge_works_count == 0


def test_observe_emits_active_sawpit_count() -> None:
    """observe includes active sawpit counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Sawpit", InfrastructureKind.SAWPIT
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_sawpit_count == 1
    assert events[0].active_forge_works_count == 0



def test_observe_emits_active_kiln_yard_count() -> None:
    """observe includes active kiln yard counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Kiln Yard", InfrastructureKind.KILN_YARD
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_kiln_yard_count == 1
    assert events[0].active_sawpit_count == 0



def test_observe_emits_active_clay_pit_count() -> None:
    """observe includes active clay pit counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Clay Pit", InfrastructureKind.CLAY_PIT
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_clay_pit_count == 1
    assert events[0].active_kiln_yard_count == 0


def test_observe_emits_active_glasshouse_count() -> None:
    """observe includes active glasshouse counts in the infrastructure event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Glasshouse", InfrastructureKind.GLASSHOUSE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = InfrastructureSystem().observe(world, bus=bus)
    assert updated == world
    events = [
        event for event in bus.history if isinstance(event, InfrastructuresObserved)
    ]
    assert len(events) == 1
    assert events[0].active_glasshouse_count == 1
    assert events[0].active_clay_pit_count == 0


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


def test_system_commission_emits_infrastructure_commissioned() -> None:
    """commission pays from an institution budget and emits the event."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=0),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        institutions=(
            Institution.create(
                0,
                0,
                0,
                "Council",
                InstitutionKind.COUNCIL,
                budget=DEFAULT_WELL_BUILD_COST + 1,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    system = InfrastructureSystem()
    built = system.commission(
        world,
        Infrastructure.create(0, 0, 0, 0, "Council Well", InfrastructureKind.WELL),
        0,
        bus=bus,
    )
    assert built.infrastructure_by_id(0) is not None
    assert built.institutions[0].budget == 1
    events = [
        event for event in bus.history if isinstance(event, InfrastructureCommissioned)
    ]
    assert len(events) == 1
    assert events[0].cost == DEFAULT_WELL_BUILD_COST
    assert events[0].budget_after == 1
    assert events[0].name == "Council Well"
