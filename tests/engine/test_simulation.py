"""Unit tests for the SimulationEngine."""

from __future__ import annotations

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentSpawned,
    NeedDecayed,
    SimulationCompleted,
    SimulationConfig,
    SimulationStarted,
    TickCompleted,
    TickStarted,
)
from civitas.engine import EventBus, SimulationEngine


def test_seed_forty_two_runs_are_identical() -> None:
    """Canonical seed 42 must produce identical worlds and event streams."""
    config = SimulationConfig(seed=42, ticks=5, agent_count=4, run_name="r")
    engine = SimulationEngine()
    first = engine.run(config)
    second = engine.run(config)
    assert first.world == second.world
    assert first.ticks_executed == second.ticks_executed == 5
    assert [event.event_type for event in first.events] == [
        event.event_type for event in second.events
    ]
    assert first.events == second.events


def test_research_default_run_is_reproducible() -> None:
    """research_default() simulations compare equal across engine runs."""
    engine = SimulationEngine()
    config = SimulationConfig.research_default()
    # Use fewer ticks for speed while still exercising the full pipeline.
    config = config.model_copy(update={"ticks": 3})
    assert engine.run(config) == engine.run(config)


def test_different_seeds_diverge() -> None:
    """Different seeds must not produce identical final worlds."""
    engine = SimulationEngine()
    left = engine.run(SimulationConfig(seed=1, ticks=3, agent_count=5))
    right = engine.run(SimulationConfig(seed=2, ticks=3, agent_count=5))
    assert left.world != right.world


def test_run_emits_lifecycle_and_tick_events() -> None:
    """A run emits started/spawn/tick/completed events in a valid envelope."""
    config = SimulationConfig(seed=42, ticks=2, agent_count=2)
    result = SimulationEngine().run(config)
    types = [event.event_type for event in result.events]

    assert types[0] == SimulationStarted.__name__
    assert types[1] == AgentSpawned.__name__
    assert types[2] == AgentSpawned.__name__
    assert types.count(TickStarted.__name__) == 2
    assert types.count(TickCompleted.__name__) == 2
    assert types[-1] == SimulationCompleted.__name__
    assert isinstance(result.events[-1], SimulationCompleted)
    assert result.events[-1].ticks_executed == 2
    assert result.world.tick.value == 2


def test_each_tick_selects_and_executes_actions() -> None:
    """Living agents receive ActionSelected and ActionCompleted each tick."""
    config = SimulationConfig(seed=42, ticks=2, agent_count=3)
    result = SimulationEngine().run(config)
    selected = [e for e in result.events if isinstance(e, ActionSelected)]
    completed = [e for e in result.events if isinstance(e, ActionCompleted)]
    assert len(selected) == 2 * 3
    assert len(completed) == 2 * 3
    assert all(event.success for event in completed)


def test_needs_decay_events_occur() -> None:
    """Need decay runs every tick and emits NeedDecayed events."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=1, agent_count=1))
    decayed = [event for event in result.events if isinstance(event, NeedDecayed)]
    assert len(decayed) == 5  # five needs for one agent


def test_run_accepts_external_event_bus() -> None:
    """Caller-supplied buses receive the full event history."""
    bus = EventBus()
    result = SimulationEngine().run(
        SimulationConfig(seed=7, ticks=1, agent_count=1),
        bus=bus,
    )
    assert result.events == bus.history
    assert bus.next_sequence == len(bus.history)


def test_final_world_population_preserved() -> None:
    """Phase 1 runs do not change population size."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=4, agent_count=6))
    assert len(result.world.agents) == 6
    assert len(result.world.alive_agents()) == 6
