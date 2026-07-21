"""Population census helpers for the world roster.

``SimulationConfig.agent_count`` is the *initial* population. Runtime
totals come from ``World.agents`` and may diverge once birth/death land.
These helpers are read-only; they never spawn or remove agents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import LocationId
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt, PositiveInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class LocationOccupancy(BaseModel):
    """Occupancy snapshot for one location."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    location_id: LocationId
    count: NonNegativeInt = Field(description="All agents at this location.")
    alive: NonNegativeInt = Field(description="Living agents at this location.")
    capacity: PositiveInt


class PopulationCensus(BaseModel):
    """Immutable population snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    initial_count: NonNegativeInt = Field(
        description="Configured initial population (config.agent_count)."
    )
    total: NonNegativeInt = Field(description="Current roster size.")
    alive: NonNegativeInt
    dead: NonNegativeInt
    by_location: tuple[LocationOccupancy, ...] = ()


def population_total(world: World) -> int:
    """Return the current roster size."""
    return len(world.agents)


def population_alive(world: World) -> int:
    """Return how many agents are currently alive."""
    return len(world.alive_agents())


def population_dead(world: World) -> int:
    """Return how many roster agents are not alive."""
    return population_total(world) - population_alive(world)


def next_agent_id(world: World) -> int:
    """Return the next unused agent id (max existing + 1, or 0 if empty)."""
    if not world.agents:
        return 0
    return max(agent.agent_id.value for agent in world.agents) + 1


def location_density(world: World, location_id: LocationId | int) -> float:
    """Return occupancy/capacity for ``location_id``, or 0.0 if missing."""
    location = world.location_by_id(location_id)
    if location is None:
        return 0.0
    return round(len(world.agents_at(location.location_id)) / location.capacity, 6)


def census(world: World) -> PopulationCensus:
    """Build a deterministic population census for ``world``."""
    alive = population_alive(world)
    total = population_total(world)
    by_location: list[LocationOccupancy] = []
    for location in world.locations:
        present = world.agents_at(location.location_id)
        alive_here = sum(1 for agent in present if agent.is_alive())
        by_location.append(
            LocationOccupancy(
                location_id=location.location_id,
                count=len(present),
                alive=alive_here,
                capacity=location.capacity,
            )
        )
    return PopulationCensus(
        tick=world.tick,
        initial_count=world.config.agent_count,
        total=total,
        alive=alive,
        dead=total - alive,
        by_location=tuple(by_location),
    )
