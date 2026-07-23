"""Unit tests for innovation models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_ABACUS,
    CAMP_AGRICULTURE,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASEPSIS,
    CAMP_ASTRONOMY,
    CAMP_BELLOWS,
    CAMP_BLUEPRINT,
    CAMP_CABINETRY,
    CAMP_CARPENTRY,
    CAMP_CARTOGRAPHY,
    CAMP_CERAMICS,
    CAMP_COMPASS,
    CAMP_COPPICE,
    CAMP_CROP_ROTATION,
    CAMP_DIALECTIC,
    CAMP_DISSECTION,
    CAMP_DOVETAIL,
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
    CAMP_JOINERY,
    CAMP_KILN,
    CAMP_LATHE,
    CAMP_LOCATION,
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
    CAMP_PLANE,
    CAMP_PLOW,
    CAMP_PLUMB_LINE,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    CAMP_PULLEY,
    CAMP_REMEDY,
    CAMP_RHETORIC,
    CAMP_SAIL,
    CAMP_SAWMILL,
    CAMP_SCRIBE,
    CAMP_SEAFARING,
    CAMP_SMITHING,
    CAMP_STAR_CHART,
    CAMP_SURVEYING,
    CAMP_SYLLOGISM,
    CAMP_TANNERY,
    CAMP_TANNING,
    CAMP_TEXTILES,
    CAMP_TOOLMAKING,
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


def test_default_innovations_seed_hearth_through_kiln() -> None:
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
        CAMP_COMPASS,
        CAMP_MAP,
        CAMP_SAIL,
        CAMP_PLOW,
        CAMP_FALLOW,
        CAMP_COPPICE,
        CAMP_LOOM,
        CAMP_MORDANT,
        CAMP_TANNERY,
        CAMP_PICKAXE,
        CAMP_BELLOWS,
        CAMP_LATHE,
        CAMP_SAWMILL,
        CAMP_PLANE,
        CAMP_DOVETAIL,
        CAMP_KILN,
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
    assert CAMP_COMPASS.kind is InnovationKind.COMPASS
    assert CAMP_COMPASS.active is False
    assert CAMP_MAP.kind is InnovationKind.MAP
    assert CAMP_MAP.active is False
    assert CAMP_MAP.technology_id == CAMP_CARTOGRAPHY.technology_id
    assert CAMP_SAIL.kind is InnovationKind.SAIL
    assert CAMP_SAIL.active is False
    assert CAMP_SAIL.technology_id == CAMP_SEAFARING.technology_id
    assert CAMP_PLOW.kind is InnovationKind.PLOW
    assert CAMP_PLOW.active is False
    assert CAMP_PLOW.technology_id == CAMP_AGRICULTURE.technology_id
    assert CAMP_FALLOW.kind is InnovationKind.FALLOW
    assert CAMP_FALLOW.active is False
    assert CAMP_FALLOW.technology_id == CAMP_CROP_ROTATION.technology_id
    assert CAMP_COPPICE.kind is InnovationKind.COPPICE
    assert CAMP_COPPICE.active is False
    assert CAMP_COPPICE.technology_id == CAMP_FORESTRY.technology_id
    assert CAMP_LOOM.kind is InnovationKind.LOOM
    assert CAMP_LOOM.active is False
    assert CAMP_LOOM.technology_id == CAMP_TEXTILES.technology_id
    assert CAMP_MORDANT.kind is InnovationKind.MORDANT
    assert CAMP_MORDANT.active is False
    assert CAMP_MORDANT.technology_id == CAMP_DYEING.technology_id
    assert CAMP_TANNERY.kind is InnovationKind.TANNERY
    assert CAMP_TANNERY.active is False
    assert CAMP_TANNERY.technology_id == CAMP_TANNING.technology_id
    assert CAMP_PICKAXE.kind is InnovationKind.PICKAXE
    assert CAMP_PICKAXE.active is False
    assert CAMP_PICKAXE.technology_id == CAMP_MINING.technology_id
    assert CAMP_BELLOWS.kind is InnovationKind.BELLOWS
    assert CAMP_BELLOWS.active is False
    assert CAMP_BELLOWS.technology_id == CAMP_SMITHING.technology_id
    assert CAMP_LATHE.kind is InnovationKind.LATHE
    assert CAMP_LATHE.active is False
    assert CAMP_LATHE.technology_id == CAMP_TOOLMAKING.technology_id
    assert CAMP_SAWMILL.kind is InnovationKind.SAWMILL
    assert CAMP_SAWMILL.active is False
    assert CAMP_SAWMILL.technology_id == CAMP_CARPENTRY.technology_id
    assert CAMP_PLANE.kind is InnovationKind.PLANE
    assert CAMP_PLANE.active is False
    assert CAMP_PLANE.technology_id == CAMP_JOINERY.technology_id
    assert CAMP_DOVETAIL.kind is InnovationKind.DOVETAIL
    assert CAMP_DOVETAIL.active is False
    assert CAMP_DOVETAIL.technology_id == CAMP_CABINETRY.technology_id
    assert CAMP_KILN.kind is InnovationKind.KILN
    assert CAMP_KILN.active is False
    assert CAMP_KILN.technology_id == CAMP_CERAMICS.technology_id


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

    discovered = discover_technology(world, CAMP_NAVIGATION.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.COMPASS
    assert innovation_by_id(world, 16) is not None
    assert innovation_by_id(world, 16).active is True
    assert innovation_for_technology(world, 16) is not None

    discovered = discover_technology(world, CAMP_CARTOGRAPHY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.MAP
    assert innovation_by_id(world, 17) is not None
    assert innovation_by_id(world, 17).active is True
    assert innovation_for_technology(world, 17) is not None

    discovered = discover_technology(world, CAMP_SEAFARING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.SAIL
    assert innovation_by_id(world, 18) is not None
    assert innovation_by_id(world, 18).active is True
    assert innovation_for_technology(world, 18) is not None

    discovered = discover_technology(world, CAMP_AGRICULTURE.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.PLOW
    assert innovation_by_id(world, 19) is not None
    assert innovation_by_id(world, 19).active is True
    assert innovation_for_technology(world, 19) is not None

    discovered = discover_technology(world, CAMP_CROP_ROTATION.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.FALLOW
    assert innovation_by_id(world, 20) is not None
    assert innovation_by_id(world, 20).active is True
    assert innovation_for_technology(world, 20) is not None

    discovered = discover_technology(world, CAMP_FORESTRY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.COPPICE
    assert innovation_by_id(world, 21) is not None
    assert innovation_by_id(world, 21).active is True
    assert innovation_for_technology(world, 21) is not None

    discovered = discover_technology(world, CAMP_TEXTILES.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.LOOM
    assert innovation_by_id(world, 22) is not None
    assert innovation_by_id(world, 22).active is True
    assert innovation_for_technology(world, 22) is not None

    discovered = discover_technology(world, CAMP_DYEING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.MORDANT
    assert innovation_by_id(world, 23) is not None
    assert innovation_by_id(world, 23).active is True
    assert innovation_for_technology(world, 23) is not None

    discovered = discover_technology(world, CAMP_TANNING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.TANNERY
    assert innovation_by_id(world, 24) is not None
    assert innovation_by_id(world, 24).active is True
    assert innovation_for_technology(world, 24) is not None

    discovered = discover_technology(world, CAMP_MINING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.PICKAXE
    assert innovation_by_id(world, 25) is not None
    assert innovation_by_id(world, 25).active is True
    assert innovation_for_technology(world, 25) is not None

    discovered = discover_technology(world, CAMP_SMITHING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.BELLOWS
    assert innovation_by_id(world, 26) is not None
    assert innovation_by_id(world, 26).active is True
    assert innovation_for_technology(world, 26) is not None

    discovered = discover_technology(world, CAMP_TOOLMAKING.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.LATHE
    assert innovation_by_id(world, 27) is not None
    assert innovation_by_id(world, 27).active is True
    assert innovation_for_technology(world, 27) is not None

    discovered = discover_technology(world, CAMP_CARPENTRY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.SAWMILL
    assert innovation_by_id(world, 28) is not None
    assert innovation_by_id(world, 28).active is True
    assert innovation_for_technology(world, 28) is not None

    discovered = discover_technology(world, CAMP_JOINERY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.PLANE
    assert innovation_by_id(world, 29) is not None
    assert innovation_by_id(world, 29).active is True
    assert innovation_for_technology(world, 29) is not None

    discovered = discover_technology(world, CAMP_CABINETRY.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.DOVETAIL
    assert innovation_by_id(world, 30) is not None
    assert innovation_by_id(world, 30).active is True
    assert innovation_for_technology(world, 30) is not None

    discovered = discover_technology(world, CAMP_CERAMICS.technology_id)
    assert discovered is not None
    world, activations = activate_due_innovations(discovered)
    assert len(activations) == 1
    assert activations[0].kind is InnovationKind.KILN
    assert innovation_by_id(world, 31) is not None
    assert innovation_by_id(world, 31).active is True
    assert innovation_for_technology(world, 31) is not None


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
    assert snap.innovation_count == 32
    assert snap.active_count == 1
    assert snap.inactive_count == 31
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
    assert snap.active_compass_count == 0
    assert snap.active_map_count == 0
    assert snap.active_sail_count == 0
    assert snap.active_plow_count == 0
    assert snap.active_fallow_count == 0
    assert snap.active_coppice_count == 0
    assert snap.active_loom_count == 0
    assert snap.active_mordant_count == 0
    assert snap.active_tannery_count == 0
    assert snap.active_pickaxe_count == 0
    assert snap.active_bellows_count == 0
    assert snap.active_lathe_count == 0
    assert snap.active_sawmill_count == 0
    assert snap.active_plane_count == 0
    assert snap.active_dovetail_count == 0
    assert snap.active_kiln_count == 0
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
