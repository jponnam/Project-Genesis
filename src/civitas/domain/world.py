"""World aggregate: the complete simulation state at a tick.

The world is immutable. Systems and the engine produce new ``World``
instances via ``model_copy`` / helpers rather than mutating in place.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from civitas.domain.agent import Agent
from civitas.domain.config import SimulationConfig
from civitas.domain.ids import AgentId, LocationId
from civitas.domain.location import Location
from civitas.domain.time import Tick


class World(BaseModel):
    """Deterministic snapshot of a civilization simulation.

    Attributes:
        config: Configuration used to construct this world.
        tick: Current discrete time (``0`` at construction).
        locations: Places on the map, ordered by ascending ``location_id``.
        agents: Agents ordered by ascending ``agent_id``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    config: SimulationConfig
    tick: Tick = Field(default_factory=Tick)
    locations: tuple[Location, ...] = ()
    agents: tuple[Agent, ...] = ()

    @model_validator(mode="after")
    def world_must_be_consistent(self) -> Self:
        """Enforce agent/location integrity constraints."""
        if len(self.agents) != self.config.agent_count:
            msg = (
                f"world has {len(self.agents)} agents but "
                f"config.agent_count is {self.config.agent_count}"
            )
            raise ValueError(msg)

        agent_ids = [agent.agent_id.value for agent in self.agents]
        if len(agent_ids) != len(set(agent_ids)):
            msg = "agent ids must be unique"
            raise ValueError(msg)
        if agent_ids != sorted(agent_ids):
            msg = "agents must be ordered by ascending agent_id"
            raise ValueError(msg)

        location_ids = [location.location_id.value for location in self.locations]
        if len(location_ids) != len(set(location_ids)):
            msg = "location ids must be unique"
            raise ValueError(msg)
        if location_ids != sorted(location_ids):
            msg = "locations must be ordered by ascending location_id"
            raise ValueError(msg)

        known = set(location_ids)
        if not known:
            msg = "world must contain at least one location"
            raise ValueError(msg)

        for agent in self.agents:
            if agent.location_id.value not in known:
                msg = (
                    f"agent {agent.agent_id.value} references unknown "
                    f"location {agent.location_id.value}"
                )
                raise ValueError(msg)

        coord_keys = {(loc.coordinates.x, loc.coordinates.y) for loc in self.locations}
        if len(coord_keys) != len(self.locations):
            msg = "location coordinates must be unique"
            raise ValueError(msg)

        return self

    def agent_by_id(self, agent_id: AgentId | int) -> Agent | None:
        """Return the agent with ``agent_id``, or ``None`` if absent."""
        target = agent_id if isinstance(agent_id, AgentId) else AgentId(value=agent_id)
        for agent in self.agents:
            if agent.agent_id == target:
                return agent
        return None

    def location_by_id(self, location_id: LocationId | int) -> Location | None:
        """Return the location with ``location_id``, or ``None`` if absent."""
        target = (
            location_id
            if isinstance(location_id, LocationId)
            else LocationId(value=location_id)
        )
        for location in self.locations:
            if location.location_id == target:
                return location
        return None

    def agents_at(self, location_id: LocationId | int) -> tuple[Agent, ...]:
        """Return agents occupying ``location_id`` in stable id order."""
        target = (
            location_id
            if isinstance(location_id, LocationId)
            else LocationId(value=location_id)
        )
        return tuple(agent for agent in self.agents if agent.location_id == target)

    def alive_agents(self) -> tuple[Agent, ...]:
        """Return living agents in stable id order."""
        return tuple(agent for agent in self.agents if agent.is_alive())

    def with_tick(self, tick: Tick) -> World:
        """Return a copy of this world at ``tick``."""
        return self.model_copy(update={"tick": tick})

    def with_agent(self, agent: Agent) -> World:
        """Return a copy replacing the agent that shares ``agent.agent_id``.

        Raises:
            ValueError: If no agent with that id exists.
        """
        updated: list[Agent] = []
        found = False
        for existing in self.agents:
            if existing.agent_id == agent.agent_id:
                updated.append(agent)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"agent id {agent.agent_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"agents": tuple(updated)})
