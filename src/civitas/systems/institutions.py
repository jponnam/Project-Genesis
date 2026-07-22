"""Institution system: organization observation and thin mutation wrappers.

Owns observe-time institution censuses that emit ``InstitutionsObserved``.
Create/dissolve/officer/budget helpers live in domain so other layers can
reason about institutions without calling this system. Funding is opt-in
via ``fund`` (mirrors taxes disabled-by-default).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    InstitutionFunded,
    InstitutionsObserved,
    census_institutions,
    create_institution,
    dissolve_institution,
    fund_institution_from_treasury,
    institution_by_id,
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
                    active_guild_count=snap.active_guild_count,
                    active_archive_count=snap.active_archive_count,
                    active_bureaucracy_count=snap.active_bureaucracy_count,
                    active_academy_count=snap.active_academy_count,
                    active_temple_count=snap.active_temple_count,
                    active_school_count=snap.active_school_count,
                    active_lyceum_count=snap.active_lyceum_count,
                    active_hospital_count=snap.active_hospital_count,
                    active_apothecary_count=snap.active_apothecary_count,
                    active_collegium_count=snap.active_collegium_count,
                    active_workshop_count=snap.active_workshop_count,
                    active_mason_count=snap.active_mason_count,
                    active_architect_count=snap.active_architect_count,
                    active_caravan_count=snap.active_caravan_count,
                    total_budget=snap.total_budget,
                    funded_count=snap.funded_count,
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

    def fund(
        self,
        world: World,
        institution_id: InstitutionId | int,
        amount: int,
        bus: EventBus | None = None,
    ) -> World:
        """Fund ``institution_id`` from its government treasury when legal.

        Emits ``InstitutionFunded`` on success. Illegal funding leaves the
        world unchanged.
        """
        updated = fund_institution_from_treasury(world, institution_id, amount)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            institution = institution_by_id(updated, institution_id)
            government = (
                None
                if institution is None
                else updated.government_by_id(institution.government_id)
            )
            if institution is not None and government is not None:
                bus.publish(
                    InstitutionFunded(
                        tick=updated.tick,
                        institution_id=institution.institution_id,
                        government_id=institution.government_id,
                        amount=amount,
                        budget_after=institution.budget,
                        treasury_after=government.treasury,
                    )
                )
        return updated
