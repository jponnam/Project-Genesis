"""Unit tests for technology catalog models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_AGRICULTURE,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASTRONOMY,
    CAMP_CARPENTRY,
    CAMP_CARTOGRAPHY,
    CAMP_CROP_ROTATION,
    CAMP_DYEING,
    CAMP_ENGINEERING,
    CAMP_FIRE,
    CAMP_FORESTRY,
    CAMP_HYGIENE,
    CAMP_IRRIGATION,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_MINING,
    CAMP_NAVIGATION,
    CAMP_PHILOSOPHY,
    CAMP_POTTERY,
    CAMP_RHETORIC,
    CAMP_SEAFARING,
    CAMP_SMITHING,
    CAMP_SURVEYING,
    CAMP_TANNING,
    CAMP_TEXTILES,
    CAMP_TOOLMAKING,
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


def test_default_technologies_seed_fire_through_carpentry() -> None:
    """Canonical catalog has fire through carpentry progression."""
    assert default_technologies() == (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
        CAMP_TANNING,
        CAMP_MINING,
        CAMP_SMITHING,
        CAMP_TOOLMAKING,
        CAMP_CARPENTRY,
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
    assert CAMP_PHILOSOPHY.kind is TechnologyKind.PHILOSOPHY
    assert CAMP_PHILOSOPHY.discovered is False
    assert CAMP_PHILOSOPHY.prerequisite_ids == (CAMP_ASTRONOMY.technology_id,)
    assert CAMP_LOGIC.kind is TechnologyKind.LOGIC
    assert CAMP_LOGIC.discovered is False
    assert CAMP_LOGIC.prerequisite_ids == (CAMP_PHILOSOPHY.technology_id,)
    assert CAMP_RHETORIC.kind is TechnologyKind.RHETORIC
    assert CAMP_RHETORIC.discovered is False
    assert CAMP_RHETORIC.prerequisite_ids == (CAMP_LOGIC.technology_id,)
    assert CAMP_MEDICINE.kind is TechnologyKind.MEDICINE
    assert CAMP_MEDICINE.discovered is False
    assert CAMP_MEDICINE.prerequisite_ids == (CAMP_RHETORIC.technology_id,)
    assert CAMP_ANATOMY.kind is TechnologyKind.ANATOMY
    assert CAMP_ANATOMY.discovered is False
    assert CAMP_ANATOMY.prerequisite_ids == (CAMP_MEDICINE.technology_id,)
    assert CAMP_HYGIENE.kind is TechnologyKind.HYGIENE
    assert CAMP_HYGIENE.discovered is False
    assert CAMP_HYGIENE.prerequisite_ids == (CAMP_ANATOMY.technology_id,)
    assert CAMP_ENGINEERING.kind is TechnologyKind.ENGINEERING
    assert CAMP_ENGINEERING.discovered is False
    assert CAMP_ENGINEERING.prerequisite_ids == (CAMP_HYGIENE.technology_id,)
    assert CAMP_ARCHITECTURE.kind is TechnologyKind.ARCHITECTURE
    assert CAMP_ARCHITECTURE.discovered is False
    assert CAMP_ARCHITECTURE.prerequisite_ids == (CAMP_ENGINEERING.technology_id,)
    assert CAMP_SURVEYING.kind is TechnologyKind.SURVEYING
    assert CAMP_SURVEYING.discovered is False
    assert CAMP_SURVEYING.prerequisite_ids == (CAMP_ARCHITECTURE.technology_id,)
    assert CAMP_NAVIGATION.kind is TechnologyKind.NAVIGATION
    assert CAMP_NAVIGATION.discovered is False
    assert CAMP_NAVIGATION.prerequisite_ids == (CAMP_SURVEYING.technology_id,)
    assert CAMP_CARTOGRAPHY.kind is TechnologyKind.CARTOGRAPHY
    assert CAMP_CARTOGRAPHY.discovered is False
    assert CAMP_CARTOGRAPHY.prerequisite_ids == (CAMP_NAVIGATION.technology_id,)
    assert CAMP_SEAFARING.kind is TechnologyKind.SEAFARING
    assert CAMP_SEAFARING.discovered is False
    assert CAMP_SEAFARING.prerequisite_ids == (CAMP_CARTOGRAPHY.technology_id,)
    assert CAMP_AGRICULTURE.kind is TechnologyKind.AGRICULTURE
    assert CAMP_AGRICULTURE.discovered is False
    assert CAMP_AGRICULTURE.prerequisite_ids == (CAMP_SEAFARING.technology_id,)
    assert CAMP_CROP_ROTATION.kind is TechnologyKind.CROP_ROTATION
    assert CAMP_CROP_ROTATION.discovered is False
    assert CAMP_CROP_ROTATION.prerequisite_ids == (CAMP_AGRICULTURE.technology_id,)
    assert CAMP_FORESTRY.kind is TechnologyKind.FORESTRY
    assert CAMP_FORESTRY.discovered is False
    assert CAMP_FORESTRY.prerequisite_ids == (CAMP_CROP_ROTATION.technology_id,)
    assert CAMP_TEXTILES.kind is TechnologyKind.TEXTILES
    assert CAMP_TEXTILES.discovered is False
    assert CAMP_TEXTILES.prerequisite_ids == (CAMP_FORESTRY.technology_id,)
    assert CAMP_DYEING.kind is TechnologyKind.DYEING
    assert CAMP_DYEING.discovered is False
    assert CAMP_DYEING.prerequisite_ids == (CAMP_TEXTILES.technology_id,)
    assert CAMP_TANNING.kind is TechnologyKind.TANNING
    assert CAMP_TANNING.discovered is False
    assert CAMP_TANNING.prerequisite_ids == (CAMP_DYEING.technology_id,)
    assert CAMP_MINING.kind is TechnologyKind.MINING
    assert CAMP_MINING.discovered is False
    assert CAMP_MINING.prerequisite_ids == (CAMP_TANNING.technology_id,)
    assert CAMP_SMITHING.kind is TechnologyKind.SMITHING
    assert CAMP_SMITHING.discovered is False
    assert CAMP_SMITHING.prerequisite_ids == (CAMP_MINING.technology_id,)
    assert CAMP_TOOLMAKING.kind is TechnologyKind.TOOLMAKING
    assert CAMP_TOOLMAKING.discovered is False
    assert CAMP_TOOLMAKING.prerequisite_ids == (CAMP_SMITHING.technology_id,)
    assert CAMP_CARPENTRY.kind is TechnologyKind.CARPENTRY
    assert CAMP_CARPENTRY.discovered is False
    assert CAMP_CARPENTRY.prerequisite_ids == (CAMP_TOOLMAKING.technology_id,)


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
    assert snap.technology_count == 29
    assert snap.discovered_count == 1
    assert snap.undiscovered_count == 28
    assert snap.discovered_fire_count == 1
    assert snap.discovered_pottery_count == 0
    assert snap.discovered_irrigation_count == 0
    assert snap.discovered_metallurgy_count == 0
    assert snap.discovered_writing_count == 0
    assert snap.discovered_mathematics_count == 0
    assert snap.discovered_astronomy_count == 0
    assert snap.discovered_philosophy_count == 0
    assert snap.discovered_logic_count == 0
    assert snap.discovered_rhetoric_count == 0
    assert snap.discovered_medicine_count == 0
    assert snap.discovered_anatomy_count == 0
    assert snap.discovered_hygiene_count == 0
    assert snap.discovered_engineering_count == 0
    assert snap.discovered_architecture_count == 0
    assert snap.discovered_surveying_count == 0
    assert snap.discovered_navigation_count == 0
    assert snap.discovered_cartography_count == 0
    assert snap.discovered_seafaring_count == 0
    assert snap.discovered_agriculture_count == 0
    assert snap.discovered_crop_rotation_count == 0
    assert snap.discovered_forestry_count == 0
    assert snap.discovered_textiles_count == 0
    assert snap.discovered_dyeing_count == 0
    assert snap.discovered_tanning_count == 0
    assert snap.discovered_mining_count == 0
    assert snap.discovered_smithing_count == 0
    assert snap.discovered_toolmaking_count == 0
    assert snap.discovered_carpentry_count == 0
    assert snap.locked_count == 27
    assert snap.researchable_count == 1
    assert prerequisites_met(world, CAMP_POTTERY) is True
    assert prerequisites_met(world, CAMP_IRRIGATION) is False
    assert prerequisites_met(world, CAMP_METALLURGY) is False
    assert prerequisites_met(world, CAMP_WRITING) is False
    assert prerequisites_met(world, CAMP_MATHEMATICS) is False
    assert prerequisites_met(world, CAMP_ASTRONOMY) is False
    assert prerequisites_met(world, CAMP_PHILOSOPHY) is False
    assert prerequisites_met(world, CAMP_LOGIC) is False
    assert prerequisites_met(world, CAMP_RHETORIC) is False
    assert prerequisites_met(world, CAMP_MEDICINE) is False
    assert prerequisites_met(world, CAMP_ANATOMY) is False
    assert prerequisites_met(world, CAMP_HYGIENE) is False
    assert prerequisites_met(world, CAMP_ENGINEERING) is False
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


def test_philosophy_locked_until_astronomy_discovered() -> None:
    """Philosophy cannot be discovered until astronomy is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_PHILOSOPHY) is False
    assert discover_technology(world, CAMP_PHILOSOPHY.technology_id) is None

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
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    assert prerequisites_met(with_math, CAMP_PHILOSOPHY) is False
    assert discover_technology(with_math, CAMP_PHILOSOPHY.technology_id) is None

    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    assert prerequisites_met(with_astronomy, CAMP_PHILOSOPHY) is True
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    assert with_philosophy.technologies[7].discovered is True


