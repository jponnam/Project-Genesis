"""Effects system: observe society modifiers from tech and infrastructure.

Owns observe-time ``EffectsObserved``. Does not apply world mutations;
the action executor reads domain effect helpers when REST/GATHER/DRINK/
MOVE/PRODUCE run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import EffectsObserved, census_effects

if TYPE_CHECKING:
    from civitas.domain import EffectsCensus, World
    from civitas.engine.event_bus import EventBus


class EffectsConfig(BaseModel):
    """Parameters controlling effects observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class EffectsSystem:
    """Observe society effect coverage from innovations and infrastructure."""

    def __init__(self, config: EffectsConfig | None = None) -> None:
        self._config = config if config is not None else EffectsConfig()

    @property
    def config(self) -> EffectsConfig:
        """Return the immutable effects configuration."""
        return self._config

    def census(self, world: World) -> EffectsCensus:
        """Return an effects census for ``world``."""
        return census_effects(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe society effects and optionally emit ``EffectsObserved``.

        The world is never modified.
        """
        snap = census_effects(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                EffectsObserved(
                    tick=snap.tick,
                    living_count=snap.living_count,
                    fire_hearth_active=snap.fire_hearth_active,
                    pottery_craft_active=snap.pottery_craft_active,
                    rest_restore_bps=snap.rest_restore_bps,
                    water_gather_amount=snap.water_gather_amount,
                    active_well_count=snap.active_well_count,
                    drink_restore_bps=snap.drink_restore_bps,
                    active_storehouse_count=snap.active_storehouse_count,
                    food_gather_amount=snap.food_gather_amount,
                    active_road_count=snap.active_road_count,
                    move_energy_cost_bps=snap.move_energy_cost_bps,
                    active_guild_count=snap.active_guild_count,
                    produce_energy_cost_bps=snap.produce_energy_cost_bps,
                )
            )
        return world
