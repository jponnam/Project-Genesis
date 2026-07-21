"""Water system: inventory-backed drinking and water-need restoration.

Owns drinking as a first-class operation that emits ``ResourceConsumed``
and ``NeedDecayed``. Consumption legality lives in domain helpers so the
action executor can apply DRINK without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    WATER_RESOURCE,
    NeedDecayed,
    ResourceConsumed,
    apply_drink,
    can_drink,
)
from civitas.domain.types import PositiveInt, UnitInterval
from civitas.domain.water import DEFAULT_DRINK_CONSUME_AMOUNT, DEFAULT_DRINK_RESTORE

if TYPE_CHECKING:
    from civitas.domain import AgentId, World
    from civitas.engine.event_bus import EventBus


class WaterConfig(BaseModel):
    """Parameters controlling inventory-backed drinking."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    restore: UnitInterval = DEFAULT_DRINK_RESTORE
    consume_amount: PositiveInt = Field(default=DEFAULT_DRINK_CONSUME_AMOUNT)


class WaterSystem:
    """Apply deterministic water consumption to agents."""

    def __init__(self, config: WaterConfig | None = None) -> None:
        self._config = config if config is not None else WaterConfig()

    @property
    def config(self) -> WaterConfig:
        """Return the immutable water configuration."""
        return self._config

    def can_drink(self, world: World, agent_id: AgentId | int) -> bool:
        """Return True when ``agent_id`` has enough water to drink."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return False
        return can_drink(agent, amount=self._config.consume_amount)

    def drink(
        self,
        world: World,
        agent_id: AgentId | int,
        bus: EventBus | None = None,
    ) -> World:
        """Consume water for ``agent_id`` when legal.

        Emits ``ResourceConsumed`` and, when the water need changes,
        ``NeedDecayed``. Illegal drinks leave the world unchanged.

        Raises:
            ValueError: If the agent is missing from the world.
        """
        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        previous_water = agent.needs.water
        updated = apply_drink(
            agent,
            restore=self._config.restore,
            amount=self._config.consume_amount,
        )
        if updated is None:
            return world

        world = world.with_agent(updated)
        if bus is not None:
            bus.publish(
                ResourceConsumed(
                    tick=world.tick,
                    agent_id=updated.agent_id,
                    resource=WATER_RESOURCE,
                    amount=self._config.consume_amount,
                )
            )
            if updated.needs.water != previous_water:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=updated.agent_id,
                        need="water",
                        previous=previous_water,
                        current=updated.needs.water,
                    )
                )
        return world
