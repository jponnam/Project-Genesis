"""Unit tests for the KnowledgeSystem."""

from __future__ import annotations

from civitas.domain import (
    FIRE_FACT,
    POTTERY_FACT,
    KnowledgeLearned,
    KnowledgeObserved,
    SimulationConfig,
)
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import KnowledgeConfig, KnowledgeSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one knowledge census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = KnowledgeSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, KnowledgeObserved)]
    assert len(events) == 1
    assert events[0].living_count == 3
    assert events[0].fire_knower_count == 3
    assert events[0].pottery_knower_count == 0
    assert events[0].coverage_bps == 10_000


def test_observe_can_suppress_events() -> None:
    """KnowledgeConfig.emit_events=False skips publishing."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    KnowledgeSystem(KnowledgeConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_apply_knowledge_disabled_is_noop() -> None:
    """KnowledgeConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = KnowledgeSystem(KnowledgeConfig(enabled=False)).apply_knowledge(
        world, bus=bus
    )
    assert updated == world
    assert bus.history == ()


def test_engine_seeds_fire_and_bootstraps_pottery() -> None:
    """Founders know fire; pottery bootstraps to a knower on discovery."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=10, agent_count=3))
    living = result.world.alive_agents()
    assert all(agent.knowledge.knows(FIRE_FACT) for agent in living)
    pottery_knowers = [agent for agent in living if agent.knowledge.knows(POTTERY_FACT)]
    # Peer teaching requires co-location; movement may leave only bootstrap.
    assert len(pottery_knowers) >= 1
    learned = [event for event in result.events if isinstance(event, KnowledgeLearned)]
    bootstrap = [
        event
        for event in learned
        if event.fact == POTTERY_FACT and event.source == "bootstrap"
    ]
    assert len(bootstrap) == 1
    assert bootstrap[0].tick.value == 10
    observed = [
        event for event in result.events if isinstance(event, KnowledgeObserved)
    ]
    assert observed[0].tick.value == 0
    assert observed[0].fire_knower_count == 3
    assert observed[-1].pottery_knower_count >= 1
