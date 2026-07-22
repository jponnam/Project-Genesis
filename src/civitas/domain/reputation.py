"""Public reputation standings derived from directed social bonds.

Standing is an observe-time analytic over *inbound* bonds from living peers.
It does not mutate agents or relationships. Reciprocity (subject also holds a
bond toward the peer) is a small weighting bonus only.
"""

from __future__ import annotations

from statistics import fmean
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import AgentId
from civitas.domain.relationships import get_bond
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt, UnitInterval
from civitas.domain.wealth import gini_bps, median_int, share_bps

if TYPE_CHECKING:
    from collections.abc import Sequence

    from civitas.domain.agent import Agent
    from civitas.domain.attributes import Relationship
    from civitas.domain.world import World

REPUTATION_TRUST_WEIGHT = 0.75
REPUTATION_RECIPROCITY_WEIGHT = 0.25


class AgentStanding(BaseModel):
    """One living agent's public standing derived from inbound peer bonds."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    agent_id: AgentId
    standing: UnitInterval = Field(
        description="Mean weighted inbound score in [0, 1], or 0 with no inbound."
    )
    standing_bps: NonNegativeInt = Field(
        ge=0,
        le=10_000,
        description="Standing expressed in basis points.",
    )
    inbound_bond_count: NonNegativeInt = Field(
        description="Count of living peers with a directed bond toward this agent."
    )


class ReputationCensus(BaseModel):
    """Aggregate public reputation snapshot for living agents."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_agent_count: NonNegativeInt
    mean_standing: UnitInterval = Field(
        description="Mean standing among living agents, or 0.0 when none."
    )
    median_standing_bps: NonNegativeInt = Field(
        ge=0,
        le=10_000,
        description="Median standing in bps, or 0 when none are alive.",
    )
    gini_standing_bps: NonNegativeInt = Field(
        ge=0,
        le=10_000,
        description="Gini of standing_bps among living agents.",
    )
    top_standing_share_bps: NonNegativeInt = Field(
        ge=0,
        le=10_000,
        description="Highest standing as a share of the standing-bps sum.",
    )
    agents_with_inbound_bonds: NonNegativeInt
    standings: tuple[AgentStanding, ...] = ()


def inbound_bonds(
    world: World,
    subject_id: AgentId | int,
) -> tuple[tuple[Agent, Relationship], ...]:
    """Return ``(peer, bond)`` pairs for living peers directed at ``subject_id``."""
    if isinstance(subject_id, AgentId):
        target = subject_id
    else:
        target = AgentId(value=subject_id)
    found: list[tuple[Agent, Relationship]] = []
    for peer in world.alive_agents():
        if peer.agent_id == target:
            continue
        bond = get_bond(peer, target)
        if bond is not None:
            found.append((peer, bond))
    return tuple(found)


def _has_reciprocal_bond(subject: Agent, peer_id: AgentId) -> bool:
    return get_bond(subject, peer_id) is not None


def _bond_contribution(bond: Relationship, *, reciprocal: bool) -> float:
    affinity_unit = (bond.affinity + 1.0) / 2.0
    bond_score = (bond.trust + affinity_unit) / 2.0
    reciprocity = 1.0 if reciprocal else 0.0
    return (
        REPUTATION_TRUST_WEIGHT * bond_score
        + REPUTATION_RECIPROCITY_WEIGHT * reciprocity
    )


def standing_of(world: World, agent_id: AgentId | int) -> AgentStanding | None:
    """Compute standing for one living agent, or ``None`` if missing/dead."""
    agent = world.agent_by_id(agent_id)
    if agent is None or not agent.is_alive():
        return None
    inbound = inbound_bonds(world, agent.agent_id)
    if not inbound:
        standing = 0.0
    else:
        contributions = [
            _bond_contribution(
                bond,
                reciprocal=_has_reciprocal_bond(agent, peer.agent_id),
            )
            for peer, bond in inbound
        ]
        standing = round(fmean(contributions), 6)
    standing_bps = max(0, min(10_000, round(standing * 10_000)))
    return AgentStanding(
        agent_id=agent.agent_id,
        standing=standing,
        standing_bps=standing_bps,
        inbound_bond_count=len(inbound),
    )


def standings(world: World) -> tuple[AgentStanding, ...]:
    """Standing rows for every living agent, sorted by agent id."""
    rows: list[AgentStanding] = []
    for agent in world.alive_agents():
        row = standing_of(world, agent.agent_id)
        if row is not None:
            rows.append(row)
    return tuple(sorted(rows, key=lambda item: item.agent_id.value))


def top_standing(standings_rows: Sequence[AgentStanding]) -> AgentStanding | None:
    """Highest standing row; ties prefer the smaller agent id."""
    if not standings_rows:
        return None
    return max(
        standings_rows,
        key=lambda row: (row.standing_bps, -row.agent_id.value),
    )


def census_reputation(world: World) -> ReputationCensus:
    """Aggregate standing inequality metrics over living agents."""
    rows = standings(world)
    bps_values = tuple(sorted(row.standing_bps for row in rows))
    if not bps_values:
        return ReputationCensus(
            tick=world.tick,
            living_agent_count=0,
            mean_standing=0.0,
            median_standing_bps=0,
            gini_standing_bps=0,
            top_standing_share_bps=0,
            agents_with_inbound_bonds=0,
            standings=(),
        )
    total_bps = sum(bps_values)
    mean = round(fmean(bps_values) / 10_000.0, 6)
    top = top_standing(rows)
    top_share = share_bps(top.standing_bps, total_bps) if top is not None else 0
    return ReputationCensus(
        tick=world.tick,
        living_agent_count=len(rows),
        mean_standing=mean,
        median_standing_bps=median_int(bps_values),
        gini_standing_bps=gini_bps(bps_values),
        top_standing_share_bps=top_share,
        agents_with_inbound_bonds=sum(1 for row in rows if row.inbound_bond_count > 0),
        standings=rows,
    )


__all__ = [
    "REPUTATION_RECIPROCITY_WEIGHT",
    "REPUTATION_TRUST_WEIGHT",
    "AgentStanding",
    "ReputationCensus",
    "census_reputation",
    "inbound_bonds",
    "standing_of",
    "standings",
    "top_standing",
]
