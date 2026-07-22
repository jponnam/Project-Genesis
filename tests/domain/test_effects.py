"""Unit tests for society effect helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    ACADEMY_TEACHINGS_PER_KNOWER_BONUS,
    AGORA_SOCIALIZE_RESTORE_BONUS,
    AGRICULTURE_FOOD_GATHER_BONUS,
    AGRONOMIST_TEACHINGS_PER_KNOWER_BONUS,
    ANATOMY_RESEARCH_POINTS_BONUS,
    APOTHECARY_DRINK_RESTORE_BONUS,
    ARCHITECT_TEACHINGS_PER_KNOWER_BONUS,
    ARCHITECTURE_RESEARCH_POINTS_BONUS,
    ARCHIVE_RETRIEVAL_LIMIT_BONUS,
    ASSEMBLY_SOCIALIZE_RESTORE_BONUS,
    ASTRONOMY_RETRIEVAL_LIMIT_BONUS,
    BATHHOUSE_REST_RESTORE_BONUS,
    BEACON_RETRIEVAL_LIMIT_BONUS,
    BRIDGE_MOVE_ENERGY_DISCOUNT,
    BUILDING_CODES_MOVE_ENERGY_DISCOUNT,
    BUREAUCRACY_MARKET_FEE_DISCOUNT,
    CALENDAR_RETRIEVAL_LIMIT_BONUS,
    CAMP_ABACUS,
    CAMP_AGRICULTURE,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASEPSIS,
    CAMP_ASTRONOMY,
    CAMP_BLUEPRINT,
    CAMP_CARTOGRAPHY,
    CAMP_COMPASS,
    CAMP_COPPICE,
    CAMP_CROP_ROTATION,
    CAMP_DIALECTIC,
    CAMP_DISSECTION,
    CAMP_DYEING,
    CAMP_ENGINEERING,
    CAMP_FALLOW,
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_FORESTRY,
    CAMP_FORGE,
    CAMP_HYGIENE,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_CANAL,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_LOOM,
    CAMP_MAP,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_MINING,
    CAMP_MORDANT,
    CAMP_NAVIGATION,
    CAMP_ORATION,
    CAMP_PHILOSOPHY,
    CAMP_PICKAXE,
    CAMP_PLOW,
    CAMP_PLUMB_LINE,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    CAMP_PULLEY,
    CAMP_REMEDY,
    CAMP_RHETORIC,
    CAMP_SAIL,
    CAMP_SCRIBE,
    CAMP_SEAFARING,
    CAMP_STAR_CHART,
    CAMP_SURVEYING,
    CAMP_SYLLOGISM,
    CAMP_TANNERY,
    CAMP_TANNING,
    CAMP_TEXTILES,
    CAMP_WRITING,
    CARAVAN_MOVE_ENERGY_DISCOUNT,
    CARTOGRAPHER_TEACHINGS_PER_KNOWER_BONUS,
    CARTOGRAPHY_RETRIEVAL_LIMIT_BONUS,
    CLINIC_DRINK_RESTORE_BONUS,
    COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS,
    CONSERVATION_WOOD_GATHER_BONUS,
    CROP_ROTATION_EAT_RESTORE_BONUS,
    CURRICULUM_TEACHINGS_PER_KNOWER_BONUS,
    CUSTOMS_PRODUCE_ENERGY_DISCOUNT,
    DEFAULT_DRINK_RESTORE,
    DEFAULT_EAT_RESTORE,
    DEFAULT_GATHER_AMOUNT,
    DEFAULT_MOVE_ENERGY_COST,
    DEFAULT_POINTS_PER_TICK,
    DEFAULT_PRODUCE_ENERGY_COST,
    DEFAULT_REST_RESTORE,
    DEFAULT_RETRIEVAL_LIMIT,
    DEFAULT_SOCIALIZE_RESTORE,
    DEFAULT_TEACHINGS_PER_KNOWER,
    DITCH_WATER_GATHER_BONUS,
    DYEING_MARKET_FEE_DISCOUNT,
    DYER_MARKET_FEE_DISCOUNT,
    EMPORIUM_MARKET_FEE_DISCOUNT,
    ENGINEERING_PRODUCE_ENERGY_DISCOUNT,
    ENTREPOT_FOOD_GATHER_BONUS,
    FARMSTEAD_FOOD_GATHER_BONUS,
    FIRE_HEARTH_REST_BONUS,
    FORESTRY_WOOD_GATHER_BONUS,
    FORUM_TEACHINGS_PER_KNOWER_BONUS,
    FOUNDRY_PRODUCE_ENERGY_DISCOUNT,
    FULLING_MILL_PRODUCE_ENERGY_DISCOUNT,
    GRANARY_FOOD_GATHER_BONUS,
    GUILD_PRODUCE_ENERGY_DISCOUNT,
    HARBOR_MARKET_FEE_DISCOUNT,
    HOSPITAL_REST_RESTORE_BONUS,
    HUSBANDMAN_FOOD_GATHER_BONUS,
    HYGIENE_DRINK_RESTORE_BONUS,
    INFIRMARY_REST_RESTORE_BONUS,
    IRRIGATION_WATER_GATHER_BONUS,
    LABOR_PRODUCE_ENERGY_DISCOUNT,
    LAND_TENURE_EAT_RESTORE_BONUS,
    LAZARETTO_DRINK_RESTORE_BONUS,
    LIBRARY_RETRIEVAL_LIMIT_BONUS,
    LOGIC_RESEARCH_POINTS_BONUS,
    LYCEUM_RETRIEVAL_LIMIT_BONUS,
    MASON_STONE_GATHER_BONUS,
    MATHEMATICS_PRODUCE_ENERGY_DISCOUNT,
    MEDICINE_REST_RESTORE_BONUS,
    MERCHANT_MARKET_FEE_DISCOUNT,
    METALLURGY_STONE_GATHER_BONUS,
    MILL_TOWN_PRODUCE_ENERGY_DISCOUNT,
    MINER_STONE_GATHER_BONUS,
    MINERAL_RIGHTS_STONE_GATHER_BONUS,
    MINESHAFT_STONE_GATHER_BONUS,
    MINING_STONE_GATHER_BONUS,
    NAVIGATION_MOVE_ENERGY_DISCOUNT,
    OBSERVATORY_RETRIEVAL_LIMIT_BONUS,
    PASSAGE_MOVE_ENERGY_DISCOUNT,
    PASTORAL_WOOD_GATHER_BONUS,
    PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS,
    POTTERY_WATER_GATHER_BONUS,
    QUARANTINE_REST_RESTORE_BONUS,
    QUARRY_STONE_GATHER_BONUS,
    RHETORIC_SOCIALIZE_RESTORE_BONUS,
    ROAD_MOVE_ENERGY_DISCOUNT,
    SANCTUARY_REST_RESTORE_BONUS,
    SANITATION_DRINK_RESTORE_BONUS,
    SCAFFOLD_WOOD_GATHER_BONUS,
    SCHOOL_TEACHINGS_PER_KNOWER_BONUS,
    SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS,
    SEAFARING_WATER_GATHER_BONUS,
    SHRINE_DRINK_RESTORE_BONUS,
    STOA_TEACHINGS_PER_KNOWER_BONUS,
    STOREHOUSE_FOOD_GATHER_BONUS,
    SUMPTUARY_MARKET_FEE_DISCOUNT,
    SURVEYING_RETRIEVAL_LIMIT_BONUS,
    TAILOR_TEACHINGS_PER_KNOWER_BONUS,
    TANNING_PRODUCE_ENERGY_DISCOUNT,
    TEMPLE_REST_RESTORE_BONUS,
    TERRACE_FOOD_GATHER_BONUS,
    TEXTILES_PRODUCE_ENERGY_DISCOUNT,
    WAREHOUSE_MARKET_FEE_DISCOUNT,
    WAYSTATION_FOOD_GATHER_BONUS,
    WEAVER_PRODUCE_ENERGY_DISCOUNT,
    WELL_DRINK_RESTORE_BONUS,
    WORKSHOP_PRODUCE_ENERGY_DISCOUNT,
    WRITING_TEACHINGS_PER_KNOWER_BONUS,
    ZONING_EAT_RESTORE_BONUS,
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
    building_codes_move_discount_for,
    census_effects,
    conservation_wood_bonus_for,
    customs_produce_discount_for,
    default_innovations,
    default_technologies,
    default_world_map,
    drink_restore_bonus,
    eat_restore_bonus,
    effective_drink_restore,
    effective_eat_restore,
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
    labor_produce_discount_for,
    land_tenure_eat_bonus_for,
    location_has_active_academy,
    location_has_active_agora,
    location_has_active_agronomist,
    location_has_active_apothecary,
    location_has_active_architect,
    location_has_active_archive,
    location_has_active_bathhouse,
    location_has_active_beacon,
    location_has_active_bridge,
    location_has_active_bureaucracy,
    location_has_active_caravan,
    location_has_active_cartographer,
    location_has_active_clinic,
    location_has_active_collegium,
    location_has_active_ditch,
    location_has_active_dyer,
    location_has_active_emporium,
    location_has_active_entrepot,
    location_has_active_farmstead,
    location_has_active_forum,
    location_has_active_foundry,
    location_has_active_fulling_mill,
    location_has_active_granary,
    location_has_active_guild,
    location_has_active_harbor,
    location_has_active_hospital,
    location_has_active_husbandman,
    location_has_active_infirmary,
    location_has_active_lazaretto,
    location_has_active_library,
    location_has_active_lyceum,
    location_has_active_mason,
    location_has_active_merchant,
    location_has_active_mill_town,
    location_has_active_miner,
    location_has_active_mineshaft,
    location_has_active_observatory,
    location_has_active_pastoral,
    location_has_active_quarry,
    location_has_active_road,
    location_has_active_sanctuary,
    location_has_active_scaffold,
    location_has_active_school,
    location_has_active_scriptorium,
    location_has_active_shrine,
    location_has_active_stoa,
    location_has_active_storehouse,
    location_has_active_tailor,
    location_has_active_temple,
    location_has_active_terrace,
    location_has_active_warehouse,
    location_has_active_waystation,
    location_has_active_weaver,
    location_has_active_well,
    location_has_active_workshop,
    market_fee_for,
    mineral_rights_stone_bonus_for,
    move_energy_discount,
    passage_move_discount_for,
    produce_energy_discount,
    quarantine_rest_bonus_for,
    research_points_bonus,
    rest_restore_bonus,
    sanitation_drink_bonus_for,
    socialize_restore_bonus,
    teachings_per_knower_bonus,
    zoning_eat_bonus_for,
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
    """Infirmary rest bonus stacks with society, temple, hospital, and bathhouse."""
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
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Seat Bathhouse", InfrastructureKind.BATHHOUSE
            ),
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
    assert location_has_active_bathhouse(world, agent.location_id) is True
    rest_bonus = (
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + HOSPITAL_REST_RESTORE_BONUS
        + INFIRMARY_REST_RESTORE_BONUS
        + BATHHOUSE_REST_RESTORE_BONUS
    )
    assert rest_restore_bonus(world, agent=agent) == pytest.approx(rest_bonus)
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + rest_bonus
    )


def test_bathhouse_boosts_rest_restore_for_colocated_agents() -> None:
    """Active bathhouses add a REST restore bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_bathhouse(world, agent.location_id) is True
    assert rest_restore_bonus(world, agent=agent) == BATHHOUSE_REST_RESTORE_BONUS
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + BATHHOUSE_REST_RESTORE_BONUS
    )
    # Without agent/location, bathhouse (seat-scoped) does not apply.
    assert rest_restore_bonus(world) == 0.0
    assert effective_rest_restore(world) == pytest.approx(DEFAULT_REST_RESTORE)
    bare = _world()
    assert location_has_active_bathhouse(bare, bare.agents[0].location_id) is False


def test_bathhouse_stacks_with_sanctuary_rest_restore_sources() -> None:
    """Bathhouse rest bonus stacks with society, temple, sanctuary, and hospital."""
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
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Seat Bathhouse", InfrastructureKind.BATHHOUSE
            ),
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
    assert location_has_active_bathhouse(world, agent.location_id) is True
    rest_bonus = (
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
        + HOSPITAL_REST_RESTORE_BONUS
        + BATHHOUSE_REST_RESTORE_BONUS
    )
    assert rest_restore_bonus(world, agent=agent) == pytest.approx(rest_bonus)
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + rest_bonus
    )


