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
    assert snap.active_count == 8
    assert (
        create_institution(
            with_lyceum,
            Institution.create(8, 0, 0, "Second Lyceum", InstitutionKind.LYCEUM),
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
