"""Directed relationship helpers and census.

Agents hold directed bonds (affinity + trust) toward other agents.
Domain helpers create, adjust, clear, and socialize without systems
calling each other. Reputation and network analytics are later
milestones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.attributes import Relationship
from civitas.domain.ids import AgentId
from civitas.domain.numeric import clamp_affinity, clamp_unit
from civitas.domain.time import Tick
from civitas.domain.types import AffinityScore, NonNegativeInt, UnitInterval

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

DEFAULT_TRUST: float = 0.5
DEFAULT_TRUST_DELTA: float = 0.05
DEFAULT_AFFINITY_DELTA: float = 0.05
DEFAULT_SOCIALIZE_RESTORE: float = 0.15


class RelationshipCensus(BaseModel):
    """Immutable directed-bond snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    bond_count: NonNegativeInt = Field(
        description="Total directed bonds in the roster."
    )
    agents_with_bonds: NonNegativeInt = Field(
        description="Agents that hold at least one outgoing bond."
    )
    living_bond_count: NonNegativeInt = Field(
        description="Bonds whose source and target are both living."
    )
    mean_affinity: float = Field(
        description="Mean affinity across all bonds, or 0.0 when none."
    )
    min_affinity: AffinityScore | None = Field(
        default=None,
        description="Minimum bond affinity, or None when no bonds exist.",
    )
    max_affinity: AffinityScore | None = Field(
        default=None,
        description="Maximum bond affinity, or None when no bonds exist.",
    )
    mean_trust: float = Field(
        default=0.0,
        description="Mean trust across all bonds, or 0.0 when none.",
    )
    min_trust: UnitInterval | None = Field(
        default=None,
        description="Minimum bond trust, or None when no bonds exist.",
    )
    max_trust: UnitInterval | None = Field(
        default=None,
        description="Maximum bond trust, or None when no bonds exist.",
    )


def get_bond(agent: Agent, other_id: AgentId | int) -> Relationship | None:
    """Return ``agent``'s bond toward ``other_id``, if any."""
    return agent.relationships.toward(other_id)


def set_bond(
    agent: Agent,
    other_id: AgentId | int,
    *,
    affinity: float,
    trust: float = DEFAULT_TRUST,
) -> Agent | None:
    """Set or replace ``agent``'s bond toward ``other_id``.

    Returns the updated agent, or ``None`` when the agent is dead or the
    target is the agent itself.
    """
    target = other_id if isinstance(other_id, AgentId) else AgentId(value=other_id)
    if not agent.is_alive():
        return None
    if agent.agent_id == target:
        return None
    bond = Relationship(
        other_id=target,
        affinity=clamp_affinity(affinity),
        trust=clamp_unit(trust),
    )
    return agent.model_copy(update={"relationships": agent.relationships.upsert(bond)})


def adjust_affinity(
    agent: Agent,
    other_id: AgentId | int,
    delta: float,
) -> Agent | None:
    """Adjust affinity toward ``other_id``, creating a bond when missing.

    Existing trust is preserved; new bonds use ``DEFAULT_TRUST``.
    """
    target = other_id if isinstance(other_id, AgentId) else AgentId(value=other_id)
    existing = get_bond(agent, target)
    if existing is None:
        return set_bond(agent, target, affinity=delta, trust=DEFAULT_TRUST)
    return set_bond(
        agent,
        target,
        affinity=existing.affinity + delta,
        trust=existing.trust,
    )


def adjust_trust(
    agent: Agent,
    other_id: AgentId | int,
    delta: float,
) -> Agent | None:
    """Adjust trust toward ``other_id``, creating a bond when missing.

    Existing affinity is preserved; new bonds start at affinity ``0.0``
    and trust ``DEFAULT_TRUST + delta`` (clamped).
    """
    target = other_id if isinstance(other_id, AgentId) else AgentId(value=other_id)
    existing = get_bond(agent, target)
    if existing is None:
        return set_bond(
            agent,
            target,
            affinity=0.0,
            trust=DEFAULT_TRUST + delta,
        )
    return set_bond(
        agent,
        target,
        affinity=existing.affinity,
        trust=existing.trust + delta,
    )


def clear_bond(agent: Agent, other_id: AgentId | int) -> Agent | None:
    """Remove ``agent``'s bond toward ``other_id`` when present.

    Returns ``None`` when the agent is dead. Missing bonds are a no-op
    success for living agents.
    """
    if not agent.is_alive():
        return None
    return agent.model_copy(
        update={"relationships": agent.relationships.without(other_id)}
    )


def set_relationship(
    world: World,
    from_id: AgentId | int,
    to_id: AgentId | int,
    *,
    affinity: float,
    trust: float = DEFAULT_TRUST,
) -> World | None:
    """Set a directed bond from ``from_id`` to ``to_id`` when legal.

    Both agents must exist and be living and distinct. Returns the updated
    world, or ``None`` if illegal.
    """
    source = world.agent_by_id(from_id)
    target = world.agent_by_id(to_id)
    if source is None or target is None:
        return None
    if not target.is_alive():
        return None
    updated = set_bond(source, target.agent_id, affinity=affinity, trust=trust)
    if updated is None:
        return None
    return world.with_agent(updated)


def adjust_relationship(
    world: World,
    from_id: AgentId | int,
    to_id: AgentId | int,
    delta: float,
) -> World | None:
    """Adjust affinity from ``from_id`` toward ``to_id`` when legal."""
    source = world.agent_by_id(from_id)
    target = world.agent_by_id(to_id)
    if source is None or target is None:
        return None
    if not target.is_alive():
        return None
    updated = adjust_affinity(source, target.agent_id, delta)
    if updated is None:
        return None
    return world.with_agent(updated)


