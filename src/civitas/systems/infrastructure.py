"""Infrastructure system: built-capacity observation and thin wrappers.

Owns observe-time infrastructure censuses that emit
``InfrastructuresObserved``. Create/dissolve helpers live in domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    InfrastructuresObserved,
    census_infrastructure,
    create_infrastructure,
    dissolve_infrastructure,
    set_infrastructure_active,
)

if TYPE_CHECKING:
    from civitas.domain import (
        Infrastructure,
        InfrastructureCensus,
        InfrastructureId,
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
