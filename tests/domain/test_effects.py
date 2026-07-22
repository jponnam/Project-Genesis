"""Unit tests for society effect helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    ACADEMY_TEACHINGS_PER_KNOWER_BONUS,
    AGORA_SOCIALIZE_RESTORE_BONUS,
    ARCHIVE_RETRIEVAL_LIMIT_BONUS,
    ASSEMBLY_SOCIALIZE_RESTORE_BONUS,
    ASTRONOMY_RETRIEVAL_LIMIT_BONUS,
    BUREAUCRACY_MARKET_FEE_DISCOUNT,
    CALENDAR_RETRIEVAL_LIMIT_BONUS,
    CAMP_ABACUS,
    CAMP_ASTRONOMY,
    CAMP_DIALECTIC,
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_FORGE,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_CANAL,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_ORATION,
    CAMP_PHILOSOPHY,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    CAMP_REMEDY,
    CAMP_RHETORIC,
    CAMP_SCRIBE,
    CAMP_STAR_CHART,
    CAMP_SYLLOGISM,
    CAMP_WRITING,
    CLINIC_DRINK_RESTORE_BONUS,
    CURRICULUM_TEACHINGS_PER_KNOWER_BONUS,
    DEFAULT_DRINK_RESTORE,
    DEFAULT_GATHER_AMOUNT,
    DEFAULT_MOVE_ENERGY_COST,
    DEFAULT_POINTS_PER_TICK,
    DEFAULT_PRODUCE_ENERGY_COST,
    DEFAULT_REST_RESTORE,
    DEFAULT_RETRIEVAL_LIMIT,
    DEFAULT_SOCIALIZE_RESTORE,
    DEFAULT_TEACHINGS_PER_KNOWER,
    FIRE_HEARTH_REST_BONUS,
    FORUM_TEACHINGS_PER_KNOWER_BONUS,
    GUILD_PRODUCE_ENERGY_DISCOUNT,
    HOSPITAL_REST_RESTORE_BONUS,
    INFIRMARY_REST_RESTORE_BONUS,
    IRRIGATION_WATER_GATHER_BONUS,
    LIBRARY_RETRIEVAL_LIMIT_BONUS,
    LOGIC_RESEARCH_POINTS_BONUS,
    LYCEUM_RETRIEVAL_LIMIT_BONUS,
    MATHEMATICS_PRODUCE_ENERGY_DISCOUNT,
    MEDICINE_REST_RESTORE_BONUS,
    METALLURGY_STONE_GATHER_BONUS,
    OBSERVATORY_RETRIEVAL_LIMIT_BONUS,
    PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS,
    POTTERY_WATER_GATHER_BONUS,
    RHETORIC_SOCIALIZE_RESTORE_BONUS,
    ROAD_MOVE_ENERGY_DISCOUNT,
    SANCTUARY_REST_RESTORE_BONUS,
    SANITATION_DRINK_RESTORE_BONUS,
    SCHOOL_TEACHINGS_PER_KNOWER_BONUS,
    SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS,
    SHRINE_DRINK_RESTORE_BONUS,
    STOA_TEACHINGS_PER_KNOWER_BONUS,
    STOREHOUSE_FOOD_GATHER_BONUS,
    TEMPLE_REST_RESTORE_BONUS,
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
    assembly_socialize_bonus_for,
    census_effects,
    default_innovations,
    default_technologies,
    default_world_map,
    drink_restore_bonus,
    effective_drink_restore,
    effective_gather_amount,
    effective_market_fee,
    effective_move_energy_cost,
    effective_produce_energy_cost,
    effective_research_points_per_tick,
    effective_rest_restore,
    effective_retrieval_limit,
    effective_socialize_restore,
    effective_teachings_per_knower,
    gather_amount_bonus,
    location_has_active_academy,
    location_has_active_agora,
    location_has_active_archive,
    location_has_active_bureaucracy,
    location_has_active_clinic,
    location_has_active_forum,
    location_has_active_guild,
    location_has_active_hospital,
    location_has_active_infirmary,
    location_has_active_library,
    location_has_active_lyceum,
    location_has_active_observatory,
    location_has_active_road,
    location_has_active_sanctuary,
    location_has_active_school,
    location_has_active_scriptorium,
    location_has_active_shrine,
    location_has_active_stoa,
    location_has_active_storehouse,
    location_has_active_temple,
    location_has_active_well,
    market_fee_for,
    research_points_bonus,
    rest_restore_bonus,
    sanitation_drink_bonus_for,
    socialize_restore_bonus,
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
            CAMP_PHILOSOPHY,
            CAMP_LOGIC,
            CAMP_RHETORIC,
            CAMP_MEDICINE,
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


def test_remedy_boosts_rest_restore_and_stacks_with_rest_seats() -> None:
    """Active remedy adds a society-wide REST restore bonus that stacks."""
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    active_remedy = CAMP_REMEDY.model_copy(update={"active": True})
    remedy_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_medicine
            if tech.technology_id == CAMP_MEDICINE.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=tuple(
            active_remedy
            if innovation.innovation_id == CAMP_REMEDY.innovation_id
            else innovation
            for innovation in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert rest_restore_bonus(remedy_only) == pytest.approx(
        FIRE_HEARTH_REST_BONUS + MEDICINE_REST_RESTORE_BONUS
    )
    assert effective_rest_restore(remedy_only) == pytest.approx(
        DEFAULT_REST_RESTORE + FIRE_HEARTH_REST_BONUS + MEDICINE_REST_RESTORE_BONUS
    )

    stacked = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Sanctuary", CityKind.SANCTUARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Seat Temple", InstitutionKind.TEMPLE),
        ),
        technologies=tuple(
            discovered_medicine
            if tech.technology_id == CAMP_MEDICINE.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=tuple(
            active_remedy
            if innovation.innovation_id == CAMP_REMEDY.innovation_id
            else innovation
            for innovation in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = stacked.agents[0]
    assert rest_restore_bonus(stacked, agent=agent) == pytest.approx(
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
    )
    assert effective_rest_restore(stacked, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE
        + FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
    )


def test_temple_boosts_rest_restore_and_stacks_with_fire_hearth() -> None:
    """Active temple seat bonus stacks with society-wide fire hearth."""
    temple_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = temple_only.agents[0]
    assert location_has_active_temple(temple_only, agent.location_id) is True
    assert rest_restore_bonus(temple_only, agent=agent) == TEMPLE_REST_RESTORE_BONUS
    assert effective_rest_restore(temple_only, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + TEMPLE_REST_RESTORE_BONUS
    )
    # Without agent/location, temple (seat-scoped) does not apply.
    assert rest_restore_bonus(temple_only) == 0.0
    assert effective_rest_restore(temple_only) == pytest.approx(DEFAULT_REST_RESTORE)

    stacked = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
        ),
        technologies=(CAMP_FIRE,),
        innovations=(CAMP_FIRE_HEARTH,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    stacked_agent = stacked.agents[0]
    assert location_has_active_temple(stacked, stacked_agent.location_id) is True
    assert rest_restore_bonus(stacked, agent=stacked_agent) == pytest.approx(
        FIRE_HEARTH_REST_BONUS + TEMPLE_REST_RESTORE_BONUS
    )
    assert effective_rest_restore(stacked, agent=stacked_agent) == pytest.approx(
        DEFAULT_REST_RESTORE + FIRE_HEARTH_REST_BONUS + TEMPLE_REST_RESTORE_BONUS
    )
    # Fire hearth still applies society-wide without a seat.
    assert rest_restore_bonus(stacked) == FIRE_HEARTH_REST_BONUS
    bare = _world()
    assert location_has_active_temple(bare, bare.agents[0].location_id) is False


def test_hospital_boosts_rest_restore_for_colocated_agents() -> None:
    """Active hospital seat bonus applies only at the hospital location."""
    hospital_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = hospital_only.agents[0]
    assert location_has_active_hospital(hospital_only, agent.location_id) is True
    assert rest_restore_bonus(hospital_only, agent=agent) == (
        HOSPITAL_REST_RESTORE_BONUS
    )
    assert effective_rest_restore(hospital_only, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + HOSPITAL_REST_RESTORE_BONUS
    )
    # Without agent/location, hospital (seat-scoped) does not apply.
    assert rest_restore_bonus(hospital_only) == 0.0
    assert effective_rest_restore(hospital_only) == pytest.approx(DEFAULT_REST_RESTORE)
    bare = _world()
    assert location_has_active_hospital(bare, bare.agents[0].location_id) is False


def test_sanctuary_boosts_rest_restore_and_stacks_with_temple() -> None:
    """Active sanctuary seat bonus stacks with temple and fire hearth."""
    sanctuary_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Sanctuary", CityKind.SANCTUARY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = sanctuary_only.agents[0]
    assert location_has_active_sanctuary(sanctuary_only, agent.location_id) is True
    assert rest_restore_bonus(sanctuary_only, agent=agent) == (
        SANCTUARY_REST_RESTORE_BONUS
    )
    assert effective_rest_restore(sanctuary_only, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + SANCTUARY_REST_RESTORE_BONUS
    )
    # Without agent/location, sanctuary (seat-scoped) does not apply.
    assert rest_restore_bonus(sanctuary_only) == 0.0
    assert effective_rest_restore(sanctuary_only) == pytest.approx(DEFAULT_REST_RESTORE)

    stacked = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Sanctuary", CityKind.SANCTUARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Seat Temple", InstitutionKind.TEMPLE),
        ),
        technologies=(CAMP_FIRE,),
        innovations=(CAMP_FIRE_HEARTH,),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    stacked_agent = stacked.agents[0]
    assert location_has_active_sanctuary(stacked, stacked_agent.location_id) is True
    assert location_has_active_temple(stacked, stacked_agent.location_id) is True
    assert rest_restore_bonus(stacked, agent=stacked_agent) == pytest.approx(
        FIRE_HEARTH_REST_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
    )
    assert effective_rest_restore(stacked, agent=stacked_agent) == pytest.approx(
        DEFAULT_REST_RESTORE
        + FIRE_HEARTH_REST_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
    )
    # Fire hearth still applies society-wide without a seat.
    assert rest_restore_bonus(stacked) == FIRE_HEARTH_REST_BONUS
    bare = _world()
    assert location_has_active_sanctuary(bare, bare.agents[0].location_id) is False


def test_hospital_stacks_with_prior_rest_restore_sources() -> None:
    """Hospital rest bonus stacks with fire, remedy, temple, and sanctuary."""
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    active_remedy = CAMP_REMEDY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Sanctuary", CityKind.SANCTUARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Seat Temple", InstitutionKind.TEMPLE),
            Institution.create(1, 0, 1, "Seat Hospital", InstitutionKind.HOSPITAL),
        ),
        technologies=tuple(
            discovered_medicine
            if tech.technology_id == CAMP_MEDICINE.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=tuple(
            active_remedy
            if innovation.innovation_id == CAMP_REMEDY.innovation_id
            else innovation
            for innovation in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_temple(world, agent.location_id) is True
    assert location_has_active_sanctuary(world, agent.location_id) is True
    assert location_has_active_hospital(world, agent.location_id) is True
    rest_bonus = (
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
        + HOSPITAL_REST_RESTORE_BONUS
    )
    assert rest_restore_bonus(world, agent=agent) == pytest.approx(rest_bonus)
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + rest_bonus
    )


def test_infirmary_boosts_rest_restore_for_residents() -> None:
    """Active infirmary cities raise REST restore for residents."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Infirmary", CityKind.INFIRMARY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_infirmary(world, agent.location_id) is True
    assert rest_restore_bonus(world, agent=agent) == INFIRMARY_REST_RESTORE_BONUS
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + INFIRMARY_REST_RESTORE_BONUS
    )
    # Without agent/location, infirmary (seat-scoped) does not apply.
    assert rest_restore_bonus(world) == 0.0
    assert effective_rest_restore(world) == pytest.approx(DEFAULT_REST_RESTORE)

    at_capital = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Infirmary", CityKind.INFIRMARY),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_infirmary(at_capital, 0) is False
    assert effective_rest_restore(at_capital, agent=at_capital.agents[0]) == (
        DEFAULT_REST_RESTORE
    )
    bare = _world()
    assert location_has_active_infirmary(bare, bare.agents[0].location_id) is False


