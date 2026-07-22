"""Unit tests for institution models, helpers, and world rules."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_COUNCIL,
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Government,
    Health,
    Institution,
    InstitutionKind,
    SimulationConfig,
    World,
    census_institutions,
    create_institution,
    credit_institution_budget,
    debit_institution_budget,
    default_institutions,
    default_world_map,
    dissolve_institution,
    fund_institution_from_treasury,
    institution_at,
    institution_budget_total,
    institution_by_id,
    institutions_for,
    next_institution_id,
    set_institution_active,
    set_officer,
    society_money_total,
)


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (Government.create(0, "Camp", 0, (0,)),),
    institutions: tuple[Institution, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        institutions=institutions,
        agents=agents,
    )


def test_default_institutions_seed_camp_council() -> None:
    """Canonical institution is an active council and no later kinds."""
    assert default_institutions() == (CAMP_COUNCIL,)
    assert CAMP_COUNCIL.kind is InstitutionKind.COUNCIL
    assert CAMP_COUNCIL.active is True
    assert CAMP_COUNCIL.officer_id is None
    assert CAMP_COUNCIL.budget == 0
    assert CAMP_COUNCIL.government_id.value == CAMP_GOVERNMENT.government_id.value
    assert CAMP_COUNCIL.location_id.value == CAMP_LOCATION.location_id.value
    assert all(
        item.kind is not InstitutionKind.ARCHIVE for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.BUREAUCRACY for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.ACADEMY for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.TEMPLE for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.SCHOOL for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.LYCEUM for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.HOSPITAL for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.APOTHECARY for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.COLLEGIUM for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.ARCHITECT for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.CARAVAN for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.MERCHANT for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.CARTOGRAPHER for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.GRANARY for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.HUSBANDMAN for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.AGRONOMIST for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.WEAVER for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.DYER for item in default_institutions()
    )
    assert all(
        item.kind is not InstitutionKind.TAILOR for item in default_institutions()
    )


def test_create_and_lookup_institution() -> None:
    """create_institution inserts sorted ids and supports lookups."""
    world = _world(Agent.create(agent_id=0, name="A"))
    created = create_institution(
        world,
        Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
    )
    assert created is not None
    assert institution_by_id(created, 0) is not None
    assert institutions_for(created, 0)[0].name == "Council"
    assert institution_at(created, 0) is not None
    assert next_institution_id(created).value == 1


def test_create_rejects_second_active_council() -> None:
    """At most one active council per government."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(Institution.create(0, 0, 0, "A", InstitutionKind.COUNCIL),),
    )
    assert (
        create_institution(
            world,
            Institution.create(1, 0, 0, "B", InstitutionKind.COUNCIL),
        )
        is None
    )


def test_create_guild_alongside_council() -> None:
    """Guilds coexist with councils; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),),
    )
    with_guild = create_institution(
        world,
        Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
    )
    assert with_guild is not None
    assert with_guild.institutions[1].kind is InstitutionKind.GUILD
    snap = census_institutions(with_guild)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 0
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 2
    assert (
        create_institution(
            with_guild,
            Institution.create(2, 0, 0, "Second Guild", InstitutionKind.GUILD),
        )
        is None
    )


def test_create_archive_alongside_council_and_guild() -> None:
    """Archives coexist with councils and guilds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        ),
    )
    with_archive = create_institution(
        world,
        Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
    )
    assert with_archive is not None
    assert with_archive.institutions[2].kind is InstitutionKind.ARCHIVE
    snap = census_institutions(with_archive)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 0
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 3
    assert (
        create_institution(
            with_archive,
            Institution.create(3, 0, 0, "Second Archive", InstitutionKind.ARCHIVE),
        )
        is None
    )


