"""Movement system: relocate agents between adjacent locations.

Owns relocation as a first-class operation that emits ``AgentMoved``.
Spatial legality and energy accounting live in domain geography helpers
so the action executor can apply MOVE without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    DEFAULT_MOVE_ENERGY_COST,
    AgentMoved,
    NeedDecayed,
    adjacent_locations,
    can_enter,
    is_adjacent,
    relocate,
)
from civitas.domain.types import UnitInterval

if TYPE_CHECKING:
    from civitas.domain import AgentId, Location, LocationId, World
    from civitas.engine.event_bus import EventBus


class MovementConfig(BaseModel):
    """Parameters controlling relocation cost."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    energy_cost: UnitInterval = DEFAULT_MOVE_ENERGY_COST


class MovementSystem:
    """Apply deterministic agent relocation on the world map."""

    def __init__(self, config: MovementConfig | None = None) -> None:
        self._config = config if config is not None else MovementConfig()

    @property
    def config(self) -> MovementConfig:
        """Return the immutable movement configuration."""
        return self._config

    def neighbors(
        self,
        world: World,
        location_id: LocationId | int,
    ) -> tuple[Location, ...]:
        """Return adjacent locations in ascending id order."""
        return adjacent_locations(world, location_id)

    def can_move(
        self,
        world: World,
        agent_id: AgentId | int,
        destination_id: LocationId | int,
    ) -> bool:
        """Return True when ``agent_id`` may legally move to ``destination_id``."""
        agent = world.agent_by_id(agent_id)
        if agent is None or not agent.is_alive():
            return False
        if agent.needs.energy < self._config.energy_cost:
            return False
        if not is_adjacent(world, agent.location_id, destination_id):
            return False
        return can_enter(world, destination_id)

    def move_to(
        self,
        world: World,
        agent_id: AgentId | int,
        destination_id: LocationId | int,
        bus: EventBus | None = None,
    ) -> World:
        """Move ``agent_id`` to ``destination_id`` when legal.

        Emits ``AgentMoved`` and, when energy changes, ``NeedDecayed``.
        Illegal moves leave the world unchanged and emit nothing.

        Raises:
            ValueError: If the agent is missing from the world.
        """
        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        from_location_id = agent.location_id
        previous_energy = agent.needs.energy
        updated = relocate(
            world,
            agent,
            destination_id,
            energy_cost=self._config.energy_cost,
        )
        if updated is None:
            return world

        world = world.with_agent(updated)
        if bus is not None:
            if updated.needs.energy != previous_energy:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=updated.agent_id,
                        need="energy",
                        previous=previous_energy,
                        current=updated.needs.energy,
                    )
                )
            bus.publish(
                AgentMoved(
                    tick=world.tick,
                    agent_id=updated.agent_id,
                    from_location_id=from_location_id,
                    to_location_id=updated.location_id,
                )
            )
        return world
