"""Institution system: organization observation and thin mutation wrappers.

Owns observe-time institution censuses that emit ``InstitutionsObserved``.
Create/dissolve/officer helpers live in domain so other layers can reason
about institutions without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    InstitutionsObserved,
    census_institutions,
    create_institution,
    dissolve_institution,
    set_institution_active,
    set_officer,
)

if TYPE_CHECKING:
    from civitas.domain import (
        AgentId,
        Institution,
        InstitutionCensus,
        InstitutionId,
        World,
    )
    from civitas.engine.event_bus import EventBus


class InstitutionConfig(BaseModel):
    """Parameters controlling institution observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class InstitutionSystem:
    """Observe institutions and apply deterministic institution mutations."""

    def __init__(self, config: InstitutionConfig | None = None) -> None:
        self._config = config if config is not None else InstitutionConfig()

    @property
    def config(self) -> InstitutionConfig:
        """Return the immutable institution configuration."""
        return self._config

    def census(self, world: World) -> InstitutionCensus:
        """Return an institution census for ``world``."""
        return census_institutions(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe institutions and optionally emit ``InstitutionsObserved``.

        The world is never modified.
        """
        snap = census_institutions(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                InstitutionsObserved(
                    tick=snap.tick,
                    institution_count=snap.institution_count,
                    active_count=snap.active_count,
                    inactive_count=snap.inactive_count,
                    governments_with_institutions=snap.governments_with_institutions,
                    staffed_count=snap.staffed_count,
                    vacant_officer_count=snap.vacant_officer_count,
                    active_council_count=snap.active_council_count,
                )
            )
        return world

    def create(self, world: World, institution: Institution) -> World:
        """Create ``institution`` when legal; otherwise leave world unchanged."""
        updated = create_institution(world, institution)
        return world if updated is None else updated

    def dissolve(self, world: World, institution_id: InstitutionId | int) -> World:
        """Dissolve ``institution_id`` when present; otherwise leave unchanged."""
        updated = dissolve_institution(world, institution_id)
        return world if updated is None else updated

    def set_active(
        self,
        world: World,
        institution_id: InstitutionId | int,
        active: bool,
    ) -> World:
        """Set active flag when legal; otherwise leave the world unchanged."""
        updated = set_institution_active(world, institution_id, active)
        return world if updated is None else updated

    def appoint_officer(
        self,
        world: World,
        institution_id: InstitutionId | int,
        officer_id: AgentId | int | None,
    ) -> World:
        """Appoint or clear an officer when legal; otherwise leave unchanged."""
        updated = set_officer(world, institution_id, officer_id)
        return world if updated is None else updated
