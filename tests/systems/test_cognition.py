"""Unit tests for the CognitionSystem."""

from __future__ import annotations

from civitas.domain import (
    AgentReflected,
    CognitionObserved,
    MemoryRecorded,
    SimulationConfig,
)
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.llm import SeededMockLanguageModel
from civitas.systems import CognitionConfig, CognitionSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one cognition census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = CognitionSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, CognitionObserved)]
    assert len(events) == 1
    assert events[0].living_count == 3
    assert events[0].total_records == 0
    assert events[0].belief_count == 0


def test_apply_cognition_encodes_and_reflects() -> None:
    """apply_cognition writes episode + reflection memories and beliefs."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    system = CognitionSystem(language_model=SeededMockLanguageModel())
    updated = system.apply_cognition(world.with_tick(world.tick), bus=bus)
    living = updated.alive_agents()
    assert all(len(agent.memory.records) == 2 for agent in living)
    assert all(agent.beliefs.entries for agent in living)
    episodes = [
        event
        for event in bus.history
        if isinstance(event, MemoryRecorded) and event.kind == "episode"
    ]
    reflections = [
        event
        for event in bus.history
        if isinstance(event, MemoryRecorded) and event.kind == "reflection"
    ]
    reflected = [event for event in bus.history if isinstance(event, AgentReflected)]
    assert len(episodes) == 2
    assert len(reflections) == 2
    assert len(reflected) == 2


def test_apply_cognition_can_disable_reflection() -> None:
    """CognitionConfig.reflect=False skips LLM reflection."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = CognitionSystem(CognitionConfig(reflect=False)).apply_cognition(
        world, bus=bus
    )
    assert all(len(agent.memory.records) == 1 for agent in updated.alive_agents())
    assert not any(isinstance(event, AgentReflected) for event in bus.history)


def test_apply_cognition_can_be_disabled() -> None:
    """CognitionConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = CognitionSystem(CognitionConfig(enabled=False)).apply_cognition(
        world, bus=bus
    )
    assert updated == world
    assert bus.history == ()


def test_engine_encodes_and_reflects_each_tick() -> None:
    """Engine writes episode+reflection memories and beliefs each tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=3))
    living = result.world.alive_agents()
    assert all(len(agent.memory.records) == 6 for agent in living)
    assert all(agent.beliefs.entries for agent in living)
    reflected = [event for event in result.events if isinstance(event, AgentReflected)]
    assert len(reflected) == 9
    observed = [
        event for event in result.events if isinstance(event, CognitionObserved)
    ]
    assert len(observed) == 4
    assert observed[0].total_records == 0
    assert observed[-1].total_records == 18
    assert observed[-1].reflection_records == 9
    assert observed[-1].belief_count == 3
