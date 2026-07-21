"""Unit tests for the GatheringSystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Health,
    Location,
    LocationKind,
    ResourceGathered,
    SimulationConfig,
    World,
    location_stock,
)
from civitas.engine import EventBus
from civitas.systems import GatheringConfig, GatheringSystem


def _forest_world() -> World:
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, forest),
        agents=(Agent.create(agent_id=0, name="A", location_id=1),),
    )


def test_gather_emits_resource_gathered_and_updates_stock() -> None:
    """Successful gather publishes ResourceGathered and mutates world state."""
    world = _forest_world()
    bus = EventBus()
    updated = GatheringSystem().gather(world, 0, "food", bus=bus)
    assert updated.agents[0].inventory.quantity("food") == 1
    assert location_stock(updated.locations[1], "food") == 23
    events = [event for event in bus.history if isinstance(event, ResourceGathered)]
    assert len(events) == 1
    assert events[0].resource == "food"
    assert events[0].amount == 1
    assert events[0].location_id.value == 1


def test_gather_respects_available_resources() -> None:
    """available lists positive stocks; can_gather rejects missing resources."""
    world = _forest_world()
    system = GatheringSystem()
    assert system.available(world, 1) == ("food", "wood")
    assert system.can_gather(world, 0, "food") is True
    assert system.can_gather(world, 0, "water") is False
    assert system.gather(world, 0, "water") == world


def test_gather_from_camp_is_impossible() -> None:
    """Camp has no deposits, so gathering is a no-op."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    system = GatheringSystem()
    assert system.available(world, 0) == ()
    assert system.gather(world, 0, "food") == world


def test_dead_agent_cannot_gather() -> None:
    """Dead agents are rejected by can_gather and gather."""
    world = _forest_world()
    dead = world.with_agent(
        world.agents[0].model_copy(
            update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
        )
    )
    system = GatheringSystem()
    assert system.can_gather(dead, 0, "food") is False
    assert system.gather(dead, 0, "food") == dead


def test_gather_amount_config() -> None:
    """GatheringConfig.amount controls transfer size."""
    world = _forest_world()
    updated = GatheringSystem(GatheringConfig(amount=3)).gather(world, 0, "wood")
    assert updated.agents[0].inventory.quantity("wood") == 3
    assert location_stock(updated.locations[1], "wood") == 13


def test_missing_agent_raises() -> None:
    """gather raises when the agent id is absent."""
    world = _forest_world()
    with pytest.raises(ValueError, match="not found"):
        GatheringSystem().gather(world, 9, "food")
