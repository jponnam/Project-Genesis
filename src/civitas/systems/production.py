"""Production system: recipe-based inventory crafting.

Owns crafting as a first-class operation that emits ``ResourceProduced``
and ``NeedDecayed`` when energy is spent. Recipe legality lives in domain
helpers so the action executor can apply PRODUCE without calling this
system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import NeedDecayed, ResourceProduced, apply_produce, can_produce
from civitas.domain.production import recipe_by_id

if TYPE_CHECKING:
    from civitas.domain import AgentId, World
    from civitas.engine.event_bus import EventBus


class ProductionConfig(BaseModel):
    """Parameters controlling production observation (reserved for expansion)."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class ProductionSystem:
    """Apply deterministic crafting recipes to agents."""

    def __init__(self, config: ProductionConfig | None = None) -> None:
        self._config = config if config is not None else ProductionConfig()

    @property
    def config(self) -> ProductionConfig:
        """Return the immutable production configuration."""
        return self._config

    def can_produce(
        self,
        world: World,
        agent_id: AgentId | int,
        recipe_id: str,
    ) -> bool:
        """Return True when ``agent_id`` can craft ``recipe_id`` right now."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return False
        return can_produce(agent, recipe_id)

    def produce(
        self,
        world: World,
        agent_id: AgentId | int,
        recipe_id: str,
        bus: EventBus | None = None,
    ) -> World:
        """Craft ``recipe_id`` for ``agent_id`` when legal.

        Emits ``ResourceProduced`` and ``NeedDecayed`` (energy) on success.
        Illegal crafts leave the world unchanged.
        """
        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        recipe = recipe_by_id(recipe_id)
        previous_energy = agent.needs.energy
        updated = apply_produce(agent, recipe_id)
        if updated is None or recipe is None:
            return world

        world = world.with_agent(updated)
        if bus is not None and self._config.emit_events:
            bus.publish(
                ResourceProduced(
                    tick=world.tick,
                    agent_id=updated.agent_id,
                    recipe_id=recipe.recipe_id,
                    outputs=tuple(
                        (stack.resource, stack.quantity) for stack in recipe.outputs
                    ),
                )
            )
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
        return world