def test_infirmary_stacks_with_rest_restore_sources() -> None:
    """Infirmary rest bonus stacks with society, temple, and hospital bonuses."""
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    active_remedy = CAMP_REMEDY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:3],
        governments=(Government.create(0, "Camp", 0, (0, 1, 2)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Infirmary", CityKind.INFIRMARY),
            City.create(2, 0, 2, "Camp Sanctuary", CityKind.SANCTUARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Seat Temple", InstitutionKind.TEMPLE),
            Institution.create(1, 0, 1, "Seat Hospital", InstitutionKind.HOSPITAL),
        ),
        technologies=tuple(
            discovered_medicine
            if tech.technology_id == CAMP_MEDICINE.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=tuple(
            active_remedy
            if innovation.innovation_id == CAMP_REMEDY.innovation_id
            else innovation
            for innovation in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_infirmary(world, agent.location_id) is True
    assert location_has_active_temple(world, agent.location_id) is True
    assert location_has_active_hospital(world, agent.location_id) is True
    assert location_has_active_sanctuary(world, agent.location_id) is False
    rest_bonus = (
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + HOSPITAL_REST_RESTORE_BONUS
        + INFIRMARY_REST_RESTORE_BONUS
    )
    assert rest_restore_bonus(world, agent=agent) == pytest.approx(rest_bonus)
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + rest_bonus
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            active_pottery,
            active_irrigation,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            active_forge,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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


def test_stoa_boosts_teachings_and_stacks_with_scriptorium() -> None:
    """Active stoa adds a seat bonus that stacks with scriptorium."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
            Infrastructure.create(1, 0, 0, 0, "Camp Stoa", InfrastructureKind.STOA),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_scriptorium(world, agent.location_id) is True
    assert location_has_active_stoa(world, agent.location_id) is True
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER
    )
    assert (
        effective_teachings_per_knower(
            world, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=agent
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
        + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
        + STOA_TEACHINGS_PER_KNOWER_BONUS
    )
    stoa_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Stoa", InfrastructureKind.STOA),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert (
        effective_teachings_per_knower(
            stoa_only, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=stoa_only.agents[0]
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + STOA_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_stoa(bare, bare.agents[0].location_id) is False


def test_stoa_stacks_with_all_teaching_bonuses() -> None:
    """Stoa teaching bonus stacks with every prior teaching capacity source."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    active_dialectic = CAMP_DIALECTIC.model_copy(update={"active": True})
    curriculum = Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(curriculum,),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            discovered_math,
            discovered_astronomy,
            discovered_philosophy,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            active_dialectic,
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Forum Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
            Infrastructure.create(1, 0, 1, 1, "Forum Stoa", InfrastructureKind.STOA),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Forum Academy", InstitutionKind.ACADEMY),
            Institution.create(1, 0, 1, "Forum School", InstitutionKind.SCHOOL),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_scriptorium(world, agent.location_id) is True
    assert location_has_active_stoa(world, agent.location_id) is True
    assert location_has_active_academy(world, agent.location_id) is True
    assert location_has_active_forum(world, agent.location_id) is True
    assert location_has_active_school(world, agent.location_id) is True
    assert (
        effective_teachings_per_knower(
            world, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=agent
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
        + WRITING_TEACHINGS_PER_KNOWER_BONUS
        + PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS
        + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
        + STOA_TEACHINGS_PER_KNOWER_BONUS
        + ACADEMY_TEACHINGS_PER_KNOWER_BONUS
        + FORUM_TEACHINGS_PER_KNOWER_BONUS
        + SCHOOL_TEACHINGS_PER_KNOWER_BONUS
        + CURRICULUM_TEACHINGS_PER_KNOWER_BONUS
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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


def test_school_boosts_teachings_and_stacks_with_academy() -> None:
    """Active school seat bonus stacks with academy, scribe, scriptorium, curriculum."""
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        institutions=(
            Institution.create(0, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(1, 0, 0, "Camp School", InstitutionKind.SCHOOL),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_school(world, agent.location_id) is True
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
        + SCHOOL_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, school (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    school_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp School", InstitutionKind.SCHOOL),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_school(school_only, 0) is True
    assert (
        effective_teachings_per_knower(
            school_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=school_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + SCHOOL_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_school(bare, bare.agents[0].location_id) is False


def test_forum_boosts_teachings_and_stacks_with_academy_scriptorium() -> None:
    """Active forum seat bonus stacks with academy, scriptorium, curriculum, scribe."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    curriculum = Law.create(0, 0, "Camp Schools", LawKind.CURRICULUM)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(curriculum,),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Forum Scriptorium", InfrastructureKind.SCRIPTORIUM
            ),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Forum Academy", InstitutionKind.ACADEMY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_forum(world, agent.location_id) is True
    assert location_has_active_academy(world, agent.location_id) is True
    assert location_has_active_scriptorium(world, agent.location_id) is True
    assert (
        effective_teachings_per_knower(
            world, base=DEFAULT_TEACHINGS_PER_KNOWER, agent=agent
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
        + WRITING_TEACHINGS_PER_KNOWER_BONUS
        + SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
        + CURRICULUM_TEACHINGS_PER_KNOWER_BONUS
        + ACADEMY_TEACHINGS_PER_KNOWER_BONUS
        + FORUM_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, seat-scoped bonuses and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    forum_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    assert location_has_active_forum(forum_only, 1) is True
    assert (
        effective_teachings_per_knower(
            forum_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=forum_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + FORUM_TEACHINGS_PER_KNOWER_BONUS
    )
    at_capital = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Forum", CityKind.FORUM),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_forum(at_capital, 0) is False
    assert (
        effective_teachings_per_knower(
            at_capital,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=at_capital.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER
    )


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


def test_shrine_boosts_drink_restore_for_colocated_agents() -> None:
    """Active shrines add a DRINK restore bonus at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Shrine", InfrastructureKind.SHRINE),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_shrine(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == SHRINE_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + SHRINE_DRINK_RESTORE_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_shrine(bare, bare.agents[0].location_id) is False
    assert drink_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_drink_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_DRINK_RESTORE
    )


def test_clinic_boosts_drink_restore_for_colocated_agents() -> None:
    """Active clinics add a DRINK restore bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_clinic(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == CLINIC_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + CLINIC_DRINK_RESTORE_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_clinic(bare, bare.agents[0].location_id) is False
    assert drink_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_drink_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_DRINK_RESTORE
    )


def test_well_shrine_and_clinic_drink_restore_bonuses_stack() -> None:
    """WELL, SHRINE, and CLINIC drink restore bonuses stack at the same seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Well", InfrastructureKind.WELL),
            Infrastructure.create(1, 0, 0, 0, "Camp Shrine", InfrastructureKind.SHRINE),
            Infrastructure.create(2, 0, 0, 0, "Camp Clinic", InfrastructureKind.CLINIC),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_well(world, agent.location_id) is True
    assert location_has_active_shrine(world, agent.location_id) is True
    assert location_has_active_clinic(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == pytest.approx(
        WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
    )
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE
        + WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
    )


def test_sanitation_boosts_drink_restore_for_subjects() -> None:
    """Active SANITATION raises DRINK restore for living subjects only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert sanitation_drink_bonus_for(world, agent) == SANITATION_DRINK_RESTORE_BONUS
    assert drink_restore_bonus(world, agent) == SANITATION_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + SANITATION_DRINK_RESTORE_BONUS
    )
    bare = _world()
    assert sanitation_drink_bonus_for(bare, bare.agents[0]) == 0.0
    assert effective_drink_restore(bare, bare.agents[0]) == DEFAULT_DRINK_RESTORE


def test_sanitation_stacks_with_well_shrine_and_clinic_drink_restore() -> None:
    """Sanitation subject bonus stacks with colocated well, shrine, and clinic."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Well", InfrastructureKind.WELL),
            Infrastructure.create(1, 0, 0, 0, "Camp Shrine", InfrastructureKind.SHRINE),
            Infrastructure.create(2, 0, 0, 0, "Camp Clinic", InfrastructureKind.CLINIC),
        ),
        laws=(Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert drink_restore_bonus(world, agent) == pytest.approx(
        WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
        + SANITATION_DRINK_RESTORE_BONUS
    )
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE
        + WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
        + SANITATION_DRINK_RESTORE_BONUS
    )


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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            active_abacus,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            active_abacus,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
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


def test_lyceum_raises_retrieval_limit_for_colocated_agents() -> None:
    """Active lyceums raise the memory retrieval limit at their seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_lyceum(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + LYCEUM_RETRIEVAL_LIMIT_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_lyceum(bare, bare.agents[0].location_id) is False
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            active_star_chart,
            CAMP_DIALECTIC,
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
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            active_star_chart,
            CAMP_DIALECTIC,
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


def test_calendar_raises_retrieval_limit_for_subjects() -> None:
    """Active CALENDAR raises retrieval limit for living subjects only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Calendar", LawKind.CALENDAR, flat_amount=5),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + CALENDAR_RETRIEVAL_LIMIT_BONUS
    )
    bare = _world()
    assert effective_retrieval_limit(bare, bare.agents[0]) == DEFAULT_RETRIEVAL_LIMIT


def test_calendar_stacks_with_retrieval_seats_and_star_chart() -> None:
    """Calendar retrieval bonus stacks with archive/library/observatory/lyceum."""
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
            Institution.create(1, 0, 1, "Library Lyceum", InstitutionKind.LYCEUM),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Library Observatory", InfrastructureKind.OBSERVATORY
            ),
        ),
        laws=(Law.create(0, 0, "Camp Calendar", LawKind.CALENDAR),),
        technologies=(
            CAMP_FIRE,
            discovered_pottery,
            discovered_irrigation,
            discovered_metallurgy,
            discovered_writing,
            discovered_math,
            discovered_astronomy,
            CAMP_PHILOSOPHY,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            active_star_chart,
            CAMP_DIALECTIC,
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_archive(world, agent.location_id) is True
    assert location_has_active_library(world, agent.location_id) is True
    assert location_has_active_observatory(world, agent.location_id) is True
    assert location_has_active_lyceum(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT
        + ARCHIVE_RETRIEVAL_LIMIT_BONUS
        + LIBRARY_RETRIEVAL_LIMIT_BONUS
        + OBSERVATORY_RETRIEVAL_LIMIT_BONUS
        + LYCEUM_RETRIEVAL_LIMIT_BONUS
        + ASTRONOMY_RETRIEVAL_LIMIT_BONUS
        + CALENDAR_RETRIEVAL_LIMIT_BONUS
    )


def test_dialectic_boosts_teachings_per_knower() -> None:
    """Active dialectic adds a society-wide teachings-per-knower bonus."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    active_dialectic = CAMP_DIALECTIC.model_copy(update={"active": True})
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
            discovered_philosophy,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            active_dialectic,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert teachings_per_knower_bonus(world) == PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert teachings_per_knower_bonus(bare) == 0
    assert (
        effective_teachings_per_knower(bare, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER
    )


def test_dialectic_stacks_with_scribe() -> None:
    """Dialectic teachings bonus stacks with scribe society-wide."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    active_scribe = CAMP_SCRIBE.model_copy(update={"active": True})
    active_dialectic = CAMP_DIALECTIC.model_copy(update={"active": True})
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
            discovered_philosophy,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            active_scribe,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            active_dialectic,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert teachings_per_knower_bonus(world) == (
        WRITING_TEACHINGS_PER_KNOWER_BONUS + PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS
    )
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER
        + WRITING_TEACHINGS_PER_KNOWER_BONUS
        + PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS
    )


def test_syllogism_boosts_research_points_per_tick() -> None:
    """Active syllogism adds a society-wide research point bonus."""
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    active_syllogism = CAMP_SYLLOGISM.model_copy(update={"active": True})
    world = World(
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
            CAMP_PHILOSOPHY,
            discovered_logic,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
            active_syllogism,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert research_points_bonus(world) == LOGIC_RESEARCH_POINTS_BONUS
    assert (
        effective_research_points_per_tick(world, base=DEFAULT_POINTS_PER_TICK)
        == DEFAULT_POINTS_PER_TICK + LOGIC_RESEARCH_POINTS_BONUS
    )
    bare = _world()
    assert research_points_bonus(bare) == 0
    assert effective_research_points_per_tick(bare) == DEFAULT_POINTS_PER_TICK


def test_oration_boosts_socialize_restore() -> None:
    """Active oration adds a society-wide SOCIALIZE restore bonus."""
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    active_oration = CAMP_ORATION.model_copy(update={"active": True})
    world = World(
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
            CAMP_PHILOSOPHY,
            CAMP_LOGIC,
            discovered_rhetoric,
        ),
        innovations=(
            CAMP_FIRE_HEARTH,
            CAMP_POTTERY_CRAFT,
            CAMP_IRRIGATION_CANAL,
            CAMP_FORGE,
            CAMP_SCRIBE,
            CAMP_ABACUS,
            CAMP_STAR_CHART,
            CAMP_DIALECTIC,
            CAMP_SYLLOGISM,
            active_oration,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert socialize_restore_bonus(world) == RHETORIC_SOCIALIZE_RESTORE_BONUS
    assert effective_socialize_restore(world) == pytest.approx(
        DEFAULT_SOCIALIZE_RESTORE + RHETORIC_SOCIALIZE_RESTORE_BONUS
    )
    bare = _world()
    assert socialize_restore_bonus(bare) == 0.0
    assert effective_socialize_restore(bare) == DEFAULT_SOCIALIZE_RESTORE


def test_assembly_boosts_socialize_restore_for_subjects() -> None:
    """Active ASSEMBLY raises SOCIALIZE restore for living subjects only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Assembly", LawKind.ASSEMBLY, flat_amount=5),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert assembly_socialize_bonus_for(world, agent) == (
        ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    assert socialize_restore_bonus(world) == 0.0
    assert socialize_restore_bonus(world, agent=agent) == (
        ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    assert effective_socialize_restore(world, agent=agent) == pytest.approx(
        DEFAULT_SOCIALIZE_RESTORE + ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    bare = _world()
    assert assembly_socialize_bonus_for(bare, bare.agents[0]) == 0.0
    assert effective_socialize_restore(bare, agent=bare.agents[0]) == (
        DEFAULT_SOCIALIZE_RESTORE
    )


def test_assembly_stacks_with_oration_socialize_restore() -> None:
    """Assembly subject bonus stacks with society-wide oration."""
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    active_oration = CAMP_ORATION.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Assembly", LawKind.ASSEMBLY),),
        technologies=tuple(
            discovered_rhetoric
            if tech.technology_id == CAMP_RHETORIC.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=tuple(
            active_oration
            if innovation.innovation_id == CAMP_ORATION.innovation_id
            else innovation
            for innovation in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert socialize_restore_bonus(world, agent=agent) == pytest.approx(
        RHETORIC_SOCIALIZE_RESTORE_BONUS + ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    assert effective_socialize_restore(world, agent=agent) == pytest.approx(
        DEFAULT_SOCIALIZE_RESTORE
        + RHETORIC_SOCIALIZE_RESTORE_BONUS
        + ASSEMBLY_SOCIALIZE_RESTORE_BONUS
    )
    # Without an agent, the subject-scoped assembly law does not apply.
    assert socialize_restore_bonus(world) == RHETORIC_SOCIALIZE_RESTORE_BONUS


def test_agora_boosts_socialize_restore_for_residents() -> None:
    """Active agora cities raise SOCIALIZE restore for residents."""
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
    agent = world.agents[0]
    assert location_has_active_agora(world, agent.location_id) is True
    assert socialize_restore_bonus(world, agent=agent) == (
        AGORA_SOCIALIZE_RESTORE_BONUS
    )
    assert effective_socialize_restore(world, agent=agent) == pytest.approx(
        DEFAULT_SOCIALIZE_RESTORE + AGORA_SOCIALIZE_RESTORE_BONUS
    )
    # Without agent, agora (seat-scoped) does not apply.
    assert socialize_restore_bonus(world) == 0.0
    assert effective_socialize_restore(world) == pytest.approx(
        DEFAULT_SOCIALIZE_RESTORE
    )

    at_capital = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Agora", CityKind.AGORA),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_agora(at_capital, 0) is False
    assert effective_socialize_restore(at_capital, agent=at_capital.agents[0]) == (
        DEFAULT_SOCIALIZE_RESTORE
    )
    bare = _world()
    assert location_has_active_agora(bare, bare.agents[0].location_id) is False


def test_agora_stacks_with_oration_and_assembly_socialize_restore() -> None:
    """Agora seat bonus stacks with society-wide oration and assembly law."""
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    active_oration = CAMP_ORATION.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Assembly", LawKind.ASSEMBLY),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Agora", CityKind.AGORA),
        ),
        technologies=tuple(
            discovered_rhetoric
            if tech.technology_id == CAMP_RHETORIC.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=tuple(
            active_oration
            if innovation.innovation_id == CAMP_ORATION.innovation_id
            else innovation
            for innovation in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_agora(world, agent.location_id) is True
    assert socialize_restore_bonus(world, agent=agent) == pytest.approx(
        RHETORIC_SOCIALIZE_RESTORE_BONUS
        + ASSEMBLY_SOCIALIZE_RESTORE_BONUS
        + AGORA_SOCIALIZE_RESTORE_BONUS
    )
    assert effective_socialize_restore(world, agent=agent) == pytest.approx(
        DEFAULT_SOCIALIZE_RESTORE
        + RHETORIC_SOCIALIZE_RESTORE_BONUS
        + ASSEMBLY_SOCIALIZE_RESTORE_BONUS
        + AGORA_SOCIALIZE_RESTORE_BONUS
    )
    # Without an agent, only the society-wide oration bonus applies.
    assert socialize_restore_bonus(world) == RHETORIC_SOCIALIZE_RESTORE_BONUS


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
