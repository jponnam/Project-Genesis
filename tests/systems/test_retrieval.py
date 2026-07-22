"""Unit tests for the RetrievalSystem."""

from __future__ import annotations

from civitas.domain import MemoryRetrieved, RetrievalObserved, SimulationConfig
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import RetrievalConfig, RetrievalSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one retrieval census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = RetrievalSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, RetrievalObserved)]
    assert len(events) == 1
    assert events[0].living_count == 3
    assert events[0].agents_with_context == 0


def test_apply_retrieval_emits_memory_retrieved() -> None:
    """apply_retrieval emits MemoryRetrieved for each living agent."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=1, agent_count=2))
    retrieved = [event for event in result.events if isinstance(event, MemoryRetrieved)]
    assert len(retrieved) == 2
    assert all(event.retrieved_count >= 1 for event in retrieved)
    assert all(agent.working_memory.records for agent in result.world.alive_agents())


def test_apply_retrieval_can_be_disabled() -> None:
    """RetrievalConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = RetrievalSystem(RetrievalConfig(enabled=False)).apply_retrieval(
        world, bus=bus
    )
    assert updated == world
    assert bus.history == ()


def test_engine_retrieves_each_tick_after_planning() -> None:
    """Engine retrieves after planning; founders have context by tick 1."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=2, agent_count=3))
    assert all(agent.working_memory.records for agent in result.world.alive_agents())
    retrieved = [event for event in result.events if isinstance(event, MemoryRetrieved)]
    assert len(retrieved) == 6
    observed = [
        event for event in result.events if isinstance(event, RetrievalObserved)
    ]
    assert len(observed) == 3
    assert observed[0].agents_with_context == 0
    assert observed[-1].agents_with_context == 3
