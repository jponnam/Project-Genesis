"""Resource stock observation system.

Emits ``ResourcesObserved`` censuses of agent inventories and market escrow.
Does not own gather/consume/produce mutations (those live in dedicated systems).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import ResourcesObserved, census_resources

if TYPE_CHECKING:
    from civitas.domain import ResourceCensus, World
    from civitas.engine.event_bus import EventBus


class ResourcesConfig(BaseModel):
    """Parameters controlling resource-stock observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class ResourcesSystem:
    """Emit deterministic resource-stock censuses."""

    def __init__(self, config: ResourcesConfig | None = None) -> None:
        self._config = config if config is not None else ResourcesConfig()

    @property
    def config(self) -> ResourcesConfig:
        """Return the immutable resources configuration."""
        return self._config

    def census(self, world: World) -> ResourceCensus:
        """Return a resource-stock census for ``world``."""
        return census_resources(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe resource stocks and optionally emit ``ResourcesObserved``.

        The world is never modified.
        """
        snap = census_resources(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                ResourcesObserved(
                    tick=snap.tick,
                    alive_count=snap.alive_count,
                    agent_holdings=snap.agent_holdings,
                    alive_totals=snap.alive_totals,
                    dead_totals=snap.dead_totals,
                    escrow_totals=snap.escrow_totals,
                    stack_count=snap.stack_count,
                    distinct_resources=snap.distinct_resources,
                )
            )
        return world
