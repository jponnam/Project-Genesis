"""Death system: deterministic agent mortality.

Owns death as a first-class tick concern that emits ``AgentDied``.
Cause selection and agent mutation live in domain helpers so other layers
can reason about death without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import AgentDied, apply_death, death_cause
from civitas.domain.death import (
    DEFAULT_ENERGY_THRESHOLD,
    DEFAULT_FOOD_THRESHOLD,
    DEFAULT_WATER_THRESHOLD,
    DeathCause,
)
from civitas.domain.types import NonNegativeInt, UnitInterval

if TYPE_CHECKING:
    from civitas.domain import Agent, World
    from civitas.engine.event_bus import EventBus


class DeathConfig(BaseModel):
    """Parameters controlling system-driven death."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    food_threshold: UnitInterval = DEFAULT_FOOD_THRESHOLD
    water_threshold: UnitInterval = DEFAULT_WATER_THRESHOLD
    energy_threshold: UnitInterval = DEFAULT_ENERGY_THRESHOLD
    max_age_ticks: NonNegativeInt | None = Field(
        default=None,
        description="Optional max age in ticks; None disables old-age death.",
    )


class DeathSystem:
    """Apply deterministic deaths after actions and before births each tick."""

    def __init__(self, config: DeathConfig | None = None) -> None:
        self._config = config if config is not None else DeathConfig()

    @property
    def config(self) -> DeathConfig:
        """Return the immutable death configuration."""
        return self._config

    def should_die(self, world: World, agent_id: int) -> bool:
        """Return True when ``agent_id`` meets a death condition right now."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return False
        return self._cause_for(world, agent) is not None

    def apply_deaths(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Mark every eligible living agent dead in ascending id order.

        Each death emits ``AgentDied``. Already-dead agents are skipped.
        """
        if not self._config.enabled:
            return world

        for agent in world.alive_agents():
            cause = self._cause_for(world, agent)
            if cause is None:
                continue
            dead = apply_death(agent)
            if dead is None:
                continue
            world = world.with_agent(dead)
            if bus is not None:
                bus.publish(
                    AgentDied(
                        tick=world.tick,
                        agent_id=dead.agent_id,
                        location_id=dead.location_id,
                        cause=cause.value,
                        name=dead.name,
                    )
                )
        return world

    def _cause_for(self, world: World, agent: Agent) -> DeathCause | None:
        return death_cause(
            agent,
            world.tick.value,
            food_threshold=self._config.food_threshold,
            water_threshold=self._config.water_threshold,
            energy_threshold=self._config.energy_threshold,
            max_age_ticks=self._config.max_age_ticks,
        )
