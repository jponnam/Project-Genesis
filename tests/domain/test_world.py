"""Unit tests for the World aggregate."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Location,
    LocationKind,
    SimulationConfig,
    Tick,
    World,
)


def _world(agent_count: int = 2) -> World:
    config = SimulationConfig(agent_count=agent_count, ticks=10, seed=1)
    agents = tuple(
        Agent.create(agent_id=index, name=f"Agent-{index}")
        for index in range(agent_count)
    )
    return World(config=config, locations=(CAMP_LOCATION,), agents=agents)


def test_world_allows_roster_size_to_diverge_from_initial_count() -> None:
    """config.agent_count is initial size; runtime roster may differ."""
    world = World(
        config=SimulationConfig(agent_count=2),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    assert world.population_size == 1
    assert world.config.agent_count == 2


def test_world_rejects_unsorted_agents() -> None:
    """Agents must be stored in ascending id order."""
    config = SimulationConfig(agent_count=2)
    with pytest.raises(ValidationError, match="ascending"):
        World(
            config=config,
            locations=(CAMP_LOCATION,),
            agents=(
                Agent.create(agent_id=1, name="B"),
                Agent.create(agent_id=0, name="A"),
            ),
        )


def test_world_requires_known_agent_locations() -> None:
    """Agents may not reference missing locations."""
    config = SimulationConfig(agent_count=1)
    with pytest.raises(ValidationError, match="unknown location"):
        World(
            config=config,
            locations=(CAMP_LOCATION,),
            agents=(Agent.create(agent_id=0, name="A", location_id=9),),
        )


def test_world_requires_at_least_one_location() -> None:
    """Empty location maps are invalid."""
    with pytest.raises(ValidationError, match="at least one location"):
        World(
            config=SimulationConfig(agent_count=1),
            locations=(),
            agents=(Agent.create(agent_id=0, name="A"),),
        )


def test_location_by_id_and_agents_at() -> None:
    """Location lookup and occupancy queries are stable."""
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    agents = (
        Agent.create(agent_id=0, name="A", location_id=0),
        Agent.create(agent_id=1, name="B", location_id=1),
    )
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION, forest),
        agents=agents,
    )
    assert world.location_by_id(1) == forest
    assert world.location_by_id(9) is None
    assert world.agents_at(0) == (agents[0],)
    assert world.agents_at(1) == (agents[1],)


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


def test_with_agents_replaces_roster() -> None:
    """with_agents replaces the full roster when ids stay sorted."""
    world = _world(1)
    expanded = world.with_agents(
        (
            Agent.create(agent_id=0, name="A"),
            Agent.create(agent_id=1, name="B"),
        )
    )
    assert expanded.population_size == 2
    assert world.population_size == 1


def test_with_agents_rejects_unsorted_roster() -> None:
    """with_agents still enforces ascending agent ids."""
    world = _world(1)
    with pytest.raises(ValidationError, match="ascending"):
        world.with_agents(
            (
                Agent.create(agent_id=1, name="B"),
                Agent.create(agent_id=0, name="A"),
            )
        )
