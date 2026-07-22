"""Retrieval system: load relevant memories into working memory.

Owns tick-time ``apply_retrieval`` and observe-time ``RetrievalObserved``.
Does not import PlanningSystem or CognitionSystem; it only reads agent
goals, beliefs, needs, and long-term memory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    DEFAULT_RETRIEVAL_LIMIT,
    MemoryRetrieved,
    RetrievalObserved,
    apply_retrieval,
    census_retrieval,
)
from civitas.domain.types import PositiveInt

if TYPE_CHECKING:
    from civitas.domain import RetrievalCensus, World
    from civitas.engine.event_bus import EventBus


class RetrievalConfig(BaseModel):
    """Parameters controlling retrieval application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    emit_events: bool = True
    limit: PositiveInt = Field(default=DEFAULT_RETRIEVAL_LIMIT)


class RetrievalSystem:
    """Apply memory retrieval and observe working-memory coverage."""

    def __init__(self, config: RetrievalConfig | None = None) -> None:
        self._config = config if config is not None else RetrievalConfig()

    @property
    def config(self) -> RetrievalConfig:
        """Return the immutable retrieval configuration."""
        return self._config

    def census(self, world: World) -> RetrievalCensus:
        """Return a retrieval census for ``world``."""
        return census_retrieval(world)

    def apply_retrieval(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Refresh working memory for each living agent."""
        if not self._config.enabled:
            return world

        world, hits = apply_retrieval(world, limit=self._config.limit)
        if bus is not None and self._config.emit_events:
            for hit in hits:
                bus.publish(
                    MemoryRetrieved(
                        tick=world.tick,
                        agent_id=hit.agent_id,
                        query=hit.query,
                        retrieved_count=hit.retrieved_count,
                        summary=hit.summary,
                    )
                )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe retrieval coverage and optionally emit ``RetrievalObserved``.

        The world is never modified.
        """
        snap = census_retrieval(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                RetrievalObserved(
                    tick=snap.tick,
                    living_count=snap.living_count,
                    agents_with_context=snap.agents_with_context,
                    total_retrieved=snap.total_retrieved,
                    mean_retrieved_bps=snap.mean_retrieved_bps,
                )
            )
        return world
