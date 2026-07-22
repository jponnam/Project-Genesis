"""Research system: apply progress each tick and observe census.

Owns tick-time ``apply_research`` (points + discovery) and observe-time
``ResearchObserved``. Discovery uses domain ``discover_technology`` —
this system does not call ``TechSystem``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    ResearchObserved,
    ResearchProgressed,
    TechnologyDiscovered,
    advance_research,
    census_research,
    technology_by_id,
)
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain import ResearchCensus, World
    from civitas.engine.event_bus import EventBus


class ResearchConfig(BaseModel):
    """Parameters controlling research application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    points_per_tick: NonNegativeInt = 1
    emit_events: bool = True


class ResearchSystem:
    """Apply research progress and observe remaining work."""

    def __init__(self, config: ResearchConfig | None = None) -> None:
        self._config = config if config is not None else ResearchConfig()

    @property
    def config(self) -> ResearchConfig:
        """Return the immutable research configuration."""
        return self._config

    def census(self, world: World) -> ResearchCensus:
        """Return a research census for ``world``."""
        return census_research(world)

    def apply_research(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Advance research rows and discover technologies when ready."""
        if not self._config.enabled:
            return world

        world, outcomes = advance_research(
            world, points_per_tick=self._config.points_per_tick
        )
        if bus is not None and self._config.emit_events:
            for outcome in outcomes:
                delta = outcome.points_after - outcome.points_before
                if delta > 0:
                    bus.publish(
                        ResearchProgressed(
                            tick=world.tick,
                            technology_id=outcome.technology_id,
                            points_after=outcome.points_after,
                            threshold=outcome.threshold,
                            delta=delta,
                        )
                    )
                if outcome.discovered:
                    technology = technology_by_id(world, outcome.technology_id)
                    if technology is not None:
                        bus.publish(
                            TechnologyDiscovered(
                                tick=world.tick,
                                technology_id=technology.technology_id,
                                name=technology.name,
                                kind=technology.kind.value,
                            )
                        )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe research progress and optionally emit ``ResearchObserved``.

        The world is never modified.
        """
        snap = census_research(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                ResearchObserved(
                    tick=snap.tick,
                    progress_count=snap.progress_count,
                    total_points=snap.total_points,
                    total_threshold=snap.total_threshold,
                    total_remaining=snap.total_remaining,
                    completion_bps=snap.completion_bps,
                )
            )
        return world