def test_quarantine_boosts_rest_restore_for_living_subjects() -> None:
    """Active QUARANTINE raises REST restore for living subjects only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Quarantine", LawKind.QUARANTINE),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert quarantine_rest_bonus_for(world, agent) == QUARANTINE_REST_RESTORE_BONUS
    assert rest_restore_bonus(world, agent=agent) == QUARANTINE_REST_RESTORE_BONUS
    assert effective_rest_restore(world, agent=agent) == pytest.approx(
        DEFAULT_REST_RESTORE + QUARANTINE_REST_RESTORE_BONUS
    )
    # Without an agent, subject-scoped QUARANTINE cannot apply.
    assert rest_restore_bonus(world) == 0.0
    assert effective_rest_restore(world) == pytest.approx(DEFAULT_REST_RESTORE)

    bare = _world()
    assert quarantine_rest_bonus_for(bare, bare.agents[0]) == 0.0


def test_quarantine_stacks_with_rest_restore_sources() -> None:
    """Quarantine rest bonus stacks with society, institution, city, and infra."""
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    active_remedy = CAMP_REMEDY.model_copy(update={"active": True})
    sanctuary_agent = Agent.create(agent_id=0, name="A", location_id=1)
    infirmary_agent = Agent.create(agent_id=1, name="B", location_id=3)
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=default_world_map()[:4],
        governments=(
            Government.create(0, "Camp", 0, (0, 1)),
            Government.create(1, "Outpost", 2, (2, 3)),
        ),
        laws=(
            Law.create(0, 0, "Camp Quarantine", LawKind.QUARANTINE),
            Law.create(1, 1, "Outpost Quarantine", LawKind.QUARANTINE),
        ),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Sanctuary", CityKind.SANCTUARY),
            City.create(2, 1, 2, "Outpost City", CityKind.SETTLEMENT, is_capital=True),
            City.create(3, 1, 3, "Outpost Infirmary", CityKind.INFIRMARY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Sanctuary Temple", InstitutionKind.TEMPLE),
            Institution.create(1, 0, 1, "Sanctuary Hospital", InstitutionKind.HOSPITAL),
            Institution.create(2, 1, 3, "Infirmary Temple", InstitutionKind.TEMPLE),
            Institution.create(3, 1, 3, "Infirmary Hospital", InstitutionKind.HOSPITAL),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Sanctuary Bathhouse", InfrastructureKind.BATHHOUSE
            ),
            Infrastructure.create(
                1, 1, 3, 3, "Infirmary Bathhouse", InfrastructureKind.BATHHOUSE
            ),
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
        agents=(sanctuary_agent, infirmary_agent),
    )
    sanctuary_bonus = (
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + QUARANTINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + SANCTUARY_REST_RESTORE_BONUS
        + HOSPITAL_REST_RESTORE_BONUS
        + BATHHOUSE_REST_RESTORE_BONUS
    )
    infirmary_bonus = (
        FIRE_HEARTH_REST_BONUS
        + MEDICINE_REST_RESTORE_BONUS
        + QUARANTINE_REST_RESTORE_BONUS
        + TEMPLE_REST_RESTORE_BONUS
        + HOSPITAL_REST_RESTORE_BONUS
        + INFIRMARY_REST_RESTORE_BONUS
        + BATHHOUSE_REST_RESTORE_BONUS
    )
    assert rest_restore_bonus(world, agent=world.agents[0]) == pytest.approx(
        sanctuary_bonus
    )
    assert effective_rest_restore(world, agent=world.agents[0]) == pytest.approx(
        DEFAULT_REST_RESTORE + sanctuary_bonus
    )
    assert rest_restore_bonus(world, agent=world.agents[1]) == pytest.approx(
        infirmary_bonus
    )
    assert effective_rest_restore(world, agent=world.agents[1]) == pytest.approx(
        DEFAULT_REST_RESTORE + infirmary_bonus
    )


def test_zoning_boosts_eat_restore_for_living_subjects() -> None:
    """Active ZONING raises EAT restore for living subjects only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Zoning", LawKind.ZONING),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert zoning_eat_bonus_for(world, agent) == ZONING_EAT_RESTORE_BONUS
    assert eat_restore_bonus(world, agent) == ZONING_EAT_RESTORE_BONUS
    assert effective_eat_restore(world, agent) == pytest.approx(
        DEFAULT_EAT_RESTORE + ZONING_EAT_RESTORE_BONUS
    )
    bare = _world()
    assert zoning_eat_bonus_for(bare, bare.agents[0]) == 0.0
    assert eat_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_eat_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_EAT_RESTORE
    )


def test_land_tenure_boosts_eat_restore_for_living_subjects() -> None:
    """Active LAND_TENURE raises EAT restore for living subjects only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Camp Land Tenure", LawKind.LAND_TENURE),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert land_tenure_eat_bonus_for(world, agent) == LAND_TENURE_EAT_RESTORE_BONUS
    assert eat_restore_bonus(world, agent) == LAND_TENURE_EAT_RESTORE_BONUS
    assert effective_eat_restore(world, agent) == pytest.approx(
        DEFAULT_EAT_RESTORE + LAND_TENURE_EAT_RESTORE_BONUS
    )
    bare = _world()
    assert land_tenure_eat_bonus_for(bare, bare.agents[0]) == 0.0
    assert eat_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_eat_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_EAT_RESTORE
    )


def test_zoning_and_land_tenure_stack_eat_restore() -> None:
    """Active ZONING and LAND_TENURE stack for EAT restore."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(
            Law.create(0, 0, "Camp Zoning", LawKind.ZONING),
            Law.create(1, 0, "Camp Land Tenure", LawKind.LAND_TENURE),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = ZONING_EAT_RESTORE_BONUS + LAND_TENURE_EAT_RESTORE_BONUS
    assert zoning_eat_bonus_for(world, agent) == ZONING_EAT_RESTORE_BONUS
    assert land_tenure_eat_bonus_for(world, agent) == LAND_TENURE_EAT_RESTORE_BONUS
    assert eat_restore_bonus(world, agent) == pytest.approx(expected)
    assert effective_eat_restore(world, agent) == pytest.approx(
        DEFAULT_EAT_RESTORE + expected
    )


def test_fallow_boosts_eat_restore_society_wide() -> None:
    """Active fallow adds a deterministic society-wide EAT restore bonus."""
    discovered_crop_rotation = CAMP_CROP_ROTATION.model_copy(
        update={"discovered": True}
    )
    active_fallow = CAMP_FALLOW.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_crop_rotation
            if item.technology_id == CAMP_CROP_ROTATION.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_fallow if item.innovation_id == CAMP_FALLOW.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert eat_restore_bonus(world, agent) == CROP_ROTATION_EAT_RESTORE_BONUS
    assert effective_eat_restore(world, agent) == pytest.approx(
        DEFAULT_EAT_RESTORE + CROP_ROTATION_EAT_RESTORE_BONUS
    )
    bare = _world()
    assert eat_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_eat_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_EAT_RESTORE
    )


def test_fallow_stacks_with_zoning_and_land_tenure_eat_restore() -> None:
    """Active fallow stacks with zoning and land tenure for EAT restore."""
    discovered_crop_rotation = CAMP_CROP_ROTATION.model_copy(
        update={"discovered": True}
    )
    active_fallow = CAMP_FALLOW.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(
            Law.create(0, 0, "Camp Zoning", LawKind.ZONING),
            Law.create(1, 0, "Camp Land Tenure", LawKind.LAND_TENURE),
        ),
        technologies=tuple(
            discovered_crop_rotation
            if item.technology_id == CAMP_CROP_ROTATION.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_fallow if item.innovation_id == CAMP_FALLOW.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = (
        CROP_ROTATION_EAT_RESTORE_BONUS
        + ZONING_EAT_RESTORE_BONUS
        + LAND_TENURE_EAT_RESTORE_BONUS
    )
    assert eat_restore_bonus(world, agent) == pytest.approx(expected)
    assert effective_eat_restore(world, agent) == pytest.approx(
        DEFAULT_EAT_RESTORE + expected
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


def test_sail_raises_water_gather_society_wide() -> None:
    """Active sail raises water gather amount for every agent."""
    discovered_seafaring = CAMP_SEAFARING.model_copy(update={"discovered": True})
    active_sail = CAMP_SAIL.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_seafaring
            if item.technology_id == CAMP_SEAFARING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_sail if item.innovation_id == CAMP_SAIL.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert gather_amount_bonus(world, "water") == SEAFARING_WATER_GATHER_BONUS
    assert gather_amount_bonus(world, "food") == 0
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "water") == (
        DEFAULT_GATHER_AMOUNT + SEAFARING_WATER_GATHER_BONUS
    )
    bare = _world()
    assert gather_amount_bonus(bare, "water") == 0
    assert effective_gather_amount(bare, "water") == DEFAULT_GATHER_AMOUNT


def test_sail_stacks_with_pottery_and_irrigation_water_gather() -> None:
    """Sail water gather bonus stacks with pottery craft and irrigation canal."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_seafaring = CAMP_SEAFARING.model_copy(update={"discovered": True})
    active_pottery = CAMP_POTTERY_CRAFT.model_copy(update={"active": True})
    active_irrigation = CAMP_IRRIGATION_CANAL.model_copy(update={"active": True})
    active_sail = CAMP_SAIL.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_pottery
            if item.technology_id == CAMP_POTTERY.technology_id
            else discovered_irrigation
            if item.technology_id == CAMP_IRRIGATION.technology_id
            else discovered_seafaring
            if item.technology_id == CAMP_SEAFARING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_pottery
            if item.innovation_id == CAMP_POTTERY_CRAFT.innovation_id
            else active_irrigation
            if item.innovation_id == CAMP_IRRIGATION_CANAL.innovation_id
            else active_sail
            if item.innovation_id == CAMP_SAIL.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    water_bonus = (
        POTTERY_WATER_GATHER_BONUS
        + IRRIGATION_WATER_GATHER_BONUS
        + SEAFARING_WATER_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "water") == water_bonus
    assert effective_gather_amount(world, "water") == (
        DEFAULT_GATHER_AMOUNT + water_bonus
    )


def test_coppice_raises_wood_gather_society_wide() -> None:
    """Active coppice raises wood gather amount for every agent."""
    discovered_forestry = CAMP_FORESTRY.model_copy(update={"discovered": True})
    active_coppice = CAMP_COPPICE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_forestry
            if item.technology_id == CAMP_FORESTRY.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_coppice
            if item.innovation_id == CAMP_COPPICE.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert gather_amount_bonus(world, "wood") == FORESTRY_WOOD_GATHER_BONUS
    assert gather_amount_bonus(world, "food") == 0
    assert gather_amount_bonus(world, "water") == 0
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "wood") == (
        DEFAULT_GATHER_AMOUNT + FORESTRY_WOOD_GATHER_BONUS
    )
    bare = _world()
    assert gather_amount_bonus(bare, "wood") == 0
    assert effective_gather_amount(bare, "wood") == DEFAULT_GATHER_AMOUNT


def test_coppice_stacks_with_scaffold_wood_gather() -> None:
    """Coppice wood gather bonus stacks with the scaffold seat bonus."""
    discovered_forestry = CAMP_FORESTRY.model_copy(update={"discovered": True})
    active_coppice = CAMP_COPPICE.model_copy(update={"active": True})
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
        technologies=tuple(
            discovered_forestry
            if item.technology_id == CAMP_FORESTRY.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_coppice
            if item.innovation_id == CAMP_COPPICE.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_scaffold(world, agent.location_id) is True
    wood_bonus = FORESTRY_WOOD_GATHER_BONUS + SCAFFOLD_WOOD_GATHER_BONUS
    assert gather_amount_bonus(world, "wood") == FORESTRY_WOOD_GATHER_BONUS
    assert (
        gather_amount_bonus(world, "wood", location_id=agent.location_id) == wood_bonus
    )
    assert effective_gather_amount(world, "wood", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + wood_bonus
    )


def test_conservation_boosts_wood_gather_for_living_subject() -> None:
    """Active CONSERVATION adds a subject-scoped wood gather bonus."""
    conservation = Law.create(0, 0, "Camp Conservation", LawKind.CONSERVATION)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(conservation,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert conservation_wood_bonus_for(world, agent) == CONSERVATION_WOOD_GATHER_BONUS
    # gather_amount_bonus stays location-scoped and unaffected by conservation.
    assert gather_amount_bonus(world, "wood", location_id=agent.location_id) == 0
    assert effective_gather_amount(world, "wood", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + CONSERVATION_WOOD_GATHER_BONUS
    )
    # Without an agent there is no subject to scope the bonus to.
    assert effective_gather_amount(world, "wood") == DEFAULT_GATHER_AMOUNT


def test_conservation_stacks_with_coppice_and_scaffold_wood_gather() -> None:
    """Conservation wood bonus stacks with coppice society-wide and scaffold."""
    discovered_forestry = CAMP_FORESTRY.model_copy(update={"discovered": True})
    active_coppice = CAMP_COPPICE.model_copy(update={"active": True})
    conservation = Law.create(0, 0, "Camp Conservation", LawKind.CONSERVATION)
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
        laws=(conservation,),
        technologies=tuple(
            discovered_forestry
            if item.technology_id == CAMP_FORESTRY.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_coppice
            if item.innovation_id == CAMP_COPPICE.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    wood_bonus = (
        FORESTRY_WOOD_GATHER_BONUS
        + SCAFFOLD_WOOD_GATHER_BONUS
        + CONSERVATION_WOOD_GATHER_BONUS
    )
    assert effective_gather_amount(world, "wood", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + wood_bonus
    )


def test_pastoral_boosts_wood_gather_for_residents() -> None:
    """Active pastoral cities add a wood gather bonus at their seat."""
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
    agent = world.agents[0]
    assert location_has_active_pastoral(world, agent.location_id) is True
    assert gather_amount_bonus(world, "wood", location_id=agent.location_id) == (
        PASTORAL_WOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "wood") == 0
    assert effective_gather_amount(world, "wood", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + PASTORAL_WOOD_GATHER_BONUS
    )


def test_pastoral_stacks_with_coppice_scaffold_and_conservation_wood_gather() -> None:
    """Pastoral wood bonus stacks with coppice, scaffold, and conservation."""
    discovered_forestry = CAMP_FORESTRY.model_copy(update={"discovered": True})
    active_coppice = CAMP_COPPICE.model_copy(update={"active": True})
    conservation = Law.create(0, 0, "Camp Conservation", LawKind.CONSERVATION)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Pastoral", CityKind.PASTORAL),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Pastoral Scaffold", InfrastructureKind.SCAFFOLD
            ),
        ),
        laws=(conservation,),
        technologies=tuple(
            discovered_forestry
            if item.technology_id == CAMP_FORESTRY.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_coppice
            if item.innovation_id == CAMP_COPPICE.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    seat_bonus = (
        FORESTRY_WOOD_GATHER_BONUS
        + SCAFFOLD_WOOD_GATHER_BONUS
        + PASTORAL_WOOD_GATHER_BONUS
    )
    assert location_has_active_pastoral(world, agent.location_id) is True
    assert location_has_active_scaffold(world, agent.location_id) is True
    assert gather_amount_bonus(world, "wood") == FORESTRY_WOOD_GATHER_BONUS
    assert gather_amount_bonus(world, "wood", location_id=agent.location_id) == (
        seat_bonus
    )
    assert effective_gather_amount(world, "wood", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + seat_bonus + CONSERVATION_WOOD_GATHER_BONUS
    )


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


def test_mason_boosts_stone_gather_for_colocated_agents() -> None:
    """Active mason seats add a stone gather bonus at their location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Mason", InstitutionKind.MASON),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_mason(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        MASON_STONE_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + MASON_STONE_GATHER_BONUS
    )


