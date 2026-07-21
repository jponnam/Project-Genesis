"""Population system: observe roster census without mutating the world.

Owns population observation as a first-class tick concern that emits
``PopulationObserved``. Census math lives in domain helpers so other
layers can query population without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import PopulationObserved, census

if TYPE_CHECKING:
    from civitas.domain import PopulationCensus, World
    from civitas.engine.event_bus import EventBus


class PopulationConfig(BaseModel):
    """Parameters controlling population observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class PopulationSystem:
    """Compute and emit deterministic population censuses."""

    def __init__(self, config: PopulationConfig | None = None) -> None:
        self._config = config if config is not None else PopulationConfig()

    @property
    def config(self) -> PopulationConfig:
        """Return the immutable population configuration."""
        return self._config

    def census(self, world: World) -> PopulationCensus:
        """Return a population census for ``world``."""
        return census(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe population and optionally emit ``PopulationObserved``.

        The world is never modified.
        """
        snap = census(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                PopulationObserved(
                    tick=snap.tick,
                    initial_count=snap.initial_count,
                    total=snap.total,
                    alive=snap.alive,
                    dead=snap.dead,
                    location_counts=tuple(
                        (entry.location_id.value, entry.count)
                        for entry in snap.by_location
                    ),
                )
            )
        return world