def test_create_bureaucracy_alongside_other_kinds() -> None:
    """Bureaucracies coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
        ),
    )
    with_bureaucracy = create_institution(
        world,
        Institution.create(3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY),
    )
    assert with_bureaucracy is not None
    assert with_bureaucracy.institutions[3].kind is InstitutionKind.BUREAUCRACY
    snap = census_institutions(with_bureaucracy)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 0
    assert snap.active_temple_count == 0
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 4
    assert (
        create_institution(
            with_bureaucracy,
            Institution.create(
                4, 0, 0, "Second Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
        )
        is None
    )


def test_create_academy_alongside_other_kinds() -> None:
    """Academies coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
        ),
    )
    with_academy = create_institution(
        world,
        Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
    )
    assert with_academy is not None
    assert with_academy.institutions[4].kind is InstitutionKind.ACADEMY
    snap = census_institutions(with_academy)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 0
    assert snap.active_school_count == 0
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 5
    assert (
        create_institution(
            with_academy,
            Institution.create(5, 0, 0, "Second Academy", InstitutionKind.ACADEMY),
        )
        is None
    )


def test_create_temple_alongside_other_kinds() -> None:
    """Temples coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
        ),
    )
    with_temple = create_institution(
        world,
        Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
    )
    assert with_temple is not None
    assert with_temple.institutions[5].kind is InstitutionKind.TEMPLE
    snap = census_institutions(with_temple)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 0
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 6
    assert (
        create_institution(
            with_temple,
            Institution.create(6, 0, 0, "Second Temple", InstitutionKind.TEMPLE),
        )
        is None
    )


def test_create_school_alongside_other_kinds() -> None:
    """Schools coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
        ),
    )
    with_school = create_institution(
        world,
        Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
    )
    assert with_school is not None
    assert with_school.institutions[6].kind is InstitutionKind.SCHOOL
    snap = census_institutions(with_school)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 1
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 7
    assert (
        create_institution(
            with_school,
            Institution.create(7, 0, 0, "Second School", InstitutionKind.SCHOOL),
        )
        is None
    )


def test_create_lyceum_alongside_other_kinds() -> None:
    """Lyceums coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
        ),
    )
    with_lyceum = create_institution(
        world,
        Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
    )
    assert with_lyceum is not None
    assert with_lyceum.institutions[7].kind is InstitutionKind.LYCEUM
    snap = census_institutions(with_lyceum)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 1
    assert snap.active_lyceum_count == 1
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 8
    assert (
        create_institution(
            with_lyceum,
            Institution.create(8, 0, 0, "Second Lyceum", InstitutionKind.LYCEUM),
        )
        is None
    )


def test_create_hospital_alongside_other_kinds() -> None:
    """Hospitals coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
        ),
    )
    with_hospital = create_institution(
        world,
        Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
    )
    assert with_hospital is not None
    assert with_hospital.institutions[8].kind is InstitutionKind.HOSPITAL
    snap = census_institutions(with_hospital)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 1
    assert snap.active_lyceum_count == 1
    assert snap.active_hospital_count == 1
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 9
    assert (
        create_institution(
            with_hospital,
            Institution.create(9, 0, 0, "Second Hospital", InstitutionKind.HOSPITAL),
        )
        is None
    )


def test_create_apothecary_alongside_other_kinds() -> None:
    """Apothecaries coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
        ),
    )
    with_apothecary = create_institution(
        world,
        Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
    )
    assert with_apothecary is not None
    assert with_apothecary.institutions[9].kind is InstitutionKind.APOTHECARY
    snap = census_institutions(with_apothecary)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 1
    assert snap.active_lyceum_count == 1
    assert snap.active_hospital_count == 1
    assert snap.active_apothecary_count == 1
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 10
    assert (
        create_institution(
            with_apothecary,
            Institution.create(
                10, 0, 0, "Second Apothecary", InstitutionKind.APOTHECARY
            ),
        )
        is None
    )


def test_create_collegium_alongside_other_kinds() -> None:
    """Collegia coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
        ),
    )
    with_collegium = create_institution(
        world,
        Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
    )
    assert with_collegium is not None
    assert with_collegium.institutions[10].kind is InstitutionKind.COLLEGIUM
    snap = census_institutions(with_collegium)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 1
    assert snap.active_lyceum_count == 1
    assert snap.active_hospital_count == 1
    assert snap.active_apothecary_count == 1
    assert snap.active_collegium_count == 1
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 11
    assert (
        create_institution(
            with_collegium,
            Institution.create(11, 0, 0, "Second Collegium", InstitutionKind.COLLEGIUM),
        )
        is None
    )


