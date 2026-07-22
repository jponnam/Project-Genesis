"""Unit tests for infrastructure models, helpers, and world rules."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_CITY,
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    CAMP_WELL,
    DEFAULT_ROAD_BUILD_COST,
    DEFAULT_SCRIPTORIUM_BUILD_COST,
    DEFAULT_STOREHOUSE_BUILD_COST,
    DEFAULT_WELL_BUILD_COST,
    Agent,
    City,
    CityKind,
    Government,
    Infrastructure,
    InfrastructureKind,
    Institution,
    InstitutionKind,
    SimulationConfig,
    World,
    build_cost_for,
    build_infrastructure,
    build_infrastructure_from_institution,
    census_infrastructure,
    create_infrastructure,
    default_cities,
    default_infrastructure,
    default_world_map,
    dissolve_infrastructure,
    infrastructure_by_id,
    next_infrastructure_id,
    society_money_total,
)


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (Government.create(0, "Camp", 0, (0,)),),
    cities: tuple[City, ...] = (
        City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
    ),
    institutions: tuple[Institution, ...] = (),
    infrastructure: tuple[Infrastructure, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        cities=cities,
        institutions=institutions,
        infrastructure=infrastructure,
        agents=agents,
    )


def test_default_infrastructure_seeds_camp_well() -> None:
    """Canonical infrastructure is an active well at Camp City."""
    assert default_infrastructure() == (CAMP_WELL,)
    assert CAMP_WELL.kind is InfrastructureKind.WELL
    assert CAMP_WELL.active is True
    assert CAMP_WELL.city_id.value == CAMP_CITY.city_id.value
    assert CAMP_WELL.government_id.value == CAMP_GOVERNMENT.government_id.value
    assert CAMP_WELL.location_id.value == CAMP_LOCATION.location_id.value


def test_create_and_lookup_infrastructure() -> None:
    """create_infrastructure inserts sorted ids and supports lookups."""
    world = _world(Agent.create(agent_id=0, name="A"))
    created = create_infrastructure(
        world,
        Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
    )
    assert created is not None
    assert infrastructure_by_id(created, 0) is not None
    assert next_infrastructure_id(created).value == 1


def test_create_rejects_second_active_well_at_location() -> None:
    """At most one active well per location."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "A", InfrastructureKind.WELL),
        ),
    )
    assert (
        create_infrastructure(
            world,
            Infrastructure.create(1, 0, 0, 0, "B", InfrastructureKind.WELL),
        )
        is None
    )


def test_dissolve_frees_active_kind_slot() -> None:
    """Soft dissolve frees the active-kind-at-location slot."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "A", InfrastructureKind.WELL),
        ),
    )
    dissolved = dissolve_infrastructure(world, 0)
    assert dissolved is not None
    assert dissolved.infrastructure[0].active is False
    recreated = create_infrastructure(
        dissolved,
        Infrastructure.create(1, 0, 0, 0, "B", InfrastructureKind.WELL),
    )
    assert recreated is not None


def test_build_infrastructure_debits_treasury() -> None:
    """Paid builds debit the government treasury then insert the piece."""
    assert build_cost_for(InfrastructureKind.WELL) == DEFAULT_WELL_BUILD_COST
    world = _world(
        Agent.create(agent_id=0, name="A", money=10),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=8),),
    )
    initial = society_money_total(world)
    built = build_infrastructure(
        world,
        Infrastructure.create(0, 0, 0, 0, "New Well", InfrastructureKind.WELL),
    )
    assert built is not None
    assert built.infrastructure[0].name == "New Well"
    assert built.governments[0].treasury == 8 - DEFAULT_WELL_BUILD_COST
    assert society_money_total(built) == initial - DEFAULT_WELL_BUILD_COST

    assert (
        build_infrastructure(
            world,
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
            cost=0,
        )
        is None
    )
    assert (
        build_infrastructure(
            world,
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
            cost=9,
        )
        is None
    )
    occupied = create_infrastructure(
        world,
        Infrastructure.create(0, 0, 0, 0, "Seed", InfrastructureKind.WELL),
    )
    assert occupied is not None
    assert (
        build_infrastructure(
            occupied,
            Infrastructure.create(1, 0, 0, 0, "Dup", InfrastructureKind.WELL),
        )
        is None
    )


def test_census_infrastructure_counts() -> None:
    """Census aggregates active well stats without mutation."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Active", InfrastructureKind.WELL),
            Infrastructure.create(
                1, 0, 0, 0, "Inactive", InfrastructureKind.WELL, active=False
            ),
        ),
    )
    snap = census_infrastructure(world)
    assert snap.infrastructure_count == 2
    assert snap.active_count == 1
    assert snap.inactive_count == 1
    assert snap.governments_with_infrastructure == 1
    assert snap.cities_with_infrastructure == 1
    assert snap.active_well_count == 1
    assert snap.active_storehouse_count == 0
    assert snap.active_road_count == 0
    assert snap.active_scriptorium_count == 0
    assert census_infrastructure(world) == snap


