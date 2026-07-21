"""Food system: inventory-backed eating and food-need restoration.

Owns eating as a first-class operation that emits ``ResourceConsumed`` and
``NeedDecayed``. Consumption legality lives in domain helpers so the
action executor can apply EAT without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    FOOD_RESOURCE,
    NeedDecayed,
    ResourceConsumed,
    apply_eat,
    can_eat,
)
from civitas.domain.food import DEFAULT_EAT_CONSUME_AMOUNT, DEFAULT_EAT_RESTORE
from civitas.domain.types import PositiveInt, UnitInterval

if TYPE_CHECKING:
    from civitas.domain import AgentId, World
    from civitas.engine.event_bus import EventBus


class FoodConfig(BaseModel):
    """Parameters controlling inventory-backed eating."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    restore: UnitInterval = DEFAULT_EAT_RESTORE
    consume_amount: PositiveInt = Field(default=DEFAULT_EAT_CONSUME_AMOUNT)


class FoodSystem:
    """Apply deterministic food consumption to agents."""

    def __init__(self, config: FoodConfig | None = None) -> None:
        self._config = config if config is not None else FoodConfig()

    @property
    def config(self) -> FoodConfig:
        """Return the immutable food configuration."""
        return self._config

    def can_eat(self, world: World, agent_id: AgentId | int) -> bool:
        """Return True when ``agent_id`` has enough food to eat."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return False
        return can_eat(agent, amount=self._config.consume_amount)

    def eat(
        self,
        world: World,
        agent_id: AgentId | int,
        bus: EventBus | None = None,
    ) -> World:
        """Consume food for ``agent_id`` when legal.

        Emits ``ResourceConsumed`` and, when the food need changes,
        ``NeedDecayed``. Illegal eats leave the world unchanged.

        Raises:
            ValueError: If the agent is missing from the world.
        """
        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        previous_food = agent.needs.food
        updated = apply_eat(
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
                    resource=FOOD_RESOURCE,
                    amount=self._config.consume_amount,
                )
            )
            if updated.needs.food != previous_food:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=updated.agent_id,
                        need="food",
                        previous=previous_food,
                        current=updated.needs.food,
                    )
                )
        return world