def test_create_workshop_alongside_other_kinds() -> None:
    """Workshops coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
        ),
    )
    with_workshop = create_institution(
        world,
        Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
    )
    assert with_workshop is not None
    assert with_workshop.institutions[11].kind is InstitutionKind.WORKSHOP
    snap = census_institutions(with_workshop)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_archive_count == 1
    assert snap.active_bureaucracy_count == 1
    assert snap.active_academy_count == 1
    assert snap.active_temple_count == 1
    assert snap.active_school_count == 1
    assert snap.active_lyceum_count == 1
    assert snap.active_hospital_count == 1
    assert snap.active_apothecary_count == 1
    assert snap.active_collegium_count == 1
    assert snap.active_workshop_count == 1
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 12
    assert (
        create_institution(
            with_workshop,
            Institution.create(12, 0, 0, "Second Workshop", InstitutionKind.WORKSHOP),
        )
        is None
    )


def test_create_mason_alongside_other_kinds() -> None:
    """Masons coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
        ),
    )
    with_mason = create_institution(
        world,
        Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
    )
    assert with_mason is not None
    assert with_mason.institutions[12].kind is InstitutionKind.MASON
    snap = census_institutions(with_mason)
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 1
    assert snap.active_workshop_count == 1
    assert snap.active_mason_count == 1
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 13
    assert (
        create_institution(
            with_mason,
            Institution.create(13, 0, 0, "Second Mason", InstitutionKind.MASON),
        )
        is None
    )


def test_create_architect_alongside_other_kinds() -> None:
    """Architects coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
        ),
    )
    with_architect = create_institution(
        world,
        Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
    )
    assert with_architect is not None
    assert with_architect.institutions[13].kind is InstitutionKind.ARCHITECT
    snap = census_institutions(with_architect)
    assert snap.active_council_count == 1
    assert snap.active_mason_count == 1
    assert snap.active_architect_count == 1
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 14
    assert (
        create_institution(
            with_architect,
            Institution.create(14, 0, 0, "Second Architect", InstitutionKind.ARCHITECT),
        )
        is None
    )


def test_create_caravan_alongside_other_kinds() -> None:
    """Caravans coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
        ),
    )
    with_caravan = create_institution(
        world,
        Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
    )
    assert with_caravan is not None
    assert with_caravan.institutions[14].kind is InstitutionKind.CARAVAN
    snap = census_institutions(with_caravan)
    assert snap.active_council_count == 1
    assert snap.active_architect_count == 1
    assert snap.active_caravan_count == 1
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 15
    assert (
        create_institution(
            with_caravan,
            Institution.create(15, 0, 0, "Second Caravan", InstitutionKind.CARAVAN),
        )
        is None
    )


def test_create_merchant_alongside_other_kinds() -> None:
    """Merchants coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
        ),
    )
    with_merchant = create_institution(
        world,
        Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
    )
    assert with_merchant is not None
    assert with_merchant.institutions[15].kind is InstitutionKind.MERCHANT
    snap = census_institutions(with_merchant)
    assert snap.active_council_count == 1
    assert snap.active_caravan_count == 1
    assert snap.active_merchant_count == 1
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 16
    assert (
        create_institution(
            with_merchant,
            Institution.create(16, 0, 0, "Second Merchant", InstitutionKind.MERCHANT),
        )
        is None
    )


def test_create_cartographer_alongside_other_kinds() -> None:
    """Cartographers coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
        ),
    )
    with_cartographer = create_institution(
        world,
        Institution.create(16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER),
    )
    assert with_cartographer is not None
    assert with_cartographer.institutions[16].kind is InstitutionKind.CARTOGRAPHER
    snap = census_institutions(with_cartographer)
    assert snap.active_council_count == 1
    assert snap.active_merchant_count == 1
    assert snap.active_cartographer_count == 1
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 17
    assert (
        create_institution(
            with_cartographer,
            Institution.create(
                17, 0, 0, "Second Cartographer", InstitutionKind.CARTOGRAPHER
            ),
        )
        is None
    )


