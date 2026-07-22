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
    default_institutions,
    default_world_map,
    dissolve_institution,
    institution_at,
    institution_by_id,
    institutions_for,
    next_institution_id,
    set_institution_active,
    set_officer,
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
    """Canonical institution is an active council at the camp."""
    assert default_institutions() == (CAMP_COUNCIL,)
    assert CAMP_COUNCIL.kind is InstitutionKind.COUNCIL
    assert CAMP_COUNCIL.active is True
    assert CAMP_COUNCIL.officer_id is None
    assert CAMP_COUNCIL.government_id.value == CAMP_GOVERNMENT.government_id.value
    assert CAMP_COUNCIL.location_id.value == CAMP_LOCATION.location_id.value


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
    assert census_institutions(world) == snap


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
