"""Cognition system: encode memories, reflect, and observe coverage.

Owns tick-time ``apply_cognition`` (episode encoding + optional reflection)
and observe-time ``CognitionObserved``. Reflection uses an injected
``LanguageModel`` port; the default is ``SeededMockLanguageModel``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    AgentReflected,
    CognitionObserved,
    MemoryRecorded,
    apply_memory_encoding,
    apply_reflections,
    census_memory,
)
from civitas.llm import SeededMockLanguageModel

if TYPE_CHECKING:
    from civitas.domain import MemoryCensus, World
    from civitas.engine.event_bus import EventBus
    from civitas.llm import LanguageModel


class CognitionConfig(BaseModel):
    """Parameters controlling cognition application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    emit_events: bool = True
    reflect: bool = True


class CognitionSystem:
    """Encode episodic memories, run reflections, and observe censuses."""

    def __init__(
        self,
        config: CognitionConfig | None = None,
        *,
        language_model: LanguageModel | None = None,
    ) -> None:
        self._config = config if config is not None else CognitionConfig()
        self._language_model = (
            language_model if language_model is not None else SeededMockLanguageModel()
        )

    @property
    def config(self) -> CognitionConfig:
        """Return the immutable cognition configuration."""
        return self._config

    @property
    def language_model(self) -> LanguageModel:
        """Return the language model used for reflection."""
        return self._language_model

    def census(self, world: World) -> MemoryCensus:
        """Return a memory census for ``world``."""
        return census_memory(world)

    def apply_cognition(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Encode episode memories, then optionally reflect via the LLM port."""
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

        if self._config.reflect:
            world, outcomes = apply_reflections(
                world,
                self._language_model,
                seed=world.config.seed + world.tick.value,
            )
            if bus is not None and self._config.emit_events:
                for outcome in outcomes:
                    bus.publish(
                        MemoryRecorded(
                            tick=world.tick,
                            agent_id=outcome.agent_id,
                            kind="reflection",
                            content=outcome.response_text,
                        )
                    )
                    bus.publish(
                        AgentReflected(
                            tick=world.tick,
                            agent_id=outcome.agent_id,
                            proposition=outcome.proposition,
                            confidence=outcome.confidence,
                            model_name=outcome.model_name,
                        )
                    )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe memory/belief coverage and emit ``CognitionObserved``.

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
                    reflection_records=snap.reflection_records,
                    belief_count=snap.belief_count,
                    mean_records_bps=snap.mean_records_bps,
                )
            )
        return world