def test_create_granary_alongside_other_kinds() -> None:
    """Granaries coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
        ),
    )
    with_granary = create_institution(
        world,
        Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
    )
    assert with_granary is not None
    assert with_granary.institutions[17].kind is InstitutionKind.GRANARY
    snap = census_institutions(with_granary)
    assert snap.active_council_count == 1
    assert snap.active_cartographer_count == 1
    assert snap.active_granary_count == 1
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 18
    assert (
        create_institution(
            with_granary,
            Institution.create(18, 0, 0, "Second Granary", InstitutionKind.GRANARY),
        )
        is None
    )


def test_create_husbandman_alongside_other_kinds() -> None:
    """Husbandmen coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
        ),
    )
    with_husbandman = create_institution(
        world,
        Institution.create(18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN),
    )
    assert with_husbandman is not None
    assert with_husbandman.institutions[18].kind is InstitutionKind.HUSBANDMAN
    snap = census_institutions(with_husbandman)
    assert snap.active_council_count == 1
    assert snap.active_granary_count == 1
    assert snap.active_husbandman_count == 1
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_count == 19
    assert (
        create_institution(
            with_husbandman,
            Institution.create(
                19, 0, 0, "Second Husbandman", InstitutionKind.HUSBANDMAN
            ),
        )
        is None
    )


