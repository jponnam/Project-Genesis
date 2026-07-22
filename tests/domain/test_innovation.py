"""Unit tests for innovation models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_LOCATION,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    Agent,
    Innovation,
    InnovationKind,
    SimulationConfig,
    Technology,
    World,
    activate_due_innovations,
    activate_innovation,
    census_innovations,
    create_innovation,
    default_innovations,
    default_technologies,
    discover_technology,
    innovation_by_id,
    innovation_by_kind,
    innovation_for_technology,
)


def _world(
    *agents: Agent,
    technologies: tuple[Technology, ...] | None = None,
    innovations: tuple[Innovation, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(default_technologies() if technologies is None else technologies),
        innovations=innovations,
        agents=agents,
    )


def test_default_innovations_seed_hearth_and_craft() -> None:
    """Canonical set has active fire hearth and inactive pottery craft."""
    assert default_innovations() == (CAMP_FIRE_HEARTH, CAMP_POTTERY_CRAFT)
    assert CAMP_FIRE_HEARTH.kind is InnovationKind.FIRE_HEARTH
    assert CAMP_FIRE_HEARTH.active is True
    assert CAMP_POTTERY_CRAFT.kind is InnovationKind.POTTERY_CRAFT
    assert CAMP_POTTERY_CRAFT.active is False


def test_activate_due_innovations_after_discovery() -> None:
    """Pottery craft activates once pottery is discovered."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        innovations=default_innovations(),
    )
    world, activations = activate_due_innovations(world)
    assert activations == ()
    assert innovation_by_kind(world, InnovationKind.POTTERY_CRAFT) is not None
    assert innovation_by_kind(world, InnovationKind.POTTERY_CRAFT).active is False

    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.POTTERY_CRAFT
    assert innovation_by_id(world, 1) is not None
    assert innovation_by_id(world, 1).active is True
    assert innovation_for_technology(world, 1) is not None


def test_activate_innovation_requires_discovered_technology() -> None:
    """Manual activate fails while the linked technology is unknown."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        innovations=default_innovations(),
    )
    assert activate_innovation(world, 1) is None


def test_create_innovation_inserts_catalog_row() -> None:
    """create_innovation appends a legal inactive adoption row."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=(CAMP_FIRE,),
    )
    created = create_innovation(
        world,
        Innovation.create(
            0,
            CAMP_FIRE.technology_id.value,
            "Hearth",
            InnovationKind.FIRE_HEARTH,
            active=True,
        ),
    )
    assert created is not None
    assert created.innovations[0].active is True


def test_census_innovations_counts() -> None:
    """Census reports active/inactive kind counts."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        innovations=default_innovations(),
    )
    snap = census_innovations(world)
    assert snap.innovation_count == 2
    assert snap.active_count == 1
    assert snap.inactive_count == 1
    assert snap.active_fire_hearth_count == 1
    assert snap.active_pottery_craft_count == 0
    assert census_innovations(world) == snap


def test_world_rejects_active_innovation_without_discovery() -> None:
    """World validation forbids active innovations on undiscovered tech."""
    with pytest.raises(ValidationError):
        _world(
            Agent.create(agent_id=0, name="A"),
            innovations=(
                Innovation.create(
                    0,
                    CAMP_POTTERY.technology_id.value,
                    "Premature Craft",
                    InnovationKind.POTTERY_CRAFT,
                    active=True,
                ),
            ),
        )


def test_world_rejects_duplicate_innovation_kinds() -> None:
    """World validation rejects duplicate innovation kinds."""
    with pytest.raises(ValidationError):
        _world(
            Agent.create(agent_id=0, name="A"),
            innovations=(
                CAMP_FIRE_HEARTH,
                Innovation.create(
                    1,
                    CAMP_POTTERY.technology_id.value,
                    "Other Hearth",
                    InnovationKind.FIRE_HEARTH,
                ),
            ),
        )
