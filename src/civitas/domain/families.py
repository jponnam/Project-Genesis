"""Kinship helpers and family-lineage census over birth parentage.

Families are observe-time analytics over ``AgentIdentity.parent_id``.
They do not mutate agents or relationships. Social-network analytics over
affinity bonds live in the networks module.
"""

from __future__ import annotations

from statistics import fmean
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import AgentId
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class FamilyLineage(BaseModel):
    """One founder-rooted lineage and its living members."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    root_id: AgentId
    living_member_count: NonNegativeInt
    living_member_ids: tuple[AgentId, ...] = ()
    generation_depth: NonNegativeInt = Field(
        description="Max generation index among living members (founder = 0)."
    )


class FamilyCensus(BaseModel):
    """Aggregate kinship snapshot for living agents."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_agent_count: NonNegativeInt
    founder_count: NonNegativeInt = Field(
        description="Living agents with no recorded parent."
    )
    parented_count: NonNegativeInt = Field(
        description="Living agents with a recorded parent_id."
    )
    orphan_count: NonNegativeInt = Field(
        description="Living parented agents whose parent is missing or dead."
    )
    living_with_living_parent: NonNegativeInt
    lineage_count: NonNegativeInt
    mean_lineage_size: float = Field(
        description="Mean living members per lineage, or 0.0 when none."
    )
    max_lineage_size: NonNegativeInt
    max_generation_depth: NonNegativeInt
    parents_with_living_children: NonNegativeInt
    mean_living_children: float = Field(
        description="Mean living children among living parents who have any."
    )
    max_living_children: NonNegativeInt
    lineages: tuple[FamilyLineage, ...] = ()


def _as_agent_id(agent_id: AgentId | int) -> AgentId:
    return agent_id if isinstance(agent_id, AgentId) else AgentId(value=agent_id)


def parent_of(world: World, agent_id: AgentId | int) -> Agent | None:
    """Return the recorded parent agent when present in the roster."""
    agent = world.agent_by_id(agent_id)
    if agent is None or agent.parent_id is None:
        return None
    return world.agent_by_id(agent.parent_id)


def children_of(
    world: World,
    parent_id: AgentId | int,
    *,
    living_only: bool = True,
) -> tuple[Agent, ...]:
    """Return children of ``parent_id``, optionally restricted to living."""
    target = _as_agent_id(parent_id)
    roster = world.alive_agents() if living_only else world.agents
    found = [
        agent
        for agent in roster
        if agent.parent_id is not None and agent.parent_id == target
    ]
    return tuple(sorted(found, key=lambda agent: agent.agent_id.value))


def siblings_of(
    world: World,
    agent_id: AgentId | int,
    *,
    living_only: bool = True,
) -> tuple[Agent, ...]:
    """Return other children of the same recorded parent."""
    agent = world.agent_by_id(agent_id)
    if agent is None or agent.parent_id is None:
        return ()
    return tuple(
        sibling
        for sibling in children_of(
            world,
            agent.parent_id,
            living_only=living_only,
        )
        if sibling.agent_id != agent.agent_id
    )


def root_of(world: World, agent_id: AgentId | int) -> AgentId | None:
    """Walk ``parent_id`` links to the founder; ``None`` if agent missing."""
    current = world.agent_by_id(agent_id)
    if current is None:
        return None
    seen: set[int] = set()
    while True:
        if current.agent_id.value in seen:
            return current.agent_id
        seen.add(current.agent_id.value)
        if current.parent_id is None:
            return current.agent_id
        parent = world.agent_by_id(current.parent_id)
        if parent is None:
            return current.agent_id
        current = parent


def generation_of(world: World, agent_id: AgentId | int) -> int | None:
    """Return generation index from founder (0), or ``None`` if missing."""
    agent = world.agent_by_id(agent_id)
    if agent is None:
        return None
    depth = 0
    seen: set[int] = set()
    current = agent
    while current.parent_id is not None:
        if current.agent_id.value in seen:
            break
        seen.add(current.agent_id.value)
        parent = world.agent_by_id(current.parent_id)
        if parent is None:
            break
        depth += 1
        current = parent
    return depth


def lineages(world: World) -> tuple[FamilyLineage, ...]:
    """Group living agents by founder root, sorted by root id."""
    buckets: dict[int, list[Agent]] = {}
    depths: dict[int, int] = {}
    for agent in world.alive_agents():
        root = root_of(world, agent.agent_id)
        if root is None:
            continue
        buckets.setdefault(root.value, []).append(agent)
        gen = generation_of(world, agent.agent_id)
        if gen is not None:
            depths[root.value] = max(depths.get(root.value, 0), gen)
    lines: list[FamilyLineage] = []
    for root_value in sorted(buckets):
        members = sorted(buckets[root_value], key=lambda item: item.agent_id.value)
        lines.append(
            FamilyLineage(
                root_id=AgentId(value=root_value),
                living_member_count=len(members),
                living_member_ids=tuple(member.agent_id for member in members),
                generation_depth=depths.get(root_value, 0),
            )
        )
    return tuple(lines)


def census_families(world: World) -> FamilyCensus:
    """Build a deterministic kinship census for ``world``."""
    alive = world.alive_agents()
    living_agent_count = len(alive)
    founder_count = sum(1 for agent in alive if agent.parent_id is None)
    parented = [agent for agent in alive if agent.parent_id is not None]
    parented_count = len(parented)
    living_with_living_parent = 0
    orphan_count = 0
    for agent in parented:
        parent = world.agent_by_id(agent.parent_id) if agent.parent_id else None
        if parent is not None and parent.is_alive():
            living_with_living_parent += 1
        else:
            orphan_count += 1

    lines = lineages(world)
    sizes = [line.living_member_count for line in lines]
    if sizes:
        mean_lineage_size = round(fmean(sizes), 6)
        max_lineage_size = max(sizes)
        max_generation_depth = max(line.generation_depth for line in lines)
    else:
        mean_lineage_size = 0.0
        max_lineage_size = 0
        max_generation_depth = 0

    child_counts = [
        len(children_of(world, agent.agent_id, living_only=True)) for agent in alive
    ]
    positive = [count for count in child_counts if count > 0]
    if positive:
        mean_living_children = round(fmean(positive), 6)
        max_living_children = max(positive)
        parents_with_living_children = len(positive)
    else:
        mean_living_children = 0.0
        max_living_children = 0
        parents_with_living_children = 0

    return FamilyCensus(
        tick=world.tick,
        living_agent_count=living_agent_count,
        founder_count=founder_count,
        parented_count=parented_count,
        orphan_count=orphan_count,
        living_with_living_parent=living_with_living_parent,
        lineage_count=len(lines),
        mean_lineage_size=mean_lineage_size,
        max_lineage_size=max_lineage_size,
        max_generation_depth=max_generation_depth,
        parents_with_living_children=parents_with_living_children,
        mean_living_children=mean_living_children,
        max_living_children=max_living_children,
        lineages=lines,
    )


__all__ = [
    "FamilyCensus",
    "FamilyLineage",
    "census_families",
    "children_of",
    "generation_of",
    "lineages",
    "parent_of",
    "root_of",
    "siblings_of",
]