def test_logic_locked_until_philosophy_discovered() -> None:
    """Logic cannot be discovered until philosophy is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_LOGIC) is False
    assert discover_technology(world, CAMP_LOGIC.technology_id) is None

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
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    assert prerequisites_met(with_astronomy, CAMP_LOGIC) is False
    assert discover_technology(with_astronomy, CAMP_LOGIC.technology_id) is None

    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    assert prerequisites_met(with_philosophy, CAMP_LOGIC) is True
    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    assert with_logic.technologies[8].discovered is True


def test_rhetoric_locked_until_logic_discovered() -> None:
    """Rhetoric cannot be discovered until logic is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_RHETORIC) is False
    assert discover_technology(world, CAMP_RHETORIC.technology_id) is None

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
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    assert prerequisites_met(with_philosophy, CAMP_RHETORIC) is False
    assert discover_technology(with_philosophy, CAMP_RHETORIC.technology_id) is None

    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    assert prerequisites_met(with_logic, CAMP_RHETORIC) is True
    with_rhetoric = discover_technology(with_logic, CAMP_RHETORIC.technology_id)
    assert with_rhetoric is not None
    assert with_rhetoric.technologies[9].discovered is True


def test_medicine_locked_until_rhetoric_discovered() -> None:
    """Medicine cannot be discovered until rhetoric is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_MEDICINE) is False
    assert discover_technology(world, CAMP_MEDICINE.technology_id) is None

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
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    assert prerequisites_met(with_logic, CAMP_MEDICINE) is False
    assert discover_technology(with_logic, CAMP_MEDICINE.technology_id) is None

    with_rhetoric = discover_technology(with_logic, CAMP_RHETORIC.technology_id)
    assert with_rhetoric is not None
    assert prerequisites_met(with_rhetoric, CAMP_MEDICINE) is True
    with_medicine = discover_technology(with_rhetoric, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    assert with_medicine.technologies[10].discovered is True


def test_anatomy_locked_until_medicine_discovered() -> None:
    """Anatomy cannot be discovered until medicine is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_ANATOMY) is False
    assert discover_technology(world, CAMP_ANATOMY.technology_id) is None

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
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    with_rhetoric = discover_technology(with_logic, CAMP_RHETORIC.technology_id)
    assert with_rhetoric is not None
    assert prerequisites_met(with_rhetoric, CAMP_ANATOMY) is False
    assert discover_technology(with_rhetoric, CAMP_ANATOMY.technology_id) is None

    with_medicine = discover_technology(with_rhetoric, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    assert prerequisites_met(with_medicine, CAMP_ANATOMY) is True
    with_anatomy = discover_technology(with_medicine, CAMP_ANATOMY.technology_id)
    assert with_anatomy is not None
    assert with_anatomy.technologies[11].discovered is True


def test_hygiene_locked_until_anatomy_discovered() -> None:
    """Hygiene cannot be discovered until anatomy is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_HYGIENE) is False
    assert discover_technology(world, CAMP_HYGIENE.technology_id) is None

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
    with_math = discover_technology(with_writing, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    with_astronomy = discover_technology(with_math, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    with_philosophy = discover_technology(with_astronomy, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    with_logic = discover_technology(with_philosophy, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    with_rhetoric = discover_technology(with_logic, CAMP_RHETORIC.technology_id)
    assert with_rhetoric is not None
    with_medicine = discover_technology(with_rhetoric, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    assert prerequisites_met(with_medicine, CAMP_HYGIENE) is False
    assert discover_technology(with_medicine, CAMP_HYGIENE.technology_id) is None

    with_anatomy = discover_technology(with_medicine, CAMP_ANATOMY.technology_id)
    assert with_anatomy is not None
    assert prerequisites_met(with_anatomy, CAMP_HYGIENE) is True
    with_hygiene = discover_technology(with_anatomy, CAMP_HYGIENE.technology_id)
    assert with_hygiene is not None
    assert with_hygiene.technologies[12].discovered is True


def test_engineering_locked_until_hygiene_discovered() -> None:
    """Engineering cannot be discovered until hygiene is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_ENGINEERING) is False
    assert discover_technology(world, CAMP_ENGINEERING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated

    assert prerequisites_met(current, CAMP_ENGINEERING) is False
    assert discover_technology(current, CAMP_ENGINEERING.technology_id) is None

    with_hygiene = discover_technology(current, CAMP_HYGIENE.technology_id)
    assert with_hygiene is not None
    assert prerequisites_met(with_hygiene, CAMP_ENGINEERING) is True
    with_engineering = discover_technology(with_hygiene, CAMP_ENGINEERING.technology_id)
    assert with_engineering is not None
    assert with_engineering.technologies[13].discovered is True


def test_architecture_locked_until_engineering_discovered() -> None:
    """Architecture cannot be discovered until engineering is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_ARCHITECTURE) is False
    assert discover_technology(world, CAMP_ARCHITECTURE.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated

    assert prerequisites_met(current, CAMP_ARCHITECTURE) is False
    assert discover_technology(current, CAMP_ARCHITECTURE.technology_id) is None

    with_engineering = discover_technology(current, CAMP_ENGINEERING.technology_id)
    assert with_engineering is not None
    assert prerequisites_met(with_engineering, CAMP_ARCHITECTURE) is True
    with_architecture = discover_technology(
        with_engineering, CAMP_ARCHITECTURE.technology_id
    )
    assert with_architecture is not None

    assert with_architecture.technologies[14].discovered is True


def test_surveying_locked_until_architecture_discovered() -> None:
    """Surveying cannot be discovered until architecture is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_SURVEYING) is False
    assert discover_technology(world, CAMP_SURVEYING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_SURVEYING) is False
    assert discover_technology(current, CAMP_SURVEYING.technology_id) is None

    with_architecture = discover_technology(current, CAMP_ARCHITECTURE.technology_id)
    assert with_architecture is not None
    assert prerequisites_met(with_architecture, CAMP_SURVEYING) is True
    with_surveying = discover_technology(
        with_architecture, CAMP_SURVEYING.technology_id
    )
    assert with_surveying is not None
    assert with_surveying.technologies[15].discovered is True


