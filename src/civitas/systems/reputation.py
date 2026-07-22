"""Reputation system: observe-only public standing censuses.

Derives standing from inbound directed bonds after relationship observation.
Does not mutate agents or relationships. Emits ``ReputationObserved``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import ReputationObserved, census_reputation, top_standing

if TYPE_CHECKING:
    from civitas.domain import ReputationCensus, World
    from civitas.engine.event_bus import EventBus


class ReputationConfig(BaseModel):
    """Parameters controlling reputation observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class ReputationSystem:
    """Emit deterministic public-standing censuses without mutating the world."""

    def __init__(self, config: ReputationConfig | None = None) -> None:
        self._config = config if config is not None else ReputationConfig()

    @property
    def config(self) -> ReputationConfig:
        """Return the immutable reputation configuration."""
        return self._config

    def census(self, world: World) -> ReputationCensus:
        """Return a reputation census for ``world``."""
        return census_reputation(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe reputation and optionally emit ``ReputationObserved``.

        The world is never modified.
        """
        snap = census_reputation(world)
        if bus is not None and self._config.emit_events:
            top = top_standing(snap.standings)
            bus.publish(
                ReputationObserved(
                    tick=snap.tick,
                    living_agent_count=snap.living_agent_count,
                    mean_standing=snap.mean_standing,
                    median_standing_bps=snap.median_standing_bps,
                    gini_standing_bps=snap.gini_standing_bps,
                    top_standing_share_bps=snap.top_standing_share_bps,
                    agents_with_inbound_bonds=snap.agents_with_inbound_bonds,
                    top_agent_id=None if top is None else top.agent_id,
                    top_standing=None if top is None else top.standing,
                )
            )
        return world
