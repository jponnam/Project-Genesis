"""World aggregate: the complete simulation state at a tick.

The world is immutable. Systems and the engine produce new ``World``
instances via ``model_copy`` / helpers rather than mutating in place.

``config.agent_count`` is the *initial* population created by the world
factory. Runtime roster size is ``len(agents)`` and may diverge once
birth and death are introduced.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from civitas.domain.agent import Agent
from civitas.domain.config import SimulationConfig
from civitas.domain.governments import Government
from civitas.domain.ids import AgentId, GovernmentId, LocationId, MarketId
from civitas.domain.location import Location
from civitas.domain.market import Market
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt


class World(BaseModel):
    """Deterministic snapshot of a civilization simulation.

    Attributes:
        config: Configuration used to construct this world.
        tick: Current discrete time (``0`` at construction).
        locations: Places on the map, ordered by ascending ``location_id``.
        markets: Market venues, ordered by ascending ``market_id``.
        governments: Polities, ordered by ascending ``government_id``.
        agents: Agents ordered by ascending ``agent_id``.
        treasury: Public money balance collected from taxes.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    config: SimulationConfig
    tick: Tick = Field(default_factory=Tick)
    locations: tuple[Location, ...] = ()
    markets: tuple[Market, ...] = ()
    governments: tuple[Government, ...] = ()
    agents: tuple[Agent, ...] = ()
    treasury: NonNegativeInt = 0

    @model_validator(mode="after")
    def world_must_be_consistent(self) -> Self:
        """Enforce agent/location/market/government integrity constraints."""
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

        market_ids = [market.market_id.value for market in self.markets]
        if len(market_ids) != len(set(market_ids)):
            msg = "market ids must be unique"
            raise ValueError(msg)
        if market_ids != sorted(market_ids):
            msg = "markets must be ordered by ascending market_id"
            raise ValueError(msg)

        market_locations = [market.location_id.value for market in self.markets]
        if len(market_locations) != len(set(market_locations)):
            msg = "at most one market is allowed per location"
            raise ValueError(msg)
        for market in self.markets:
            if market.location_id.value not in known:
                msg = (
                    f"market {market.market_id.value} references unknown "
                    f"location {market.location_id.value}"
                )
                raise ValueError(msg)

        government_ids = [
            government.government_id.value for government in self.governments
        ]
        if len(government_ids) != len(set(government_ids)):
            msg = "government ids must be unique"
            raise ValueError(msg)
        if government_ids != sorted(government_ids):
            msg = "governments must be ordered by ascending government_id"
            raise ValueError(msg)

        claimed: set[int] = set()
        for government in self.governments:
            for location in government.jurisdiction:
                if location.value not in known:
                    msg = (
                        f"government {government.government_id.value} references "
                        f"unknown location {location.value}"
                    )
                    raise ValueError(msg)
                if location.value in claimed:
                    msg = "government jurisdictions must be disjoint"
                    raise ValueError(msg)
                claimed.add(location.value)
            if government.leader_id is not None:
                leader = self.agent_by_id(government.leader_id)
                if leader is None:
                    msg = (
                        f"government {government.government_id.value} references "
                        f"unknown leader {government.leader_id.value}"
                    )
                    raise ValueError(msg)

        return self

    @property
    def population_size(self) -> int:
        """Return the current roster size."""
        return len(self.agents)

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

    def market_by_id(self, market_id: MarketId | int) -> Market | None:
        """Return the market with ``market_id``, or ``None`` if absent."""
        target = (
            market_id if isinstance(market_id, MarketId) else MarketId(value=market_id)
        )
        for market in self.markets:
            if market.market_id == target:
                return market
        return None

    def government_by_id(
        self,
        government_id: GovernmentId | int,
    ) -> Government | None:
        """Return the government with ``government_id``, or ``None`` if absent."""
        target = (
            government_id
            if isinstance(government_id, GovernmentId)
            else GovernmentId(value=government_id)
        )
        for government in self.governments:
            if government.government_id == target:
                return government
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

    def with_agents(self, agents: tuple[Agent, ...]) -> World:
        """Return a copy with a replaced agent roster.

        The roster must remain uniquely id-sorted; validation enforces this.
        """
        return World(
            config=self.config,
            tick=self.tick,
            locations=self.locations,
            markets=self.markets,
            governments=self.governments,
            agents=agents,
            treasury=self.treasury,
        )

    def with_treasury(self, balance: int) -> World:
        """Return a copy with ``treasury`` set to ``balance``.

        Raises:
            ValueError: If ``balance`` is negative.
        """
        if balance < 0:
            msg = f"treasury balance must be >= 0, got {balance}"
            raise ValueError(msg)
        return self.model_copy(update={"treasury": balance})

    def with_location(self, location: Location) -> World:
        """Return a copy replacing the location that shares ``location_id``.

        Raises:
            ValueError: If no location with that id exists.
        """
        updated: list[Location] = []
        found = False
        for existing in self.locations:
            if existing.location_id == location.location_id:
                updated.append(location)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"location id {location.location_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"locations": tuple(updated)})

    def with_market(self, market: Market) -> World:
        """Return a copy replacing the market that shares ``market_id``.

        Raises:
            ValueError: If no market with that id exists.
        """
        updated: list[Market] = []
        found = False
        for existing in self.markets:
            if existing.market_id == market.market_id:
                updated.append(market)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"market id {market.market_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"markets": tuple(updated)})

    def with_government(self, government: Government) -> World:
        """Return a copy replacing the government that shares ``government_id``.

        Raises:
            ValueError: If no government with that id exists.
        """
        updated: list[Government] = []
        found = False
        for existing in self.governments:
            if existing.government_id == government.government_id:
                updated.append(government)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"government id {government.government_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"governments": tuple(updated)})