def test_navigation_locked_until_surveying_discovered() -> None:
    """Navigation cannot be discovered until surveying is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_NAVIGATION) is False
    assert discover_technology(world, CAMP_NAVIGATION.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_NAVIGATION) is False
    assert discover_technology(current, CAMP_NAVIGATION.technology_id) is None

    with_surveying = discover_technology(current, CAMP_SURVEYING.technology_id)
    assert with_surveying is not None
    assert prerequisites_met(with_surveying, CAMP_NAVIGATION) is True
    with_navigation = discover_technology(with_surveying, CAMP_NAVIGATION.technology_id)
    assert with_navigation is not None
    assert with_navigation.technologies[16].discovered is True


def test_cartography_locked_until_navigation_discovered() -> None:
    """Cartography cannot be discovered until navigation is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_CARTOGRAPHY) is False
    assert discover_technology(world, CAMP_CARTOGRAPHY.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_CARTOGRAPHY) is False
    assert discover_technology(current, CAMP_CARTOGRAPHY.technology_id) is None

    with_navigation = discover_technology(current, CAMP_NAVIGATION.technology_id)
    assert with_navigation is not None
    assert prerequisites_met(with_navigation, CAMP_CARTOGRAPHY) is True
    with_cartography = discover_technology(
        with_navigation, CAMP_CARTOGRAPHY.technology_id
    )
    assert with_cartography is not None
    assert with_cartography.technologies[17].discovered is True


