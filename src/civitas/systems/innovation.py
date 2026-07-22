"""Innovation system: activate due adoptions and observe census.

Owns tick-time ``apply_innovations`` (activate when tech is discovered)
and observe-time ``InnovationsObserved``. Activation uses domain helpers
— this system does not call ``TechSystem`` or ``ResearchSystem``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    InnovationActivated,
    InnovationsObserved,
    activate_due_innovations,
    activate_innovation,
    census_innovations,
    create_innovation,
)

if TYPE_CHECKING:
    from civitas.domain import (
        Innovation,
        InnovationCensus,
        InnovationId,
        World,
    )
    from civitas.engine.event_bus import EventBus


class InnovationConfig(BaseModel):
    """Parameters controlling innovation application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    emit_events: bool = True


class InnovationSystem:
    """Apply due innovation activations and observe adoption state."""

    def __init__(self, config: InnovationConfig | None = None) -> None:
        self._config = config if config is not None else InnovationConfig()

    @property
    def config(self) -> InnovationConfig:
        """Return the immutable innovation configuration."""
        return self._config

    def census(self, world: World) -> InnovationCensus:
        """Return an innovation census for ``world``."""
        return census_innovations(world)

    def apply_innovations(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Activate innovations whose technologies are already discovered."""
        if not self._config.enabled:
            return world

        world, activations = activate_due_innovations(world)
        if bus is not None and self._config.emit_events:
            for activation in activations:
                bus.publish(
                    InnovationActivated(
                        tick=world.tick,
                        innovation_id=activation.innovation_id,
                        technology_id=activation.technology_id,
                        name=activation.name,
                        kind=activation.kind.value,
                    )
                )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe innovations and optionally emit ``InnovationsObserved``.

        The world is never modified.
        """
        snap = census_innovations(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                InnovationsObserved(
                    tick=snap.tick,
                    innovation_count=snap.innovation_count,
                    active_count=snap.active_count,
                    inactive_count=snap.inactive_count,
                    active_fire_hearth_count=snap.active_fire_hearth_count,
                    active_pottery_craft_count=snap.active_pottery_craft_count,
                    active_irrigation_canal_count=(snap.active_irrigation_canal_count),
                    active_forge_count=snap.active_forge_count,
                    active_scribe_count=snap.active_scribe_count,
                    active_abacus_count=snap.active_abacus_count,
                    active_star_chart_count=snap.active_star_chart_count,
                    active_dialectic_count=snap.active_dialectic_count,
                    active_syllogism_count=snap.active_syllogism_count,
                    active_oration_count=snap.active_oration_count,
                    active_remedy_count=snap.active_remedy_count,
                    active_dissection_count=snap.active_dissection_count,
                    active_asepsis_count=snap.active_asepsis_count,
                    active_pulley_count=snap.active_pulley_count,
                    active_blueprint_count=snap.active_blueprint_count,
                    active_plumb_line_count=snap.active_plumb_line_count,
                    active_compass_count=snap.active_compass_count,
                    active_map_count=snap.active_map_count,
                    active_sail_count=snap.active_sail_count,
                    active_plow_count=snap.active_plow_count,
                    active_fallow_count=snap.active_fallow_count,
                    active_coppice_count=snap.active_coppice_count,
                    active_loom_count=snap.active_loom_count,
                    active_mordant_count=snap.active_mordant_count,
                )
            )
        return world

    def create(self, world: World, innovation: Innovation) -> World:
        """Create ``innovation`` when legal; otherwise leave world unchanged."""
        updated = create_innovation(world, innovation)
        return world if updated is None else updated

    def activate(
        self,
        world: World,
        innovation_id: InnovationId | int,
    ) -> World:
        """Activate ``innovation_id`` when legal; otherwise leave unchanged."""
        updated = activate_innovation(world, innovation_id)
        return world if updated is None else updated
