"""Government system: polity observation and thin mutation wrappers.

Owns observe-time government censuses that emit ``GovernmentsObserved``.
Leader appointment and treasury helpers live in domain so other layers can
reason about polities without calling this system. Elections may appoint
leaders via ``VoteSystem.conduct``; tax redirection remains a later
Phase 5 milestone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    GovernmentsObserved,
    census_governments,
    credit_government_treasury,
    debit_government_treasury,
    set_leader,
)

if TYPE_CHECKING:
    from civitas.domain import AgentId, GovernmentCensus, GovernmentId, World
    from civitas.engine.event_bus import EventBus


class GovernmentConfig(BaseModel):
    """Parameters controlling government observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class GovernmentSystem:
    """Observe polities and apply deterministic government mutations."""

    def __init__(self, config: GovernmentConfig | None = None) -> None:
        self._config = config if config is not None else GovernmentConfig()

    @property
    def config(self) -> GovernmentConfig:
        """Return the immutable government configuration."""
        return self._config

    def census(self, world: World) -> GovernmentCensus:
        """Return a government census for ``world``."""
        return census_governments(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe governments and optionally emit ``GovernmentsObserved``.

        The world is never modified.
        """
        snap = census_governments(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                GovernmentsObserved(
                    tick=snap.tick,
                    government_count=snap.government_count,
                    covered_location_count=snap.covered_location_count,
                    uncovered_location_count=snap.uncovered_location_count,
                    total_treasury=snap.total_treasury,
                    led_count=snap.led_count,
                    vacant_leader_count=snap.vacant_leader_count,
                    living_subject_count=snap.living_subject_count,
                    mean_subjects=snap.mean_subjects,
                    max_subjects=snap.max_subjects,
                    max_subjects_government_id=snap.max_subjects_government_id,
                )
            )
        return world

    def appoint_leader(
        self,
        world: World,
        government_id: GovernmentId | int,
        leader_id: AgentId | int | None,
    ) -> World:
        """Appoint or clear a leader when legal; otherwise leave world unchanged."""
        updated = set_leader(world, government_id, leader_id)
        return world if updated is None else updated

    def credit_treasury(
        self,
        world: World,
        government_id: GovernmentId | int,
        amount: int,
    ) -> World:
        """Credit government treasury when legal; otherwise leave world unchanged."""
        updated = credit_government_treasury(world, government_id, amount)
        return world if updated is None else updated

    def debit_treasury(
        self,
        world: World,
        government_id: GovernmentId | int,
        amount: int,
    ) -> World:
        """Debit government treasury when affordable; otherwise leave unchanged."""
        updated = debit_government_treasury(world, government_id, amount)
        return world if updated is None else updated