def test_seafaring_locked_until_cartography_discovered() -> None:
    """Seafaring cannot be discovered until cartography is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_SEAFARING) is False
    assert discover_technology(world, CAMP_SEAFARING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_SEAFARING) is False
    assert discover_technology(current, CAMP_SEAFARING.technology_id) is None

    with_cartography = discover_technology(current, CAMP_CARTOGRAPHY.technology_id)
    assert with_cartography is not None
    assert prerequisites_met(with_cartography, CAMP_SEAFARING) is True
    with_seafaring = discover_technology(with_cartography, CAMP_SEAFARING.technology_id)
    assert with_seafaring is not None
    assert with_seafaring.technologies[18].discovered is True


def test_agriculture_locked_until_seafaring_discovered() -> None:
    """Agriculture cannot be discovered until seafaring is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_AGRICULTURE) is False
    assert discover_technology(world, CAMP_AGRICULTURE.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_AGRICULTURE) is False
    assert discover_technology(current, CAMP_AGRICULTURE.technology_id) is None

    with_seafaring = discover_technology(current, CAMP_SEAFARING.technology_id)
    assert with_seafaring is not None
    assert prerequisites_met(with_seafaring, CAMP_AGRICULTURE) is True
    with_agriculture = discover_technology(
        with_seafaring, CAMP_AGRICULTURE.technology_id
    )
    assert with_agriculture is not None
    assert with_agriculture.technologies[19].discovered is True


