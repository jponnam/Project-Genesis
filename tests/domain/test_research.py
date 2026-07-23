"""Unit tests for research progress models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_AGRICULTURE,
    CAMP_AGRICULTURE_RESEARCH,
    CAMP_ANATOMY,
    CAMP_ANATOMY_RESEARCH,
    CAMP_ARCHITECTURE,
    CAMP_ARCHITECTURE_RESEARCH,
    CAMP_ASTRONOMY,
    CAMP_ASTRONOMY_RESEARCH,
    CAMP_CABINETRY,
    CAMP_CABINETRY_RESEARCH,
    CAMP_CARPENTRY,
    CAMP_CARPENTRY_RESEARCH,
    CAMP_CARTOGRAPHY,
    CAMP_CARTOGRAPHY_RESEARCH,
    CAMP_CERAMICS,
    CAMP_CERAMICS_RESEARCH,
    CAMP_CROP_ROTATION,
    CAMP_CROP_ROTATION_RESEARCH,
    CAMP_DYEING,
    CAMP_DYEING_RESEARCH,
    CAMP_ENGINEERING,
    CAMP_ENGINEERING_RESEARCH,
    CAMP_FIRE,
    CAMP_FORESTRY,
    CAMP_FORESTRY_RESEARCH,
    CAMP_GLAZING,
    CAMP_GLAZING_RESEARCH,
    CAMP_HYGIENE,
    CAMP_HYGIENE_RESEARCH,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_RESEARCH,
    CAMP_JOINERY,
    CAMP_JOINERY_RESEARCH,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_LOGIC_RESEARCH,
    CAMP_MATHEMATICS,
    CAMP_MATHEMATICS_RESEARCH,
    CAMP_MEDICINE,
    CAMP_MEDICINE_RESEARCH,
    CAMP_METALLURGY,
    CAMP_METALLURGY_RESEARCH,
    CAMP_MINING,
    CAMP_MINING_RESEARCH,
    CAMP_NAVIGATION,
    CAMP_NAVIGATION_RESEARCH,
    CAMP_PHILOSOPHY,
    CAMP_PHILOSOPHY_RESEARCH,
    CAMP_POTTERY,
    CAMP_POTTERY_RESEARCH,
    CAMP_RHETORIC,
    CAMP_RHETORIC_RESEARCH,
    CAMP_SEAFARING,
    CAMP_SEAFARING_RESEARCH,
    CAMP_SMITHING,
    CAMP_SMITHING_RESEARCH,
    CAMP_SURVEYING,
    CAMP_SURVEYING_RESEARCH,
    CAMP_SYLLOGISM,
    CAMP_TANNING,
    CAMP_TANNING_RESEARCH,
    CAMP_TEXTILES,
    CAMP_TEXTILES_RESEARCH,
    CAMP_TOOLMAKING,
    CAMP_TOOLMAKING_RESEARCH,
    CAMP_WRITING,
    CAMP_WRITING_RESEARCH,
    Agent,
    Innovation,
    ResearchProgress,
    SimulationConfig,
    Technology,
    TechnologyKind,
    World,
    advance_research,
    census_research,
    default_innovations,
    default_research_progress,
    default_technologies,
    discover_technology,
    research_by_technology_id,
)


def _world(
    *agents: Agent,
    technologies: tuple[Technology, ...] | None = None,
    research_progress: tuple[ResearchProgress, ...] = (),
    innovations: tuple[Innovation, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(default_technologies() if technologies is None else technologies),
        research_progress=research_progress,
        innovations=innovations,
        agents=agents,
    )


def test_default_research_progress_seeds_pottery_through_glazing() -> None:
    """Canonical research tracks undiscovered technologies at zero points."""
    assert default_research_progress() == (
        CAMP_POTTERY_RESEARCH,
        CAMP_IRRIGATION_RESEARCH,
        CAMP_METALLURGY_RESEARCH,
        CAMP_WRITING_RESEARCH,
        CAMP_MATHEMATICS_RESEARCH,
        CAMP_ASTRONOMY_RESEARCH,
        CAMP_PHILOSOPHY_RESEARCH,
        CAMP_LOGIC_RESEARCH,
        CAMP_RHETORIC_RESEARCH,
        CAMP_MEDICINE_RESEARCH,
        CAMP_ANATOMY_RESEARCH,
        CAMP_HYGIENE_RESEARCH,
        CAMP_ENGINEERING_RESEARCH,
        CAMP_ARCHITECTURE_RESEARCH,
        CAMP_SURVEYING_RESEARCH,
        CAMP_NAVIGATION_RESEARCH,
        CAMP_CARTOGRAPHY_RESEARCH,
        CAMP_SEAFARING_RESEARCH,
        CAMP_AGRICULTURE_RESEARCH,
        CAMP_CROP_ROTATION_RESEARCH,
        CAMP_FORESTRY_RESEARCH,
        CAMP_TEXTILES_RESEARCH,
        CAMP_DYEING_RESEARCH,
        CAMP_TANNING_RESEARCH,
        CAMP_MINING_RESEARCH,
        CAMP_SMITHING_RESEARCH,
        CAMP_TOOLMAKING_RESEARCH,
        CAMP_CARPENTRY_RESEARCH,
        CAMP_JOINERY_RESEARCH,
        CAMP_CABINETRY_RESEARCH,
        CAMP_CERAMICS_RESEARCH,
        CAMP_GLAZING_RESEARCH,
    )
    assert CAMP_POTTERY_RESEARCH.technology_id == CAMP_POTTERY.technology_id
    assert CAMP_POTTERY_RESEARCH.points == 0
    assert CAMP_POTTERY_RESEARCH.threshold == 10
    assert CAMP_IRRIGATION_RESEARCH.technology_id == CAMP_IRRIGATION.technology_id
    assert CAMP_IRRIGATION_RESEARCH.points == 0
    assert CAMP_IRRIGATION_RESEARCH.threshold == 10
    assert CAMP_METALLURGY_RESEARCH.technology_id == CAMP_METALLURGY.technology_id
    assert CAMP_METALLURGY_RESEARCH.points == 0
    assert CAMP_METALLURGY_RESEARCH.threshold == 10
    assert CAMP_WRITING_RESEARCH.technology_id == CAMP_WRITING.technology_id
    assert CAMP_WRITING_RESEARCH.points == 0
    assert CAMP_WRITING_RESEARCH.threshold == 10
    assert CAMP_MATHEMATICS_RESEARCH.technology_id == CAMP_MATHEMATICS.technology_id
    assert CAMP_MATHEMATICS_RESEARCH.points == 0
    assert CAMP_MATHEMATICS_RESEARCH.threshold == 10
    assert CAMP_ASTRONOMY_RESEARCH.technology_id == CAMP_ASTRONOMY.technology_id
    assert CAMP_ASTRONOMY_RESEARCH.points == 0
    assert CAMP_ASTRONOMY_RESEARCH.threshold == 10
    assert CAMP_PHILOSOPHY_RESEARCH.technology_id == CAMP_PHILOSOPHY.technology_id
    assert CAMP_PHILOSOPHY_RESEARCH.points == 0
    assert CAMP_PHILOSOPHY_RESEARCH.threshold == 10
    assert CAMP_LOGIC_RESEARCH.technology_id == CAMP_LOGIC.technology_id
    assert CAMP_LOGIC_RESEARCH.points == 0
    assert CAMP_LOGIC_RESEARCH.threshold == 10
    assert CAMP_RHETORIC_RESEARCH.technology_id == CAMP_RHETORIC.technology_id
    assert CAMP_RHETORIC_RESEARCH.points == 0
    assert CAMP_RHETORIC_RESEARCH.threshold == 10
    assert CAMP_MEDICINE_RESEARCH.technology_id == CAMP_MEDICINE.technology_id
    assert CAMP_MEDICINE_RESEARCH.points == 0
    assert CAMP_MEDICINE_RESEARCH.threshold == 10
    assert CAMP_ANATOMY_RESEARCH.technology_id == CAMP_ANATOMY.technology_id
    assert CAMP_ANATOMY_RESEARCH.points == 0
    assert CAMP_ANATOMY_RESEARCH.threshold == 10
    assert CAMP_HYGIENE_RESEARCH.technology_id == CAMP_HYGIENE.technology_id
    assert CAMP_HYGIENE_RESEARCH.points == 0
    assert CAMP_HYGIENE_RESEARCH.threshold == 10
    assert CAMP_ENGINEERING_RESEARCH.technology_id == CAMP_ENGINEERING.technology_id
    assert CAMP_ENGINEERING_RESEARCH.points == 0
    assert CAMP_ENGINEERING_RESEARCH.threshold == 10
    assert CAMP_ARCHITECTURE_RESEARCH.technology_id == CAMP_ARCHITECTURE.technology_id
    assert CAMP_ARCHITECTURE_RESEARCH.points == 0
    assert CAMP_ARCHITECTURE_RESEARCH.threshold == 10
    assert CAMP_SURVEYING_RESEARCH.technology_id == CAMP_SURVEYING.technology_id
    assert CAMP_SURVEYING_RESEARCH.points == 0
    assert CAMP_SURVEYING_RESEARCH.threshold == 10
    assert CAMP_NAVIGATION_RESEARCH.technology_id == CAMP_NAVIGATION.technology_id
    assert CAMP_NAVIGATION_RESEARCH.points == 0
    assert CAMP_NAVIGATION_RESEARCH.threshold == 10
    assert CAMP_CARTOGRAPHY_RESEARCH.technology_id == CAMP_CARTOGRAPHY.technology_id
    assert CAMP_CARTOGRAPHY_RESEARCH.points == 0
    assert CAMP_CARTOGRAPHY_RESEARCH.threshold == 10
    assert CAMP_SEAFARING_RESEARCH.technology_id == CAMP_SEAFARING.technology_id
    assert CAMP_SEAFARING_RESEARCH.points == 0
    assert CAMP_SEAFARING_RESEARCH.threshold == 10
    assert CAMP_AGRICULTURE_RESEARCH.technology_id == CAMP_AGRICULTURE.technology_id
    assert CAMP_AGRICULTURE_RESEARCH.points == 0
    assert CAMP_AGRICULTURE_RESEARCH.threshold == 10
    assert CAMP_CROP_ROTATION_RESEARCH.technology_id == CAMP_CROP_ROTATION.technology_id
    assert CAMP_CROP_ROTATION_RESEARCH.points == 0
    assert CAMP_CROP_ROTATION_RESEARCH.threshold == 10
    assert CAMP_FORESTRY_RESEARCH.technology_id == CAMP_FORESTRY.technology_id
    assert CAMP_FORESTRY_RESEARCH.points == 0
    assert CAMP_FORESTRY_RESEARCH.threshold == 10
    assert CAMP_TEXTILES_RESEARCH.technology_id == CAMP_TEXTILES.technology_id
    assert CAMP_TEXTILES_RESEARCH.points == 0
    assert CAMP_TEXTILES_RESEARCH.threshold == 10
    assert CAMP_DYEING_RESEARCH.technology_id == CAMP_DYEING.technology_id
    assert CAMP_DYEING_RESEARCH.points == 0
    assert CAMP_DYEING_RESEARCH.threshold == 10
    assert CAMP_TANNING_RESEARCH.technology_id == CAMP_TANNING.technology_id
    assert CAMP_TANNING_RESEARCH.points == 0
    assert CAMP_TANNING_RESEARCH.threshold == 10
    assert CAMP_MINING_RESEARCH.technology_id == CAMP_MINING.technology_id
    assert CAMP_MINING_RESEARCH.points == 0
    assert CAMP_MINING_RESEARCH.threshold == 10
    assert CAMP_SMITHING_RESEARCH.technology_id == CAMP_SMITHING.technology_id
    assert CAMP_SMITHING_RESEARCH.points == 0
    assert CAMP_SMITHING_RESEARCH.threshold == 10
    assert CAMP_TOOLMAKING_RESEARCH.technology_id == CAMP_TOOLMAKING.technology_id
    assert CAMP_TOOLMAKING_RESEARCH.points == 0
    assert CAMP_TOOLMAKING_RESEARCH.threshold == 10
    assert CAMP_CARPENTRY_RESEARCH.technology_id == CAMP_CARPENTRY.technology_id
    assert CAMP_CARPENTRY_RESEARCH.points == 0
    assert CAMP_CARPENTRY_RESEARCH.threshold == 10
    assert CAMP_JOINERY_RESEARCH.technology_id == CAMP_JOINERY.technology_id
    assert CAMP_JOINERY_RESEARCH.points == 0
    assert CAMP_JOINERY_RESEARCH.threshold == 10
    assert CAMP_CABINETRY_RESEARCH.technology_id == CAMP_CABINETRY.technology_id
    assert CAMP_CABINETRY_RESEARCH.points == 0
    assert CAMP_CABINETRY_RESEARCH.threshold == 10
    assert CAMP_CERAMICS_RESEARCH.technology_id == CAMP_CERAMICS.technology_id
    assert CAMP_CERAMICS_RESEARCH.points == 0
    assert CAMP_CERAMICS_RESEARCH.threshold == 10
    assert CAMP_GLAZING_RESEARCH.technology_id == CAMP_GLAZING.technology_id
    assert CAMP_GLAZING_RESEARCH.points == 0
    assert CAMP_GLAZING_RESEARCH.threshold == 10


def test_advance_research_increments_and_discovers() -> None:
    """Points accumulate until threshold, then pottery is discovered."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
    world, outcomes = advance_research(world, points_per_tick=1)
    assert len(outcomes) == 1
    assert outcomes[0].points_after == 1
    assert outcomes[0].discovered is False
    assert research_by_technology_id(world, 1) is not None
    assert world.technologies[1].discovered is False

    for _ in range(9):
        world, outcomes = advance_research(world, points_per_tick=1)
    assert outcomes[0].discovered is True
    assert world.research_progress == (
        CAMP_IRRIGATION_RESEARCH,
        CAMP_METALLURGY_RESEARCH,
        CAMP_WRITING_RESEARCH,
        CAMP_MATHEMATICS_RESEARCH,
        CAMP_ASTRONOMY_RESEARCH,
        CAMP_PHILOSOPHY_RESEARCH,
        CAMP_LOGIC_RESEARCH,
        CAMP_RHETORIC_RESEARCH,
        CAMP_MEDICINE_RESEARCH,
        CAMP_ANATOMY_RESEARCH,
        CAMP_HYGIENE_RESEARCH,
        CAMP_ENGINEERING_RESEARCH,
        CAMP_ARCHITECTURE_RESEARCH,
        CAMP_SURVEYING_RESEARCH,
        CAMP_NAVIGATION_RESEARCH,
        CAMP_CARTOGRAPHY_RESEARCH,
        CAMP_SEAFARING_RESEARCH,
        CAMP_AGRICULTURE_RESEARCH,
        CAMP_CROP_ROTATION_RESEARCH,
        CAMP_FORESTRY_RESEARCH,
        CAMP_TEXTILES_RESEARCH,
        CAMP_DYEING_RESEARCH,
        CAMP_TANNING_RESEARCH,
        CAMP_MINING_RESEARCH,
        CAMP_SMITHING_RESEARCH,
        CAMP_TOOLMAKING_RESEARCH,
        CAMP_CARPENTRY_RESEARCH,
        CAMP_JOINERY_RESEARCH,
        CAMP_CABINETRY_RESEARCH,
        CAMP_CERAMICS_RESEARCH,
        CAMP_GLAZING_RESEARCH,
    )
    assert world.technologies[1].discovered is True
    assert world.technologies[1].kind is TechnologyKind.POTTERY


