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
    agoras_for,
    capital_for,
    census_cities,
    city_at,
    city_by_id,
    create_city,
    default_cities,
    default_world_map,
    dissolve_city,
    forums_for,
    foundries_for,
    harbors_for,
    infirmaries_for,
    lazarettos_for,
    libraries_for,
    next_city_id,
    outposts_for,
    quarries_for,
    resident_count,
    sanctuaries_for,
    set_capital,
)
from civitas.engine import WorldFactory


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
    assert snap.active_outpost_count == 0
    assert snap.active_library_count == 0
    assert snap.active_forum_count == 0
    assert snap.active_sanctuary_count == 0
    assert snap.active_agora_count == 0
    assert snap.active_infirmary_count == 0
    assert snap.active_lazaretto_count == 0
    assert snap.active_foundry_count == 0
    assert snap.active_quarry_count == 0
    assert snap.active_harbor_count == 0
    assert census_cities(world) == snap


def test_create_outpost_under_camp_government() -> None:
    """Outposts may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    outpost = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Outpost",
        CityKind.OUTPOST,
    )
    created = create_city(world, outpost)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.OUTPOST  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert outposts_for(created, CAMP_GOVERNMENT.government_id.value) == (outpost,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_outpost_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_outpost() -> None:
    """Outposts cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Outpost",
                CityKind.OUTPOST,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_outpost() -> None:
    """set_capital cannot promote an outpost to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Outpost",
                CityKind.OUTPOST,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_outpost() -> None:
    """World validation rejects outposts flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.OUTPOST,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_factory_still_seeds_one_settlement_capital() -> None:
    """Seed-42 factory defaults remain a single settlement capital."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    assert world.cities == (CAMP_CITY,)
    assert world.cities[0].kind is CityKind.SETTLEMENT
    assert world.cities[0].is_capital is True
    snap = census_cities(world)
    assert snap.active_settlement_count == 1
    assert snap.active_outpost_count == 0
    assert snap.active_library_count == 0
    assert snap.active_forum_count == 0
    assert snap.active_sanctuary_count == 0
    assert snap.active_agora_count == 0
    assert snap.active_infirmary_count == 0
    assert snap.active_lazaretto_count == 0
    assert snap.active_foundry_count == 0
    assert snap.active_quarry_count == 0
    assert snap.active_harbor_count == 0


def test_create_library_under_camp_government() -> None:
    """Libraries may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    library = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Library",
        CityKind.LIBRARY,
    )
    created = create_city(world, library)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.LIBRARY  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert libraries_for(created, CAMP_GOVERNMENT.government_id.value) == (library,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_library_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_library() -> None:
    """Libraries cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Library",
                CityKind.LIBRARY,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_library() -> None:
    """set_capital cannot promote a library to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Library",
                CityKind.LIBRARY,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_library() -> None:
    """World validation rejects libraries flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.LIBRARY,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_forum_under_camp_government() -> None:
    """Forums may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    forum = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Forum",
        CityKind.FORUM,
    )
    created = create_city(world, forum)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.FORUM  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert forums_for(created, CAMP_GOVERNMENT.government_id.value) == (forum,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_forum_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_forum() -> None:
    """Forums cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Forum",
                CityKind.FORUM,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_forum() -> None:
    """set_capital cannot promote a forum to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Forum",
                CityKind.FORUM,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_forum() -> None:
    """World validation rejects forums flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.FORUM,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_sanctuary_under_camp_government() -> None:
    """Sanctuaries may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    sanctuary = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Sanctuary",
        CityKind.SANCTUARY,
    )
    created = create_city(world, sanctuary)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.SANCTUARY  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert sanctuaries_for(created, CAMP_GOVERNMENT.government_id.value) == (sanctuary,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_sanctuary_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_sanctuary() -> None:
    """Sanctuaries cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Sanctuary",
                CityKind.SANCTUARY,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_sanctuary() -> None:
    """set_capital cannot promote a sanctuary to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Sanctuary",
                CityKind.SANCTUARY,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_sanctuary() -> None:
    """World validation rejects sanctuaries flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.SANCTUARY,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_agora_under_camp_government() -> None:
    """Agoras may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agora = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Agora",
        CityKind.AGORA,
    )
    created = create_city(world, agora)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.AGORA  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert agoras_for(created, CAMP_GOVERNMENT.government_id.value) == (agora,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_agora_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_agora() -> None:
    """Agoras cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Agora",
                CityKind.AGORA,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_agora() -> None:
    """set_capital cannot promote an agora to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Agora",
                CityKind.AGORA,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_agora() -> None:
    """World validation rejects agoras flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.AGORA,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_infirmary_under_camp_government() -> None:
    """Infirmaries may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    infirmary = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Infirmary",
        CityKind.INFIRMARY,
    )
    created = create_city(world, infirmary)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.INFIRMARY  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert infirmaries_for(created, CAMP_GOVERNMENT.government_id.value) == (infirmary,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_infirmary_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_infirmary() -> None:
    """Infirmaries cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Infirmary",
                CityKind.INFIRMARY,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_infirmary() -> None:
    """set_capital cannot promote an infirmary to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Infirmary",
                CityKind.INFIRMARY,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_infirmary() -> None:
    """World validation rejects infirmaries flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.INFIRMARY,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_lazaretto_under_camp_government() -> None:
    """Lazarettos may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    lazaretto = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Lazaretto",
        CityKind.LAZARETTO,
    )
    created = create_city(world, lazaretto)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.LAZARETTO  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert lazarettos_for(created, CAMP_GOVERNMENT.government_id.value) == (lazaretto,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_lazaretto_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_lazaretto() -> None:
    """Lazarettos cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Lazaretto",
                CityKind.LAZARETTO,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_lazaretto() -> None:
    """set_capital cannot promote a lazaretto to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Lazaretto",
                CityKind.LAZARETTO,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_lazaretto() -> None:
    """World validation rejects lazarettos flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.LAZARETTO,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_foundry_under_camp_government() -> None:
    """Foundries may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    foundry = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Foundry",
        CityKind.FOUNDRY,
    )
    created = create_city(world, foundry)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.FOUNDRY  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert foundries_for(created, CAMP_GOVERNMENT.government_id.value) == (foundry,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_foundry_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_foundry() -> None:
    """Foundries cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Foundry",
                CityKind.FOUNDRY,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_foundry() -> None:
    """set_capital cannot promote a foundry to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Foundry",
                CityKind.FOUNDRY,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_foundry() -> None:
    """World validation rejects foundries flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.FOUNDRY,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_quarry_under_camp_government() -> None:
    """Quarries may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    quarry = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Quarry",
        CityKind.QUARRY,
    )
    created = create_city(world, quarry)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.QUARRY  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert quarries_for(created, CAMP_GOVERNMENT.government_id.value) == (quarry,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_quarry_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_quarry() -> None:
    """Quarries cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Quarry",
                CityKind.QUARRY,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_quarry() -> None:
    """set_capital cannot promote a quarry to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Quarry",
                CityKind.QUARRY,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_quarry() -> None:
    """World validation rejects quarries flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.QUARRY,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_create_harbor_under_camp_government() -> None:
    """Harbors may share a government with the capital on a distinct seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    harbor = City.create(
        1,
        CAMP_GOVERNMENT.government_id.value,
        1,
        "Plain Harbor",
        CityKind.HARBOR,
    )
    created = create_city(world, harbor)
    assert created is not None
    assert city_by_id(created, 1) is not None
    assert city_by_id(created, 1).kind is CityKind.HARBOR  # type: ignore[union-attr]
    assert city_by_id(created, 1).is_capital is False  # type: ignore[union-attr]
    assert harbors_for(created, CAMP_GOVERNMENT.government_id.value) == (harbor,)
    snap = census_cities(created)
    assert snap.active_settlement_count == 1
    assert snap.active_harbor_count == 1
    assert snap.capital_count == 1
    assert snap.city_count == 2


def test_create_rejects_capital_harbor() -> None:
    """Harbors cannot be capitals."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(CAMP_CITY,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        create_city(
            world,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Bad Harbor",
                CityKind.HARBOR,
                is_capital=True,
            ),
        )
        is None
    )


def test_set_capital_rejects_harbor() -> None:
    """set_capital cannot promote a harbor to capital."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=(
            CAMP_CITY,
            City.create(
                1,
                CAMP_GOVERNMENT.government_id.value,
                1,
                "Plain Harbor",
                CityKind.HARBOR,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert set_capital(world, 1, True) is None
    assert capital_for(world, 0) == CAMP_CITY


def test_world_rejects_capital_harbor() -> None:
    """World validation rejects harbors flagged as capital."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(
                City.create(
                    0,
                    0,
                    0,
                    "Bad",
                    CityKind.HARBOR,
                    is_capital=True,
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


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