def test_mason_stacks_with_forge_stone_gather() -> None:
    """Mason seat stone bonus stacks with society-wide forge metallurgy."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Mason", InstitutionKind.MASON),
        ),
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
    agent = world.agents[0]
    expected = METALLURGY_STONE_GATHER_BONUS + MASON_STONE_GATHER_BONUS
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_quarry_boosts_stone_gather_for_residents() -> None:
    """Active quarry cities add a stone gather bonus at their seat."""
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
    agent = world.agents[0]
    assert location_has_active_quarry(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        QUARRY_STONE_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + QUARRY_STONE_GATHER_BONUS
    )


def test_quarry_stacks_with_forge_and_mason_stone_gather() -> None:
    """Quarry stone bonus stacks with forge and mason."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Quarry", CityKind.QUARRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Quarry Mason", InstitutionKind.MASON),
        ),
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
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        METALLURGY_STONE_GATHER_BONUS
        + MASON_STONE_GATHER_BONUS
        + QUARRY_STONE_GATHER_BONUS
    )
    assert location_has_active_quarry(world, agent.location_id) is True
    assert location_has_active_mason(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_pickaxe_boosts_stone_gather_society_wide() -> None:
    """Active pickaxe adds a deterministic stone gather bonus society-wide."""
    discovered_mining = CAMP_MINING.model_copy(update={"discovered": True})
    active_pickaxe = CAMP_PICKAXE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_mining
            if item.technology_id == CAMP_MINING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_pickaxe
            if item.innovation_id == CAMP_PICKAXE.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert gather_amount_bonus(world, "stone") == MINING_STONE_GATHER_BONUS
    assert gather_amount_bonus(world, "water") == 0
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + MINING_STONE_GATHER_BONUS
    )


def test_pickaxe_stacks_with_forge_mason_and_quarry_stone_gather() -> None:
    """Pickaxe stone bonus stacks with forge, mason seat, and quarry city."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    active_pickaxe = CAMP_PICKAXE.model_copy(update={"active": True})
    innovations = tuple(
        active_forge
        if item.innovation_id == CAMP_FORGE.innovation_id
        else active_pickaxe
        if item.innovation_id == CAMP_PICKAXE.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Quarry", CityKind.QUARRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Quarry Mason", InstitutionKind.MASON),
        ),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        METALLURGY_STONE_GATHER_BONUS
        + MINING_STONE_GATHER_BONUS
        + MASON_STONE_GATHER_BONUS
        + QUARRY_STONE_GATHER_BONUS
    )
    assert location_has_active_quarry(world, agent.location_id) is True
    assert location_has_active_mason(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_mineral_rights_boosts_stone_gather_for_living_subject() -> None:
    """Active MINERAL_RIGHTS adds a subject-scoped stone gather bonus."""
    mineral_rights = Law.create(0, 0, "Camp Mineral Rights", LawKind.MINERAL_RIGHTS)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(mineral_rights,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert mineral_rights_stone_bonus_for(world, agent) == (
        MINERAL_RIGHTS_STONE_GATHER_BONUS
    )
    # gather_amount_bonus stays location-scoped and unaffected by mineral rights.
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == 0
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + MINERAL_RIGHTS_STONE_GATHER_BONUS
    )
    # Without an agent there is no subject to scope the bonus to.
    assert effective_gather_amount(world, "stone") == DEFAULT_GATHER_AMOUNT


def test_mineral_rights_stacks_with_pickaxe_forge_mason_and_quarry() -> None:
    """Mineral rights stone bonus stacks with pickaxe, forge, mason, quarry."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    active_pickaxe = CAMP_PICKAXE.model_copy(update={"active": True})
    innovations = tuple(
        active_forge
        if item.innovation_id == CAMP_FORGE.innovation_id
        else active_pickaxe
        if item.innovation_id == CAMP_PICKAXE.innovation_id
        else item
        for item in default_innovations()
    )
    mineral_rights = Law.create(0, 0, "Camp Mineral Rights", LawKind.MINERAL_RIGHTS)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Quarry", CityKind.QUARRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Quarry Mason", InstitutionKind.MASON),
        ),
        laws=(mineral_rights,),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    seat_bonus = (
        METALLURGY_STONE_GATHER_BONUS
        + MINING_STONE_GATHER_BONUS
        + MASON_STONE_GATHER_BONUS
        + QUARRY_STONE_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        seat_bonus
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + seat_bonus + MINERAL_RIGHTS_STONE_GATHER_BONUS
    )


def test_miner_boosts_stone_gather_for_colocated_agents() -> None:
    """Active miner seats add a stone gather bonus at their location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Miner", InstitutionKind.MINER),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_miner(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        MINER_STONE_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + MINER_STONE_GATHER_BONUS
    )


def test_miner_stacks_with_forge_stone_gather() -> None:
    """Miner seat stone bonus stacks with society-wide forge metallurgy."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Miner", InstitutionKind.MINER),
        ),
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
    agent = world.agents[0]
    expected = METALLURGY_STONE_GATHER_BONUS + MINER_STONE_GATHER_BONUS
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_miner_stacks_with_pickaxe_forge_mason_and_quarry_stone_gather() -> None:
    """Miner seat bonus stacks with pickaxe, forge, mason seat, and quarry."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    active_pickaxe = CAMP_PICKAXE.model_copy(update={"active": True})
    innovations = tuple(
        active_forge
        if item.innovation_id == CAMP_FORGE.innovation_id
        else active_pickaxe
        if item.innovation_id == CAMP_PICKAXE.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Quarry", CityKind.QUARRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Quarry Mason", InstitutionKind.MASON),
            Institution.create(1, 0, 1, "Quarry Miner", InstitutionKind.MINER),
        ),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        METALLURGY_STONE_GATHER_BONUS
        + MINING_STONE_GATHER_BONUS
        + MASON_STONE_GATHER_BONUS
        + MINER_STONE_GATHER_BONUS
        + QUARRY_STONE_GATHER_BONUS
    )
    assert location_has_active_quarry(world, agent.location_id) is True
    assert location_has_active_mason(world, agent.location_id) is True
    assert location_has_active_miner(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_mineshaft_boosts_stone_gather_for_colocated_agents() -> None:
    """Active mineshafts add a stone gather bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_mineshaft(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        MINESHAFT_STONE_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + MINESHAFT_STONE_GATHER_BONUS
    )


def test_mineshaft_stacks_with_pickaxe_forge_seats_and_quarry_stone_gather() -> None:
    """Mineshaft bonus stacks with pickaxe, forge, mason/miner seats, quarry."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_forge = CAMP_FORGE.model_copy(update={"active": True})
    active_pickaxe = CAMP_PICKAXE.model_copy(update={"active": True})
    innovations = tuple(
        active_forge
        if item.innovation_id == CAMP_FORGE.innovation_id
        else active_pickaxe
        if item.innovation_id == CAMP_PICKAXE.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Quarry", CityKind.QUARRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Quarry Mason", InstitutionKind.MASON),
            Institution.create(1, 0, 1, "Quarry Miner", InstitutionKind.MINER),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Quarry Mineshaft", InfrastructureKind.MINESHAFT
            ),
        ),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        METALLURGY_STONE_GATHER_BONUS
        + MINING_STONE_GATHER_BONUS
        + MASON_STONE_GATHER_BONUS
        + MINER_STONE_GATHER_BONUS
        + QUARRY_STONE_GATHER_BONUS
        + MINESHAFT_STONE_GATHER_BONUS
    )
    assert location_has_active_quarry(world, agent.location_id) is True
    assert location_has_active_mason(world, agent.location_id) is True
    assert location_has_active_miner(world, agent.location_id) is True
    assert location_has_active_mineshaft(world, agent.location_id) is True
    assert gather_amount_bonus(world, "stone", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "stone", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
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


def test_collegium_stacks_with_all_teaching_bonuses() -> None:
    """Collegium teaching bonus stacks with every teaching capacity source."""
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
            Institution.create(2, 0, 1, "Forum Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 1, "Forum Architect", InstitutionKind.ARCHITECT),
            Institution.create(
                4, 0, 1, "Forum Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(
                5, 0, 1, "Forum Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(6, 0, 1, "Forum Tailor", InstitutionKind.TAILOR),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_scriptorium(world, agent.location_id) is True
    assert location_has_active_stoa(world, agent.location_id) is True
    assert location_has_active_academy(world, agent.location_id) is True
    assert location_has_active_forum(world, agent.location_id) is True
    assert location_has_active_school(world, agent.location_id) is True
    assert location_has_active_collegium(world, agent.location_id) is True
    assert location_has_active_architect(world, agent.location_id) is True
    assert location_has_active_cartographer(world, agent.location_id) is True
    assert location_has_active_agronomist(world, agent.location_id) is True
    assert location_has_active_tailor(world, agent.location_id) is True
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
        + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
        + ARCHITECT_TEACHINGS_PER_KNOWER_BONUS
        + CARTOGRAPHER_TEACHINGS_PER_KNOWER_BONUS
        + AGRONOMIST_TEACHINGS_PER_KNOWER_BONUS
        + TAILOR_TEACHINGS_PER_KNOWER_BONUS
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


def test_collegium_boosts_teachings_and_stacks_with_school() -> None:
    """Active collegium seat bonus stacks with school and prior teaching sources."""
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
            Institution.create(2, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_collegium(world, agent.location_id) is True
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
        + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, collegium (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    collegium_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_collegium(collegium_only, 0) is True
    assert (
        effective_teachings_per_knower(
            collegium_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=collegium_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_collegium(bare, bare.agents[0].location_id) is False


def test_architect_boosts_teachings_and_stacks_with_collegium() -> None:
    """Active architect seat bonus stacks with collegium and prior teaching sources."""
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
            Institution.create(2, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_architect(world, agent.location_id) is True
    assert location_has_active_collegium(world, agent.location_id) is True
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
        + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
        + ARCHITECT_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, architect (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    architect_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_architect(architect_only, 0) is True
    assert (
        effective_teachings_per_knower(
            architect_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=architect_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + ARCHITECT_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_architect(bare, bare.agents[0].location_id) is False


def test_cartographer_boosts_teachings_and_stacks_with_architect() -> None:
    """Active cartographer seat bonus stacks with architect and prior sources."""
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
            Institution.create(2, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(
                4, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_cartographer(world, agent.location_id) is True
    assert location_has_active_architect(world, agent.location_id) is True
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
        + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
        + ARCHITECT_TEACHINGS_PER_KNOWER_BONUS
        + CARTOGRAPHER_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, cartographer (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    cartographer_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_cartographer(cartographer_only, 0) is True
    assert (
        effective_teachings_per_knower(
            cartographer_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=cartographer_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + CARTOGRAPHER_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_cartographer(bare, bare.agents[0].location_id) is False


def test_agronomist_boosts_teachings_and_stacks_with_cartographer() -> None:
    """Active agronomist seat bonus stacks with cartographer and prior sources."""
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
            Institution.create(2, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(
                4, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(
                5, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_agronomist(world, agent.location_id) is True
    assert location_has_active_cartographer(world, agent.location_id) is True
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
        + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
        + ARCHITECT_TEACHINGS_PER_KNOWER_BONUS
        + CARTOGRAPHER_TEACHINGS_PER_KNOWER_BONUS
        + AGRONOMIST_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, agronomist (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    agronomist_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_agronomist(agronomist_only, 0) is True
    assert (
        effective_teachings_per_knower(
            agronomist_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=agronomist_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + AGRONOMIST_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_agronomist(bare, bare.agents[0].location_id) is False


def test_tailor_boosts_teachings_and_stacks_with_agronomist() -> None:
    """Active tailor seat bonus stacks with agronomist and prior sources."""
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
            Institution.create(2, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(3, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(
                4, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(
                5, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(6, 0, 0, "Camp Tailor", InstitutionKind.TAILOR),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_tailor(world, agent.location_id) is True
    assert location_has_active_agronomist(world, agent.location_id) is True
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
        + COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
        + ARCHITECT_TEACHINGS_PER_KNOWER_BONUS
        + CARTOGRAPHER_TEACHINGS_PER_KNOWER_BONUS
        + AGRONOMIST_TEACHINGS_PER_KNOWER_BONUS
        + TAILOR_TEACHINGS_PER_KNOWER_BONUS
    )
    # Without agent/location, tailor (seat-scoped) and curriculum do not apply.
    assert (
        effective_teachings_per_knower(world, base=DEFAULT_TEACHINGS_PER_KNOWER)
        == DEFAULT_TEACHINGS_PER_KNOWER + WRITING_TEACHINGS_PER_KNOWER_BONUS
    )
    tailor_only = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Tailor", InstitutionKind.TAILOR),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_tailor(tailor_only, 0) is True
    assert (
        effective_teachings_per_knower(
            tailor_only,
            base=DEFAULT_TEACHINGS_PER_KNOWER,
            agent=tailor_only.agents[0],
        )
        == DEFAULT_TEACHINGS_PER_KNOWER + TAILOR_TEACHINGS_PER_KNOWER_BONUS
    )
    bare = _world()
    assert location_has_active_tailor(bare, bare.agents[0].location_id) is False


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


def test_apothecary_boosts_drink_restore_for_colocated_agents() -> None:
    """Active apothecaries add a DRINK restore bonus at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_apothecary(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == APOTHECARY_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + APOTHECARY_DRINK_RESTORE_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_apothecary(bare, bare.agents[0].location_id) is False
    assert drink_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_drink_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_DRINK_RESTORE
    )


