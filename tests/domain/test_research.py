"""Unit tests for research progress models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_ASTRONOMY,
    CAMP_ASTRONOMY_RESEARCH,
    CAMP_FIRE,
    CAMP_IRRIGATION,
    CAMP_IRRIGATION_RESEARCH,
    CAMP_LOCATION,
    CAMP_LOGIC,
    CAMP_LOGIC_RESEARCH,
    CAMP_MATHEMATICS,
    CAMP_MATHEMATICS_RESEARCH,
    CAMP_METALLURGY,
    CAMP_METALLURGY_RESEARCH,
    CAMP_PHILOSOPHY,
    CAMP_PHILOSOPHY_RESEARCH,
    CAMP_POTTERY,
    CAMP_POTTERY_RESEARCH,
    CAMP_RHETORIC,
    CAMP_RHETORIC_RESEARCH,
    CAMP_SYLLOGISM,
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


def test_default_research_progress_seeds_pottery_through_rhetoric() -> None:
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
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_LOGIC.technology_id
    ]
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
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_LOGIC.technology_id
    ]
    rhetoric = research_by_technology_id(world, CAMP_RHETORIC.technology_id)
    assert rhetoric == CAMP_RHETORIC_RESEARCH

    with_logic = discover_technology(world, CAMP_LOGIC.technology_id)
    assert with_logic is not None
    world, outcomes = advance_research(with_logic, points_per_tick=1)
    assert [outcome.technology_id for outcome in outcomes] == [
        CAMP_RHETORIC.technology_id
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
