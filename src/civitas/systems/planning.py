"""Planning system: set satisfy-need goals from reflection beliefs.

Owns tick-time ``apply_planning`` and observe-time ``PlansObserved``.
Does not import CognitionSystem; it only reads agent beliefs/needs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import PlansObserved, PlanUpdated, apply_planning, census_plans

if TYPE_CHECKING:
    from civitas.domain import PlanCensus, World
    from civitas.engine.event_bus import EventBus


class PlanningConfig(BaseModel):
    """Parameters controlling planning application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    emit_events: bool = True


class PlanningSystem:
    """Apply planned goals and observe plan coverage."""

    def __init__(self, config: PlanningConfig | None = None) -> None:
        self._config = config if config is not None else PlanningConfig()

    @property
    def config(self) -> PlanningConfig:
        """Return the immutable planning configuration."""
        return self._config

    def census(self, world: World) -> PlanCensus:
        """Return a planning census for ``world``."""
        return census_plans(world)

    def apply_planning(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Set one satisfy-need goal for each living agent."""
        if not self._config.enabled:
            return world

        world, updates = apply_planning(world)
        if bus is not None and self._config.emit_events:
            for update in updates:
                bus.publish(
                    PlanUpdated(
                        tick=world.tick,
                        agent_id=update.agent_id,
                        goal_kind=update.goal_kind,
                        priority=update.priority,
                        target=update.target,
                    )
                )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe plans and optionally emit ``PlansObserved``.

        The world is never modified.
        """
        snap = census_plans(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                PlansObserved(
                    tick=snap.tick,
                    living_count=snap.living_count,
                    agents_with_plans=snap.agents_with_plans,
                    satisfy_food_count=snap.satisfy_food_count,
                    satisfy_water_count=snap.satisfy_water_count,
                    satisfy_energy_count=snap.satisfy_energy_count,
                )
            )
        return world
