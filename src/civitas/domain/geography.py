"""Pure geography helpers for adjacency, occupancy, and relocation.

These functions are domain logic shared by policy, movement, and action
execution. Systems must not call each other to answer spatial questions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.ids import LocationId
    from civitas.domain.location import Location
    from civitas.domain.world import World

# Default energy spent when an agent relocates one step.
DEFAULT_MOVE_ENERGY_COST: float = 0.05


def occupancy(world: World, location_id: LocationId | int) -> int:
    """Return how many agents currently occupy ``location_id``."""
    return len(world.agents_at(location_id))


def can_enter(world: World, location_id: LocationId | int) -> bool:
    """Return True when ``location_id`` exists and is below capacity."""
    location = world.location_by_id(location_id)
    if location is None:
        return False
    return occupancy(world, location.location_id) < location.capacity


def is_adjacent(
    world: World,
    origin_id: LocationId | int,
    destination_id: LocationId | int,
    *,
    max_distance: int = 1,
) -> bool:
    """Return True when destinations are within Manhattan ``max_distance``."""
    if max_distance < 1:
        msg = f"max_distance must be >= 1, got {max_distance}"
        raise ValueError(msg)
    origin = world.location_by_id(origin_id)
    destination = world.location_by_id(destination_id)
    if origin is None or destination is None:
        return False
    if origin.location_id == destination.location_id:
        return False
    distance = origin.coordinates.manhattan_distance(destination.coordinates)
    return distance <= max_distance


def adjacent_locations(
    world: World,
    location_id: LocationId | int,
    *,
    max_distance: int = 1,
) -> tuple[Location, ...]:
    """Return neighboring locations in ascending id order."""
    origin = world.location_by_id(location_id)
    if origin is None:
        return ()
    neighbors = [
        location
        for location in world.locations
        if is_adjacent(
            world,
            origin.location_id,
            location.location_id,
            max_distance=max_distance,
        )
    ]
    return tuple(neighbors)


def enterable_neighbors(
    world: World,
    location_id: LocationId | int,
    *,
    max_distance: int = 1,
) -> tuple[Location, ...]:
    """Return adjacent locations that currently have free capacity."""
    return tuple(
        location
        for location in adjacent_locations(
            world, location_id, max_distance=max_distance
        )
        if can_enter(world, location.location_id)
    )


def relocate(
    world: World,
    agent: Agent,
    destination_id: LocationId | int,
    *,
    energy_cost: float = DEFAULT_MOVE_ENERGY_COST,
) -> Agent | None:
    """Return ``agent`` moved to ``destination_id``, or ``None`` if illegal.

    A move is legal when the destination is adjacent, has free capacity,
    and the agent has at least ``energy_cost`` energy. Energy is deducted
    and clamped to the unit interval. No events are emitted.
    """
    if energy_cost < 0.0:
        msg = f"energy_cost must be >= 0, got {energy_cost}"
        raise ValueError(msg)
    destination = world.location_by_id(destination_id)
    if destination is None:
        return None
    if not is_adjacent(world, agent.location_id, destination.location_id):
        return None
    if not can_enter(world, destination.location_id):
        return None

    # Lazy import avoids a geography <-> energy circular import at module load.
    from civitas.domain.energy import spend_energy

    spent = spend_energy(agent, energy_cost)
    if spent is None:
        return None
    return spent.model_copy(update={"location_id": destination.location_id})
