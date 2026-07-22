"""Unit tests for the EffectsSystem."""

from __future__ import annotations

from civitas.domain import EffectsObserved, SimulationConfig
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import EffectsConfig, EffectsSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one effects census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = EffectsSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, EffectsObserved)]
    assert len(events) == 1
    assert events[0].living_count == 3
    assert events[0].fire_hearth_active == 1
    assert events[0].rest_restore_bps == 2500
    assert events[0].active_well_count == 1
    assert events[0].drink_restore_bps == 3500


def test_observe_can_disable_events() -> None:
    """EffectsConfig.emit_events=False emits nothing."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    EffectsSystem(EffectsConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_engine_observes_effects_each_tick_including_start() -> None:
    """Engine emits an initial effects census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=2, agent_count=3))
    observed = [event for event in result.events if isinstance(event, EffectsObserved)]
    assert len(observed) == 3
    assert observed[0].tick.value == 0
    assert observed[0].fire_hearth_active == 1
    assert observed[-1].tick.value == 2
