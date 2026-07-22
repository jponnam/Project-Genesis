"""Vote system: election observation and thin conduct wrapper.

Owns observe-time election censuses that emit ``ElectionsObserved``.
Conducting an election lives in domain helpers; when a bus is provided,
``conduct`` also emits ``ElectionResolved``. Elections are not auto-run
each tick — callers invoke ``conduct`` when a vote should fire.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    ElectionResolved,
    ElectionsObserved,
    census_elections,
    conduct_election,
)

if TYPE_CHECKING:
    from civitas.domain import ElectionCensus, GovernmentId, World
    from civitas.engine.event_bus import EventBus


class VoteConfig(BaseModel):
    """Parameters controlling election observation and conduct events."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class VoteSystem:
    """Observe archived elections and apply deterministic conduct mutations."""

    def __init__(self, config: VoteConfig | None = None) -> None:
        self._config = config if config is not None else VoteConfig()

    @property
    def config(self) -> VoteConfig:
        """Return the immutable vote configuration."""
        return self._config

    def census(self, world: World) -> ElectionCensus:
        """Return an election census for ``world``."""
        return census_elections(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe elections and optionally emit ``ElectionsObserved``.

        The world is never modified.
        """
        snap = census_elections(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                ElectionsObserved(
                    tick=snap.tick,
                    election_count=snap.election_count,
                    closed_count=snap.closed_count,
                    open_count=snap.open_count,
                    governments_with_elections=snap.governments_with_elections,
                )
            )
        return world

    def conduct(
        self,
        world: World,
        government_id: GovernmentId | int,
        bus: EventBus | None = None,
    ) -> World:
        """Conduct one election when legal; otherwise leave the world unchanged.

        On success, optionally emit ``ElectionResolved`` for the new archive
        entry.
        """
        before_count = len(world.elections)
        updated = conduct_election(world, government_id)
        if updated is None:
            return world

        if (
            bus is not None
            and self._config.emit_events
            and len(updated.elections) > before_count
        ):
            election = updated.elections[-1]
            bus.publish(
                ElectionResolved(
                    tick=updated.tick,
                    election_id=election.election_id,
                    government_id=election.government_id,
                    winner_id=election.winner_id,
                    franchise_count=len(election.franchise),
                    ballot_count=len(election.ballots),
                )
            )
        return updated
