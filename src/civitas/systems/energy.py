"""Energy system: REST recovery for the energy need.

Owns resting as a first-class operation that emits ``NeedDecayed`` when
energy changes. Recovery legality lives in domain helpers so the action
executor can apply REST without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import NeedDecayed, apply_rest, can_rest
from civitas.domain.energy import DEFAULT_REST_RESTORE
from civitas.domain.types import UnitInterval

if TYPE_CHECKING:
    from civitas.domain import AgentId, World
    from civitas.engine.event_bus import EventBus


class EnergyConfig(BaseModel):
    """Parameters controlling REST energy restoration."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    restore: UnitInterval = DEFAULT_REST_RESTORE


class EnergySystem:
    """Apply deterministic energy recovery to agents."""

    def __init__(self, config: EnergyConfig | None = None) -> None:
        self._config = config if config is not None else EnergyConfig()

    @property
    def config(self) -> EnergyConfig:
        """Return the immutable energy configuration."""
        return self._config

    def can_rest(self, world: World, agent_id: AgentId | int) -> bool:
        """Return True when ``agent_id`` can usefully rest."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return False
        return can_rest(agent)

    def rest(
        self,
        world: World,
        agent_id: AgentId | int,
        bus: EventBus | None = None,
    ) -> World:
        """Restore energy for ``agent_id`` when legal.

        Emits ``NeedDecayed`` when energy changes. Illegal rests leave the
        world unchanged.

        Raises:
            ValueError: If the agent is missing from the world.
        """
        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        previous_energy = agent.needs.energy
        updated = apply_rest(agent, restore=self._config.restore)
        if updated is None:
            return world

        world = world.with_agent(updated)
        if bus is not None and updated.needs.energy != previous_energy:
            bus.publish(
                NeedDecayed(
                    tick=world.tick,
                    agent_id=updated.agent_id,
                    need="energy",
                    previous=previous_energy,
                    current=updated.needs.energy,
                )
            )
        return world
