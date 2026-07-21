"""Unit tests for the World aggregate."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import Agent, SimulationConfig, Tick, World


def _world(agent_count: int = 2) -> World:
    config = SimulationConfig(agent_count=agent_count, ticks=10, seed=1)
    agents = tuple(
        Agent.create(agent_id=index, name=f"Agent-{index}")
        for index in range(agent_count)
    )
    return World(config=config, agents=agents)


def test_world_rejects_population_mismatch() -> None:
    """Agent count must match config.agent_count."""
    config = SimulationConfig(agent_count=2)
    with pytest.raises(ValidationError, match="agent_count"):
        World(config=config, agents=(Agent.create(agent_id=0, name="A"),))


def test_world_rejects_unsorted_agents() -> None:
    """Agents must be stored in ascending id order."""
    config = SimulationConfig(agent_count=2)
    with pytest.raises(ValidationError, match="ascending"):
        World(
            config=config,
            agents=(
                Agent.create(agent_id=1, name="B"),
                Agent.create(agent_id=0, name="A"),
            ),
        )


def test_agent_by_id_and_alive_agents() -> None:
    """Lookups and alive filtering work in stable order."""
    world = _world(3)
    assert world.agent_by_id(1) is not None
    assert world.agent_by_id(1).name == "Agent-1"
    assert world.agent_by_id(99) is None
    assert len(world.alive_agents()) == 3


def test_with_tick_and_with_agent_return_new_worlds() -> None:
    """World updates are immutable and replace the targeted agent."""
    world = _world(2)
    moved = world.with_tick(Tick(value=5))
    assert world.tick.value == 0
    assert moved.tick.value == 5

    richer = world.agents[0].model_copy(update={"money": 50})
    updated = world.with_agent(richer)
    assert world.agents[0].money == 0
    assert updated.agents[0].money == 50


def test_with_agent_unknown_id_raises() -> None:
    """Replacing a missing agent is an error."""
    world = _world(1)
    stranger = Agent.create(agent_id=9, name="X")
    with pytest.raises(ValueError, match="not found"):
        world.with_agent(stranger)
