"""Unit tests for city models, helpers, and world rules."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_CITY,
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    Agent,
    City,
    CityKind,
    Government,
    SimulationConfig,
    World,
    capital_for,
    census_cities,
    city_at,
    city_by_id,
    create_city,
    default_cities,
    default_world_map,
    dissolve_city,
    next_city_id,
    resident_count,
    set_capital,
)


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (Government.create(0, "Camp", 0, (0,)),),
    cities: tuple[City, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        cities=cities,
        agents=agents,
    )


def test_default_cities_seed_camp_city() -> None:
    """Canonical city is an active capital settlement at the camp."""
    assert default_cities() == (CAMP_CITY,)
    assert CAMP_CITY.kind is CityKind.SETTLEMENT
    assert CAMP_CITY.active is True
    assert CAMP_CITY.is_capital is True
    assert CAMP_CITY.government_id.value == CAMP_GOVERNMENT.government_id.value
    assert CAMP_CITY.location_id.value == CAMP_LOCATION.location_id.value


def test_create_and_lookup_city() -> None:
    """create_city inserts sorted ids and supports lookups."""
    world = _world(Agent.create(agent_id=0, name="A"))
    created = create_city(
        world,
        City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
    )
    assert created is not None
    assert city_by_id(created, 0) is not None
    assert city_at(created, 0) is not None
    assert capital_for(created, 0) is not None
    assert resident_count(created, 0) == 1
    assert next_city_id(created).value == 1


def test_create_rejects_second_city_on_same_location() -> None:
    """At most one city per location."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        cities=(City.create(0, 0, 0, "A", CityKind.SETTLEMENT),),
    )
    assert (
        create_city(
            world,
            City.create(1, 0, 0, "B", CityKind.SETTLEMENT),
        )
        is None
    )


def test_set_capital_clears_previous() -> None:
    """Setting a capital clears the previous capital for that government."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "A", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "B", CityKind.SETTLEMENT),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    updated = set_capital(world, 1, True)
    assert updated is not None
    assert updated.cities[0].is_capital is False
    assert updated.cities[1].is_capital is True
    assert capital_for(updated, 0).city_id.value == 1  # type: ignore[union-attr]


def test_dissolve_city() -> None:
    """Soft dissolve deactivates without removing the archive entry."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        cities=(City.create(0, 0, 0, "A", CityKind.SETTLEMENT, is_capital=True),),
    )
    dissolved = dissolve_city(world, 0)
    assert dissolved is not None
    assert dissolved.cities[0].active is False


def test_census_cities_counts_residents() -> None:
    """Census aggregates residency for active cities."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
    )
    snap = census_cities(world)
    assert snap.city_count == 1
    assert snap.active_count == 1
    assert snap.capital_count == 1
    assert snap.total_residents == 2
    assert snap.mean_residents == 2.0
    assert snap.max_residents == 2
    assert snap.active_settlement_count == 1
    assert census_cities(world) == snap


def test_world_rejects_second_active_capital() -> None:
    """World validation rejects two active capitals for one government."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(0, 0, 0, "A", CityKind.SETTLEMENT, is_capital=True),
                City.create(1, 0, 1, "B", CityKind.SETTLEMENT, is_capital=True),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_factory_shaped_defaults_validate() -> None:
    """Factory-shaped governments and cities validate together."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=default_cities(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert world.cities[0].name == "Camp City"
