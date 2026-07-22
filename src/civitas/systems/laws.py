"""Law system: statute observation and thin mutation wrappers.

Owns observe-time law censuses that emit ``LawsObserved``. Enactment and
repeal live in domain helpers. Active tax schedules affect levies through
domain tax helpers without systems calling each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    LawsObserved,
    census_laws,
    enact_law,
    repeal_law,
    set_law_active,
)

if TYPE_CHECKING:
    from civitas.domain import Law, LawCensus, LawId, World
    from civitas.engine.event_bus import EventBus


class LawConfig(BaseModel):
    """Parameters controlling law observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class LawSystem:
    """Observe statutes and apply deterministic law mutations."""

    def __init__(self, config: LawConfig | None = None) -> None:
        self._config = config if config is not None else LawConfig()

    @property
    def config(self) -> LawConfig:
        """Return the immutable law configuration."""
        return self._config

    def census(self, world: World) -> LawCensus:
        """Return a law census for ``world``."""
        return census_laws(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe laws and optionally emit ``LawsObserved``.

        The world is never modified.
        """
        snap = census_laws(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                LawsObserved(
                    tick=snap.tick,
                    law_count=snap.law_count,
                    active_count=snap.active_count,
                    inactive_count=snap.inactive_count,
                    governments_with_active_laws=snap.governments_with_active_laws,
                    active_tax_schedule_count=snap.active_tax_schedule_count,
                    active_market_fee_count=snap.active_market_fee_count,
                    active_curriculum_count=snap.active_curriculum_count,
                    active_calendar_count=snap.active_calendar_count,
                    active_ethics_count=snap.active_ethics_count,
                    active_assembly_count=snap.active_assembly_count,
                    active_sanitation_count=snap.active_sanitation_count,
                    active_quarantine_count=snap.active_quarantine_count,
                    active_building_codes_count=snap.active_building_codes_count,
                    active_zoning_count=snap.active_zoning_count,
                    active_passage_count=snap.active_passage_count,
                    active_customs_count=snap.active_customs_count,
                    active_land_tenure_count=snap.active_land_tenure_count,
                    active_conservation_count=snap.active_conservation_count,
                    active_labor_count=snap.active_labor_count,
                )
            )
        return world

    def enact(self, world: World, law: Law) -> World:
        """Enact ``law`` when legal; otherwise leave the world unchanged."""
        updated = enact_law(world, law)
        return world if updated is None else updated

    def repeal(self, world: World, law_id: LawId | int) -> World:
        """Repeal ``law_id`` when present; otherwise leave the world unchanged."""
        updated = repeal_law(world, law_id)
        return world if updated is None else updated

    def set_active(self, world: World, law_id: LawId | int, active: bool) -> World:
        """Set active flag when legal; otherwise leave the world unchanged."""
        updated = set_law_active(world, law_id, active)
        return world if updated is None else updated
