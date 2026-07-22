"""Unit tests for technology catalog models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_ASTRONOMY,
    CAMP_FIRE,
    CAMP_IRRIGATION,
    CAMP_LOCATION,
    CAMP_MATHEMATICS,
    CAMP_METALLURGY,
    CAMP_POTTERY,
    CAMP_WRITING,
    Agent,
    SimulationConfig,
    Technology,
    TechnologyKind,
    World,
    census_technologies,
    create_technology,
    default_technologies,
    discover_technology,
    discovered_technologies,
    next_technology_id,
    prerequisites_met,
    technology_by_id,
    technology_by_kind,
)


def _world(*agents: Agent, technologies: tuple[Technology, ...] = ()) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=technologies,
        agents=agents,
    )


def test_default_technologies_seed_fire_through_astronomy() -> None:
    """Canonical catalog has fire through astronomy progression."""
    assert default_technologies() == (
        CAMP_FIRE,
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
    )
    assert CAMP_FIRE.kind is TechnologyKind.FIRE
    assert CAMP_FIRE.discovered is True
    assert CAMP_POTTERY.kind is TechnologyKind.POTTERY
    assert CAMP_POTTERY.discovered is False
    assert CAMP_POTTERY.prerequisite_ids == (CAMP_FIRE.technology_id,)
    assert CAMP_IRRIGATION.kind is TechnologyKind.IRRIGATION
    assert CAMP_IRRIGATION.discovered is False
    assert CAMP_IRRIGATION.prerequisite_ids == (CAMP_POTTERY.technology_id,)
    assert CAMP_METALLURGY.kind is TechnologyKind.METALLURGY
    assert CAMP_METALLURGY.discovered is False
    assert CAMP_METALLURGY.prerequisite_ids == (CAMP_IRRIGATION.technology_id,)
    assert CAMP_WRITING.kind is TechnologyKind.WRITING
    assert CAMP_WRITING.discovered is False
    assert CAMP_WRITING.prerequisite_ids == (CAMP_METALLURGY.technology_id,)
    assert CAMP_MATHEMATICS.kind is TechnologyKind.MATHEMATICS
    assert CAMP_MATHEMATICS.discovered is False
    assert CAMP_MATHEMATICS.prerequisite_ids == (CAMP_WRITING.technology_id,)
    assert CAMP_ASTRONOMY.kind is TechnologyKind.ASTRONOMY
    assert CAMP_ASTRONOMY.discovered is False
    assert CAMP_ASTRONOMY.prerequisite_ids == (CAMP_MATHEMATICS.technology_id,)


def test_create_and_discover_technology() -> None:
    """create inserts catalog rows; discover flips the flag."""
    world = _world(Agent.create(agent_id=0, name="A"))
    world = create_technology(
        world, Technology.create(0, "Fire", TechnologyKind.FIRE, discovered=False)
    )
    assert world is not None
    assert technology_by_id(world, 0) is not None
    assert technology_by_kind(world, TechnologyKind.FIRE) is not None
    assert next_technology_id(world).value == 1
    discovered = discover_technology(world, 0)
    assert discovered is not None
    assert discovered.technologies[0].discovered is True
    assert discovered_technologies(discovered)[0].kind is TechnologyKind.FIRE
    assert discover_technology(discovered, 0) == discovered


def test_create_rejects_duplicate_kind() -> None:
    """Each technology kind may appear once in the catalog."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=(CAMP_FIRE,),
    )
    assert (
        create_technology(
            world, Technology.create(1, "Other Fire", TechnologyKind.FIRE)
        )
        is None
    )


