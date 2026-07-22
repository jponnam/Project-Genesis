"""Technology system: catalog observation and thin discovery wrappers.

Owns observe-time technology censuses that emit ``TechnologiesObserved``.
Discovery lives in domain helpers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    TechnologiesObserved,
    census_technologies,
    create_technology,
    discover_technology,
)

if TYPE_CHECKING:
    from civitas.domain import (
        Technology,
        TechnologyCensus,
        TechnologyId,
        World,
    )
    from civitas.engine.event_bus import EventBus


class TechConfig(BaseModel):
    """Parameters controlling technology observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class TechSystem:
    """Observe technologies and apply deterministic discovery mutations."""

    def __init__(self, config: TechConfig | None = None) -> None:
        self._config = config if config is not None else TechConfig()

    @property
    def config(self) -> TechConfig:
        """Return the immutable technology configuration."""
        return self._config

    def census(self, world: World) -> TechnologyCensus:
        """Return a technology census for ``world``."""
        return census_technologies(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe technologies and optionally emit ``TechnologiesObserved``.

        The world is never modified.
        """
        snap = census_technologies(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                TechnologiesObserved(
                    tick=snap.tick,
                    technology_count=snap.technology_count,
                    discovered_count=snap.discovered_count,
                    undiscovered_count=snap.undiscovered_count,
                    discovered_fire_count=snap.discovered_fire_count,
                    discovered_pottery_count=snap.discovered_pottery_count,
                    discovered_irrigation_count=snap.discovered_irrigation_count,
                    discovered_metallurgy_count=snap.discovered_metallurgy_count,
                    discovered_writing_count=snap.discovered_writing_count,
                    discovered_mathematics_count=snap.discovered_mathematics_count,
                    discovered_astronomy_count=snap.discovered_astronomy_count,
                    discovered_philosophy_count=snap.discovered_philosophy_count,
                    discovered_logic_count=snap.discovered_logic_count,
                    discovered_rhetoric_count=snap.discovered_rhetoric_count,
                    discovered_medicine_count=snap.discovered_medicine_count,
                    discovered_anatomy_count=snap.discovered_anatomy_count,
                    discovered_hygiene_count=snap.discovered_hygiene_count,
                    discovered_engineering_count=snap.discovered_engineering_count,
                    discovered_architecture_count=snap.discovered_architecture_count,
                    discovered_surveying_count=snap.discovered_surveying_count,
                    discovered_navigation_count=snap.discovered_navigation_count,
                    discovered_cartography_count=snap.discovered_cartography_count,
                    discovered_seafaring_count=snap.discovered_seafaring_count,
                    discovered_agriculture_count=snap.discovered_agriculture_count,
                    discovered_crop_rotation_count=snap.discovered_crop_rotation_count,
                    locked_count=snap.locked_count,
                    researchable_count=snap.researchable_count,
                )
            )
        return world

    def create(self, world: World, technology: Technology) -> World:
        """Create ``technology`` when legal; otherwise leave world unchanged."""
        updated = create_technology(world, technology)
        return world if updated is None else updated

    def discover(
        self,
        world: World,
        technology_id: TechnologyId | int,
    ) -> World:
        """Discover ``technology_id`` when present; otherwise leave unchanged."""
        updated = discover_technology(world, technology_id)
        return world if updated is None else updated