def test_lazaretto_boosts_drink_restore_for_residents() -> None:
    """Active lazaretto cities raise DRINK restore for residents."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Lazaretto", CityKind.LAZARETTO),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_lazaretto(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == LAZARETTO_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + LAZARETTO_DRINK_RESTORE_BONUS
    )

    at_capital = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp City", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Lazaretto", CityKind.LAZARETTO),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_lazaretto(at_capital, 0) is False
    assert effective_drink_restore(at_capital, at_capital.agents[0]) == pytest.approx(
        DEFAULT_DRINK_RESTORE
    )
    bare = _world()
    assert location_has_active_lazaretto(bare, bare.agents[0].location_id) is False


def test_asepsis_boosts_drink_restore_society_wide() -> None:
    """Active asepsis adds a DRINK restore bonus for every agent."""
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    active_asepsis = CAMP_ASEPSIS.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_hygiene
            if tech.technology_id == CAMP_HYGIENE.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=(active_asepsis,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert drink_restore_bonus(world, agent) == HYGIENE_DRINK_RESTORE_BONUS
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE + HYGIENE_DRINK_RESTORE_BONUS
    )
    snap = census_effects(world)
    assert snap.drink_restore_bps == round(
        (DEFAULT_DRINK_RESTORE + HYGIENE_DRINK_RESTORE_BONUS) * 10_000
    )
    bare = _world()
    assert drink_restore_bonus(bare, bare.agents[0]) == 0.0
    assert effective_drink_restore(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_DRINK_RESTORE
    )


def test_well_shrine_clinic_apothecary_and_lazaretto_bonuses_stack() -> None:
    """Drink seat bonuses stack when colocated at a lazaretto."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Lazaretto", CityKind.LAZARETTO),
        ),
        infrastructure=(
            Infrastructure.create(0, 0, 1, 1, "Camp Well", InfrastructureKind.WELL),
            Infrastructure.create(1, 0, 1, 1, "Camp Shrine", InfrastructureKind.SHRINE),
            Infrastructure.create(2, 0, 1, 1, "Camp Clinic", InfrastructureKind.CLINIC),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Camp Apothecary", InstitutionKind.APOTHECARY),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_well(world, agent.location_id) is True
    assert location_has_active_shrine(world, agent.location_id) is True
    assert location_has_active_clinic(world, agent.location_id) is True
    assert location_has_active_apothecary(world, agent.location_id) is True
    assert location_has_active_lazaretto(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == pytest.approx(
        WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
        + APOTHECARY_DRINK_RESTORE_BONUS
        + LAZARETTO_DRINK_RESTORE_BONUS
    )
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE
        + WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
        + APOTHECARY_DRINK_RESTORE_BONUS
        + LAZARETTO_DRINK_RESTORE_BONUS
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


def test_sanitation_and_asepsis_stack_with_all_drink_restore_seats() -> None:
    """Sanitation and asepsis stack with every colocated drink source."""
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    active_asepsis = CAMP_ASEPSIS.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Lazaretto", CityKind.LAZARETTO),
        ),
        technologies=tuple(
            discovered_hygiene
            if tech.technology_id == CAMP_HYGIENE.technology_id
            else tech
            for tech in default_technologies()
        ),
        innovations=(active_asepsis,),
        infrastructure=(
            Infrastructure.create(0, 0, 1, 1, "Camp Well", InfrastructureKind.WELL),
            Infrastructure.create(1, 0, 1, 1, "Camp Shrine", InfrastructureKind.SHRINE),
            Infrastructure.create(2, 0, 1, 1, "Camp Clinic", InfrastructureKind.CLINIC),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Camp Apothecary", InstitutionKind.APOTHECARY),
        ),
        laws=(Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION),),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_lazaretto(world, agent.location_id) is True
    assert drink_restore_bonus(world, agent) == pytest.approx(
        WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
        + APOTHECARY_DRINK_RESTORE_BONUS
        + LAZARETTO_DRINK_RESTORE_BONUS
        + SANITATION_DRINK_RESTORE_BONUS
        + HYGIENE_DRINK_RESTORE_BONUS
    )
    assert effective_drink_restore(world, agent) == pytest.approx(
        DEFAULT_DRINK_RESTORE
        + WELL_DRINK_RESTORE_BONUS
        + SHRINE_DRINK_RESTORE_BONUS
        + CLINIC_DRINK_RESTORE_BONUS
        + APOTHECARY_DRINK_RESTORE_BONUS
        + LAZARETTO_DRINK_RESTORE_BONUS
        + SANITATION_DRINK_RESTORE_BONUS
        + HYGIENE_DRINK_RESTORE_BONUS
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


def test_waystation_boosts_food_gather_for_colocated_agents() -> None:
    """Active waystations add a food gather bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_waystation(world, agent.location_id) is True
    assert (
        gather_amount_bonus(world, "food", location_id=agent.location_id)
        == WAYSTATION_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert (
        effective_gather_amount(world, "food", agent=agent)
        == DEFAULT_GATHER_AMOUNT + WAYSTATION_FOOD_GATHER_BONUS
    )
    snap = census_effects(world)
    assert snap.active_storehouse_count == 0
    assert snap.food_gather_amount == (
        DEFAULT_GATHER_AMOUNT + WAYSTATION_FOOD_GATHER_BONUS
    )


def test_waystation_stacks_with_storehouse_food_gather() -> None:
    """Waystation and storehouse food gather bonuses stack at the same seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Storehouse", InfrastructureKind.STOREHOUSE
            ),
            Infrastructure.create(
                1, 0, 0, 0, "Camp Waystation", InfrastructureKind.WAYSTATION
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_storehouse(world, agent.location_id) is True
    assert location_has_active_waystation(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        STOREHOUSE_FOOD_GATHER_BONUS + WAYSTATION_FOOD_GATHER_BONUS
    )
    assert (
        effective_gather_amount(world, "food", agent=agent)
        == DEFAULT_GATHER_AMOUNT
        + STOREHOUSE_FOOD_GATHER_BONUS
        + WAYSTATION_FOOD_GATHER_BONUS
    )
    snap = census_effects(world)
    assert snap.active_storehouse_count == 1
    assert snap.food_gather_amount == (
        DEFAULT_GATHER_AMOUNT
        + STOREHOUSE_FOOD_GATHER_BONUS
        + WAYSTATION_FOOD_GATHER_BONUS
    )


def test_terrace_boosts_food_gather_for_colocated_agents() -> None:
    """Active terraces add a food gather bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_terrace(world, agent.location_id) is True
    assert (
        gather_amount_bonus(world, "food", location_id=agent.location_id)
        == TERRACE_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert (
        effective_gather_amount(world, "food", agent=agent)
        == DEFAULT_GATHER_AMOUNT + TERRACE_FOOD_GATHER_BONUS
    )


def test_terrace_stacks_with_storehouse_food_gather() -> None:
    """Terrace and storehouse food gather bonuses stack at the same seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Storehouse", InfrastructureKind.STOREHOUSE
            ),
            Infrastructure.create(
                1, 0, 0, 0, "Camp Terrace", InfrastructureKind.TERRACE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_storehouse(world, agent.location_id) is True
    assert location_has_active_terrace(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        STOREHOUSE_FOOD_GATHER_BONUS + TERRACE_FOOD_GATHER_BONUS
    )
    assert (
        effective_gather_amount(world, "food", agent=agent)
        == DEFAULT_GATHER_AMOUNT
        + STOREHOUSE_FOOD_GATHER_BONUS
        + TERRACE_FOOD_GATHER_BONUS
    )


def test_entrepot_boosts_food_gather_for_residents() -> None:
    """Active entrepot cities add a food gather bonus at their seat."""
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
    agent = world.agents[0]
    assert location_has_active_entrepot(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        ENTREPOT_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + ENTREPOT_FOOD_GATHER_BONUS
    )


def test_entrepot_stacks_with_storehouse_and_waystation_food_gather() -> None:
    """Entrepot food bonus stacks with storehouse and waystation at the seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Entrepot", CityKind.ENTREPOT),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Entrepot Storehouse", InfrastructureKind.STOREHOUSE
            ),
            Infrastructure.create(
                1, 0, 1, 1, "Entrepot Waystation", InfrastructureKind.WAYSTATION
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        STOREHOUSE_FOOD_GATHER_BONUS
        + WAYSTATION_FOOD_GATHER_BONUS
        + ENTREPOT_FOOD_GATHER_BONUS
    )
    assert location_has_active_entrepot(world, agent.location_id) is True
    assert location_has_active_storehouse(world, agent.location_id) is True
    assert location_has_active_waystation(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_farmstead_boosts_food_gather_for_residents() -> None:
    """Active farmstead cities add a food gather bonus at their seat."""
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
    agent = world.agents[0]
    assert location_has_active_farmstead(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        FARMSTEAD_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + FARMSTEAD_FOOD_GATHER_BONUS
    )


def test_farmstead_stacks_with_storehouse_and_waystation_food_gather() -> None:
    """Farmstead food bonus stacks with storehouse and waystation at the seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Farmstead", CityKind.FARMSTEAD),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Farmstead Storehouse", InfrastructureKind.STOREHOUSE
            ),
            Infrastructure.create(
                1, 0, 1, 1, "Farmstead Waystation", InfrastructureKind.WAYSTATION
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        STOREHOUSE_FOOD_GATHER_BONUS
        + WAYSTATION_FOOD_GATHER_BONUS
        + FARMSTEAD_FOOD_GATHER_BONUS
    )
    assert location_has_active_farmstead(world, agent.location_id) is True
    assert location_has_active_storehouse(world, agent.location_id) is True
    assert location_has_active_waystation(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_plow_raises_food_gather_society_wide() -> None:
    """Active plow raises food gather amount for every agent."""
    discovered_agriculture = CAMP_AGRICULTURE.model_copy(update={"discovered": True})
    active_plow = CAMP_PLOW.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_agriculture
            if item.technology_id == CAMP_AGRICULTURE.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_plow if item.innovation_id == CAMP_PLOW.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert gather_amount_bonus(world, "food") == AGRICULTURE_FOOD_GATHER_BONUS
    assert gather_amount_bonus(world, "water") == 0
    assert gather_amount_bonus(world, "stone") == 0
    assert effective_gather_amount(world, "food") == (
        DEFAULT_GATHER_AMOUNT + AGRICULTURE_FOOD_GATHER_BONUS
    )
    bare = _world()
    assert gather_amount_bonus(bare, "food") == 0
    assert effective_gather_amount(bare, "food") == DEFAULT_GATHER_AMOUNT


def test_granary_boosts_food_gather_for_colocated_agents() -> None:
    """Active granary seats add a food gather bonus at their location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_granary(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        GRANARY_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + GRANARY_FOOD_GATHER_BONUS
    )


def test_husbandman_boosts_food_gather_for_colocated_agents() -> None:
    """Active husbandman seats add a food gather bonus at their location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_husbandman(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        HUSBANDMAN_FOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "food") == 0
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + HUSBANDMAN_FOOD_GATHER_BONUS
    )


