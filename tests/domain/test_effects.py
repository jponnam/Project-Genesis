"""Unit tests for society effect helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_CANAL,
    CAMP_LOCATION,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    DEFAULT_DRINK_RESTORE,
    DEFAULT_GATHER_AMOUNT,
    DEFAULT_REST_RESTORE,
    FIRE_HEARTH_REST_BONUS,
    IRRIGATION_WATER_GATHER_BONUS,
    POTTERY_WATER_GATHER_BONUS,
    STOREHOUSE_FOOD_GATHER_BONUS,
    WELL_DRINK_RESTORE_BONUS,
    Agent,
    City,
    CityKind,
    Government,
    Infrastructure,
    InfrastructureKind,
    SimulationConfig,
    World,
    census_effects,
    drink_restore_bonus,
    effective_drink_restore,
    effective_gather_amount,
    effective_rest_restore,
    gather_amount_bonus,
    location_has_active_storehouse,
    location_has_active_well,
    rest_restore_bonus,
)
from civitas.engine import WorldFactory


def _world(*, innovations: tuple = ()) -> World:
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(CAMP_FIRE, CAMP_POTTERY, CAMP_IRRIGATION),
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A"),),
    )


def test_fire_hearth_boosts_rest_restore() -> None:
    """Active fire hearth adds a deterministic REST restore bonus."""
    bare = _world()
    with_fire = _world(innovations=(CAMP_FIRE_HEARTH,))
    assert rest_restore_bonus(bare) == 0.0
    assert rest_restore_bonus(with_fire) == FIRE_HEARTH_REST_BONUS
    assert effective_rest_restore(with_fire) == pytest.approx(
        DEFAULT_REST_RESTORE + FIRE_HEARTH_REST_BONUS
    )


def test_pottery_and_irrigation_stack_water_gather_bonus() -> None:
    """Active pottery craft and irrigation canal stack for water gather."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    active_pottery = CAMP_POTTERY_CRAFT.model_copy(update={"active": True})
    active_irrigation = CAMP_IRRIGATION_CANAL.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(CAMP_FIRE, discovered_pottery, discovered_irrigation),
        innovations=(CAMP_FIRE_HEARTH, active_pottery, active_irrigation),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    water_bonus = POTTERY_WATER_GATHER_BONUS + IRRIGATION_WATER_GATHER_BONUS
    assert gather_amount_bonus(world, "water") == water_bonus
    assert gather_amount_bonus(world, "food") == 0
    assert (
        effective_gather_amount(world, "water") == DEFAULT_GATHER_AMOUNT + water_bonus
    )
    assert effective_gather_amount(world, "food") == DEFAULT_GATHER_AMOUNT


def test_census_effects_reports_active_bonuses() -> None:
    """Census encodes active innovations and effective amounts in bps/units."""
    world = _world(innovations=(CAMP_FIRE_HEARTH,))
    snap = census_effects(world)
    assert snap.fire_hearth_active == 1
    assert snap.pottery_craft_active == 0
    assert snap.rest_restore_bps == 2500
    assert snap.water_gather_amount == 1
    assert snap.active_well_count == 0
    assert snap.drink_restore_bps == 3000


def test_well_boosts_drink_restore_for_colocated_agents() -> None:
    """Active wells add a DRINK restore bonus at their seat location."""
    world = WorldFactory().create(SimulationConfig(seed=1, agent_count=1))
    agent = world.agents[0]
    assert location_has_active_well(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == WELL_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + WELL_DRINK_RESTORE_BONUS
    )
    snap = census_effects(world)
    assert snap.active_well_count == 1
    assert snap.drink_restore_bps == 3500
    assert snap.active_storehouse_count == 0
    assert snap.food_gather_amount == DEFAULT_GATHER_AMOUNT


def test_storehouse_boosts_food_gather_for_colocated_agents() -> None:
    """Active storehouses add a food gather bonus at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Storehouse", InfrastructureKind.STOREHOUSE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_storehouse(world, agent.location_id) is True
    assert (
        gather_amount_bonus(world, "food", location_id=agent.location_id)
        == STOREHOUSE_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert (
        effective_gather_amount(world, "food", agent=agent)
        == DEFAULT_GATHER_AMOUNT + STOREHOUSE_FOOD_GATHER_BONUS
    )
    snap = census_effects(world)
    assert snap.active_storehouse_count == 1
    assert snap.food_gather_amount == (
        DEFAULT_GATHER_AMOUNT + STOREHOUSE_FOOD_GATHER_BONUS
    )
