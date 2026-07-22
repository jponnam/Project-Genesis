"""Cognition system: encode episodic memories and observe coverage.

Owns tick-time ``apply_cognition`` (deterministic episode encoding) and
observe-time ``CognitionObserved``. An optional ``LanguageModel`` may be
injected for later milestones; Milestone 1 does not call it during apply.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    CognitionObserved,
    MemoryRecorded,
    apply_memory_encoding,
    census_memory,
)

if TYPE_CHECKING:
    from civitas.domain import MemoryCensus, World
    from civitas.engine.event_bus import EventBus
    from civitas.llm import LanguageModel


class CognitionConfig(BaseModel):
    """Parameters controlling cognition application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    emit_events: bool = True


class CognitionSystem:
    """Encode episodic memories and observe agent memory censuses."""

    def __init__(
        self,
        config: CognitionConfig | None = None,
        *,
        language_model: LanguageModel | None = None,
    ) -> None:
        self._config = config if config is not None else CognitionConfig()
        self._language_model = language_model

    @property
    def config(self) -> CognitionConfig:
        """Return the immutable cognition configuration."""
        return self._config

    @property
    def language_model(self) -> LanguageModel | None:
        """Return the optional injected language model, if any."""
        return self._language_model

    def census(self, world: World) -> MemoryCensus:
        """Return a memory census for ``world``."""
        return census_memory(world)

    def apply_cognition(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Encode one episode memory per living agent.

        The optional language model is intentionally unused in Milestone 1
        so default runs stay offline and deterministic.
        """
        if not self._config.enabled:
            return world

        world, writes = apply_memory_encoding(world)
        if bus is not None and self._config.emit_events:
            for write in writes:
                bus.publish(
                    MemoryRecorded(
                        tick=world.tick,
                        agent_id=write.agent_id,
                        kind=write.kind,
                        content=write.content,
                    )
                )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe memory coverage and optionally emit ``CognitionObserved``.

        The world is never modified.
        """
        snap = census_memory(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                CognitionObserved(
                    tick=snap.tick,
                    living_count=snap.living_count,
                    total_records=snap.total_records,
                    agents_with_memory=snap.agents_with_memory,
                    episode_records=snap.episode_records,
                    mean_records_bps=snap.mean_records_bps,
                )
            )
        return world
