"""Unit tests for the ResearchSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_POTTERY,
    Agent,
    ResearchObserved,
    ResearchProgress,
    ResearchProgressed,
    SimulationConfig,
    TechnologyDiscovered,
    World,
    default_research_progress,
    default_technologies,
)
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import ResearchConfig, ResearchSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one research census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = ResearchSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, ResearchObserved)]
    assert len(events) == 1
    assert events[0].progress_count == 4
    assert events[0].total_points == 0
    assert events[0].total_threshold == 40
    assert events[0].completion_bps == 0


def test_observe_can_suppress_events() -> None:
    """ResearchConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    ResearchSystem(ResearchConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_apply_research_emits_progress_and_discovery() -> None:
    """apply_research publishes progress deltas and discovery on completion."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        research_progress=(
            ResearchProgress.create(
                CAMP_POTTERY.technology_id.value,
                points=9,
                threshold=10,
            ),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    updated = ResearchSystem().apply_research(world, bus=bus)
    assert updated.research_progress == ()
    assert updated.technologies[1].discovered is True
    progressed = [
        event for event in bus.history if isinstance(event, ResearchProgressed)
    ]
    discovered = [
        event for event in bus.history if isinstance(event, TechnologyDiscovered)
    ]
    assert len(progressed) == 1
    assert progressed[0].points_after == 10
    assert progressed[0].delta == 1
    assert len(discovered) == 1
    assert discovered[0].name == "Camp Pottery"
    assert discovered[0].kind == "pottery"


def test_apply_research_can_be_disabled() -> None:
    """ResearchConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = ResearchSystem(ResearchConfig(enabled=False)).apply_research(
        world, bus=bus
    )
    assert updated == world
    assert bus.history == ()


def test_engine_discovers_pottery_by_tick_ten() -> None:
    """Default research discovers pottery on the tenth apply tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=10, agent_count=3))
    assert result.world.technologies[1].discovered is True
    assert len(result.world.research_progress) == 3
    assert result.world.research_progress[0].technology_id.value == 2
    assert result.world.research_progress[0].points == 0
    assert result.world.research_progress[1].technology_id.value == 3
    assert result.world.research_progress[1].points == 0
    assert result.world.research_progress[2].technology_id.value == 4
    assert result.world.research_progress[2].points == 0
    discovered = [
        event for event in result.events if isinstance(event, TechnologyDiscovered)
    ]
    assert len(discovered) == 1
    assert discovered[0].tick.value == 10
