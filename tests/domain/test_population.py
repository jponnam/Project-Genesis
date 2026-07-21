"""Unit tests for domain population census helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Health,
    Location,
    LocationKind,
    SimulationConfig,
    World,
    census,
    location_density,
    next_agent_id,
    population_alive,
    population_dead,
    population_total,
)


def _world_with_dead() -> World:
    forest = Location.create(1, "Forest", 1, 0, kind=LocationKind.FOREST)
    living = Agent.create(agent_id=0, name="A", location_id=0)
    dead = Agent.create(agent_id=1, name="B", location_id=1).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    return World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION, forest),
        agents=(living, dead),
    )


def test_census_totals_and_location_breakdown() -> None:
    """Census reports totals, dead split, and per-location occupancy."""
    world = _world_with_dead()
    snap = census(world)
    assert snap.initial_count == 2
    assert snap.total == 2
    assert snap.alive == 1
    assert snap.dead == 1
    assert [entry.location_id.value for entry in snap.by_location] == [0, 1]
    assert snap.by_location[0].count == 1
    assert snap.by_location[0].alive == 1
    assert snap.by_location[1].count == 1
    assert snap.by_location[1].alive == 0


def test_population_counters() -> None:
    """Counter helpers match census fields."""
    world = _world_with_dead()
    assert population_total(world) == 2
    assert population_alive(world) == 1
    assert population_dead(world) == 1


def test_next_agent_id_and_density() -> None:
    """next_agent_id and location_density are deterministic."""
    world = _world_with_dead()
    assert next_agent_id(world) == 2
    assert location_density(world, 0) == pytest.approx(1 / CAMP_LOCATION.capacity)
    assert location_density(world, 9) == 0.0


def test_empty_roster_next_agent_id_is_zero() -> None:
    """An empty roster starts agent ids at 0."""
    world = World(
        config=SimulationConfig(agent_count=3, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(),
    )
    assert next_agent_id(world) == 0
    assert world.population_size == 0