def test_crop_rotation_locked_until_agriculture_discovered() -> None:
    """Crop rotation cannot be discovered until agriculture is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_CROP_ROTATION) is False
    assert discover_technology(world, CAMP_CROP_ROTATION.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_CROP_ROTATION) is False
    assert discover_technology(current, CAMP_CROP_ROTATION.technology_id) is None

    with_agriculture = discover_technology(current, CAMP_AGRICULTURE.technology_id)
    assert with_agriculture is not None
    assert prerequisites_met(with_agriculture, CAMP_CROP_ROTATION) is True
    with_crop_rotation = discover_technology(
        with_agriculture, CAMP_CROP_ROTATION.technology_id
    )
    assert with_crop_rotation is not None
    assert with_crop_rotation.technologies[20].discovered is True


def test_forestry_locked_until_crop_rotation_discovered() -> None:
    """Forestry cannot be discovered until crop rotation is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_FORESTRY) is False
    assert discover_technology(world, CAMP_FORESTRY.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_FORESTRY) is False
    assert discover_technology(current, CAMP_FORESTRY.technology_id) is None

    with_crop_rotation = discover_technology(
        current, CAMP_CROP_ROTATION.technology_id
    )
    assert with_crop_rotation is not None
    assert prerequisites_met(with_crop_rotation, CAMP_FORESTRY) is True
    with_forestry = discover_technology(
        with_crop_rotation, CAMP_FORESTRY.technology_id
    )
    assert with_forestry is not None
    assert with_forestry.technologies[21].discovered is True


def test_textiles_locked_until_forestry_discovered() -> None:
    """Textiles cannot be discovered until forestry is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_TEXTILES) is False
    assert discover_technology(world, CAMP_TEXTILES.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_TEXTILES) is False
    assert discover_technology(current, CAMP_TEXTILES.technology_id) is None

    with_forestry = discover_technology(current, CAMP_FORESTRY.technology_id)
    assert with_forestry is not None
    assert prerequisites_met(with_forestry, CAMP_TEXTILES) is True
    with_textiles = discover_technology(
        with_forestry, CAMP_TEXTILES.technology_id
    )
    assert with_textiles is not None
    assert with_textiles.technologies[22].discovered is True


def test_dyeing_locked_until_textiles_discovered() -> None:
    """Dyeing cannot be discovered until textiles is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_DYEING) is False
    assert discover_technology(world, CAMP_DYEING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_DYEING) is False
    assert discover_technology(current, CAMP_DYEING.technology_id) is None

    with_textiles = discover_technology(current, CAMP_TEXTILES.technology_id)
    assert with_textiles is not None
    assert prerequisites_met(with_textiles, CAMP_DYEING) is True
    with_dyeing = discover_technology(
        with_textiles, CAMP_DYEING.technology_id
    )
    assert with_dyeing is not None
    assert with_dyeing.technologies[23].discovered is True