def test_create_agronomist_alongside_other_kinds() -> None:
    """Agronomists coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(
                18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN
            ),
        ),
    )
    with_agronomist = create_institution(
        world,
        Institution.create(19, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST),
    )
    assert with_agronomist is not None
    assert with_agronomist.institutions[19].kind is InstitutionKind.AGRONOMIST
    snap = census_institutions(with_agronomist)
    assert snap.active_council_count == 1
    assert snap.active_husbandman_count == 1
    assert snap.active_agronomist_count == 1
    assert snap.active_weaver_count == 0
    assert snap.active_count == 20
    assert (
        create_institution(
            with_agronomist,
            Institution.create(
                20, 0, 0, "Second Agronomist", InstitutionKind.AGRONOMIST
            ),
        )
        is None
    )


def test_create_weaver_alongside_other_kinds() -> None:
    """Weavers coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(
                18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN
            ),
            Institution.create(
                19, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
        ),
    )
    with_weaver = create_institution(
        world,
        Institution.create(20, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
    )
    assert with_weaver is not None
    assert with_weaver.institutions[20].kind is InstitutionKind.WEAVER
    snap = census_institutions(with_weaver)
    assert snap.active_council_count == 1
    assert snap.active_agronomist_count == 1
    assert snap.active_weaver_count == 1
    assert snap.active_count == 21
    assert (
        create_institution(
            with_weaver,
            Institution.create(21, 0, 0, "Second Weaver", InstitutionKind.WEAVER),
        )
        is None
    )


def test_create_dyer_alongside_other_kinds() -> None:
    """Dyers coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(
                18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN
            ),
            Institution.create(
                19, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(20, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
        ),
    )
    with_dyer = create_institution(
        world,
        Institution.create(21, 0, 0, "Camp Dyer", InstitutionKind.DYER),
    )
    assert with_dyer is not None
    assert with_dyer.institutions[21].kind is InstitutionKind.DYER
    snap = census_institutions(with_dyer)
    assert snap.active_council_count == 1
    assert snap.active_weaver_count == 1
    assert snap.active_dyer_count == 1
    assert snap.active_count == 22
    assert (
        create_institution(
            with_dyer,
            Institution.create(22, 0, 0, "Second Dyer", InstitutionKind.DYER),
        )
        is None
    )


def test_create_tailor_alongside_other_kinds() -> None:
    """Tailors coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(
                18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN
            ),
            Institution.create(
                19, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(20, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
            Institution.create(21, 0, 0, "Camp Dyer", InstitutionKind.DYER),
        ),
    )
    with_tailor = create_institution(
        world,
        Institution.create(22, 0, 0, "Camp Tailor", InstitutionKind.TAILOR),
    )
    assert with_tailor is not None
    assert with_tailor.institutions[22].kind is InstitutionKind.TAILOR
    snap = census_institutions(with_tailor)
    assert snap.active_council_count == 1
    assert snap.active_dyer_count == 1
    assert snap.active_tailor_count == 1
    assert snap.active_count == 23
    assert (
        create_institution(
            with_tailor,
            Institution.create(23, 0, 0, "Second Tailor", InstitutionKind.TAILOR),
        )
        is None
    )


def test_create_miner_alongside_other_kinds() -> None:
    """Miners coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(
                18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN
            ),
            Institution.create(
                19, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(20, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
            Institution.create(21, 0, 0, "Camp Dyer", InstitutionKind.DYER),
            Institution.create(22, 0, 0, "Camp Tailor", InstitutionKind.TAILOR),
        ),
    )
    with_miner = create_institution(
        world,
        Institution.create(23, 0, 0, "Camp Miner", InstitutionKind.MINER),
    )
    assert with_miner is not None
    assert with_miner.institutions[23].kind is InstitutionKind.MINER
    snap = census_institutions(with_miner)
    assert snap.active_council_count == 1
    assert snap.active_mason_count == 1
    assert snap.active_tailor_count == 1
    assert snap.active_miner_count == 1
    assert snap.active_count == 24
    assert (
        create_institution(
            with_miner,
            Institution.create(24, 0, 0, "Second Miner", InstitutionKind.MINER),
        )
        is None
    )


def test_create_smelter_alongside_other_kinds() -> None:
    """Smelters coexist with other kinds; census counts each kind."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),
            Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
            Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
            Institution.create(
                3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
            ),
            Institution.create(4, 0, 0, "Camp Academy", InstitutionKind.ACADEMY),
            Institution.create(5, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
            Institution.create(6, 0, 0, "Camp School", InstitutionKind.SCHOOL),
            Institution.create(7, 0, 0, "Camp Lyceum", InstitutionKind.LYCEUM),
            Institution.create(8, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
            Institution.create(9, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY),
            Institution.create(10, 0, 0, "Camp Collegium", InstitutionKind.COLLEGIUM),
            Institution.create(11, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
            Institution.create(12, 0, 0, "Camp Mason", InstitutionKind.MASON),
            Institution.create(13, 0, 0, "Camp Architect", InstitutionKind.ARCHITECT),
            Institution.create(14, 0, 0, "Camp Caravan", InstitutionKind.CARAVAN),
            Institution.create(15, 0, 0, "Camp Merchant", InstitutionKind.MERCHANT),
            Institution.create(
                16, 0, 0, "Camp Cartographer", InstitutionKind.CARTOGRAPHER
            ),
            Institution.create(17, 0, 0, "Camp Granary", InstitutionKind.GRANARY),
            Institution.create(
                18, 0, 0, "Camp Husbandman", InstitutionKind.HUSBANDMAN
            ),
            Institution.create(
                19, 0, 0, "Camp Agronomist", InstitutionKind.AGRONOMIST
            ),
            Institution.create(20, 0, 0, "Camp Weaver", InstitutionKind.WEAVER),
            Institution.create(21, 0, 0, "Camp Dyer", InstitutionKind.DYER),
            Institution.create(22, 0, 0, "Camp Tailor", InstitutionKind.TAILOR),
            Institution.create(23, 0, 0, "Camp Miner", InstitutionKind.MINER),
        ),
    )
    with_smelter = create_institution(
        world,
        Institution.create(24, 0, 0, "Camp Smelter", InstitutionKind.SMELTER),
    )
    assert with_smelter is not None
    assert with_smelter.institutions[24].kind is InstitutionKind.SMELTER
    snap = census_institutions(with_smelter)
    assert snap.active_council_count == 1
    assert snap.active_weaver_count == 1
    assert snap.active_miner_count == 1
    assert snap.active_smelter_count == 1
    assert snap.active_count == 25
    assert (
        create_institution(
            with_smelter,
            Institution.create(25, 0, 0, "Second Smelter", InstitutionKind.SMELTER),
        )
        is None
    )


def test_dissolve_and_reactivate() -> None:
    """Soft dissolve frees the active-kind slot for reactivation."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(Institution.create(0, 0, 0, "A", InstitutionKind.COUNCIL),),
    )
    dissolved = dissolve_institution(world, 0)
    assert dissolved is not None
    assert dissolved.institutions[0].active is False
    recreated = create_institution(
        dissolved,
        Institution.create(1, 0, 0, "B", InstitutionKind.COUNCIL),
    )
    assert recreated is not None
    assert set_institution_active(recreated, 0, True) is None


def test_set_officer_requires_living_subject() -> None:
    """Officers must be alive subjects inside the government jurisdiction."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),),
    )
    staffed = set_officer(world, 0, 0)
    assert staffed is not None
    assert staffed.institutions[0].officer_id is not None
    assert staffed.institutions[0].officer_id.value == 0

    dead = staffed.agents[0].model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    staffed = staffed.with_agent(dead)
    assert set_officer(staffed, 0, 0) is None
    cleared = set_officer(staffed, 0, None)
    assert cleared is not None
    assert cleared.institutions[0].officer_id is None


def test_census_institutions_counts() -> None:
    """Census aggregates active/staffed stats without mutation."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(
            Institution.create(0, 0, 0, "Active", InstitutionKind.COUNCIL),
            Institution.create(
                1, 0, 0, "Inactive", InstitutionKind.COUNCIL, active=False
            ),
        ),
    )
    world = set_officer(world, 0, 0)
    assert world is not None
    snap = census_institutions(world)
    assert snap.institution_count == 2
    assert snap.active_count == 1
    assert snap.inactive_count == 1
    assert snap.governments_with_institutions == 1
    assert snap.staffed_count == 1
    assert snap.vacant_officer_count == 1
    assert snap.active_council_count == 1
    assert snap.active_guild_count == 0
    assert snap.active_archive_count == 0
    assert snap.active_bureaucracy_count == 0
    assert snap.active_academy_count == 0
    assert snap.active_temple_count == 0
    assert snap.active_school_count == 0
    assert snap.active_lyceum_count == 0
    assert snap.active_hospital_count == 0
    assert snap.active_apothecary_count == 0
    assert snap.active_collegium_count == 0
    assert snap.active_workshop_count == 0
    assert snap.active_mason_count == 0
    assert snap.active_architect_count == 0
    assert snap.active_caravan_count == 0
    assert snap.active_merchant_count == 0
    assert snap.active_cartographer_count == 0
    assert snap.active_granary_count == 0
    assert snap.active_husbandman_count == 0
    assert snap.active_agronomist_count == 0
    assert snap.active_weaver_count == 0
    assert snap.active_dyer_count == 0
    assert snap.active_tailor_count == 0
    assert snap.active_miner_count == 0
    assert snap.active_smelter_count == 0
    assert snap.total_budget == 0
    assert snap.funded_count == 0
    assert census_institutions(world) == snap


def test_fund_institution_from_treasury_moves_money() -> None:
    """Funding debits the government treasury and credits the institution."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=10),
        governments=(Government.create(0, "Camp", 0, (0,), treasury=5),),
        institutions=(Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),),
    )
    initial = society_money_total(world)
    funded = fund_institution_from_treasury(world, 0, 3)
    assert funded is not None
    assert funded.governments[0].treasury == 2
    assert funded.institutions[0].budget == 3
    assert institution_budget_total(funded) == 3
    assert society_money_total(funded) == initial
    snap = census_institutions(funded)
    assert snap.total_budget == 3
    assert snap.funded_count == 1

    assert fund_institution_from_treasury(funded, 0, 9) is None
    assert fund_institution_from_treasury(world, 0, 0) is None
    dissolved = dissolve_institution(world, 0)
    assert dissolved is not None
    assert fund_institution_from_treasury(dissolved, 0, 1) is None


def test_credit_and_debit_institution_budget() -> None:
    """Direct budget helpers reject non-positive and overdraft amounts."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        institutions=(Institution.create(0, 0, 0, "Council", InstitutionKind.COUNCIL),),
    )
    credited = credit_institution_budget(world, 0, 4)
    assert credited is not None
    assert credited.institutions[0].budget == 4
    assert debit_institution_budget(credited, 0, 5) is None
    debited = debit_institution_budget(credited, 0, 2)
    assert debited is not None
    assert debited.institutions[0].budget == 2
    assert credit_institution_budget(world, 0, 0) is None


def test_world_rejects_seat_outside_jurisdiction() -> None:
    """Institution seats must lie inside the parent government."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=(CAMP_LOCATION,),
            governments=(Government.create(0, "Camp", 0, (0,)),),
            institutions=(Institution.create(0, 0, 1, "Bad", InstitutionKind.COUNCIL),),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_factory_shaped_defaults_validate() -> None:
    """Factory-shaped governments and institutions validate together."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        governments=(CAMP_GOVERNMENT,),
        institutions=default_institutions(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert world.institutions[0].name == "Camp Council"