def test_advance_research_large_step_discovers_immediately() -> None:
    """A points_per_tick that meets threshold discovers in one apply."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
    world, outcomes = advance_research(world, points_per_tick=10)
    assert outcomes[0].discovered is True
    assert outcomes[0].points_after == 10
    assert world.research_progress == (
        CAMP_IRRIGATION_RESEARCH,
        CAMP_METALLURGY_RESEARCH,
        CAMP_WRITING_RESEARCH,
        CAMP_MATHEMATICS_RESEARCH,
        CAMP_ASTRONOMY_RESEARCH,
        CAMP_PHILOSOPHY_RESEARCH,
        CAMP_LOGIC_RESEARCH,
        CAMP_RHETORIC_RESEARCH,
        CAMP_MEDICINE_RESEARCH,
        CAMP_ANATOMY_RESEARCH,
        CAMP_HYGIENE_RESEARCH,
        CAMP_ENGINEERING_RESEARCH,
        CAMP_ARCHITECTURE_RESEARCH,
        CAMP_SURVEYING_RESEARCH,
        CAMP_NAVIGATION_RESEARCH,
        CAMP_CARTOGRAPHY_RESEARCH,
        CAMP_SEAFARING_RESEARCH,
        CAMP_AGRICULTURE_RESEARCH,
        CAMP_CROP_ROTATION_RESEARCH,
        CAMP_FORESTRY_RESEARCH,
        CAMP_TEXTILES_RESEARCH,
        CAMP_DYEING_RESEARCH,
        CAMP_TANNING_RESEARCH,
        CAMP_MINING_RESEARCH,
        CAMP_SMITHING_RESEARCH,
        CAMP_TOOLMAKING_RESEARCH,
        CAMP_CARPENTRY_RESEARCH,
        CAMP_JOINERY_RESEARCH,
        CAMP_CABINETRY_RESEARCH,
        CAMP_CERAMICS_RESEARCH,
        CAMP_GLAZING_RESEARCH,
    )
    assert world.technologies[1].discovered is True


def test_irrigation_research_locked_until_pottery_discovered() -> None:
    """Irrigation progress is preserved but blocked until pottery is discovered."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
    world, outcomes = advance_research(world, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_POTTERY.technology_id
    ]
    irrigation = research_by_technology_id(world, CAMP_IRRIGATION.technology_id)
    assert irrigation == CAMP_IRRIGATION_RESEARCH
    metallurgy = research_by_technology_id(world, CAMP_METALLURGY.technology_id)
    assert metallurgy == CAMP_METALLURGY_RESEARCH
    writing = research_by_technology_id(world, CAMP_WRITING.technology_id)
    assert writing == CAMP_WRITING_RESEARCH
    mathematics = research_by_technology_id(world, CAMP_MATHEMATICS.technology_id)
    assert mathematics == CAMP_MATHEMATICS_RESEARCH
    astronomy = research_by_technology_id(world, CAMP_ASTRONOMY.technology_id)
    assert astronomy == CAMP_ASTRONOMY_RESEARCH
    philosophy = research_by_technology_id(world, CAMP_PHILOSOPHY.technology_id)
    assert philosophy == CAMP_PHILOSOPHY_RESEARCH
    logic = research_by_technology_id(world, CAMP_LOGIC.technology_id)
    assert logic == CAMP_LOGIC_RESEARCH
    rhetoric = research_by_technology_id(world, CAMP_RHETORIC.technology_id)
    assert rhetoric == CAMP_RHETORIC_RESEARCH
    medicine = research_by_technology_id(world, CAMP_MEDICINE.technology_id)
    assert medicine == CAMP_MEDICINE_RESEARCH
    anatomy = research_by_technology_id(world, CAMP_ANATOMY.technology_id)
    assert anatomy == CAMP_ANATOMY_RESEARCH
    hygiene = research_by_technology_id(world, CAMP_HYGIENE.technology_id)
    assert hygiene == CAMP_HYGIENE_RESEARCH
    engineering = research_by_technology_id(world, CAMP_ENGINEERING.technology_id)
    assert engineering == CAMP_ENGINEERING_RESEARCH

    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    world, outcomes = advance_research(discovered, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_IRRIGATION.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_metallurgy_research_locked_until_irrigation_discovered() -> None:
    """Metallurgy progress is preserved but blocked until irrigation is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    world, outcomes = advance_research(with_pottery, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_IRRIGATION.technology_id
    ]
    metallurgy = research_by_technology_id(world, CAMP_METALLURGY.technology_id)
    assert metallurgy == CAMP_METALLURGY_RESEARCH

    with_irrigation = discover_technology(world, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    world, outcomes = advance_research(with_irrigation, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_METALLURGY.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_writing_research_locked_until_metallurgy_discovered() -> None:
    """Writing progress is preserved but blocked until metallurgy is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    world, outcomes = advance_research(with_irrigation, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_METALLURGY.technology_id
    ]
    writing = research_by_technology_id(world, CAMP_WRITING.technology_id)
    assert writing == CAMP_WRITING_RESEARCH

    with_metallurgy = discover_technology(world, CAMP_METALLURGY.technology_id)
    assert with_metallurgy is not None
    world, outcomes = advance_research(with_metallurgy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_WRITING.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_mathematics_research_locked_until_writing_discovered() -> None:
    """Mathematics progress is preserved but blocked until writing is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
    with_pottery = discover_technology(world, CAMP_POTTERY.technology_id)
    assert with_pottery is not None
    with_irrigation = discover_technology(with_pottery, CAMP_IRRIGATION.technology_id)
    assert with_irrigation is not None
    with_metallurgy = discover_technology(
        with_irrigation, CAMP_METALLURGY.technology_id
    )
    assert with_metallurgy is not None
    world, outcomes = advance_research(with_metallurgy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_WRITING.technology_id
    ]
    mathematics = research_by_technology_id(world, CAMP_MATHEMATICS.technology_id)
    assert mathematics == CAMP_MATHEMATICS_RESEARCH

    with_writing = discover_technology(world, CAMP_WRITING.technology_id)
    assert with_writing is not None
    world, outcomes = advance_research(with_writing, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_MATHEMATICS.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_astronomy_research_locked_until_mathematics_discovered() -> None:
    """Astronomy progress is preserved but blocked until mathematics is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_writing, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_MATHEMATICS.technology_id
    ]
    astronomy = research_by_technology_id(world, CAMP_ASTRONOMY.technology_id)
    assert astronomy == CAMP_ASTRONOMY_RESEARCH

    with_math = discover_technology(world, CAMP_MATHEMATICS.technology_id)
    assert with_math is not None
    world, outcomes = advance_research(with_math, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_ASTRONOMY.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_philosophy_research_locked_until_astronomy_discovered() -> None:
    """Philosophy progress is preserved but blocked until astronomy is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_math, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_ASTRONOMY.technology_id
    ]
    philosophy = research_by_technology_id(world, CAMP_PHILOSOPHY.technology_id)
    assert philosophy == CAMP_PHILOSOPHY_RESEARCH

    with_astronomy = discover_technology(world, CAMP_ASTRONOMY.technology_id)
    assert with_astronomy is not None
    world, outcomes = advance_research(with_astronomy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_PHILOSOPHY.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_logic_research_locked_until_philosophy_discovered() -> None:
    """Logic progress is preserved but blocked until philosophy is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_astronomy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_PHILOSOPHY.technology_id
    ]
    logic = research_by_technology_id(world, CAMP_LOGIC.technology_id)
    assert logic == CAMP_LOGIC_RESEARCH

    with_philosophy = discover_technology(world, CAMP_PHILOSOPHY.technology_id)
    assert with_philosophy is not None
    world, outcomes = advance_research(with_philosophy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [CAMP_LOGIC.technology_id]
    assert outcomes[0].points_after == 1


def test_rhetoric_research_locked_until_logic_discovered() -> None:
    """Rhetoric progress is preserved but blocked until logic is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_philosophy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [CAMP_LOGIC.technology_id]
    rhetoric = research_by_technology_id(world, CAMP_RHETORIC.technology_id)
    assert rhetoric == CAMP_RHETORIC_RESEARCH

    with_logic = discover_technology(world, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    world, outcomes = advance_research(with_logic, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_RHETORIC.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_medicine_research_locked_until_rhetoric_discovered() -> None:
    """Medicine progress is preserved but blocked until rhetoric is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_logic, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_RHETORIC.technology_id
    ]
    medicine = research_by_technology_id(world, CAMP_MEDICINE.technology_id)
    assert medicine == CAMP_MEDICINE_RESEARCH

    with_rhetoric = discover_technology(world, CAMP_RHETORIC.technology_id)
    assert with_rhetoric is not None
    world, outcomes = advance_research(with_rhetoric, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_MEDICINE.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_anatomy_research_locked_until_medicine_discovered() -> None:
    """Anatomy progress is preserved but blocked until medicine is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_rhetoric, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_MEDICINE.technology_id
    ]
    anatomy = research_by_technology_id(world, CAMP_ANATOMY.technology_id)
    assert anatomy == CAMP_ANATOMY_RESEARCH

    with_medicine = discover_technology(world, CAMP_MEDICINE.technology_id)
    assert with_medicine is not None
    world, outcomes = advance_research(with_medicine, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_ANATOMY.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_hygiene_research_locked_until_anatomy_discovered() -> None:
    """Hygiene progress is preserved but blocked until anatomy is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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
    world, outcomes = advance_research(with_medicine, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_ANATOMY.technology_id
    ]
    hygiene = research_by_technology_id(world, CAMP_HYGIENE.technology_id)
    assert hygiene == CAMP_HYGIENE_RESEARCH

    with_anatomy = discover_technology(world, CAMP_ANATOMY.technology_id)
    assert with_anatomy is not None
    world, outcomes = advance_research(with_anatomy, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_HYGIENE.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_engineering_research_locked_until_hygiene_discovered() -> None:
    """Engineering progress is preserved but blocked until hygiene is known."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=default_research_progress(),
    )
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

    world, outcomes = advance_research(current, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_HYGIENE.technology_id
    ]
    engineering = research_by_technology_id(world, CAMP_ENGINEERING.technology_id)
    assert engineering == CAMP_ENGINEERING_RESEARCH

    with_hygiene = discover_technology(world, CAMP_HYGIENE.technology_id)
    assert with_hygiene is not None
    world, outcomes = advance_research(with_hygiene, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_ENGINEERING.technology_id
    ]
    assert outcomes[0].points_after == 1


def test_active_syllogism_adds_research_point_per_tick() -> None:
    """Active syllogism increases effective research progress by one."""
    discovered_logic = CAMP_LOGIC.model_copy(update={"discovered": True})
    active_syllogism = CAMP_SYLLOGISM.model_copy(update={"active": True})
    world = _world(
        Agent.create(agent_id=0, name="A"),
        technologies=(
            CAMP_FIRE,
            CAMP_POTTERY,
            CAMP_IRRIGATION,
            CAMP_METALLURGY,
            CAMP_WRITING,
            CAMP_MATHEMATICS,
            CAMP_ASTRONOMY,
            CAMP_PHILOSOPHY,
            discovered_logic,
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
            CAMP_JOINERY,
            CAMP_CABINETRY,
            CAMP_CERAMICS,
            CAMP_GLAZING,
        ),
        research_progress=(CAMP_POTTERY_RESEARCH,),
        innovations=tuple(
            active_syllogism
            if item.innovation_id == CAMP_SYLLOGISM.innovation_id
            else item
            for item in default_innovations()
        ),
    )
    world, outcomes = advance_research(world, points_per_tick=1)
    assert outcomes[0].points_before == 0
    assert outcomes[0].points_after == 2
    assert world.research_progress[0].points == 2


def test_census_research_counts() -> None:
    """Census reports aggregate points and completion basis points."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        research_progress=(ResearchProgress.create(1, points=4, threshold=10),),
    )
    snap = census_research(world)
    assert snap.progress_count == 1
    assert snap.total_points == 4
    assert snap.total_threshold == 10
    assert snap.total_remaining == 6
    assert snap.completion_bps == 4_000
    assert census_research(world) == snap


def test_world_rejects_research_on_discovered_technology() -> None:
    """World validation forbids progress rows for discovered technologies."""
    with pytest.raises(ValidationError):
        _world(
            Agent.create(agent_id=0, name="A"),
            technologies=(CAMP_FIRE, CAMP_POTTERY),
            research_progress=(
                ResearchProgress.create(
                    CAMP_FIRE.technology_id.value,
                    points=0,
                    threshold=5,
                ),
            ),
        )


def test_world_rejects_points_above_threshold() -> None:
    """World validation forbids points greater than threshold."""
    with pytest.raises(ValidationError):
        _world(
            Agent.create(agent_id=0, name="A"),
            research_progress=(ResearchProgress.create(1, points=11, threshold=10),),
        )


def test_world_rejects_unknown_research_target() -> None:
    """World validation forbids progress toward missing technologies."""
    with pytest.raises(ValidationError):
        _world(
            Agent.create(agent_id=0, name="A"),
            technologies=(CAMP_FIRE,),
            research_progress=(ResearchProgress.create(1, points=0, threshold=10),),
        )