def test_census_technologies_counts() -> None:
    """Census reports discovered/undiscovered kind counts."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    snap = census_technologies(world)
    assert snap.technology_count == 7
    assert snap.discovered_count == 1
    assert snap.undiscovered_count == 6
    assert snap.discovered_fire_count == 1
    assert snap.discovered_pottery_count == 0
    assert snap.discovered_irrigation_count == 0
    assert snap.discovered_metallurgy_count == 0
    assert snap.discovered_writing_count == 0
    assert snap.discovered_mathematics_count == 0
    assert snap.discovered_astronomy_count == 0
    assert snap.locked_count == 5
    assert snap.researchable_count == 1
    assert prerequisites_met(world, CAMP_POTTERY) is True
    assert prerequisites_met(world, CAMP_IRRIGATION) is False
    assert prerequisites_met(world, CAMP_METALLURGY) is False
    assert prerequisites_met(world, CAMP_WRITING) is False
    assert prerequisites_met(world, CAMP_MATHEMATICS) is False
    assert prerequisites_met(world, CAMP_ASTRONOMY) is False
    assert census_technologies(world) == snap


def test_discover_requires_prerequisites() -> None:
    """Discovery fails when a prerequisite technology is still unknown."""
    pottery_only = Technology.create(
        1,
        "Camp Pottery",
        TechnologyKind.POTTERY,
        prerequisite_ids=(0,),
    )
    fire = Technology.create(0, "Camp Fire", TechnologyKind.FIRE, discovered=False)
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=(fire, pottery_only),
    )
    assert prerequisites_met(world, pottery_only) is False
    assert discover_technology(world, 1) is None
    unlocked = discover_technology(world, 0)
    assert unlocked is not None
    discovered = discover_technology(unlocked, 1)
    assert discovered is not None
    assert discovered.technologies[1].discovered is True


def test_irrigation_locked_until_pottery_discovered() -> None:
    """Irrigation cannot be discovered until pottery is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_IRRIGATION) is False
    assert discover_technology(world, CAMP_IRRIGATION.technology_id) is None

    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    assert prerequisites_met(with_pottery, CAMP_IRRIGATION) is True
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    assert with_irrigation.technologies[2].discovered is True


def test_metallurgy_locked_until_irrigation_discovered() -> None:
    """Metallurgy cannot be discovered until irrigation is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_METALLURGY) is False
    assert discover_technology(world, CAMP_METALLURGY.technology_id) is None

    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    assert prerequisites_met(with_pottery, CAMP_METALLURGY) is False
    assert discover_technology(with_pottery, CAMP_METALLURGY.technology_id) is None

    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    assert prerequisites_met(with_irrigation, CAMP_METALLURGY) is True
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    assert with_metallurgy.technologies[3].discovered is True


def test_writing_locked_until_metallurgy_discovered() -> None:
    """Writing cannot be discovered until metallurgy is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_WRITING) is False
    assert discover_technology(world, CAMP_WRITING.technology_id) is None

    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    assert prerequisites_met(with_irrigation, CAMP_WRITING) is False
    assert discover_technology(with_irrigation, CAMP_WRITING.technology_id) is None

    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    assert prerequisites_met(with_metallurgy, CAMP_WRITING) is True
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    assert with_writing.technologies[4].discovered is True


def test_mathematics_locked_until_writing_discovered() -> None:
    """Mathematics cannot be discovered until writing is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_MATHEMATICS) is False
    assert discover_technology(world, CAMP_MATHEMATICS.technology_id) is None

    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    assert prerequisites_met(with_metallurgy, CAMP_MATHEMATICS) is False
    assert discover_technology(with_metallurgy, CAMP_MATHEMATICS.technology_id) is None

    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    assert prerequisites_met(with_writing, CAMP_MATHEMATICS) is True
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    assert with_math.technologies[5].discovered is True


def test_astronomy_locked_until_mathematics_discovered() -> None:
    """Astronomy cannot be discovered until mathematics is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_ASTRONOMY) is False
    assert discover_technology(world, CAMP_ASTRONOMY.technology_id) is None

    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    with_writing = discover_technology(with_metallurgy, CAMP_WRITING.technology_id)
    assert with_writing is not None
    assert prerequisites_met(with_writing, CAMP_ASTRONOMY) is False
    assert discover_technology(with_writing, CAMP_ASTRONOMY.technology_id) is None

    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    assert prerequisites_met(with_math, CAMP_ASTRONOMY) is True
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    assert with_astronomy.technologies[6].discovered is True


def test_world_rejects_duplicate_kinds() -> None:
    """World validation rejects duplicate technology kinds."""
    with pytest.raises(ValidationError):
        _world(
            Agent.create(agent_id=0, name="A"),
            technologies=(
                Technology.create(0, "A", TechnologyKind.FIRE),
                Technology.create(1, "B", TechnologyKind.FIRE),
            ),
        )
