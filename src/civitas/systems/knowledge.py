"""Knowledge system: diffuse discovered-tech facts among agents.

Owns tick-time ``apply_knowledge`` (bootstrap + trust-gated peer teach)
and observe-time ``KnowledgeObserved``. Uses domain helpers only — does
not call Tech/Research/Innovation systems.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    DEFAULT_MIN_TEACH_TRUST,
    KnowledgeLearned,
    KnowledgeObserved,
    apply_knowledge_diffusion,
    census_knowledge,
)
from civitas.domain.types import NonNegativeInt, UnitInterval

if TYPE_CHECKING:
    from civitas.domain import KnowledgeCensus, World
    from civitas.engine.event_bus import EventBus


class KnowledgeConfig(BaseModel):
    """Parameters controlling knowledge application and observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = True
    emit_events: bool = True
    teachings_per_knower: NonNegativeInt = 1
    min_teach_trust: UnitInterval = DEFAULT_MIN_TEACH_TRUST


class KnowledgeSystem:
    """Apply knowledge diffusion and observe coverage."""

    def __init__(self, config: KnowledgeConfig | None = None) -> None:
        self._config = config if config is not None else KnowledgeConfig()

    @property
    def config(self) -> KnowledgeConfig:
        """Return the immutable knowledge configuration."""
        return self._config

    def census(self, world: World) -> KnowledgeCensus:
        """Return a knowledge census for ``world``."""
        return census_knowledge(world)

    def apply_knowledge(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Bootstrap missing knowers and diffuse facts among co-located agents."""
        if not self._config.enabled:
            return world

        world, gains = apply_knowledge_diffusion(
            world,
            teachings_per_knower=self._config.teachings_per_knower,
            min_trust=float(self._config.min_teach_trust),
        )
        if bus is not None and self._config.emit_events:
            for gain in gains:
                bus.publish(
                    KnowledgeLearned(
                        tick=world.tick,
                        agent_id=gain.agent_id,
                        fact=gain.fact,
                        source=gain.source.value,
                        teacher_id=gain.teacher_id,
                    )
                )
        return world

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe knowledge coverage and optionally emit ``KnowledgeObserved``.

        The world is never modified.
        """
        snap = census_knowledge(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                KnowledgeObserved(
                    tick=snap.tick,
                    living_count=snap.living_count,
                    discovered_technology_count=snap.discovered_technology_count,
                    fire_knower_count=snap.fire_knower_count,
                    pottery_knower_count=snap.pottery_knower_count,
                    irrigation_knower_count=snap.irrigation_knower_count,
                    metallurgy_knower_count=snap.metallurgy_knower_count,
                    writing_knower_count=snap.writing_knower_count,
                    mathematics_knower_count=snap.mathematics_knower_count,
                    astronomy_knower_count=snap.astronomy_knower_count,
                    philosophy_knower_count=snap.philosophy_knower_count,
                    logic_knower_count=snap.logic_knower_count,
                    rhetoric_knower_count=snap.rhetoric_knower_count,
                    medicine_knower_count=snap.medicine_knower_count,
                    anatomy_knower_count=snap.anatomy_knower_count,
                    hygiene_knower_count=snap.hygiene_knower_count,
                    engineering_knower_count=snap.engineering_knower_count,
                    architecture_knower_count=snap.architecture_knower_count,
                    surveying_knower_count=snap.surveying_knower_count,
                    navigation_knower_count=snap.navigation_knower_count,
                    cartography_knower_count=snap.cartography_knower_count,
                    seafaring_knower_count=snap.seafaring_knower_count,
                    agriculture_knower_count=snap.agriculture_knower_count,
                    crop_rotation_knower_count=snap.crop_rotation_knower_count,
                    forestry_knower_count=snap.forestry_knower_count,
                    total_fact_instances=snap.total_fact_instances,
                    coverage_bps=snap.coverage_bps,
                )
            )
        return world