def adjust_relationship_trust(
    world: World,
    from_id: AgentId | int,
    to_id: AgentId | int,
    delta: float,
) -> World | None:
    """Adjust trust from ``from_id`` toward ``to_id`` when legal."""
    source = world.agent_by_id(from_id)
    target = world.agent_by_id(to_id)
    if source is None or target is None:
        return None
    if not target.is_alive():
        return None
    updated = adjust_trust(source, target.agent_id, delta)
    if updated is None:
        return None
    return world.with_agent(updated)


def can_socialize(
    world: World,
    actor_id: AgentId | int,
    partner_id: AgentId | int,
) -> bool:
    """Return True when ``actor_id`` can SOCIALIZE with ``partner_id``."""
    actor = world.agent_by_id(actor_id)
    partner = world.agent_by_id(partner_id)
    if actor is None or partner is None:
        return False
    if actor.agent_id == partner.agent_id:
        return False
    if not actor.is_alive() or not partner.is_alive():
        return False
    return actor.location_id == partner.location_id


def _boost_bond(
    agent: Agent,
    other_id: AgentId,
    *,
    affinity_delta: float,
    trust_delta: float,
) -> Agent | None:
    """Raise affinity and trust toward ``other_id``, creating when missing."""
    existing = get_bond(agent, other_id)
    if existing is None:
        return set_bond(
            agent,
            other_id,
            affinity=affinity_delta,
            trust=DEFAULT_TRUST + trust_delta,
        )
    return set_bond(
        agent,
        other_id,
        affinity=existing.affinity + affinity_delta,
        trust=existing.trust + trust_delta,
    )


def apply_socialize(
    world: World,
    actor_id: AgentId | int,
    partner_id: AgentId | int,
    *,
    trust_delta: float = DEFAULT_TRUST_DELTA,
    affinity_delta: float = DEFAULT_AFFINITY_DELTA,
    restore: float = DEFAULT_SOCIALIZE_RESTORE,
) -> World | None:
    """Apply a co-located SOCIALIZE encounter when legal.

    Restores the actor's social need and raises mutual directed affinity
    and trust. Returns the updated world, or ``None`` if illegal.
    """
    if not can_socialize(world, actor_id, partner_id):
        return None

    actor = world.agent_by_id(actor_id)
    partner = world.agent_by_id(partner_id)
    if actor is None or partner is None:
        return None

    previous_social = actor.needs.social
    new_social = clamp_unit(previous_social + restore)
    if new_social != previous_social:
        actor = actor.model_copy(
            update={"needs": actor.needs.model_copy(update={"social": new_social})}
        )

    boosted_actor = _boost_bond(
        actor,
        partner.agent_id,
        affinity_delta=affinity_delta,
        trust_delta=trust_delta,
    )
    boosted_partner = _boost_bond(
        partner,
        actor.agent_id,
        affinity_delta=affinity_delta,
        trust_delta=trust_delta,
    )
    if boosted_actor is None or boosted_partner is None:
        return None

    if boosted_actor.agent_id.value <= boosted_partner.agent_id.value:
        world = world.with_agent(boosted_actor)
        return world.with_agent(boosted_partner)
    world = world.with_agent(boosted_partner)
    return world.with_agent(boosted_actor)


def clear_relationship(
    world: World,
    from_id: AgentId | int,
    to_id: AgentId | int,
) -> World | None:
    """Clear the directed bond from ``from_id`` to ``to_id`` when legal."""
    source = world.agent_by_id(from_id)
    if source is None:
        return None
    updated = clear_bond(source, to_id)
    if updated is None:
        return None
    return world.with_agent(updated)


def bond_count(world: World) -> int:
    """Return the number of directed bonds across the full roster."""
    return sum(len(agent.relationships.bonds) for agent in world.agents)


def census_relationships(world: World) -> RelationshipCensus:
    """Build a deterministic relationship census for ``world``."""
    affinities: list[float] = []
    trusts: list[float] = []
    agents_with_bonds = 0
    living_bond_count = 0
    living_ids = {agent.agent_id for agent in world.alive_agents()}

    for agent in world.agents:
        bonds = agent.relationships.bonds
        if bonds:
            agents_with_bonds += 1
        for bond in bonds:
            affinities.append(bond.affinity)
            trusts.append(bond.trust)
            if agent.agent_id in living_ids and bond.other_id in living_ids:
                living_bond_count += 1

    bond_total = len(affinities)
    if bond_total == 0:
        mean_affinity = 0.0
        min_affinity: float | None = None
        max_affinity: float | None = None
        mean_trust = 0.0
        min_trust: float | None = None
        max_trust: float | None = None
    else:
        mean_affinity = round(sum(affinities) / bond_total, 6)
        min_affinity = min(affinities)
        max_affinity = max(affinities)
        mean_trust = round(sum(trusts) / bond_total, 6)
        min_trust = min(trusts)
        max_trust = max(trusts)

    return RelationshipCensus(
        tick=world.tick,
        bond_count=bond_total,
        agents_with_bonds=agents_with_bonds,
        living_bond_count=living_bond_count,
        mean_affinity=mean_affinity,
        min_affinity=min_affinity,
        max_affinity=max_affinity,
        mean_trust=mean_trust,
        min_trust=min_trust,
        max_trust=max_trust,
    )
