"""Unit tests for the CitySystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    CitiesObserved,
    City,
    CityKind,
    Government,
    SimulationConfig,
    World,
    default_world_map,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import CityConfig, CitySystem


def test_observe_emits_cities_observed_without_mutating_world() -> None:
    """observe publishes one city census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = CitySystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].city_count == 1
    assert events[0].capital_count == 1
    assert events[0].total_residents == 3
    assert events[0].active_settlement_count == 1
    assert events[0].active_outpost_count == 0
    assert events[0].active_library_count == 0
    assert events[0].active_forum_count == 0
    assert events[0].active_sanctuary_count == 0
    assert events[0].active_agora_count == 0
    assert events[0].active_infirmary_count == 0
    assert events[0].active_lazaretto_count == 0
    assert events[0].active_foundry_count == 0
    assert events[0].active_quarry_count == 0
    assert events[0].active_harbor_count == 0
    assert events[0].active_entrepot_count == 0
    assert events[0].active_farmstead_count == 0
    assert events[0].active_pastoral_count == 0
    assert events[0].active_mill_town_count == 0
    assert events[0].active_emporium_count == 0
    assert events[0].active_mining_camp_count == 0
    assert events[0].active_ironworks_count == 0
    assert events[0].active_timber_town_count == 0
    assert events[0].active_guildhall_count == 0
    assert events[0].active_pottery_town_count == 0


def test_observe_can_suppress_events() -> None:
    """CityConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    CitySystem(CityConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_observe_reports_active_agora_count() -> None:
    """observe publishes the active agora city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Agora", CityKind.AGORA),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_agora_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_infirmary_count() -> None:
    """observe publishes the active infirmary city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Infirmary", CityKind.INFIRMARY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_infirmary_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_lazaretto_count() -> None:
    """observe publishes the active lazaretto city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Lazaretto", CityKind.LAZARETTO),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_lazaretto_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_foundry_count() -> None:
    """observe publishes the active foundry city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Foundry", CityKind.FOUNDRY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_foundry_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_quarry_count() -> None:
    """observe publishes the active quarry city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Quarry", CityKind.QUARRY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_quarry_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_harbor_count() -> None:
    """observe publishes the active harbor city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Harbor", CityKind.HARBOR),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_harbor_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_entrepot_count() -> None:
    """observe publishes the active entrepot city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Entrepot", CityKind.ENTREPOT),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_entrepot_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_farmstead_count() -> None:
    """observe publishes the active farmstead city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Farmstead", CityKind.FARMSTEAD),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_farmstead_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_pastoral_count() -> None:
    """observe publishes the active pastoral city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Pastoral", CityKind.PASTORAL),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_pastoral_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_mill_town_count() -> None:
    """observe publishes the active mill town city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Mill Town", CityKind.MILL_TOWN),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_mill_town_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_emporium_count() -> None:
    """observe publishes the active emporium city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Emporium", CityKind.EMPORIUM),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_emporium_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_mining_camp_count() -> None:
    """observe publishes the active mining camp city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Ore Camp", CityKind.MINING_CAMP),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_mining_camp_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_ironworks_count() -> None:
    """observe publishes the active ironworks city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Iron Town", CityKind.IRONWORKS),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_ironworks_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_timber_town_count() -> None:
    """observe publishes the active timber town city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Timber Town", CityKind.TIMBER_TOWN),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_timber_town_count == 1
    assert events[0].total_residents == 1


def test_observe_reports_active_guildhall_count() -> None:
    """observe publishes the active guildhall city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Guild Town", CityKind.GUILDHALL),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_guildhall_count == 1
    assert events[0].total_residents == 1




def test_observe_reports_active_pottery_town_count() -> None:
    """observe publishes the active pottery town city count."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Pottery Town", CityKind.POTTERY_TOWN),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    bus = EventBus()
    CitySystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, CitiesObserved)]
    assert len(events) == 1
    assert events[0].active_pottery_town_count == 1
    assert events[0].total_residents == 1

def test_system_wrappers_create_dissolve_and_capital() -> None:
    """System wrappers apply legal city mutations."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = CitySystem()
    created = system.create(
        world,
        City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
    )
    assert created.city_by_id(0) is not None
    cleared = system.set_capital_flag(created, 0, False)
    assert cleared.cities[0].is_capital is False
    dissolved = system.dissolve(cleared, 0)
    assert dissolved.cities[0].active is False
