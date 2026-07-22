"""Directed relationship helpers and census.

Agents hold directed bonds (affinity + trust) toward other agents.
Domain helpers create, adjust, and clear bonds without systems calling
each other. Trust dynamics and social actions are later milestones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.attributes import Relationship
from civitas.domain.ids import AgentId
from civitas.domain.numeric import clamp_affinity, clamp_unit
from civitas.domain.time import Tick
from civitas.domain.types import AffinityScore, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

DEFAULT_TRUST: float = 0.5


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
    agents_with_bonds = 0
    living_bond_count = 0
    living_ids = {agent.agent_id for agent in world.alive_agents()}

    for agent in world.agents:
        bonds = agent.relationships.bonds
        if bonds:
            agents_with_bonds += 1
        for bond in bonds:
            affinities.append(bond.affinity)
            if agent.agent_id in living_ids and bond.other_id in living_ids:
                living_bond_count += 1

    bond_total = len(affinities)
    if bond_total == 0:
        mean_affinity = 0.0
        min_affinity: float | None = None
        max_affinity: float | None = None
    else:
        mean_affinity = round(sum(affinities) / bond_total, 6)
        min_affinity = min(affinities)
        max_affinity = max(affinities)

    return RelationshipCensus(
        tick=world.tick,
        bond_count=bond_total,
        agents_with_bonds=agents_with_bonds,
        living_bond_count=living_bond_count,
        mean_affinity=mean_affinity,
        min_affinity=min_affinity,
        max_affinity=max_affinity,
    )
