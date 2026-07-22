"""Gathering system: transfer location deposits into agent inventory.

Owns gathering as a first-class operation that emits ``ResourceGathered``.
Deposit legality lives in domain helpers so the action executor can apply
GATHER without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    ResourceGathered,
    apply_gather,
    effective_gather_amount,
    gatherable_resources,
    location_stock,
)
from civitas.domain.resources import DEFAULT_GATHER_AMOUNT
from civitas.domain.types import PositiveInt

if TYPE_CHECKING:
    from civitas.domain import AgentId, LocationId, World
    from civitas.engine.event_bus import EventBus


class GatheringConfig(BaseModel):
    """Parameters controlling how much stock a gather transfers."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    amount: PositiveInt = Field(default=DEFAULT_GATHER_AMOUNT)


class GatheringSystem:
    """Apply deterministic resource gathering on the world map."""

    def __init__(self, config: GatheringConfig | None = None) -> None:
        self._config = config if config is not None else GatheringConfig()

    @property
    def config(self) -> GatheringConfig:
        """Return the immutable gathering configuration."""
        return self._config

    def available(
        self,
        world: World,
        location_id: LocationId | int,
    ) -> tuple[str, ...]:
        """Return gatherable resource names at ``location_id``."""
        location = world.location_by_id(location_id)
        if location is None:
            return ()
        return gatherable_resources(location)

    def can_gather(
        self,
        world: World,
        agent_id: AgentId | int,
        resource: str,
    ) -> bool:
        """Return True when ``agent_id`` may gather ``resource`` here."""
        agent = world.agent_by_id(agent_id)
        if agent is None or not agent.is_alive():
            return False
        location = world.location_by_id(agent.location_id)
        if location is None:
            return False
        amount = effective_gather_amount(
            world,
            resource,
            base=int(self._config.amount),
            agent=agent,
        )
        return location_stock(location, resource) >= amount

    def gather(
        self,
        world: World,
        agent_id: AgentId | int,
        resource: str,
        bus: EventBus | None = None,
    ) -> World:
        """Gather ``resource`` for ``agent_id`` when legal.

        Emits ``ResourceGathered`` on success. Illegal gathers leave the
        world unchanged and emit nothing.

        Raises:
            ValueError: If the agent is missing from the world.
        """
        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        amount = effective_gather_amount(
            world,
            resource,
            base=int(self._config.amount),
            agent=agent,
        )
        updated = apply_gather(
            world,
            agent,
            resource,
            amount=amount,
        )
        if updated is None:
            return world

        if bus is not None:
            bus.publish(
                ResourceGathered(
                    tick=updated.tick,
                    agent_id=agent.agent_id,
                    location_id=agent.location_id,
                    resource=resource,
                    amount=amount,
                )
            )
        return updated
