"""Infrastructure system: built-capacity observation and thin wrappers.

Owns observe-time infrastructure censuses that emit
``InfrastructuresObserved``. Create/dissolve/build helpers live in domain.
Paid construction is opt-in via ``build`` (mirrors institution funding).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    InfrastructureBuilt,
    InfrastructureCommissioned,
    InfrastructuresObserved,
    build_cost_for,
    build_infrastructure,
    build_infrastructure_from_institution,
    census_infrastructure,
    create_infrastructure,
    dissolve_infrastructure,
    infrastructure_by_id,
    institution_by_id,
    set_infrastructure_active,
)

if TYPE_CHECKING:
    from civitas.domain import (
        Infrastructure,
        InfrastructureCensus,
        InfrastructureId,
        InstitutionId,
        World,
    )
    from civitas.engine.event_bus import EventBus


class InfrastructureConfig(BaseModel):
    """Parameters controlling infrastructure observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class InfrastructureSystem:
    """Observe infrastructure and apply deterministic mutations."""

    def __init__(self, config: InfrastructureConfig | None = None) -> None:
        self._config = config if config is not None else InfrastructureConfig()

    @property
    def config(self) -> InfrastructureConfig:
        """Return the immutable infrastructure configuration."""
        return self._config

    def census(self, world: World) -> InfrastructureCensus:
        """Return an infrastructure census for ``world``."""
        return census_infrastructure(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe infrastructure and optionally emit ``InfrastructuresObserved``.

        The world is never modified.
        """
        snap = census_infrastructure(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                InfrastructuresObserved(
                    tick=snap.tick,
                    infrastructure_count=snap.infrastructure_count,
                    active_count=snap.active_count,
                    inactive_count=snap.inactive_count,
                    governments_with_infrastructure=(
                        snap.governments_with_infrastructure
                    ),
                    cities_with_infrastructure=snap.cities_with_infrastructure,
                    active_well_count=snap.active_well_count,
                    active_storehouse_count=snap.active_storehouse_count,
                    active_road_count=snap.active_road_count,
                    active_scriptorium_count=snap.active_scriptorium_count,
                    active_stoa_count=snap.active_stoa_count,
                    active_observatory_count=snap.active_observatory_count,
                    active_shrine_count=snap.active_shrine_count,
                )
            )
        return world

    def create(self, world: World, item: Infrastructure) -> World:
        """Create ``item`` when legal; otherwise leave the world unchanged."""
        updated = create_infrastructure(world, item)
        return world if updated is None else updated

    def dissolve(
        self,
        world: World,
        infrastructure_id: InfrastructureId | int,
    ) -> World:
        """Dissolve ``infrastructure_id`` when present; otherwise unchanged."""
        updated = dissolve_infrastructure(world, infrastructure_id)
        return world if updated is None else updated

    def set_active(
        self,
        world: World,
        infrastructure_id: InfrastructureId | int,
        active: bool,
    ) -> World:
        """Set active flag when legal; otherwise leave the world unchanged."""
        updated = set_infrastructure_active(world, infrastructure_id, active)
        return world if updated is None else updated

    def build(
        self,
        world: World,
        item: Infrastructure,
        bus: EventBus | None = None,
        *,
        cost: int | None = None,
    ) -> World:
        """Pay to construct ``item`` from its government treasury when legal.

        Emits ``InfrastructureBuilt`` on success. Illegal builds leave the
        world unchanged. ``cost`` defaults to the catalog price for the kind.
        """
        amount = build_cost_for(item.kind) if cost is None else cost
        updated = build_infrastructure(world, item, cost=cost)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            built = infrastructure_by_id(updated, item.infrastructure_id)
            government = (
                None if built is None else updated.government_by_id(built.government_id)
            )
            if built is not None and government is not None:
                bus.publish(
                    InfrastructureBuilt(
                        tick=updated.tick,
                        infrastructure_id=built.infrastructure_id,
                        government_id=built.government_id,
                        city_id=built.city_id,
                        location_id=built.location_id,
                        name=built.name,
                        kind=built.kind.value,
                        cost=amount,
                        treasury_after=government.treasury,
                    )
                )
        return updated

    def commission(
        self,
        world: World,
        item: Infrastructure,
        institution_id: InstitutionId | int,
        bus: EventBus | None = None,
        *,
        cost: int | None = None,
    ) -> World:
        """Pay to construct ``item`` from an institution budget when legal.

        Emits ``InfrastructureCommissioned`` on success. Illegal builds leave
        the world unchanged. ``cost`` defaults to the catalog price.
        """
        amount = build_cost_for(item.kind) if cost is None else cost
        updated = build_infrastructure_from_institution(
            world, item, institution_id, cost=cost
        )
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            built = infrastructure_by_id(updated, item.infrastructure_id)
            institution = institution_by_id(updated, institution_id)
            if built is not None and institution is not None:
                bus.publish(
                    InfrastructureCommissioned(
                        tick=updated.tick,
                        infrastructure_id=built.infrastructure_id,
                        government_id=built.government_id,
                        institution_id=institution.institution_id,
                        city_id=built.city_id,
                        location_id=built.location_id,
                        name=built.name,
                        kind=built.kind.value,
                        cost=amount,
                        budget_after=institution.budget,
                    )
                )
        return updated
