"""Unit tests for society effect helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    ACADEMY_TEACHINGS_PER_KNOWER_BONUS,
    ARCHIVE_RETRIEVAL_LIMIT_BONUS,
    ASTRONOMY_RETRIEVAL_LIMIT_BONUS,
    BUREAUCRACY_MARKET_FEE_DISCOUNT,
    CAMP_ABACUS,
    CAMP_ASTRONOMY,
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_FORGE,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_CANAL,
    CAMP_LOCATION,
    CAMP_MATHEMATICS,
    CAMP_METALLURGY,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    CAMP_SCRIBE,
    CAMP_STAR_CHART,
    CAMP_WRITING,
    CURRICULUM_TEACHINGS_PER_KNOWER_BONUS,
    DEFAULT_DRINK_RESTORE,
    DEFAULT_GATHER_AMOUNT,
    DEFAULT_MOVE_ENERGY_COST,
    DEFAULT_PRODUCE_ENERGY_COST,
    DEFAULT_REST_RESTORE,
    DEFAULT_RETRIEVAL_LIMIT,
    DEFAULT_TEACHINGS_PER_KNOWER,
    FIRE_HEARTH_REST_BONUS,
    GUILD_PRODUCE_ENERGY_DISCOUNT,
    IRRIGATION_WATER_GATHER_BONUS,
    LIBRARY_RETRIEVAL_LIMIT_BONUS,
    MATHEMATICS_PRODUCE_ENERGY_DISCOUNT,
    METALLURGY_STONE_GATHER_BONUS,
    OBSERVATORY_RETRIEVAL_LIMIT_BONUS,
    POTTERY_WATER_GATHER_BONUS,
    ROAD_MOVE_ENERGY_DISCOUNT,
    SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS,
    STOREHOUSE_FOOD_GATHER_BONUS,
    WELL_DRINK_RESTORE_BONUS,
    WRITING_TEACHINGS_PER_KNOWER_BONUS,
    Agent,
    City,
    CityKind,
    Government,
    Infrastructure,
    InfrastructureKind,
    Institution,
    InstitutionKind,
    Law,
    LawKind,
    SimulationConfig,
    World,
    census_effects,
    default_world_map,
    drink_restore_bonus,
    effective_drink_restore,
    effective_gather_amount,
    effective_market_fee,
    effective_move_energy_cost,
    effective_produce_energy_cost,
    effective_rest_restore,
    effective_retrieval_limit,
    effective_teachings_per_knower,
    gather_amount_bonus,
    location_has_active_academy,
    location_has_active_archive,
    location_has_active_bureaucracy,
    location_has_active_guild,
    location_has_active_library,
    location_has_active_observatory,
    location_has_active_road,
    location_has_active_scriptorium,
    location_has_active_storehouse,
    location_has_active_well,
    market_fee_for,
    rest_restore_bonus,
    teachings_per_knower_bonus,
)
from civitas.engine import WorldFactory


def _world(*, innovations: tuple = ()) -> World:
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(
            CAMP_FIRE,
            CAMP_POTTERY,
            CAMP_IRRIGATION,
            CAMP_METALLURGY,
            CAMP_WRITING,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
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
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            CAMP_METALLURGY,
            CAMP_WRITING,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            active_pottery,
            active_irrigation,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    water_bonus = POTTERY_WATER_GATHER_BONUS + IRRIGATION_WATER_GATHER_BONUS
    assert gather_amount_bonus(world, "water") == water_bonus
    assert gather_amount_bonus(world, "food") == 0
    assert gather_amount_bonus(world, "stone") == 0
    assert (
        effective_gather_amount(world, "water") == DEFAULT_GATHER_AMOUNT + water_bonus
    )
    assert effective_gather_amount(world, "food") == DEFAULT_GATHER_AMOUNT


def test_forge_boosts_stone_gather_bonus() -> None:
    """Active forge adds a deterministic stone gather bonus."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            CAMP_WRITING,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            active_forge,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert gather_amount_bonus(world, "stone") == METALLURGY_STONE_GATHER_BONUS
    assert gather_amount_bonus(world, "water") == 0
    assert (
        effective_gather_amount(world, "stone")
        == DEFAULT_GATHER_AMOUNT + METALLURGY_STONE_GATHER_BONUS
    )


