"""Tests for ResourcesSystem observation."""

from __future__ import annotations

from civitas.domain import (
    Inventory,
    ResourcesObserved,
    ResourceStack,
    SimulationConfig,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import ResourcesConfig, ResourcesSystem


def test_observe_emits_resources_observed() -> None:
    """observe publishes ResourcesObserved when emit_events is enabled."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2, ticks=1))
    agents = list(world.agents)
    agents[0] = agents[0].model_copy(
        update={
            "inventory": Inventory(stacks=(ResourceStack(resource="food", quantity=2),))
        }
    )
    world = world.model_copy(update={"agents": tuple(agents)})
    bus = EventBus()
    before = world
    after = ResourcesSystem().observe(world, bus=bus)
    assert after == before
    events = [event for event in bus.history if isinstance(event, ResourcesObserved)]
    assert len(events) == 1
    assert events[0].alive_totals == (("food", 2),)
    assert events[0].agent_holdings == ((0, "food", 2),)


def test_observe_can_suppress_events() -> None:
    """emit_events=False still returns the world unchanged with no publish."""
    world = WorldFactory().create(SimulationConfig(seed=7, agent_count=1, ticks=1))
    bus = EventBus()
    ResourcesSystem(ResourcesConfig(emit_events=False)).observe(world, bus=bus)
    assert not any(isinstance(event, ResourcesObserved) for event in bus.history)
