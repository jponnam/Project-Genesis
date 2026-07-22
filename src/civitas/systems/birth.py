"""Birth system: deterministic agent reproduction.

Owns birth as a first-class tick concern that emits ``AgentBorn`` and
``KnowledgeLearned`` (source=birth) for inherited parental facts.
Eligibility and world mutation live in domain helpers so other layers can
reason about birth without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    AgentBorn,
    KnowledgeLearned,
    KnowledgeSource,
    apply_birth,
    can_birth,
)
from civitas.domain.birth import (
    DEFAULT_MIN_ENERGY,
    DEFAULT_MIN_FOOD,
    DEFAULT_MIN_PARENT_AGE_TICKS,
    DEFAULT_MIN_WATER,
    DEFAULT_PARENT_ENERGY_COST,
    DEFAULT_PERSONALITY_REGRESSION,
)
from civitas.domain.types import NonNegativeInt, PositiveInt, UnitInterval

if TYPE_CHECKING:
    from civitas.domain import Agent, World
    from civitas.engine.event_bus import EventBus


class BirthConfig(BaseModel):
    """Parameters controlling system-driven birth."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    min_food: UnitInterval = DEFAULT_MIN_FOOD
    min_water: UnitInterval = DEFAULT_MIN_WATER
    min_energy: UnitInterval = DEFAULT_MIN_ENERGY
    min_parent_age_ticks: NonNegativeInt = DEFAULT_MIN_PARENT_AGE_TICKS
    max_births_per_tick: PositiveInt = 1
    max_population: PositiveInt | None = Field(
        default=None,
        description="Optional hard ceiling on roster size; None means unlimited.",
    )
    parent_energy_cost: UnitInterval = DEFAULT_PARENT_ENERGY_COST
    personality_regression: UnitInterval = DEFAULT_PERSONALITY_REGRESSION


class BirthSystem:
    """Apply deterministic births after agent actions each tick."""

    def __init__(self, config: BirthConfig | None = None) -> None:
        self._config = config if config is not None else BirthConfig()

    @property
    def config(self) -> BirthConfig:
        """Return the immutable birth configuration."""
        return self._config

    def can_birth(self, world: World, agent_id: int) -> bool:
        """Return True when ``agent_id`` is an eligible parent right now."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return False
        return self._eligible(world, agent)

    def apply_births(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Spawn up to ``max_births_per_tick`` children from eligible parents.

        Parents are considered in ascending agent id order. Each parent
        births at most once per call. Location capacity and population
        ceilings are rechecked after every successful birth.
        """
        if not self._config.enabled:
            return world

        births = 0
        birthed_parents: set[int] = set()
        while births < self._config.max_births_per_tick:
            parent = self._next_eligible_parent(world, birthed_parents)
            if parent is None:
                break
            result = apply_birth(
                world,
                parent,
                min_food=self._config.min_food,
                min_water=self._config.min_water,
                min_energy=self._config.min_energy,
                min_parent_age_ticks=self._config.min_parent_age_ticks,
                max_population=self._config.max_population,
                parent_energy_cost=self._config.parent_energy_cost,
                personality_regression=self._config.personality_regression,
            )
            if result is None:
                break
            world, child = result
            birthed_parents.add(parent.agent_id.value)
            births += 1
            if bus is not None:
                bus.publish(
                    AgentBorn(
                        tick=world.tick,
                        agent_id=child.agent_id,
                        parent_id=parent.agent_id,
                        location_id=child.location_id,
                        name=child.name,
                    )
                )
                for fact in sorted(child.knowledge.facts):
                    bus.publish(
                        KnowledgeLearned(
                            tick=world.tick,
                            agent_id=child.agent_id,
                            fact=fact,
                            source=KnowledgeSource.BIRTH.value,
                            teacher_id=parent.agent_id,
                        )
                    )
        return world

    def _eligible(self, world: World, parent: Agent) -> bool:
        return can_birth(
            world,
            parent,
            min_food=self._config.min_food,
            min_water=self._config.min_water,
            min_energy=self._config.min_energy,
            min_parent_age_ticks=self._config.min_parent_age_ticks,
            max_population=self._config.max_population,
            parent_energy_cost=self._config.parent_energy_cost,
        )

    def _next_eligible_parent(
        self,
        world: World,
        birthed_parents: set[int],
    ) -> Agent | None:
        for agent in world.alive_agents():
            if agent.agent_id.value in birthed_parents:
                continue
            if self._eligible(world, agent):
                return agent
        return None
