"""Unit tests for research progress models and helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_FIRE,
    CAMP_LOCATION,
    CAMP_POTTERY,
    CAMP_POTTERY_RESEARCH,
    Agent,
    ResearchProgress,
    SimulationConfig,
    Technology,
    TechnologyKind,
    World,
    advance_research,
    census_research,
    default_research_progress,
    default_technologies,
    research_by_technology_id,
)


def _world(
    *agents: Agent,
    technologies: tuple[Technology, ...] | None = None,
    research_progress: tuple[ResearchProgress, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(default_technologies() if technologies is None else technologies),
        research_progress=research_progress,
        agents=agents,
    )


def test_default_research_progress_seeds_pottery() -> None:
    """Canonical research tracks undiscovered pottery at zero points."""
    assert default_research_progress() == (CAMP_POTTERY_RESEARCH,)
    assert CAMP_POTTERY_RESEARCH.technology_id == CAMP_POTTERY.technology_id
    assert CAMP_POTTERY_RESEARCH.points == 0
    assert CAMP_POTTERY_RESEARCH.threshold == 10


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
    assert world.research_progress == ()
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
    assert world.research_progress == ()
    assert world.technologies[1].discovered is True


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
