"""Relationship system: directed bond mutations and observation.

Owns relationship mutations that emit ``RelationshipUpdated`` and
tick-level censuses that emit ``RelationshipsObserved``. Bond legality
and census math live in domain helpers so other layers can reason about
relationships without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    RelationshipsObserved,
    RelationshipUpdated,
    adjust_relationship,
    adjust_relationship_trust,
    census_relationships,
    clear_relationship,
    get_bond,
    set_relationship,
)
from civitas.domain.relationships import DEFAULT_TRUST

if TYPE_CHECKING:
    from civitas.domain import AgentId, RelationshipCensus, World
    from civitas.engine.event_bus import EventBus


class RelationshipConfig(BaseModel):
    """Parameters controlling relationship observation and mutations."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class RelationshipSystem:
    """Apply directed bond updates and emit deterministic relationship censuses."""

    def __init__(self, config: RelationshipConfig | None = None) -> None:
        self._config = config if config is not None else RelationshipConfig()

    @property
    def config(self) -> RelationshipConfig:
        """Return the immutable relationship configuration."""
        return self._config

    def census(self, world: World) -> RelationshipCensus:
        """Return a relationship census for ``world``."""
        return census_relationships(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe relationships and optionally emit ``RelationshipsObserved``.

        The world is never modified.
        """
        snap = census_relationships(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                RelationshipsObserved(
                    tick=snap.tick,
                    bond_count=snap.bond_count,
                    agents_with_bonds=snap.agents_with_bonds,
                    living_bond_count=snap.living_bond_count,
                    mean_affinity=snap.mean_affinity,
                    min_affinity=snap.min_affinity,
                    max_affinity=snap.max_affinity,
                    mean_trust=snap.mean_trust,
                    min_trust=snap.min_trust,
                    max_trust=snap.max_trust,
                )
            )
        return world

    def set_bond(
        self,
        world: World,
        from_id: AgentId | int,
        to_id: AgentId | int,
        *,
        affinity: float,
        trust: float = DEFAULT_TRUST,
        bus: EventBus | None = None,
    ) -> World:
        """Set a directed bond when legal; emit ``RelationshipUpdated``.

        Illegal updates leave the world unchanged.
        """
        source = world.agent_by_id(from_id)
        created = source is None or get_bond(source, to_id) is None
        updated = set_relationship(
            world,
            from_id,
            to_id,
            affinity=affinity,
            trust=trust,
        )
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            source_after = updated.agent_by_id(from_id)
            bond = get_bond(source_after, to_id) if source_after is not None else None
            if source_after is not None and bond is not None:
                bus.publish(
                    RelationshipUpdated(
                        tick=updated.tick,
                        from_agent_id=source_after.agent_id,
                        to_agent_id=bond.other_id,
                        affinity=bond.affinity,
                        trust=bond.trust,
                        created=created,
                    )
                )
        return updated

    def adjust_affinity(
        self,
        world: World,
        from_id: AgentId | int,
        to_id: AgentId | int,
        delta: float,
        bus: EventBus | None = None,
    ) -> World:
        """Adjust affinity when legal; emit ``RelationshipUpdated``."""
        source = world.agent_by_id(from_id)
        created = source is None or get_bond(source, to_id) is None
        updated = adjust_relationship(world, from_id, to_id, delta)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            source_after = updated.agent_by_id(from_id)
            bond = get_bond(source_after, to_id) if source_after is not None else None
            if source_after is not None and bond is not None:
                bus.publish(
                    RelationshipUpdated(
                        tick=updated.tick,
                        from_agent_id=source_after.agent_id,
                        to_agent_id=bond.other_id,
                        affinity=bond.affinity,
                        trust=bond.trust,
                        created=created,
                    )
                )
        return updated

    def adjust_trust(
        self,
        world: World,
        from_id: AgentId | int,
        to_id: AgentId | int,
        delta: float,
        bus: EventBus | None = None,
    ) -> World:
        """Adjust trust when legal; emit ``RelationshipUpdated``."""
        source = world.agent_by_id(from_id)
        created = source is None or get_bond(source, to_id) is None
        updated = adjust_relationship_trust(world, from_id, to_id, delta)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            source_after = updated.agent_by_id(from_id)
            bond = get_bond(source_after, to_id) if source_after is not None else None
            if source_after is not None and bond is not None:
                bus.publish(
                    RelationshipUpdated(
                        tick=updated.tick,
                        from_agent_id=source_after.agent_id,
                        to_agent_id=bond.other_id,
                        affinity=bond.affinity,
                        trust=bond.trust,
                        created=created,
                    )
                )
        return updated

    def clear_bond(
        self,
        world: World,
        from_id: AgentId | int,
        to_id: AgentId | int,
    ) -> World:
        """Clear a directed bond when legal.

        Illegal clears leave the world unchanged.
        """
        updated = clear_relationship(world, from_id, to_id)
        return world if updated is None else updated
