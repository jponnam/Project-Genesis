"""Unit tests for innovation models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_ABACUS,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASEPSIS,
    CAMP_ASTRONOMY,
    CAMP_BLUEPRINT,
    CAMP_DIALECTIC,
    CAMP_DISSECTION,
    CAMP_ENGINEERING,
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_FORGE,
    CAMP_HYGIENE,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_CANAL,
    CAMP_LOCATION,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_ORATION,
    CAMP_PHILOSOPHY,
    CAMP_PLUMB_LINE,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    CAMP_PULLEY,
    CAMP_REMEDY,
    CAMP_RHETORIC,
    CAMP_SCRIBE,
    CAMP_STAR_CHART,
    CAMP_SURVEYING,
    CAMP_SYLLOGISM,
    CAMP_WRITING,
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


def test_default_innovations_seed_hearth_through_plumb_line() -> None:
    """Canonical set has active hearth and inactive later adoptions."""
    assert default_innovations() == (
        CAMP_FIRE_HEARTH,
        CAMP_POTTERY_CRAFT,
        CAMP_IRRIGATION_CANAL,
        CAMP_FORGE,
        CAMP_SCRIBE,
        CAMP_ABACUS,
        CAMP_STAR_CHART,
        CAMP_DIALECTIC,
        CAMP_SYLLOGISM,
        CAMP_ORATION,
        CAMP_REMEDY,
        CAMP_DISSECTION,
        CAMP_ASEPSIS,
        CAMP_PULLEY,
        CAMP_BLUEPRINT,
        CAMP_PLUMB_LINE,
    )
    assert CAMP_FIRE_HEARTH.kind is InnovationKind.FIRE_HEARTH
    assert CAMP_FIRE_HEARTH.active is True
    assert CAMP_POTTERY_CRAFT.kind is InnovationKind.POTTERY_CRAFT
    assert CAMP_POTTERY_CRAFT.active is False
    assert CAMP_IRRIGATION_CANAL.kind is InnovationKind.IRRIGATION_CANAL
    assert CAMP_IRRIGATION_CANAL.active is False
    assert CAMP_FORGE.kind is InnovationKind.FORGE
    assert CAMP_FORGE.active is False
    assert CAMP_SCRIBE.kind is InnovationKind.SCRIBE
    assert CAMP_SCRIBE.active is False
    assert CAMP_ABACUS.kind is InnovationKind.ABACUS
    assert CAMP_ABACUS.active is False
    assert CAMP_STAR_CHART.kind is InnovationKind.STAR_CHART
    assert CAMP_STAR_CHART.active is False
    assert CAMP_DIALECTIC.kind is InnovationKind.DIALECTIC
    assert CAMP_DIALECTIC.active is False
    assert CAMP_SYLLOGISM.kind is InnovationKind.SYLLOGISM
    assert CAMP_SYLLOGISM.active is False
    assert CAMP_ORATION.kind is InnovationKind.ORATION
    assert CAMP_ORATION.active is False
    assert CAMP_REMEDY.kind is InnovationKind.REMEDY
    assert CAMP_REMEDY.active is False
    assert CAMP_DISSECTION.kind is InnovationKind.DISSECTION
    assert CAMP_DISSECTION.active is False
    assert CAMP_ASEPSIS.kind is InnovationKind.ASEPSIS
    assert CAMP_ASEPSIS.active is False
    assert CAMP_PULLEY.kind is InnovationKind.PULLEY
    assert CAMP_PULLEY.active is False
    assert CAMP_BLUEPRINT.kind is InnovationKind.BLUEPRINT
    assert CAMP_BLUEPRINT.active is False
    assert CAMP_PLUMB_LINE.kind is InnovationKind.PLUMB_LINE
    assert CAMP_PLUMB_LINE.active is False


def test_activate_due_innovations_after_discovery() -> None:
    """Innovations activate once their technologies are discovered."""
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

    discovered = discover_technology(world, CAMP_IRRIGATION.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.IRRIGATION_CANAL
    assert innovation_by_id(world, 2) is not None
    assert innovation_by_id(world, 2).active is True
    assert innovation_for_technology(world, 2) is not None

    discovered = discover_technology(world, CAMP_METALLURGY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.FORGE
    assert innovation_by_id(world, 3) is not None
    assert innovation_by_id(world, 3).active is True
    assert innovation_for_technology(world, 3) is not None

    discovered = discover_technology(world, CAMP_WRITING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.SCRIBE
    assert innovation_by_id(world, 4) is not None
    assert innovation_by_id(world, 4).active is True
    assert innovation_for_technology(world, 4) is not None

    discovered = discover_technology(world, CAMP_MATHEMATICS.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.ABACUS
    assert innovation_by_id(world, 5) is not None
    assert innovation_by_id(world, 5).active is True
    assert innovation_for_technology(world, 5) is not None

    discovered = discover_technology(world, CAMP_ASTRONOMY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.STAR_CHART
    assert innovation_by_id(world, 6) is not None
    assert innovation_by_id(world, 6).active is True
    assert innovation_for_technology(world, 6) is not None

    discovered = discover_technology(world, CAMP_PHILOSOPHY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.DIALECTIC
    assert innovation_by_id(world, 7) is not None
    assert innovation_by_id(world, 7).active is True
    assert innovation_for_technology(world, 7) is not None

    discovered = discover_technology(world, 8)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.SYLLOGISM
    assert innovation_by_id(world, 8) is not None
    assert innovation_by_id(world, 8).active is True
    assert innovation_for_technology(world, 8) is not None

    discovered = discover_technology(world, CAMP_RHETORIC.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.ORATION
    assert innovation_by_id(world, 9) is not None
    assert innovation_by_id(world, 9).active is True
    assert innovation_for_technology(world, 9) is not None

    discovered = discover_technology(world, CAMP_MEDICINE.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.REMEDY
    assert innovation_by_id(world, 10) is not None
    assert innovation_by_id(world, 10).active is True
    assert innovation_for_technology(world, 10) is not None

    discovered = discover_technology(world, CAMP_ANATOMY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.DISSECTION
    assert innovation_by_id(world, 11) is not None
    assert innovation_by_id(world, 11).active is True
    assert innovation_for_technology(world, 11) is not None

    discovered = discover_technology(world, CAMP_HYGIENE.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.ASEPSIS
    assert innovation_by_id(world, 12) is not None
    assert innovation_by_id(world, 12).active is True
    assert innovation_for_technology(world, 12) is not None

    discovered = discover_technology(world, CAMP_ENGINEERING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.PULLEY
    assert innovation_by_id(world, 13) is not None
    assert innovation_by_id(world, 13).active is True
    assert innovation_for_technology(world, 13) is not None

    discovered = discover_technology(world, CAMP_ARCHITECTURE.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.BLUEPRINT
    assert innovation_by_id(world, 14) is not None
    assert innovation_by_id(world, 14).active is True
    assert innovation_for_technology(world, 14) is not None

    discovered = discover_technology(world, CAMP_SURVEYING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.PLUMB_LINE
    assert innovation_by_id(world, 15) is not None
    assert innovation_by_id(world, 15).active is True
    assert innovation_for_technology(world, 15) is not None


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
    assert snap.innovation_count == 16
    assert snap.active_count == 1
    assert snap.inactive_count == 15
    assert snap.active_fire_hearth_count == 1
    assert snap.active_pottery_craft_count == 0
    assert snap.active_irrigation_canal_count == 0
    assert snap.active_forge_count == 0
    assert snap.active_scribe_count == 0
    assert snap.active_abacus_count == 0
    assert snap.active_star_chart_count == 0
    assert snap.active_dialectic_count == 0
    assert snap.active_syllogism_count == 0
    assert snap.active_oration_count == 0
    assert snap.active_remedy_count == 0
    assert snap.active_dissection_count == 0
    assert snap.active_asepsis_count == 0
    assert snap.active_pulley_count == 0
    assert snap.active_blueprint_count == 0
    assert snap.active_plumb_line_count == 0
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
