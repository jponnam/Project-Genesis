"""Unit tests for the PlanningSystem."""

from __future__ import annotations

from civitas.domain import PlansObserved, PlanUpdated, SimulationConfig
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import PlanningConfig, PlanningSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one plan census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = PlanningSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, PlansObserved)]
    assert len(events) == 1
    assert events[0].living_count == 3
    assert events[0].agents_with_plans == 0


def test_apply_planning_emits_plan_updated() -> None:
    """apply_planning sets goals and emits PlanUpdated for each living agent."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = PlanningSystem().apply_planning(world, bus=bus)
    assert all(agent.goals.goals for agent in updated.alive_agents())
    events = [event for event in bus.history if isinstance(event, PlanUpdated)]
    assert len(events) == 2
    assert all(event.goal_kind.startswith("satisfy_") for event in events)


def test_apply_planning_can_be_disabled() -> None:
    """PlanningConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = PlanningSystem(PlanningConfig(enabled=False)).apply_planning(
        world, bus=bus
    )
    assert updated == world
    assert bus.history == ()


def test_engine_plans_each_tick_after_cognition() -> None:
    """Engine plans after cognition; founders have goals by tick 1."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=2, agent_count=3))
    assert all(agent.goals.goals for agent in result.world.alive_agents())
    planned = [event for event in result.events if isinstance(event, PlanUpdated)]
    assert len(planned) == 6
    observed = [event for event in result.events if isinstance(event, PlansObserved)]
    assert len(observed) == 3
    assert observed[0].agents_with_plans == 0
    assert observed[-1].agents_with_plans == 3
