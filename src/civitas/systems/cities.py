"""City system: settlement observation and thin mutation wrappers.

Owns observe-time city censuses that emit ``CitiesObserved``. Create,
dissolve, and capital helpers live in domain so other layers can reason
about settlements without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    CitiesObserved,
    census_cities,
    create_city,
    dissolve_city,
    set_capital,
    set_city_active,
)

if TYPE_CHECKING:
    from civitas.domain import City, CityCensus, CityId, World
    from civitas.engine.event_bus import EventBus


class CityConfig(BaseModel):
    """Parameters controlling city observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class CitySystem:
    """Observe cities and apply deterministic city mutations."""

    def __init__(self, config: CityConfig | None = None) -> None:
        self._config = config if config is not None else CityConfig()

    @property
    def config(self) -> CityConfig:
        """Return the immutable city configuration."""
        return self._config

    def census(self, world: World) -> CityCensus:
        """Return a city census for ``world``."""
        return census_cities(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe cities and optionally emit ``CitiesObserved``.

        The world is never modified.
        """
        snap = census_cities(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                CitiesObserved(
                    tick=snap.tick,
                    city_count=snap.city_count,
                    active_count=snap.active_count,
                    inactive_count=snap.inactive_count,
                    governments_with_cities=snap.governments_with_cities,
                    capital_count=snap.capital_count,
                    total_residents=snap.total_residents,
                    mean_residents=snap.mean_residents,
                    max_residents=snap.max_residents,
                    max_residents_city_id=snap.max_residents_city_id,
                    active_settlement_count=snap.active_settlement_count,
                    active_outpost_count=snap.active_outpost_count,
                    active_library_count=snap.active_library_count,
                    active_forum_count=snap.active_forum_count,
                    active_sanctuary_count=snap.active_sanctuary_count,
                    active_agora_count=snap.active_agora_count,
                    active_infirmary_count=snap.active_infirmary_count,
                    active_lazaretto_count=snap.active_lazaretto_count,
                    active_foundry_count=snap.active_foundry_count,
                    active_quarry_count=snap.active_quarry_count,
                    active_harbor_count=snap.active_harbor_count,
                    active_entrepot_count=snap.active_entrepot_count,
                    active_farmstead_count=snap.active_farmstead_count,
                    active_pastoral_count=snap.active_pastoral_count,
                    active_mill_town_count=snap.active_mill_town_count,
                    active_emporium_count=snap.active_emporium_count,
                    active_mining_camp_count=snap.active_mining_camp_count,
                    active_ironworks_count=snap.active_ironworks_count,
                    active_timber_town_count=snap.active_timber_town_count,
                    active_guildhall_count=snap.active_guildhall_count,
                    active_pottery_town_count=snap.active_pottery_town_count,
                )
            )
        return world

    def create(self, world: World, city: City) -> World:
        """Create ``city`` when legal; otherwise leave the world unchanged."""
        updated = create_city(world, city)
        return world if updated is None else updated

    def dissolve(self, world: World, city_id: CityId | int) -> World:
        """Dissolve ``city_id`` when present; otherwise leave unchanged."""
        updated = dissolve_city(world, city_id)
        return world if updated is None else updated

    def set_active(self, world: World, city_id: CityId | int, active: bool) -> World:
        """Set active flag when legal; otherwise leave the world unchanged."""
        updated = set_city_active(world, city_id, active)
        return world if updated is None else updated

    def set_capital_flag(
        self,
        world: World,
        city_id: CityId | int,
        is_capital: bool,
    ) -> World:
        """Set or clear capital when legal; otherwise leave unchanged."""
        updated = set_capital(world, city_id, is_capital)
        return world if updated is None else updated
