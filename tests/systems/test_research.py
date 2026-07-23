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
    assert events[0].progress_count == 36
    assert events[0].total_points == 0
    assert events[0].total_threshold == 360
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
    assert len(result.world.research_progress) == 35
    assert result.world.research_progress[0].technology_id.value == 2
    assert result.world.research_progress[0].points == 0
    assert result.world.research_progress[1].technology_id.value == 3
    assert result.world.research_progress[1].points == 0
    assert result.world.research_progress[2].technology_id.value == 4
    assert result.world.research_progress[2].points == 0
    assert result.world.research_progress[3].technology_id.value == 5
    assert result.world.research_progress[3].points == 0
    assert result.world.research_progress[4].technology_id.value == 6
    assert result.world.research_progress[4].points == 0
    assert result.world.research_progress[5].technology_id.value == 7
    assert result.world.research_progress[5].points == 0
    assert result.world.research_progress[6].technology_id.value == 8
    assert result.world.research_progress[6].points == 0
    assert result.world.research_progress[7].technology_id.value == 9
    assert result.world.research_progress[7].points == 0
    assert result.world.research_progress[8].technology_id.value == 10
    assert result.world.research_progress[8].points == 0
    assert result.world.research_progress[9].technology_id.value == 11
    assert result.world.research_progress[9].points == 0
    assert result.world.research_progress[10].technology_id.value == 12
    assert result.world.research_progress[10].points == 0
    assert result.world.research_progress[11].technology_id.value == 13
    assert result.world.research_progress[11].points == 0
    assert result.world.research_progress[12].technology_id.value == 14
    assert result.world.research_progress[12].points == 0
    assert result.world.research_progress[13].technology_id.value == 15
    assert result.world.research_progress[13].points == 0
    assert result.world.research_progress[14].technology_id.value == 16
    assert result.world.research_progress[14].points == 0
    assert result.world.research_progress[15].technology_id.value == 17
    assert result.world.research_progress[15].points == 0
    assert result.world.research_progress[16].technology_id.value == 18
    assert result.world.research_progress[16].points == 0
    assert result.world.research_progress[17].technology_id.value == 19
    assert result.world.research_progress[17].points == 0
    assert result.world.research_progress[18].technology_id.value == 20
    assert result.world.research_progress[18].points == 0
    assert result.world.research_progress[19].technology_id.value == 21
    assert result.world.research_progress[19].points == 0
    assert result.world.research_progress[20].technology_id.value == 22
    assert result.world.research_progress[20].points == 0
    assert result.world.research_progress[21].technology_id.value == 23
    assert result.world.research_progress[21].points == 0
    assert result.world.research_progress[22].technology_id.value == 24
    assert result.world.research_progress[22].points == 0
    assert result.world.research_progress[23].technology_id.value == 25
    assert result.world.research_progress[23].points == 0
    assert result.world.research_progress[24].technology_id.value == 26
    assert result.world.research_progress[24].points == 0
    assert result.world.research_progress[25].technology_id.value == 27
    assert result.world.research_progress[25].points == 0
    assert result.world.research_progress[26].technology_id.value == 28
    assert result.world.research_progress[26].points == 0
    assert result.world.research_progress[27].technology_id.value == 29
    assert result.world.research_progress[27].points == 0
    assert result.world.research_progress[28].technology_id.value == 30
    assert result.world.research_progress[28].points == 0
    assert result.world.research_progress[29].technology_id.value == 31
    assert result.world.research_progress[29].points == 0
    discovered = [
        event for event in result.events if isinstance(event, TechnologyDiscovered)
    ]
    assert len(discovered) == 1
    assert discovered[0].tick.value == 10