def test_tanning_locked_until_dyeing_discovered() -> None:
    """Tanning cannot be discovered until dyeing is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_TANNING) is False
    assert discover_technology(world, CAMP_TANNING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_TANNING) is False
    assert discover_technology(current, CAMP_TANNING.technology_id) is None

    with_dyeing = discover_technology(current, CAMP_DYEING.technology_id)
    assert with_dyeing is not None
    assert prerequisites_met(with_dyeing, CAMP_TANNING) is True
    with_tanning = discover_technology(
        with_dyeing, CAMP_TANNING.technology_id
    )
    assert with_tanning is not None
    assert with_tanning.technologies[24].discovered is True


def test_mining_locked_until_tanning_discovered() -> None:
    """Mining cannot be discovered until tanning is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_MINING) is False
    assert discover_technology(world, CAMP_MINING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_MINING) is False
    assert discover_technology(current, CAMP_MINING.technology_id) is None

    with_tanning = discover_technology(current, CAMP_TANNING.technology_id)
    assert with_tanning is not None
    assert prerequisites_met(with_tanning, CAMP_MINING) is True
    with_mining = discover_technology(
        with_tanning, CAMP_MINING.technology_id
    )
    assert with_mining is not None
    assert with_mining.technologies[25].discovered is True


def test_smithing_locked_until_mining_discovered() -> None:
    """Smithing cannot be discovered until mining is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_SMITHING) is False
    assert discover_technology(world, CAMP_SMITHING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
        CAMP_TANNING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_SMITHING) is False
    assert discover_technology(current, CAMP_SMITHING.technology_id) is None

    with_mining = discover_technology(current, CAMP_MINING.technology_id)
    assert with_mining is not None
    assert prerequisites_met(with_mining, CAMP_SMITHING) is True
    with_smithing = discover_technology(
        with_mining, CAMP_SMITHING.technology_id
    )
    assert with_smithing is not None
    assert with_smithing.technologies[26].discovered is True


def test_toolmaking_locked_until_smithing_discovered() -> None:
    """Toolmaking cannot be discovered until smithing is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_TOOLMAKING) is False
    assert discover_technology(world, CAMP_TOOLMAKING.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
        CAMP_TANNING,
        CAMP_MINING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_TOOLMAKING) is False
    assert discover_technology(current, CAMP_TOOLMAKING.technology_id) is None

    with_smithing = discover_technology(current, CAMP_SMITHING.technology_id)
    assert with_smithing is not None
    assert prerequisites_met(with_smithing, CAMP_TOOLMAKING) is True
    with_toolmaking = discover_technology(
        with_smithing, CAMP_TOOLMAKING.technology_id
    )
    assert with_toolmaking is not None
    assert with_toolmaking.technologies[27].discovered is True


def test_carpentry_locked_until_toolmaking_discovered() -> None:
    """Carpentry cannot be discovered until toolmaking is already known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=default_technologies(),
    )
    assert prerequisites_met(world, CAMP_CARPENTRY) is False
    assert discover_technology(world, CAMP_CARPENTRY.technology_id) is None

    current = world
    for technology in (
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
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
        CAMP_NAVIGATION,
        CAMP_CARTOGRAPHY,
        CAMP_SEAFARING,
        CAMP_AGRICULTURE,
        CAMP_CROP_ROTATION,
        CAMP_FORESTRY,
        CAMP_TEXTILES,
        CAMP_DYEING,
        CAMP_TANNING,
        CAMP_MINING,
        CAMP_SMITHING,
    ):
        updated = discover_technology(current, technology.technology_id)
        assert updated is not None
        current = updated
    assert prerequisites_met(current, CAMP_CARPENTRY) is False
    assert discover_technology(current, CAMP_CARPENTRY.technology_id) is None

    with_toolmaking = discover_technology(current, CAMP_TOOLMAKING.technology_id)
    assert with_toolmaking is not None
    assert prerequisites_met(with_toolmaking, CAMP_CARPENTRY) is True
    with_carpentry = discover_technology(
        with_toolmaking, CAMP_CARPENTRY.technology_id
    )
    assert with_carpentry is not None
    assert with_carpentry.technologies[28].discovered is True


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
