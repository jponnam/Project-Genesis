"""Unit tests for domain geography helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Location,
    LocationKind,
    SimulationConfig,
    World,
    adjacent_locations,
    can_enter,
    default_world_map,
    enterable_neighbors,
    is_adjacent,
    occupancy,
    relocate,
)


def _two_cell_world(*, capacity: int = 2) -> World:
    camp = CAMP_LOCATION
    plain = Location.create(
        1, "Plain", 1, 0, kind=LocationKind.PLAIN, capacity=capacity
    )
    agents = (
        Agent.create(agent_id=0, name="A", location_id=0),
        Agent.create(agent_id=1, name="B", location_id=0),
    )
    return World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(camp, plain),
        agents=agents,
    )


def test_default_map_camp_neighbors_are_orthogonal() -> None:
    """Camp (0,0) is adjacent to Plain-1-0 and River-0-1 only."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    neighbors = adjacent_locations(world, 0)
    assert [loc.location_id.value for loc in neighbors] == [1, 3]


def test_is_adjacent_rejects_self_and_diagonal() -> None:
    """Self and diagonal cells are not adjacent at max_distance=1."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    assert is_adjacent(world, 0, 0) is False
    assert is_adjacent(world, 0, 4) is False  # diagonal (1,1)
    assert is_adjacent(world, 0, 1) is True


def test_occupancy_and_can_enter_respect_capacity() -> None:
    """can_enter is false once a location is at capacity."""
    world = _two_cell_world(capacity=1)
    # Move one agent into the plain via model_copy to fill capacity.
    filled = world.with_agent(
        world.agents[0].model_copy(
            update={"location_id": world.locations[1].location_id}
        )
    )
    assert occupancy(filled, 1) == 1
    assert can_enter(filled, 1) is False
    assert can_enter(filled, 0) is True


def test_relocate_moves_agent_and_costs_energy() -> None:
    """Legal relocation updates location and deducts energy."""
    world = _two_cell_world()
    agent = world.agents[0]
    moved = relocate(world, agent, 1, energy_cost=0.05)
    assert moved is not None
    assert moved.location_id.value == 1
    assert moved.needs.energy == pytest.approx(0.95)


def test_relocate_rejects_non_adjacent_and_full_destination() -> None:
    """Illegal destinations return None without mutation."""
    world = _two_cell_world(capacity=1)
    filled = world.with_agent(
        world.agents[0].model_copy(
            update={"location_id": world.locations[1].location_id}
        )
    )
    assert relocate(filled, filled.agents[1], 1) is None
    far = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    assert relocate(far, far.agents[0], 8) is None


def test_enterable_neighbors_filters_capacity() -> None:
    """enterable_neighbors omits destinations that are full."""
    world = _two_cell_world(capacity=1)
    filled = world.with_agent(
        world.agents[0].model_copy(
            update={"location_id": world.locations[1].location_id}
        )
    )
    assert enterable_neighbors(filled, 0) == ()
