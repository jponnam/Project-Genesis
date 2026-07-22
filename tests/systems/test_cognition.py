"""Unit tests for the CognitionSystem."""

from __future__ import annotations

from civitas.domain import CognitionObserved, MemoryRecorded, SimulationConfig
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


def test_apply_cognition_encodes_memories_without_calling_llm() -> None:
    """apply_cognition writes episode memories even when an LLM is injected."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    model = SeededMockLanguageModel()
    system = CognitionSystem(language_model=model)
    updated = system.apply_cognition(world.with_tick(world.tick), bus=bus)
    assert all(len(agent.memory.records) == 1 for agent in updated.alive_agents())
    recorded = [event for event in bus.history if isinstance(event, MemoryRecorded)]
    assert len(recorded) == 2
    assert all(event.kind == "episode" for event in recorded)
    assert system.language_model is model


def test_apply_cognition_can_be_disabled() -> None:
    """CognitionConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = CognitionSystem(CognitionConfig(enabled=False)).apply_cognition(
        world, bus=bus
    )
    assert updated == world
    assert bus.history == ()


def test_engine_encodes_memories_each_tick() -> None:
    """Engine writes one episode per living agent per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=3))
    living = result.world.alive_agents()
    assert all(len(agent.memory.records) == 3 for agent in living)
    recorded = [event for event in result.events if isinstance(event, MemoryRecorded)]
    assert len(recorded) == 9
    observed = [
        event for event in result.events if isinstance(event, CognitionObserved)
    ]
    assert len(observed) == 4
    assert observed[0].total_records == 0
    assert observed[-1].total_records == 9
