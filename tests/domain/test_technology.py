"""Unit tests for technology catalog models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_FIRE,
    CAMP_LOCATION,
    CAMP_POTTERY,
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


def test_default_technologies_seed_fire_and_pottery() -> None:
    """Canonical catalog has discovered fire and undiscovered pottery."""
    assert default_technologies() == (CAMP_FIRE, CAMP_POTTERY)
    assert CAMP_FIRE.kind is TechnologyKind.FIRE
    assert CAMP_FIRE.discovered is True
    assert CAMP_POTTERY.kind is TechnologyKind.POTTERY
    assert CAMP_POTTERY.discovered is False
    assert CAMP_POTTERY.prerequisite_ids == (CAMP_FIRE.technology_id,)


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
    assert snap.technology_count == 2
    assert snap.discovered_count == 1
    assert snap.undiscovered_count == 1
    assert snap.discovered_fire_count == 1
    assert snap.discovered_pottery_count == 0
    assert snap.locked_count == 0
    assert snap.researchable_count == 1
    assert prerequisites_met(world, CAMP_POTTERY) is True
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
