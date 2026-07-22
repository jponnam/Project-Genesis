"""Unit tests for government models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Government,
    Health,
    Location,
    LocationKind,
    SimulationConfig,
    World,
    census_governments,
    credit_government_treasury,
    debit_government_treasury,
    default_governments,
    default_world_map,
    government_at,
    set_leader,
    subject_count,
)


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (),
    locations: tuple[Location, ...] | None = None,
) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=locations if locations is not None else (CAMP_LOCATION,),
        governments=governments,
        agents=agents,
    )


def test_government_rejects_invalid_jurisdiction() -> None:
    """Empty, unsorted, duplicate, or seat-missing jurisdictions fail."""
    with pytest.raises(ValidationError, match="non-empty"):
        Government.create(0, "X", 0, ())
    with pytest.raises(ValidationError, match="ascending"):
        Government.create(0, "X", 1, (1, 0))
    with pytest.raises(ValidationError, match="unique"):
        Government.create(0, "X", 0, (0, 0))
    with pytest.raises(ValidationError, match="inside jurisdiction"):
        Government.create(0, "X", 1, (0,))


def test_world_rejects_overlapping_jurisdictions() -> None:
    """Two governments may not claim the same location."""
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    left = Government.create(0, "A", 0, (0,))
    right = Government.create(1, "B", 0, (0, 1))
    with pytest.raises(ValidationError, match="disjoint"):
        _world(
            Agent.create(agent_id=0, name="A"),
            locations=(CAMP_LOCATION, forest),
            governments=(left, right),
        )


def test_default_governments_cover_full_map() -> None:
    """Canonical polity covers every default map location from camp."""
    governments = default_governments()
    assert governments == (CAMP_GOVERNMENT,)
    assert CAMP_GOVERNMENT.name == "Camp Authority"
    assert CAMP_GOVERNMENT.seat_location_id.value == 0
    assert len(CAMP_GOVERNMENT.jurisdiction) == len(default_world_map())
    assert default_governments() == default_governments()


def test_government_at_and_subject_count() -> None:
    """Lookup and living subject counts respect jurisdiction."""
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    government = Government.create(0, "Camp", 0, (0, 1))
    world = _world(
        Agent.create(agent_id=0, name="A", location_id=0),
        Agent.create(agent_id=1, name="B", location_id=1),
        Agent.create(agent_id=2, name="C", location_id=0).model_copy(
            update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
        ),
        governments=(government,),
        locations=(CAMP_LOCATION, forest),
    )
    assert government_at(world, 1) is not None
    assert government_at(world, 1).government_id.value == 0  # type: ignore[union-attr]
    assert subject_count(world, 0) == 2


def test_set_leader_and_vacant_on_death() -> None:
    """Leaders must be living subjects; dead leaders count as vacant."""
    government = Government.create(0, "Camp", 0, (0,))
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B", location_id=0),
        governments=(government,),
    )
    appointed = set_leader(world, 0, 0)
    assert appointed is not None
    assert appointed.government_by_id(0).leader_id.value == 0  # type: ignore[union-attr]
    assert set_leader(world, 0, 9) is None

    dead_leader = appointed.agent_by_id(0)
    assert dead_leader is not None
    dead_world = appointed.with_agent(
        dead_leader.model_copy(
            update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
        )
    )
    snap = census_governments(dead_world)
    assert snap.led_count == 0
    assert snap.vacant_leader_count == 1


def test_treasury_credit_and_debit() -> None:
    """Government treasury helpers are integer-only and fail closed."""
    government = Government.create(0, "Camp", 0, (0,), treasury=5)
    world = _world(Agent.create(agent_id=0, name="A"), governments=(government,))
    credited = credit_government_treasury(world, 0, 3)
    assert credited is not None
    assert credited.government_by_id(0).treasury == 8  # type: ignore[union-attr]
    assert debit_government_treasury(credited, 0, 9) is None
    debited = debit_government_treasury(credited, 0, 2)
    assert debited is not None
    assert debited.government_by_id(0).treasury == 6  # type: ignore[union-attr]
    assert credit_government_treasury(world, 0, 0) is None


def test_census_governments_aggregates() -> None:
    """Census reports coverage, subjects, and treasury totals."""
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    plain = Location.create(2, "Plain", 2, 0, kind=LocationKind.PLAIN)
    left = Government.create(0, "A", 0, (0,), treasury=2, leader_id=0)
    right = Government.create(1, "B", 1, (1,), treasury=5)
    world = _world(
        Agent.create(agent_id=0, name="A", location_id=0),
        Agent.create(agent_id=1, name="B", location_id=1),
        Agent.create(agent_id=2, name="C", location_id=1),
        governments=(left, right),
        locations=(CAMP_LOCATION, forest, plain),
    )
    snap = census_governments(world)
    assert snap.government_count == 2
    assert snap.covered_location_count == 2
    assert snap.uncovered_location_count == 1
    assert snap.total_treasury == 7
    assert snap.led_count == 1
    assert snap.vacant_leader_count == 1
    assert snap.living_subject_count == 3
    assert snap.max_subjects == 2
    assert snap.max_subjects_government_id is not None
    assert snap.max_subjects_government_id.value == 1
    assert census_governments(world) == snap