def test_scribe_boosts_teachings_per_knower() -> None:
    """Active scribe adds a deterministic teachings-per-knower bonus."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert teachings_per_knower_bonus(world) == WRITING_TEACHINGS_PER_KNOWER_BONUS
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert teachings_per_knower_bonus(bare) == 0
    assert (
        effective_teachings_per_knower(bare, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER
    )


def test_scriptorium_boosts_teachings_and_stacks_with_scribe() -> None:
    """Active scriptorium adds a seat bonus that stacks with scribe."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_scriptorium(world, agent.location_id) is True
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    assert (
        effective_teachings_per_knower(
            world, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=agent
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
        + WRITING_TEACHINGS_PER_KNOWER_BONUS
        + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        effective_teachings_per_knower(
            bare, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=bare.agents[0]
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
    )


def test_curriculum_boosts_teachings_and_stacks_with_scribe_scriptorium() -> None:
    """Active CURRICULUM stacks with scribe and scriptorium for subjects."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    curriculum = Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(curriculum,),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert (
        effective_teachings_per_knower(
            world, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=agent
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
        + WRITING_TEACHINGS_PER_KNOWER_BONUS
        + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
        + CURRICULUM_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent, curriculum does not apply (subject-scoped).
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    curriculum_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(curriculum,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        effective_teachings_per_knower(
            curriculum_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=curriculum_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + CURRICULUM_TEACHINGS_PER_KNOWER_BONUS
    )


def test_academy_boosts_teachings_and_stacks_with_prior_bonuses() -> None:
    """Active academy seat bonus stacks with scribe, scriptorium, and curriculum."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    curriculum = Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(curriculum,),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        institutions=(
            Institution.create(0, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_academy(world, agent.location_id) is True
    assert (
        effective_teachings_per_knower(
            world, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=agent
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
        + WRITING_TEACHINGS_PER_KNOWER_BONUS
        + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
        + CURRICULUM_TEACHINGS_PER_KNOWER_BONUS
        + ACADEMY_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, academy (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    academy_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_academy(academy_only, 0) is True
    assert (
        effective_teachings_per_knower(
            academy_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=academy_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + ACADEMY_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_academy(bare, bare.agents[0].location_id) is False


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
    assert snap.active_road_count == 0
    assert snap.move_energy_cost_bps == round(DEFAULT_MOVE_ENERGY_COST * 10_000)


def test_road_reduces_move_energy_for_colocated_agents() -> None:
    """Active roads discount MOVE energy at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_road(world, agent.location_id) is True
    assert effective_move_energy_cost(world, agent) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST - ROAD_MOVE_ENERGY_DISCOUNT
    )
    snap = census_effects(world)
    assert snap.active_road_count == 1
    assert snap.move_energy_cost_bps == round(
        (DEFAULT_MOVE_ENERGY_COST - ROAD_MOVE_ENERGY_DISCOUNT) * 10_000
    )
    assert snap.active_guild_count == 0
    assert snap.produce_energy_cost_bps == round(DEFAULT_PRODUCE_ENERGY_COST * 10_000)


def test_guild_reduces_produce_energy_for_colocated_agents() -> None:
    """Active guilds discount PRODUCE energy at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_guild(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - GUILD_PRODUCE_ENERGY_DISCOUNT)
    snap = census_effects(world)
    assert snap.active_guild_count == 1
    assert snap.produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - GUILD_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )


def test_abacus_reduces_produce_energy_and_stacks_with_guild() -> None:
    """Active abacus discounts PRODUCE energy society-wide and stacks with guild."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            discovered_math,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            active_abacus,
            CAMP_STAR_CHART,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = bare.agents[0]
    assert effective_produce_energy_cost(
        bare,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(
        DEFAULT_PRODUCE_ENERGY_COST - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
    )
    snap = census_effects(bare)
    assert snap.produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )

    stacked = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            discovered_math,
            CAMP_ASTRONOMY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            active_abacus,
            CAMP_STAR_CHART,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    stacked_agent = stacked.agents[0]
    assert location_has_active_guild(stacked, stacked_agent.location_id) is True
    assert effective_produce_energy_cost(
        stacked,
        stacked_agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(
        DEFAULT_PRODUCE_ENERGY_COST
        - GUILD_PRODUCE_ENERGY_DISCOUNT
        - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
    )
    stacked_snap = census_effects(stacked)
    assert stacked_snap.active_guild_count == 1
    assert stacked_snap.produce_energy_cost_bps == round(
        (
            DEFAULT_PRODUCE_ENERGY_COST
            - GUILD_PRODUCE_ENERGY_DISCOUNT
            - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        )
        * 10_000
    )


def test_archive_raises_retrieval_limit_for_colocated_agents() -> None:
    """Active archives raise the memory retrieval limit at their seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_archive(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + ARCHIVE_RETRIEVAL_LIMIT_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_archive(bare, bare.agents[0].location_id) is False
    assert effective_retrieval_limit(bare, bare.agents[0]) == DEFAULT_RETRIEVAL_LIMIT


def test_library_raises_retrieval_limit_for_residents() -> None:
    """Active library cities raise the memory retrieval limit for residents."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Library", CityKind.LIBRARY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_library(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + LIBRARY_RETRIEVAL_LIMIT_BONUS
    )
    at_capital = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Library", CityKind.LIBRARY),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_library(at_capital, 0) is False
    assert (
        effective_retrieval_limit(at_capital, at_capital.agents[0])
        == DEFAULT_RETRIEVAL_LIMIT
    )


def test_archive_and_library_retrieval_bonuses_stack() -> None:
    """Archive institution and library city bonuses stack at the same seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Library", CityKind.LIBRARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Library Archive", InstitutionKind.ARCHIVE),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_archive(world, agent.location_id) is True
    assert location_has_active_library(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT
        + ARCHIVE_RETRIEVAL_LIMIT_BONUS
        + LIBRARY_RETRIEVAL_LIMIT_BONUS
    )


def test_observatory_raises_retrieval_limit_for_colocated_agents() -> None:
    """Active observatories raise the memory retrieval limit at their seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Observatory", InfrastructureKind.OBSERVATORY
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_observatory(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + OBSERVATORY_RETRIEVAL_LIMIT_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_observatory(bare, bare.agents[0].location_id) is False
    assert effective_retrieval_limit(bare, bare.agents[0]) == DEFAULT_RETRIEVAL_LIMIT


def test_archive_library_and_observatory_retrieval_bonuses_stack() -> None:
    """Archive, library, and observatory retrieval bonuses stack at one seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Library", CityKind.LIBRARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Library Archive", InstitutionKind.ARCHIVE),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Library Observatory", InfrastructureKind.OBSERVATORY
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_archive(world, agent.location_id) is True
    assert location_has_active_library(world, agent.location_id) is True
    assert location_has_active_observatory(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT
        + ARCHIVE_RETRIEVAL_LIMIT_BONUS
        + LIBRARY_RETRIEVAL_LIMIT_BONUS
        + OBSERVATORY_RETRIEVAL_LIMIT_BONUS
    )


def test_star_chart_raises_retrieval_limit_society_wide() -> None:
    """Active star chart raises retrieval limit for every agent."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    active_star_chart = CAMP_STAR_CHART.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            discovered_math,
            discovered_astronomy,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            active_star_chart,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + ASTRONOMY_RETRIEVAL_LIMIT_BONUS
    )
    bare = _world()
    assert effective_retrieval_limit(bare, bare.agents[0]) == DEFAULT_RETRIEVAL_LIMIT


def test_star_chart_stacks_with_archive_library_and_observatory() -> None:
    """Star chart retrieval bonus stacks with location archive/library/observatory."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    active_star_chart = CAMP_STAR_CHART.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Library", CityKind.LIBRARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Library Archive", InstitutionKind.ARCHIVE),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Library Observatory", InfrastructureKind.OBSERVATORY
            ),
        ),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            discovered_math,
            discovered_astronomy,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            active_star_chart,
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_archive(world, agent.location_id) is True
    assert location_has_active_library(world, agent.location_id) is True
    assert location_has_active_observatory(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT
        + ARCHIVE_RETRIEVAL_LIMIT_BONUS
        + LIBRARY_RETRIEVAL_LIMIT_BONUS
        + OBSERVATORY_RETRIEVAL_LIMIT_BONUS
        + ASTRONOMY_RETRIEVAL_LIMIT_BONUS
    )


def test_bureaucracy_discounts_market_fee_at_seat() -> None:
    """Active bureaucracy reduces market fee by 1 at its seat (floor 0)."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_bureaucracy(world, 0) is True
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - BUREAUCRACY_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert effective_market_fee(floored, 0) == 0
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_bureaucracy(bare, 0) is False
    assert effective_market_fee(bare, 0) == 2