def test_create_and_build_storehouse() -> None:
    """STOREHOUSE is a distinct kind with its own catalog build cost."""
    assert (
        build_cost_for(InfrastructureKind.STOREHOUSE) == DEFAULT_STOREHOUSE_BUILD_COST
    )
    world = _world(
        Agent.create(agent_id=0, name="A", money=4),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=20),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
        ),
    )
    # Storehouse may coexist with a well at the same seat.
    created = create_infrastructure(
        world,
        Infrastructure.create(1, 0, 0, 0, "Store", InfrastructureKind.STOREHOUSE),
    )
    assert created is not None
    assert created.infrastructure[1].kind is InfrastructureKind.STOREHOUSE
    snap = census_infrastructure(created)
    assert snap.active_well_count == 1
    assert snap.active_storehouse_count == 1

    empty = _world(
        Agent.create(agent_id=0, name="A"),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=20),),
    )
    built = build_infrastructure(
        empty,
        Infrastructure.create(0, 0, 0, 0, "Paid Store", InfrastructureKind.STOREHOUSE),
    )
    assert built is not None
    assert built.governments[0].treasury == 20 - DEFAULT_STOREHOUSE_BUILD_COST


def test_build_infrastructure_from_institution_budget() -> None:
    """Institution budgets can commission infrastructure of their government."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=3),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=0),),
        institutions=(
            Institution.create(
                0,
                0,
                0,
                "Council",
                InstitutionKind.COUNCIL,
                budget=DEFAULT_WELL_BUILD_COST + 2,
            ),
        ),
    )
    initial = society_money_total(world)
    built = build_infrastructure_from_institution(
        world,
        Infrastructure.create(0, 0, 0, 0, "Council Well", InfrastructureKind.WELL),
        0,
    )
    assert built is not None
    assert built.infrastructure[0].name == "Council Well"
    assert built.institutions[0].budget == 2
    assert built.governments[0].treasury == 0
    assert society_money_total(built) == initial - DEFAULT_WELL_BUILD_COST

    assert (
        build_infrastructure_from_institution(
            world,
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
            0,
            cost=0,
        )
        is None
    )
    broke = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL, budget=1),
        ),
    )
    assert (
        build_infrastructure_from_institution(
            broke,
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
            0,
        )
        is None
    )


def test_create_and_build_road() -> None:
    """ROAD is a distinct kind with its own catalog build cost."""
    assert build_cost_for(InfrastructureKind.ROAD) == DEFAULT_ROAD_BUILD_COST
    world = _world(
        Agent.create(agent_id=0, name="A"),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=20),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
        ),
    )
    created = create_infrastructure(
        world,
        Infrastructure.create(1, 0, 0, 0, "Road", InfrastructureKind.ROAD),
    )
    assert created is not None
    assert created.infrastructure[1].kind is InfrastructureKind.ROAD
    assert census_infrastructure(created).active_road_count == 1

    empty = _world(
        Agent.create(agent_id=0, name="A"),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=20),),
    )
    built = build_infrastructure(
        empty,
        Infrastructure.create(0, 0, 0, 0, "Paid Road", InfrastructureKind.ROAD),
    )
    assert built is not None
    assert built.governments[0].treasury == 20 - DEFAULT_ROAD_BUILD_COST


def test_create_and_build_scriptorium() -> None:
    """SCRIPTORIUM is a distinct kind with its own catalog build cost."""
    assert (
        build_cost_for(InfrastructureKind.SCRIPTORIUM) == DEFAULT_SCRIPTORIUM_BUILD_COST
    )
    world = _world(
        Agent.create(agent_id=0, name="A"),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=20),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Well", InfrastructureKind.WELL),
        ),
    )
    # Scriptorium may coexist with a well at the same seat.
    created = create_infrastructure(
        world,
        Infrastructure.create(
            1, 0, 0, 0, "Scriptorium", InfrastructureKind.SCRIPTORIUM
        ),
    )
    assert created is not None
    assert created.infrastructure[1].kind is InfrastructureKind.SCRIPTORIUM
    snap = census_infrastructure(created)
    assert snap.active_well_count == 1
    assert snap.active_scriptorium_count == 1

    empty = _world(
        Agent.create(agent_id=0, name="A"),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=20),),
    )
    built = build_infrastructure(
        empty,
        Infrastructure.create(
            0, 0, 0, 0, "Paid Scriptorium", InfrastructureKind.SCRIPTORIUM
        ),
    )
    assert built is not None
    assert built.governments[0].treasury == 20 - DEFAULT_SCRIPTORIUM_BUILD_COST


def test_world_rejects_city_location_mismatch() -> None:
    """Infrastructure location must match its city seat."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=default_world_map()[:2],
            governments=(Government.create(0, "Camp", 0, (0, 1)),),
            cities=(City.create(0, 0, 0, "A", CityKind.SETTLEMENT, is_capital=True),),
            infrastructure=(
                Infrastructure.create(0, 0, 0, 1, "Bad", InfrastructureKind.WELL),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_factory_shaped_defaults_validate() -> None:
    """Factory-shaped cities and infrastructure validate together."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        cities=default_cities(),
        infrastructure=default_infrastructure(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert world.infrastructure[0].name == "Camp Well"
