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
