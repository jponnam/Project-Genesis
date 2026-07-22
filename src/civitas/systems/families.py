"""Family system: observe-only kinship censuses.

Derives lineage metrics from ``AgentIdentity.parent_id`` after birth has
settled the roster. Does not mutate agents or relationships. Emits
``FamiliesObserved``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import FamiliesObserved, census_families

if TYPE_CHECKING:
    from civitas.domain import FamilyCensus, World
    from civitas.engine.event_bus import EventBus


class FamilyConfig(BaseModel):
    """Parameters controlling family observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class FamilySystem:
    """Emit deterministic kinship censuses without mutating the world."""

    def __init__(self, config: FamilyConfig | None = None) -> None:
        self._config = config if config is not None else FamilyConfig()

    @property
    def config(self) -> FamilyConfig:
        """Return the immutable family configuration."""
        return self._config

    def census(self, world: World) -> FamilyCensus:
        """Return a family census for ``world``."""
        return census_families(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe families and optionally emit ``FamiliesObserved``.

        The world is never modified.
        """
        snap = census_families(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                FamiliesObserved(
                    tick=snap.tick,
                    living_agent_count=snap.living_agent_count,
                    founder_count=snap.founder_count,
                    parented_count=snap.parented_count,
                    orphan_count=snap.orphan_count,
                    living_with_living_parent=snap.living_with_living_parent,
                    lineage_count=snap.lineage_count,
                    mean_lineage_size=snap.mean_lineage_size,
                    max_lineage_size=snap.max_lineage_size,
                    max_generation_depth=snap.max_generation_depth,
                    parents_with_living_children=snap.parents_with_living_children,
                    mean_living_children=snap.mean_living_children,
                    max_living_children=snap.max_living_children,
                )
            )
        return world