def test_plow_stacks_with_storehouse_waystation_entrepot_and_granary_food_gather() -> (
    None
):
    """Plow stacks with storehouse, waystation, entrepot, granary, and husbandman."""
    discovered_agriculture = CAMP_AGRICULTURE.model_copy(update={"discovered": True})
    active_plow = CAMP_PLOW.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Entrepot", CityKind.ENTREPOT),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Entrepot Storehouse", InfrastructureKind.STOREHOUSE
            ),
            Infrastructure.create(
                1, 0, 1, 1, "Entrepot Waystation", InfrastructureKind.WAYSTATION
            ),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Entrepot Granary", InstitutionKind.GRANARY),
            Institution.create(
                1, 0, 1, "Entrepot Husbandman", InstitutionKind.HUSBANDMAN
            ),
        ),
        technologies=tuple(
            discovered_agriculture
            if item.technology_id == CAMP_AGRICULTURE.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_plow if item.innovation_id == CAMP_PLOW.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        AGRICULTURE_FOOD_GATHER_BONUS
        + STOREHOUSE_FOOD_GATHER_BONUS
        + WAYSTATION_FOOD_GATHER_BONUS
        + ENTREPOT_FOOD_GATHER_BONUS
        + GRANARY_FOOD_GATHER_BONUS
        + HUSBANDMAN_FOOD_GATHER_BONUS
    )
    assert location_has_active_granary(world, agent.location_id) is True
    assert location_has_active_husbandman(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food") == AGRICULTURE_FOOD_GATHER_BONUS
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_plow_stacks_with_storehouse_waystation_farmstead_and_granary_food_gather() -> (
    None
):
    """Plow stacks with storehouse, waystation, farmstead, granary, and husbandman."""
    discovered_agriculture = CAMP_AGRICULTURE.model_copy(update={"discovered": True})
    active_plow = CAMP_PLOW.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Farmstead", CityKind.FARMSTEAD),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Farmstead Storehouse", InfrastructureKind.STOREHOUSE
            ),
            Infrastructure.create(
                1, 0, 1, 1, "Farmstead Waystation", InfrastructureKind.WAYSTATION
            ),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Farmstead Granary", InstitutionKind.GRANARY),
            Institution.create(
                1, 0, 1, "Farmstead Husbandman", InstitutionKind.HUSBANDMAN
            ),
        ),
        technologies=tuple(
            discovered_agriculture
            if item.technology_id == CAMP_AGRICULTURE.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_plow if item.innovation_id == CAMP_PLOW.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected = (
        AGRICULTURE_FOOD_GATHER_BONUS
        + STOREHOUSE_FOOD_GATHER_BONUS
        + WAYSTATION_FOOD_GATHER_BONUS
        + FARMSTEAD_FOOD_GATHER_BONUS
        + GRANARY_FOOD_GATHER_BONUS
        + HUSBANDMAN_FOOD_GATHER_BONUS
    )
    assert location_has_active_farmstead(world, agent.location_id) is True
    assert location_has_active_granary(world, agent.location_id) is True
    assert location_has_active_husbandman(world, agent.location_id) is True
    assert gather_amount_bonus(world, "food") == AGRICULTURE_FOOD_GATHER_BONUS
    assert gather_amount_bonus(world, "food", location_id=agent.location_id) == (
        expected
    )
    assert effective_gather_amount(world, "food", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + expected
    )


def test_scaffold_boosts_wood_gather_for_colocated_agents() -> None:
    """Active scaffolds add a wood gather bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_scaffold(world, agent.location_id) is True
    assert (
        gather_amount_bonus(world, "wood", location_id=agent.location_id)
        == SCAFFOLD_WOOD_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "wood") == 0
    assert (
        effective_gather_amount(world, "wood", agent=agent)
        == DEFAULT_GATHER_AMOUNT + SCAFFOLD_WOOD_GATHER_BONUS
    )
    snap = census_effects(world)
    assert snap.active_scaffold_count == 1
    assert snap.wood_gather_amount == (
        DEFAULT_GATHER_AMOUNT + SCAFFOLD_WOOD_GATHER_BONUS
    )
    assert snap.active_storehouse_count == 0
    assert snap.food_gather_amount == DEFAULT_GATHER_AMOUNT


def test_ditch_boosts_water_gather_for_colocated_agents() -> None:
    """Active ditches add a water gather bonus at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_ditch(world, agent.location_id) is True
    assert (
        gather_amount_bonus(world, "water", location_id=agent.location_id)
        == DITCH_WATER_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "water") == 0
    assert (
        effective_gather_amount(world, "water", agent=agent)
        == DEFAULT_GATHER_AMOUNT + DITCH_WATER_GATHER_BONUS
    )
    snap = census_effects(world)
    assert snap.active_ditch_count == 1
    assert snap.water_gather_amount == (
        DEFAULT_GATHER_AMOUNT + DITCH_WATER_GATHER_BONUS
    )
    assert snap.active_scaffold_count == 0
    assert snap.wood_gather_amount == DEFAULT_GATHER_AMOUNT


def test_ditch_stacks_with_pottery_irrigation_and_sail_water_gather() -> None:
    """Ditch water gather bonus stacks with pottery, irrigation canal, and sail."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_seafaring = CAMP_SEAFARING.model_copy(update={"discovered": True})
    active_pottery = CAMP_POTTERY_CRAFT.model_copy(update={"active": True})
    active_irrigation = CAMP_IRRIGATION_CANAL.model_copy(update={"active": True})
    active_sail = CAMP_SAIL.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        technologies=tuple(
            discovered_pottery
            if item.technology_id == CAMP_POTTERY.technology_id
            else discovered_irrigation
            if item.technology_id == CAMP_IRRIGATION.technology_id
            else discovered_seafaring
            if item.technology_id == CAMP_SEAFARING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_pottery
            if item.innovation_id == CAMP_POTTERY_CRAFT.innovation_id
            else active_irrigation
            if item.innovation_id == CAMP_IRRIGATION_CANAL.innovation_id
            else active_sail
            if item.innovation_id == CAMP_SAIL.innovation_id
            else item
            for item in default_innovations()
        ),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Ditch", InfrastructureKind.DITCH),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    water_bonus = (
        POTTERY_WATER_GATHER_BONUS
        + IRRIGATION_WATER_GATHER_BONUS
        + SEAFARING_WATER_GATHER_BONUS
        + DITCH_WATER_GATHER_BONUS
    )
    assert gather_amount_bonus(world, "water", location_id=agent.location_id) == (
        water_bonus
    )
    assert gather_amount_bonus(world, "water") == (
        POTTERY_WATER_GATHER_BONUS
        + IRRIGATION_WATER_GATHER_BONUS
        + SEAFARING_WATER_GATHER_BONUS
    )
    assert effective_gather_amount(world, "water", agent=agent) == (
        DEFAULT_GATHER_AMOUNT + water_bonus
    )


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


def test_building_codes_reduce_move_energy_and_stack_with_road() -> None:
    """Building-code laws discount MOVE energy and stack with road seats."""
    law = Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    road = Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(law,),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(road,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = ROAD_MOVE_ENERGY_DISCOUNT + BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    assert building_codes_move_discount_for(world, agent) == (
        BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    )
    assert move_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_move_energy_cost(world, agent) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST - expected_discount
    )

    without_road = world.model_copy(update={"infrastructure": ()})
    assert effective_move_energy_cost(without_road, without_road.agents[0]) == (
        pytest.approx(DEFAULT_MOVE_ENERGY_COST - BUILDING_CODES_MOVE_ENERGY_DISCOUNT)
    )


def test_passage_reduces_move_energy_and_stack_with_road() -> None:
    """Passage laws discount MOVE energy and stack with road seats."""
    law = Law.create(0, 0, "Camp Passage", LawKind.PASSAGE)
    road = Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(law,),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(road,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = ROAD_MOVE_ENERGY_DISCOUNT + PASSAGE_MOVE_ENERGY_DISCOUNT
    assert passage_move_discount_for(world, agent) == PASSAGE_MOVE_ENERGY_DISCOUNT
    assert move_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_move_energy_cost(world, agent) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST - expected_discount
    )

    without_road = world.model_copy(update={"infrastructure": ()})
    assert effective_move_energy_cost(without_road, without_road.agents[0]) == (
        pytest.approx(DEFAULT_MOVE_ENERGY_COST - PASSAGE_MOVE_ENERGY_DISCOUNT)
    )


def test_bridge_reduces_move_energy_for_colocated_agents() -> None:
    """Active bridges discount MOVE energy at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_bridge(world, agent.location_id) is True
    assert effective_move_energy_cost(world, agent) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST - BRIDGE_MOVE_ENERGY_DISCOUNT
    )
    snap = census_effects(world)
    assert snap.move_energy_cost_bps == round(
        (DEFAULT_MOVE_ENERGY_COST - BRIDGE_MOVE_ENERGY_DISCOUNT) * 10_000
    )


def test_bridge_stacks_with_road_and_building_codes() -> None:
    """Bridge seat discount stacks with road seats and building-code laws."""
    law = Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(law,),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD),
            Infrastructure.create(1, 0, 0, 0, "Camp Bridge", InfrastructureKind.BRIDGE),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = (
        ROAD_MOVE_ENERGY_DISCOUNT
        + BRIDGE_MOVE_ENERGY_DISCOUNT
        + BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    )
    assert location_has_active_bridge(world, agent.location_id) is True
    assert move_energy_discount(world, agent) == pytest.approx(expected_discount)
    # Full stack exceeds the default move cost and clamps to zero.
    assert effective_move_energy_cost(world, agent) == pytest.approx(0.0)
    assert census_effects(world).move_energy_cost_bps == round(
        max(
            0.0,
            DEFAULT_MOVE_ENERGY_COST
            - ROAD_MOVE_ENERGY_DISCOUNT
            - BRIDGE_MOVE_ENERGY_DISCOUNT,
        )
        * 10_000
    )


def test_compass_reduces_move_energy_society_wide() -> None:
    """Active compass discounts MOVE energy for every agent."""
    discovered_navigation = CAMP_NAVIGATION.model_copy(update={"discovered": True})
    active_compass = CAMP_COMPASS.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_navigation
            if item.technology_id == CAMP_NAVIGATION.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_compass if item.innovation_id == CAMP_COMPASS.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert move_energy_discount(world, agent) == pytest.approx(
        NAVIGATION_MOVE_ENERGY_DISCOUNT
    )
    assert effective_move_energy_cost(world, agent) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST - NAVIGATION_MOVE_ENERGY_DISCOUNT
    )
    snap = census_effects(world)
    assert snap.move_energy_cost_bps == round(
        (DEFAULT_MOVE_ENERGY_COST - NAVIGATION_MOVE_ENERGY_DISCOUNT) * 10_000
    )
    bare = _world()
    assert effective_move_energy_cost(bare, bare.agents[0]) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST
    )


