"""Unit tests for the SimulationEngine."""

from __future__ import annotations

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentMoved,
    AgentSpawned,
    LocationCreated,
    NeedDecayed,
    ResourceConsumed,
    ResourceGathered,
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
    assert types.count(LocationCreated.__name__) == 9
    assert types.count(AgentSpawned.__name__) == 2
    assert types[1] == LocationCreated.__name__
    assert types[10] == AgentSpawned.__name__
    assert types.count(TickStarted.__name__) == 2
    assert types.count(TickCompleted.__name__) == 2
    assert types[-1] == SimulationCompleted.__name__
    assert isinstance(result.events[-1], SimulationCompleted)
    assert result.events[-1].ticks_executed == 2
    assert result.world.tick.value == 2
    assert len(result.world.locations) == 9


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
    # Five needs decay each tick; MOVE may add an extra energy NeedDecayed.
    assert {event.need for event in decayed} == {
        "food",
        "water",
        "energy",
        "social",
        "safety",
    }
    assert len(decayed) >= 5


def test_agents_can_move_during_engine_run() -> None:
    """Open agents may leave Camp via MOVE within a short seeded run."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=5, agent_count=8))
    moved = [event for event in result.events if isinstance(event, AgentMoved)]
    assert moved
    assert any(agent.location_id.value != 0 for agent in result.world.agents)


def test_agents_can_gather_during_engine_run() -> None:
    """Seeded runs eventually gather resources from biome deposits."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=30, agent_count=10))
    gathered = [event for event in result.events if isinstance(event, ResourceGathered)]
    assert gathered
    assert any(agent.inventory.stacks for agent in result.world.agents)


def test_agents_can_eat_gathered_food_during_engine_run() -> None:
    """After gathering food, hungry agents consume it via EAT."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=50, agent_count=12))
    eaten = [
        event
        for event in result.events
        if isinstance(event, ResourceConsumed) and event.resource == "food"
    ]
    assert eaten
    assert any(
        isinstance(event, ResourceGathered) and event.resource == "food"
        for event in result.events
    )


def test_agents_can_drink_gathered_water_during_engine_run() -> None:
    """After gathering water, thirsty agents consume it via DRINK."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=50, agent_count=12))
    drunk = [
        event
        for event in result.events
        if isinstance(event, ResourceConsumed) and event.resource == "water"
    ]
    assert drunk
    assert any(
        isinstance(event, ResourceGathered) and event.resource == "water"
        for event in result.events
    )


def test_agents_can_rest_during_engine_run() -> None:
    """Seeded runs include successful REST actions as energy decays."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=40, agent_count=10))
    rested = [
        event
        for event in result.events
        if isinstance(event, ActionCompleted)
        and event.action == "rest"
        and event.success
    ]
    assert rested


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