def test_compass_stacks_with_road_bridge_and_building_codes() -> None:
    """Compass MOVE discount stacks with road, bridge, and building codes."""
    discovered_navigation = CAMP_NAVIGATION.model_copy(update={"discovered": True})
    active_compass = CAMP_COMPASS.model_copy(update={"active": True})
    law = Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(law,),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD),
            Infrastructure.create(1, 0, 0, 0, "Camp Bridge", InfrastructureKind.BRIDGE),
        ),
        technologies=tuple(
            discovered_navigation
            if item.technology_id == CAMP_NAVIGATION.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_compass if item.innovation_id == CAMP_COMPASS.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = (
        ROAD_MOVE_ENERGY_DISCOUNT
        + BRIDGE_MOVE_ENERGY_DISCOUNT
        + BUILDING_CODES_MOVE_ENERGY_DISCOUNT
        + NAVIGATION_MOVE_ENERGY_DISCOUNT
    )
    assert move_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_move_energy_cost(world, agent) == pytest.approx(0.0)
    assert census_effects(world).move_energy_cost_bps == round(
        max(
            0.0,
            DEFAULT_MOVE_ENERGY_COST
            - ROAD_MOVE_ENERGY_DISCOUNT
            - BRIDGE_MOVE_ENERGY_DISCOUNT
            - NAVIGATION_MOVE_ENERGY_DISCOUNT,
        )
        * 10_000
    )


def test_passage_stacks_with_road_bridge_building_codes_and_compass() -> None:
    """Passage MOVE discount stacks with road, bridge, building codes, compass."""
    discovered_navigation = CAMP_NAVIGATION.model_copy(update={"discovered": True})
    active_compass = CAMP_COMPASS.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(
            Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES),
            Law.create(1, 0, "Camp Passage", LawKind.PASSAGE),
        ),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD),
            Infrastructure.create(1, 0, 0, 0, "Camp Bridge", InfrastructureKind.BRIDGE),
        ),
        technologies=tuple(
            discovered_navigation
            if item.technology_id == CAMP_NAVIGATION.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_compass if item.innovation_id == CAMP_COMPASS.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = (
        ROAD_MOVE_ENERGY_DISCOUNT
        + BRIDGE_MOVE_ENERGY_DISCOUNT
        + BUILDING_CODES_MOVE_ENERGY_DISCOUNT
        + PASSAGE_MOVE_ENERGY_DISCOUNT
        + NAVIGATION_MOVE_ENERGY_DISCOUNT
    )
    assert passage_move_discount_for(world, agent) == PASSAGE_MOVE_ENERGY_DISCOUNT
    assert move_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_move_energy_cost(world, agent) == pytest.approx(0.0)
    # census_effects move path omits statute discounts (building_codes/passage).
    assert census_effects(world).move_energy_cost_bps == round(
        max(
            0.0,
            DEFAULT_MOVE_ENERGY_COST
            - ROAD_MOVE_ENERGY_DISCOUNT
            - BRIDGE_MOVE_ENERGY_DISCOUNT
            - NAVIGATION_MOVE_ENERGY_DISCOUNT,
        )
        * 10_000
    )


def test_caravan_reduces_move_energy_for_colocated_agents() -> None:
    """Active caravans discount MOVE energy at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_caravan(world, agent.location_id) is True
    assert effective_move_energy_cost(world, agent) == pytest.approx(
        DEFAULT_MOVE_ENERGY_COST - CARAVAN_MOVE_ENERGY_DISCOUNT
    )
    snap = census_effects(world)
    assert snap.move_energy_cost_bps == round(
        (DEFAULT_MOVE_ENERGY_COST - CARAVAN_MOVE_ENERGY_DISCOUNT) * 10_000
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_caravan(bare, bare.agents[0].location_id) is False


def test_caravan_stacks_with_road_bridge_building_codes_passage_and_compass() -> None:
    """Caravan seat discount stacks with road, bridge, statutes, and compass."""
    discovered_navigation = CAMP_NAVIGATION.model_copy(update={"discovered": True})
    active_compass = CAMP_COMPASS.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(
            Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES),
            Law.create(1, 0, "Camp Passage", LawKind.PASSAGE),
        ),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Road", InfrastructureKind.ROAD),
            Infrastructure.create(1, 0, 0, 0, "Camp Bridge", InfrastructureKind.BRIDGE),
        ),
        institutions=(
            Institution.create(0, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
        ),
        technologies=tuple(
            discovered_navigation
            if item.technology_id == CAMP_NAVIGATION.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_compass if item.innovation_id == CAMP_COMPASS.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = (
        ROAD_MOVE_ENERGY_DISCOUNT
        + BRIDGE_MOVE_ENERGY_DISCOUNT
        + CARAVAN_MOVE_ENERGY_DISCOUNT
        + BUILDING_CODES_MOVE_ENERGY_DISCOUNT
        + PASSAGE_MOVE_ENERGY_DISCOUNT
        + NAVIGATION_MOVE_ENERGY_DISCOUNT
    )
    assert location_has_active_caravan(world, agent.location_id) is True
    assert move_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_move_energy_cost(world, agent) == pytest.approx(0.0)
    # census_effects move path omits statute discounts (building_codes/passage).
    assert census_effects(world).move_energy_cost_bps == round(
        max(
            0.0,
            DEFAULT_MOVE_ENERGY_COST
            - ROAD_MOVE_ENERGY_DISCOUNT
            - BRIDGE_MOVE_ENERGY_DISCOUNT
            - CARAVAN_MOVE_ENERGY_DISCOUNT
            - NAVIGATION_MOVE_ENERGY_DISCOUNT,
        )
        * 10_000
    )


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


def test_customs_reduces_produce_energy_and_stacks_with_guild() -> None:
    """Customs laws discount PRODUCE energy and stack with guild seats."""
    law = Law.create(0, 0, "Camp Customs", LawKind.CUSTOMS)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(law,),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = GUILD_PRODUCE_ENERGY_DISCOUNT + CUSTOMS_PRODUCE_ENERGY_DISCOUNT
    assert customs_produce_discount_for(world, agent) == CUSTOMS_PRODUCE_ENERGY_DISCOUNT
    assert produce_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - expected_discount)

    without_guild = world.model_copy(update={"institutions": ()})
    assert effective_produce_energy_cost(
        without_guild,
        without_guild.agents[0],
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - CUSTOMS_PRODUCE_ENERGY_DISCOUNT)
    # census_effects produce path omits statute discounts (customs).
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - GUILD_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )


def test_labor_reduces_produce_energy_and_stacks_with_guild() -> None:
    """Labor laws discount PRODUCE energy and stack with guild seats."""
    law = Law.create(0, 0, "Camp Labor", LawKind.LABOR)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(law,),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = GUILD_PRODUCE_ENERGY_DISCOUNT + LABOR_PRODUCE_ENERGY_DISCOUNT
    assert labor_produce_discount_for(world, agent) == LABOR_PRODUCE_ENERGY_DISCOUNT
    assert produce_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - expected_discount)

    without_guild = world.model_copy(update={"institutions": ()})
    assert effective_produce_energy_cost(
        without_guild,
        without_guild.agents[0],
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - LABOR_PRODUCE_ENERGY_DISCOUNT)
    # census_effects produce path omits statute discounts (labor).
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - GUILD_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )


def test_workshop_reduces_produce_energy_for_colocated_agents() -> None:
    """Active workshops discount PRODUCE energy at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_workshop(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - WORKSHOP_PRODUCE_ENERGY_DISCOUNT)
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - WORKSHOP_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_workshop(bare, bare.agents[0].location_id) is False


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


def test_pulley_reduces_produce_energy_and_stacks_with_guild_and_abacus() -> None:
    """Active pulley discounts PRODUCE energy society-wide and stacks."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    discovered_anatomy = CAMP_ANATOMY.model_copy(update={"discovered": True})
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    discovered_engineering = CAMP_ENGINEERING.model_copy(update={"discovered": True})
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    world = World(
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
            discovered_astronomy,
            discovered_philosophy,
            discovered_logic,
            discovered_rhetoric,
            discovered_medicine,
            discovered_anatomy,
            discovered_hygiene,
            discovered_engineering,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            active_pulley,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = (
        DEFAULT_PRODUCE_ENERGY_COST
        - GUILD_PRODUCE_ENERGY_DISCOUNT
        - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        - ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    )
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_loom_reduces_produce_energy_and_stacks_with_guild_abacus_pulley() -> None:
    """Active loom discounts PRODUCE energy society-wide and stacks."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    active_loom = CAMP_LOOM.model_copy(update={"active": True})
    innovations = tuple(
        active_abacus
        if item.innovation_id == CAMP_ABACUS.innovation_id
        else active_pulley
        if item.innovation_id == CAMP_PULLEY.innovation_id
        else active_loom
        if item.innovation_id == CAMP_LOOM.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = (
        DEFAULT_PRODUCE_ENERGY_COST
        - GUILD_PRODUCE_ENERGY_DISCOUNT
        - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        - ENGINEERING_PRODUCE_ENERGY_DISCOUNT
        - TEXTILES_PRODUCE_ENERGY_DISCOUNT
    )
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_loom_raises_produce_discount_society_wide() -> None:
    """Active loom discounts PRODUCE energy for every agent society-wide."""
    discovered_textiles = CAMP_TEXTILES.model_copy(update={"discovered": True})
    active_loom = CAMP_LOOM.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_textiles
            if item.technology_id == CAMP_TEXTILES.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_loom
            if item.innovation_id == CAMP_LOOM.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = DEFAULT_PRODUCE_ENERGY_COST - TEXTILES_PRODUCE_ENERGY_DISCOUNT
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)
    bare = _world()
    assert census_effects(bare).produce_energy_cost_bps == round(
        DEFAULT_PRODUCE_ENERGY_COST * 10_000
    )


def test_tannery_reduces_produce_energy_and_stacks_with_guild_abacus_loom() -> None:
    """Active tannery discounts PRODUCE energy society-wide and stacks."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    active_loom = CAMP_LOOM.model_copy(update={"active": True})
    active_tannery = CAMP_TANNERY.model_copy(update={"active": True})
    innovations = tuple(
        active_abacus
        if item.innovation_id == CAMP_ABACUS.innovation_id
        else active_pulley
        if item.innovation_id == CAMP_PULLEY.innovation_id
        else active_loom
        if item.innovation_id == CAMP_LOOM.innovation_id
        else active_tannery
        if item.innovation_id == CAMP_TANNERY.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = (
        DEFAULT_PRODUCE_ENERGY_COST
        - GUILD_PRODUCE_ENERGY_DISCOUNT
        - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        - ENGINEERING_PRODUCE_ENERGY_DISCOUNT
        - TEXTILES_PRODUCE_ENERGY_DISCOUNT
        - TANNING_PRODUCE_ENERGY_DISCOUNT
    )
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_tannery_raises_produce_discount_society_wide() -> None:
    """Active tannery discounts PRODUCE energy for every agent society-wide."""
    discovered_tanning = CAMP_TANNING.model_copy(update={"discovered": True})
    active_tannery = CAMP_TANNERY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_tanning
            if item.technology_id == CAMP_TANNING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_tannery
            if item.innovation_id == CAMP_TANNERY.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = DEFAULT_PRODUCE_ENERGY_COST - TANNING_PRODUCE_ENERGY_DISCOUNT
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)
    bare = _world()
    assert census_effects(bare).produce_energy_cost_bps == round(
        DEFAULT_PRODUCE_ENERGY_COST * 10_000
    )


def test_workshop_stacks_with_guild_abacus_and_pulley() -> None:
    """Workshop seat discount stacks with guild, abacus, and pulley."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    discovered_anatomy = CAMP_ANATOMY.model_copy(update={"discovered": True})
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    discovered_engineering = CAMP_ENGINEERING.model_copy(update={"discovered": True})
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
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
            discovered_logic,
            discovered_rhetoric,
            discovered_medicine,
            discovered_anatomy,
            discovered_hygiene,
            discovered_engineering,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            active_pulley,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = (
        DEFAULT_PRODUCE_ENERGY_COST
        - GUILD_PRODUCE_ENERGY_DISCOUNT
        - WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        - ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    )
    assert location_has_active_workshop(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_weaver_reduces_produce_energy_for_colocated_agents() -> None:
    """Active weavers discount PRODUCE energy at their seat location."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert location_has_active_weaver(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - WEAVER_PRODUCE_ENERGY_DISCOUNT)
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - WEAVER_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_weaver(bare, bare.agents[0].location_id) is False


def test_weaver_stacks_with_guild_workshop_abacus_and_pulley() -> None:
    """Weaver seat discount stacks with guild, workshop, abacus, and pulley."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    discovered_anatomy = CAMP_ANATOMY.model_copy(update={"discovered": True})
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    discovered_engineering = CAMP_ENGINEERING.model_copy(update={"discovered": True})
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(2, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
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
            discovered_logic,
            discovered_rhetoric,
            discovered_medicine,
            discovered_anatomy,
            discovered_hygiene,
            discovered_engineering,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            active_pulley,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected = (
        DEFAULT_PRODUCE_ENERGY_COST
        - GUILD_PRODUCE_ENERGY_DISCOUNT
        - WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        - WEAVER_PRODUCE_ENERGY_DISCOUNT
        - MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        - ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    )
    assert location_has_active_weaver(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_fulling_mill_reduces_produce_energy_for_colocated_agents() -> None:
    """Active fulling mills discount PRODUCE energy at their seat location."""
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
    agent = world.agents[0]
    assert location_has_active_fulling_mill(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(
        DEFAULT_PRODUCE_ENERGY_COST - FULLING_MILL_PRODUCE_ENERGY_DISCOUNT
    )
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - FULLING_MILL_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_fulling_mill(bare, bare.agents[0].location_id) is False


def test_fulling_mill_stacks_with_guild_workshop_and_weaver() -> None:
    """Fulling mill seat discount stacks with guild, workshop, and weaver."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(2, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Fulling Mill", InfrastructureKind.FULLING_MILL
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    expected_discount = (
        GUILD_PRODUCE_ENERGY_DISCOUNT
        + WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        + WEAVER_PRODUCE_ENERGY_DISCOUNT
        + FULLING_MILL_PRODUCE_ENERGY_DISCOUNT
    )
    assert location_has_active_fulling_mill(world, agent.location_id) is True
    assert produce_energy_discount(world, agent) == pytest.approx(expected_discount)
    expected = DEFAULT_PRODUCE_ENERGY_COST - expected_discount
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_foundry_reduces_produce_energy_for_residents() -> None:
    """Active foundry cities discount PRODUCE energy for residents at the seat."""
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
    agent = world.agents[0]
    assert location_has_active_foundry(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - FOUNDRY_PRODUCE_ENERGY_DISCOUNT)
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - FOUNDRY_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )


def test_foundry_stacks_with_guild_workshop_abacus_and_pulley() -> None:
    """Foundry seat discount stacks with guild, workshop, abacus, and pulley."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    discovered_anatomy = CAMP_ANATOMY.model_copy(update={"discovered": True})
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    discovered_engineering = CAMP_ENGINEERING.model_copy(update={"discovered": True})
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Foundry", CityKind.FOUNDRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 1, "Camp Workshop", InstitutionKind.WORKSHOP),
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
            discovered_logic,
            discovered_rhetoric,
            discovered_medicine,
            discovered_anatomy,
            discovered_hygiene,
            discovered_engineering,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            active_pulley,
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected_discount = (
        GUILD_PRODUCE_ENERGY_DISCOUNT
        + WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        + FOUNDRY_PRODUCE_ENERGY_DISCOUNT
        + MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        + ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    )
    assert location_has_active_foundry(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(0.0)
    assert census_effects(world).produce_energy_cost_bps == 0
    assert expected_discount == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST)


def test_mill_town_reduces_produce_energy_for_residents() -> None:
    """Active mill town cities discount PRODUCE energy for residents at the seat."""
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
    agent = world.agents[0]
    assert location_has_active_mill_town(world, agent.location_id) is True
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(DEFAULT_PRODUCE_ENERGY_COST - MILL_TOWN_PRODUCE_ENERGY_DISCOUNT)
    assert census_effects(world).produce_energy_cost_bps == round(
        (DEFAULT_PRODUCE_ENERGY_COST - MILL_TOWN_PRODUCE_ENERGY_DISCOUNT) * 10_000
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_mill_town(bare, bare.agents[0].location_id) is False


def test_mill_town_stacks_with_guild_workshop_weaver_and_fulling_mill() -> None:
    """Mill town seat discount stacks with guild, workshop, weaver, fulling mill."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Mill Town", CityKind.MILL_TOWN),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 1, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(2, 0, 1, "Camp Weaver", InstitutionKind.WEAVER),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 1, 1, "Camp Fulling Mill", InfrastructureKind.FULLING_MILL
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected_discount = (
        GUILD_PRODUCE_ENERGY_DISCOUNT
        + WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        + WEAVER_PRODUCE_ENERGY_DISCOUNT
        + FULLING_MILL_PRODUCE_ENERGY_DISCOUNT
        + MILL_TOWN_PRODUCE_ENERGY_DISCOUNT
    )
    assert location_has_active_mill_town(world, agent.location_id) is True
    assert produce_energy_discount(world, agent) == pytest.approx(expected_discount)
    expected = DEFAULT_PRODUCE_ENERGY_COST - expected_discount
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(expected)
    assert census_effects(world).produce_energy_cost_bps == round(expected * 10_000)


def test_customs_stacks_with_guild_workshop_foundry_abacus_and_pulley() -> None:
    """Customs PRODUCE discount stacks with guild, workshop, foundry, abacus, pulley."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_philosophy = CAMP_PHILOSOPHY.model_copy(update={"discovered": True})
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    discovered_rhetoric = CAMP_RHETORIC.model_copy(update={"discovered": True})
    discovered_medicine = CAMP_MEDICINE.model_copy(update={"discovered": True})
    discovered_anatomy = CAMP_ANATOMY.model_copy(update={"discovered": True})
    discovered_hygiene = CAMP_HYGIENE.model_copy(update={"discovered": True})
    discovered_engineering = CAMP_ENGINEERING.model_copy(update={"discovered": True})
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Customs", LawKind.CUSTOMS),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Foundry", CityKind.FOUNDRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 1, "Camp Workshop", InstitutionKind.WORKSHOP),
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
            discovered_logic,
            discovered_rhetoric,
            discovered_medicine,
            discovered_anatomy,
            discovered_hygiene,
            discovered_engineering,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            active_pulley,
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected_discount = (
        GUILD_PRODUCE_ENERGY_DISCOUNT
        + WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        + FOUNDRY_PRODUCE_ENERGY_DISCOUNT
        + CUSTOMS_PRODUCE_ENERGY_DISCOUNT
        + MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        + ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    )
    assert customs_produce_discount_for(world, agent) == CUSTOMS_PRODUCE_ENERGY_DISCOUNT
    assert produce_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(0.0)
    # census_effects produce path omits statute discounts (customs).
    assert census_effects(world).produce_energy_cost_bps == 0


def test_labor_stacks_with_craft_seats_customs_abacus_pulley_and_loom() -> None:
    """Labor PRODUCE discount stacks with craft seats, customs, and tech."""
    discovered = tuple(
        item.model_copy(update={"discovered": True})
        for item in default_technologies()
    )
    active_abacus = CAMP_ABACUS.model_copy(update={"active": True})
    active_pulley = CAMP_PULLEY.model_copy(update={"active": True})
    active_loom = CAMP_LOOM.model_copy(update={"active": True})
    innovations = tuple(
        active_abacus
        if item.innovation_id == CAMP_ABACUS.innovation_id
        else active_pulley
        if item.innovation_id == CAMP_PULLEY.innovation_id
        else active_loom
        if item.innovation_id == CAMP_LOOM.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(
            Law.create(0, 0, "Camp Customs", LawKind.CUSTOMS),
            Law.create(1, 0, "Camp Labor", LawKind.LABOR),
        ),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Foundry", CityKind.FOUNDRY),
        ),
        institutions=(
            Institution.create(0, 0, 1, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(1, 0, 1, "Camp Workshop", InstitutionKind.WORKSHOP),
        ),
        technologies=discovered,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    expected_discount = (
        GUILD_PRODUCE_ENERGY_DISCOUNT
        + WORKSHOP_PRODUCE_ENERGY_DISCOUNT
        + FOUNDRY_PRODUCE_ENERGY_DISCOUNT
        + CUSTOMS_PRODUCE_ENERGY_DISCOUNT
        + LABOR_PRODUCE_ENERGY_DISCOUNT
        + MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
        + ENGINEERING_PRODUCE_ENERGY_DISCOUNT
        + TEXTILES_PRODUCE_ENERGY_DISCOUNT
    )
    assert labor_produce_discount_for(world, agent) == LABOR_PRODUCE_ENERGY_DISCOUNT
    assert produce_energy_discount(world, agent) == pytest.approx(expected_discount)
    assert effective_produce_energy_cost(
        world,
        agent,
        base=DEFAULT_PRODUCE_ENERGY_COST,
    ) == pytest.approx(0.0)
    # census_effects produce path omits statute discounts (customs, labor).
    assert census_effects(world).produce_energy_cost_bps == 0


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


def test_beacon_raises_retrieval_limit_for_colocated_agents() -> None:
    """Active beacons raise the memory retrieval limit at their seat."""
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
    agent = world.agents[0]
    assert location_has_active_beacon(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + BEACON_RETRIEVAL_LIMIT_BONUS
    )
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_beacon(bare, bare.agents[0].location_id) is False
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


def test_plumb_line_raises_retrieval_limit_society_wide() -> None:
    """Active plumb line raises retrieval limit for every agent."""
    discovered_surveying = CAMP_SURVEYING.model_copy(update={"discovered": True})
    active_plumb_line = CAMP_PLUMB_LINE.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_surveying
            if item.technology_id == CAMP_SURVEYING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_plumb_line
            if item.innovation_id == CAMP_PLUMB_LINE.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + SURVEYING_RETRIEVAL_LIMIT_BONUS
    )
    bare = _world()
    assert effective_retrieval_limit(bare, bare.agents[0]) == DEFAULT_RETRIEVAL_LIMIT


def test_plumb_line_stacks_with_star_chart_and_retrieval_seats() -> None:
    """Plumb line retrieval bonus stacks with star chart and retrieval seats."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_surveying = CAMP_SURVEYING.model_copy(update={"discovered": True})
    active_star_chart = CAMP_STAR_CHART.model_copy(update={"active": True})
    active_plumb_line = CAMP_PLUMB_LINE.model_copy(update={"active": True})
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
            CAMP_LOGIC,
            CAMP_RHETORIC,
            CAMP_MEDICINE,
            CAMP_ANATOMY,
            CAMP_HYGIENE,
            CAMP_ENGINEERING,
            CAMP_ARCHITECTURE,
            discovered_surveying,
            CAMP_NAVIGATION,
            CAMP_CARTOGRAPHY,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            CAMP_PULLEY,
            CAMP_BLUEPRINT,
            active_plumb_line,
            CAMP_COMPASS,
            CAMP_MAP,
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT
        + ARCHIVE_RETRIEVAL_LIMIT_BONUS
        + LIBRARY_RETRIEVAL_LIMIT_BONUS
        + OBSERVATORY_RETRIEVAL_LIMIT_BONUS
        + ASTRONOMY_RETRIEVAL_LIMIT_BONUS
        + SURVEYING_RETRIEVAL_LIMIT_BONUS
    )


def test_map_raises_retrieval_limit_society_wide() -> None:
    """Active map raises retrieval limit for every agent."""
    discovered_cartography = CAMP_CARTOGRAPHY.model_copy(update={"discovered": True})
    active_map = CAMP_MAP.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=tuple(
            discovered_cartography
            if item.technology_id == CAMP_CARTOGRAPHY.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_map if item.innovation_id == CAMP_MAP.innovation_id else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    agent = world.agents[0]
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT + CARTOGRAPHY_RETRIEVAL_LIMIT_BONUS
    )
    bare = _world()
    assert effective_retrieval_limit(bare, bare.agents[0]) == DEFAULT_RETRIEVAL_LIMIT


def test_map_stacks_with_star_chart_plumb_line_seats_and_calendar() -> None:
    """Map retrieval bonus stacks with star chart, plumb line, seats, calendar."""
    discovered_pottery = CAMP_POTTERY.model_copy(update={"discovered": True})
    discovered_irrigation = CAMP_IRRIGATION.model_copy(update={"discovered": True})
    discovered_metallurgy = CAMP_METALLURGY.model_copy(update={"discovered": True})
    discovered_writing = CAMP_WRITING.model_copy(update={"discovered": True})
    discovered_math = CAMP_MATHEMATICS.model_copy(update={"discovered": True})
    discovered_astronomy = CAMP_ASTRONOMY.model_copy(update={"discovered": True})
    discovered_surveying = CAMP_SURVEYING.model_copy(update={"discovered": True})
    discovered_cartography = CAMP_CARTOGRAPHY.model_copy(update={"discovered": True})
    active_star_chart = CAMP_STAR_CHART.model_copy(update={"active": True})
    active_plumb_line = CAMP_PLUMB_LINE.model_copy(update={"active": True})
    active_map = CAMP_MAP.model_copy(update={"active": True})
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
            Infrastructure.create(
                1, 0, 1, 1, "Library Beacon", InfrastructureKind.BEACON
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
            CAMP_LOGIC,
            CAMP_RHETORIC,
            CAMP_MEDICINE,
            CAMP_ANATOMY,
            CAMP_HYGIENE,
            CAMP_ENGINEERING,
            CAMP_ARCHITECTURE,
            discovered_surveying,
            CAMP_NAVIGATION,
            discovered_cartography,
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
            CAMP_SYLLOGISM,
            CAMP_ORATION,
            CAMP_REMEDY,
            CAMP_DISSECTION,
            CAMP_ASEPSIS,
            CAMP_PULLEY,
            CAMP_BLUEPRINT,
            active_plumb_line,
            CAMP_COMPASS,
            active_map,
        ),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )
    agent = world.agents[0]
    assert location_has_active_beacon(world, agent.location_id) is True
    assert effective_retrieval_limit(world, agent) == (
        DEFAULT_RETRIEVAL_LIMIT
        + ARCHIVE_RETRIEVAL_LIMIT_BONUS
        + LIBRARY_RETRIEVAL_LIMIT_BONUS
        + OBSERVATORY_RETRIEVAL_LIMIT_BONUS
        + BEACON_RETRIEVAL_LIMIT_BONUS
        + LYCEUM_RETRIEVAL_LIMIT_BONUS
        + ASTRONOMY_RETRIEVAL_LIMIT_BONUS
        + SURVEYING_RETRIEVAL_LIMIT_BONUS
        + CARTOGRAPHY_RETRIEVAL_LIMIT_BONUS
        + CALENDAR_RETRIEVAL_LIMIT_BONUS
    )


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
    """Active syllogism, dissection, and blueprint stack research bonuses."""
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    discovered_anatomy = CAMP_ANATOMY.model_copy(update={"discovered": True})
    discovered_architecture = CAMP_ARCHITECTURE.model_copy(update={"discovered": True})
    active_syllogism = CAMP_SYLLOGISM.model_copy(update={"active": True})
    active_dissection = CAMP_DISSECTION.model_copy(update={"active": True})
    active_blueprint = CAMP_BLUEPRINT.model_copy(update={"active": True})
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
            CAMP_RHETORIC,
            CAMP_MEDICINE,
            discovered_anatomy,
            CAMP_HYGIENE,
            CAMP_ENGINEERING,
            discovered_architecture,
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
            CAMP_ORATION,
            CAMP_REMEDY,
            active_dissection,
            CAMP_ASEPSIS,
            CAMP_PULLEY,
            active_blueprint,
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert research_points_bonus(world) == (
        LOGIC_RESEARCH_POINTS_BONUS
        + ANATOMY_RESEARCH_POINTS_BONUS
        + ARCHITECTURE_RESEARCH_POINTS_BONUS
    )
    assert (
        effective_research_points_per_tick(world, base=DEFAULT_POINTS_PER_TICK)
        == DEFAULT_POINTS_PER_TICK
        + LOGIC_RESEARCH_POINTS_BONUS
        + ANATOMY_RESEARCH_POINTS_BONUS
        + ARCHITECTURE_RESEARCH_POINTS_BONUS
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


def test_harbor_discounts_market_fee_at_seat() -> None:
    """Active harbor cities reduce market fee by 1 at their seat (floor 0)."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_harbor(world, 0) is True
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - HARBOR_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
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
    assert location_has_active_harbor(bare, 0) is False
    assert effective_market_fee(bare, 0) == 2


def test_harbor_stacks_with_bureaucracy_market_fee_discount() -> None:
    """Harbor and bureaucracy market-fee discounts stack at the same seat."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=3),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_harbor(world, 0) is True
    assert location_has_active_bureaucracy(world, 0) is True
    assert market_fee_for(world, 0) == 3
    assert effective_market_fee(world, 0) == (
        3 - BUREAUCRACY_MARKET_FEE_DISCOUNT - HARBOR_MARKET_FEE_DISCOUNT
    )


def test_merchant_discounts_market_fee_at_seat() -> None:
    """Active merchant reduces market fee by 1 at its seat (floor 0)."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_merchant(world, 0) is True
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - MERCHANT_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
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
    assert location_has_active_merchant(bare, 0) is False
    assert effective_market_fee(bare, 0) == 2


def test_merchant_stacks_with_bureaucracy_and_harbor_market_fee_discount() -> None:
    """Merchant, bureaucracy, and harbor market-fee discounts stack."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=4),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(1, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_harbor(world, 0) is True
    assert location_has_active_bureaucracy(world, 0) is True
    assert location_has_active_merchant(world, 0) is True
    assert market_fee_for(world, 0) == 4
    assert effective_market_fee(world, 0) == (
        4
        - BUREAUCRACY_MARKET_FEE_DISCOUNT
        - HARBOR_MARKET_FEE_DISCOUNT
        - MERCHANT_MARKET_FEE_DISCOUNT
    )


def test_dyer_discounts_market_fee_at_seat() -> None:
    """Active dyer reduces market fee by 1 at its seat (floor 0)."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_dyer(world, 0) is True
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - DYER_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Dyer", InstitutionKind.DYER),
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
    assert location_has_active_dyer(bare, 0) is False
    assert effective_market_fee(bare, 0) == 2


def test_dyer_stacks_with_bureaucracy_harbor_and_merchant_market_fee_discount() -> None:
    """Dyer, bureaucracy, harbor, and merchant market-fee discounts stack."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=5),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(1, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(2, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_harbor(world, 0) is True
    assert location_has_active_bureaucracy(world, 0) is True
    assert location_has_active_merchant(world, 0) is True
    assert location_has_active_dyer(world, 0) is True
    assert market_fee_for(world, 0) == 5
    assert effective_market_fee(world, 0) == (
        5
        - BUREAUCRACY_MARKET_FEE_DISCOUNT
        - HARBOR_MARKET_FEE_DISCOUNT
        - MERCHANT_MARKET_FEE_DISCOUNT
        - DYER_MARKET_FEE_DISCOUNT
    )


def test_mordant_discounts_market_fee_society_wide() -> None:
    """Active mordant reduces market fee by 1 society-wide (floor 0)."""
    discovered_dyeing = CAMP_DYEING.model_copy(update={"discovered": True})
    active_mordant = CAMP_MORDANT.model_copy(update={"active": True})
    technologies = tuple(
        discovered_dyeing
        if item.technology_id == CAMP_DYEING.technology_id
        else item
        for item in default_technologies()
    )
    innovations = tuple(
        active_mordant
        if item.innovation_id == CAMP_MORDANT.innovation_id
        else item
        for item in default_innovations()
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        technologies=technologies,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - DYEING_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
        technologies=technologies,
        innovations=innovations,
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert effective_market_fee(floored, 0) == 0
    bare = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        technologies=default_technologies(),
        innovations=default_innovations(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert effective_market_fee(bare, 0) == 2


def test_mordant_stacks_with_bureaucracy_harbor_merchant_and_dyer() -> None:
    """Mordant, bureaucracy, harbor, merchant, and dyer discounts all stack."""
    discovered_dyeing = CAMP_DYEING.model_copy(update={"discovered": True})
    active_mordant = CAMP_MORDANT.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=6),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(1, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(2, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
        technologies=tuple(
            discovered_dyeing
            if item.technology_id == CAMP_DYEING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_mordant
            if item.innovation_id == CAMP_MORDANT.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_harbor(world, 0) is True
    assert location_has_active_bureaucracy(world, 0) is True
    assert location_has_active_merchant(world, 0) is True
    assert location_has_active_dyer(world, 0) is True
    assert market_fee_for(world, 0) == 6
    assert effective_market_fee(world, 0) == (
        6
        - BUREAUCRACY_MARKET_FEE_DISCOUNT
        - HARBOR_MARKET_FEE_DISCOUNT
        - MERCHANT_MARKET_FEE_DISCOUNT
        - DYER_MARKET_FEE_DISCOUNT
        - DYEING_MARKET_FEE_DISCOUNT
    )


def test_warehouse_discounts_market_fee_at_seat() -> None:
    """Active warehouse reduces market fee by 1 at its seat (floor 0)."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Warehouse", InfrastructureKind.WAREHOUSE
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_warehouse(world, 0) is True
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - WAREHOUSE_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Warehouse", InfrastructureKind.WAREHOUSE
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
    assert location_has_active_warehouse(bare, 0) is False
    assert effective_market_fee(bare, 0) == 2


def test_warehouse_stacks_with_all_market_fee_discounts() -> None:
    """Warehouse stacks with bureaucracy, harbor, merchant, dyer, and mordant."""
    discovered_dyeing = CAMP_DYEING.model_copy(update={"discovered": True})
    active_mordant = CAMP_MORDANT.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=7),),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(1, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(2, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Warehouse", InfrastructureKind.WAREHOUSE
            ),
        ),
        technologies=tuple(
            discovered_dyeing
            if item.technology_id == CAMP_DYEING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_mordant
            if item.innovation_id == CAMP_MORDANT.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_harbor(world, 0) is True
    assert location_has_active_bureaucracy(world, 0) is True
    assert location_has_active_merchant(world, 0) is True
    assert location_has_active_dyer(world, 0) is True
    assert location_has_active_warehouse(world, 0) is True
    assert market_fee_for(world, 0) == 7
    assert effective_market_fee(world, 0) == (
        7
        - BUREAUCRACY_MARKET_FEE_DISCOUNT
        - HARBOR_MARKET_FEE_DISCOUNT
        - MERCHANT_MARKET_FEE_DISCOUNT
        - DYER_MARKET_FEE_DISCOUNT
        - DYEING_MARKET_FEE_DISCOUNT
        - WAREHOUSE_MARKET_FEE_DISCOUNT
    )


def test_sumptuary_stacks_with_all_market_fee_discounts() -> None:
    """SUMPTUARY stacks with seats, dyer, mordant, and warehouse discounts."""
    discovered_dyeing = CAMP_DYEING.model_copy(update={"discovered": True})
    active_mordant = CAMP_MORDANT.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR),),
        laws=(
            Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=9),
            Law.create(1, 0, "Camp Sumptuary", LawKind.SUMPTUARY),
        ),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(1, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(2, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Warehouse", InfrastructureKind.WAREHOUSE
            ),
        ),
        technologies=tuple(
            discovered_dyeing
            if item.technology_id == CAMP_DYEING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_mordant
            if item.innovation_id == CAMP_MORDANT.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert market_fee_for(world, 0) == 9
    assert effective_market_fee(world, 0) == (
        9
        - BUREAUCRACY_MARKET_FEE_DISCOUNT
        - HARBOR_MARKET_FEE_DISCOUNT
        - MERCHANT_MARKET_FEE_DISCOUNT
        - DYER_MARKET_FEE_DISCOUNT
        - DYEING_MARKET_FEE_DISCOUNT
        - WAREHOUSE_MARKET_FEE_DISCOUNT
        - SUMPTUARY_MARKET_FEE_DISCOUNT
    )


def test_emporium_discounts_market_fee_at_seat() -> None:
    """Active emporium cities reduce market fee by 1 at their seat (floor 0)."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Emporium", CityKind.EMPORIUM),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_emporium(world, 0) is True
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 2 - EMPORIUM_MARKET_FEE_DISCOUNT
    floored = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Emporium", CityKind.EMPORIUM),),
        laws=(Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1),),
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
    assert location_has_active_emporium(bare, 0) is False
    assert effective_market_fee(bare, 0) == 2


def test_emporium_stacks_with_all_market_fee_discounts() -> None:
    """Emporium stacks with bureaucracy, merchant, dyer, mordant, warehouse, sumptuary.

    An emporium occupies the seat's single city slot, so a harbor cannot
    also stand there; every other market-fee discount still stacks.
    """
    discovered_dyeing = CAMP_DYEING.model_copy(update={"discovered": True})
    active_mordant = CAMP_MORDANT.model_copy(update={"active": True})
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp Emporium", CityKind.EMPORIUM),),
        laws=(
            Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=9),
            Law.create(1, 0, "Camp Sumptuary", LawKind.SUMPTUARY),
        ),
        institutions=(
            Institution.create(
                0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(1, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(2, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Warehouse", InfrastructureKind.WAREHOUSE
            ),
        ),
        technologies=tuple(
            discovered_dyeing
            if item.technology_id == CAMP_DYEING.technology_id
            else item
            for item in default_technologies()
        ),
        innovations=tuple(
            active_mordant
            if item.innovation_id == CAMP_MORDANT.innovation_id
            else item
            for item in default_innovations()
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert location_has_active_emporium(world, 0) is True
    assert location_has_active_bureaucracy(world, 0) is True
    assert location_has_active_merchant(world, 0) is True
    assert location_has_active_dyer(world, 0) is True
    assert location_has_active_warehouse(world, 0) is True
    assert market_fee_for(world, 0) == 9
    assert effective_market_fee(world, 0) == (
        9
        - BUREAUCRACY_MARKET_FEE_DISCOUNT
        - MERCHANT_MARKET_FEE_DISCOUNT
        - DYER_MARKET_FEE_DISCOUNT
        - DYEING_MARKET_FEE_DISCOUNT
        - WAREHOUSE_MARKET_FEE_DISCOUNT
        - EMPORIUM_MARKET_FEE_DISCOUNT
        - SUMPTUARY_MARKET_FEE_DISCOUNT
    )
