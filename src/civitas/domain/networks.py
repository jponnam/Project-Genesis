"""Social-network analytics over living directed relationship bonds.

Observe-time graph metrics over ``RelationshipMap`` edges among living
agents. Does not mutate agents or relationships. Kinship lineage is covered
by families; this module measures the social bond graph.
"""

from __future__ import annotations

from collections import deque
from statistics import fmean
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import AgentId
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt, UnitInterval
from civitas.domain.wealth import share_bps

if TYPE_CHECKING:
    from civitas.domain.attributes import Relationship
    from civitas.domain.world import World


class AgentDegree(BaseModel):
    """Degree summary for one living agent in the social graph."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    agent_id: AgentId
    undirected_degree: NonNegativeInt
    out_degree: NonNegativeInt
    in_degree: NonNegativeInt


class NetworkComponent(BaseModel):
    """One weakly connected component of living agents."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    component_id: NonNegativeInt
    size: NonNegativeInt
    member_ids: tuple[AgentId, ...] = ()


class StrongestTie(BaseModel):
    """Highest-strength undirected living pair, with deterministic ids."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    from_id: AgentId = Field(description="Smaller agent id of the pair.")
    to_id: AgentId = Field(description="Larger agent id of the pair.")
    strength: UnitInterval
    strength_bps: NonNegativeInt = Field(ge=0, le=10_000)
    reciprocal: bool


class NetworkCensus(BaseModel):
    """Aggregate social-network snapshot for living agents."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_agent_count: NonNegativeInt
    directed_edge_count: NonNegativeInt
    undirected_edge_count: NonNegativeInt
    reciprocal_pair_count: NonNegativeInt
    reciprocity_rate: float
    reciprocity_bps: NonNegativeInt
    mean_degree: float
    max_degree: NonNegativeInt
    max_degree_agent_id: AgentId | None = None
    isolated_count: NonNegativeInt
    component_count: NonNegativeInt
    largest_component_size: NonNegativeInt
    mean_component_size: float
    density: float
    density_bps: NonNegativeInt
    strongest_tie: StrongestTie | None = None
    degrees: tuple[AgentDegree, ...] = ()
    components: tuple[NetworkComponent, ...] = ()


def directed_strength(bond: Relationship) -> float:
    """Map a directed bond to a unit-interval strength score."""
    affinity_unit = (bond.affinity + 1.0) / 2.0
    return round((bond.trust + affinity_unit) / 2.0, 6)


def directed_edges(
    world: World,
) -> tuple[tuple[AgentId, AgentId, Relationship], ...]:
    """Return living→living directed bonds sorted by ``(from_id, to_id)``."""
    alive_ids = {agent.agent_id.value for agent in world.alive_agents()}
    found: list[tuple[AgentId, AgentId, Relationship]] = []
    for source in world.alive_agents():
        for bond in source.relationships.bonds:
            if bond.other_id.value not in alive_ids:
                continue
            if bond.other_id == source.agent_id:
                continue
            found.append((source.agent_id, bond.other_id, bond))
    found.sort(key=lambda item: (item[0].value, item[1].value))
    return tuple(found)


def _undirected_adjacency(world: World) -> dict[int, set[int]]:
    alive = [agent.agent_id.value for agent in world.alive_agents()]
    adj: dict[int, set[int]] = {agent_id: set() for agent_id in alive}
    for source_id, target_id, _bond in directed_edges(world):
        adj[source_id.value].add(target_id.value)
        adj[target_id.value].add(source_id.value)
    return adj


def undirected_neighbors(world: World, agent_id: AgentId | int) -> tuple[AgentId, ...]:
    """Return sorted living neighbor ids connected in either direction."""
    target = agent_id if isinstance(agent_id, AgentId) else AgentId(value=agent_id)
    adj = _undirected_adjacency(world)
    neighbors = adj.get(target.value, set())
    return tuple(AgentId(value=value) for value in sorted(neighbors))


def degrees(world: World) -> tuple[AgentDegree, ...]:
    """Degree rows for every living agent, sorted by agent id."""
    edges = directed_edges(world)
    out_counts: dict[int, int] = {}
    in_counts: dict[int, int] = {}
    for source_id, target_id, _bond in edges:
        out_counts[source_id.value] = out_counts.get(source_id.value, 0) + 1
        in_counts[target_id.value] = in_counts.get(target_id.value, 0) + 1
    adj = _undirected_adjacency(world)
    rows: list[AgentDegree] = []
    for agent in world.alive_agents():
        agent_value = agent.agent_id.value
        rows.append(
            AgentDegree(
                agent_id=agent.agent_id,
                undirected_degree=len(adj.get(agent_value, ())),
                out_degree=out_counts.get(agent_value, 0),
                in_degree=in_counts.get(agent_value, 0),
            )
        )
    return tuple(sorted(rows, key=lambda row: row.agent_id.value))


def weak_components(world: World) -> tuple[NetworkComponent, ...]:
    """Weakly connected components via BFS in ascending seed-id order."""
    adj = _undirected_adjacency(world)
    remaining = sorted(adj)
    seen: set[int] = set()
    components: list[NetworkComponent] = []
    component_id = 0
    for seed in remaining:
        if seed in seen:
            continue
        queue: deque[int] = deque([seed])
        seen.add(seed)
        members: list[int] = []
        while queue:
            current = queue.popleft()
            members.append(current)
            for neighbor in sorted(adj[current]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        members.sort()
        components.append(
            NetworkComponent(
                component_id=component_id,
                size=len(members),
                member_ids=tuple(AgentId(value=value) for value in members),
            )
        )
        component_id += 1
    return tuple(components)


def _undirected_pairs(
    world: World,
) -> dict[tuple[int, int], list[Relationship]]:
    pairs: dict[tuple[int, int], list[Relationship]] = {}
    for source_id, target_id, bond in directed_edges(world):
        low, high = sorted((source_id.value, target_id.value))
        pairs.setdefault((low, high), []).append(bond)
    return pairs


def strongest_tie(world: World) -> StrongestTie | None:
    """Highest mean directed strength among undirected living pairs."""
    best: StrongestTie | None = None
    for (low, high), bonds in sorted(_undirected_pairs(world).items()):
        strength = round(fmean(directed_strength(bond) for bond in bonds), 6)
        strength_bps = max(0, min(10_000, round(strength * 10_000)))
        candidate = StrongestTie(
            from_id=AgentId(value=low),
            to_id=AgentId(value=high),
            strength=strength,
            strength_bps=strength_bps,
            reciprocal=len(bonds) >= 2,
        )
        if best is None:
            best = candidate
            continue
        best_key = (best.strength_bps, -best.from_id.value, -best.to_id.value)
        cand_key = (
            candidate.strength_bps,
            -candidate.from_id.value,
            -candidate.to_id.value,
        )
        if cand_key > best_key:
            best = candidate
    return best


def census_networks(world: World) -> NetworkCensus:
    """Build a deterministic social-network census for ``world``."""
    alive = world.alive_agents()
    n = len(alive)
    edges = directed_edges(world)
    pairs = _undirected_pairs(world)
    directed_edge_count = len(edges)
    undirected_edge_count = len(pairs)
    reciprocal_pair_count = sum(1 for bonds in pairs.values() if len(bonds) >= 2)
    reciprocity_rate = (
        round(reciprocal_pair_count / undirected_edge_count, 6)
        if undirected_edge_count
        else 0.0
    )
    reciprocity_bps = share_bps(reciprocal_pair_count, undirected_edge_count)

    degree_rows = degrees(world)
    undirected_degrees = [row.undirected_degree for row in degree_rows]
    if n == 0:
        mean_degree = 0.0
        max_degree = 0
        max_degree_agent_id: AgentId | None = None
        isolated_count = 0
    else:
        mean_degree = round(fmean(undirected_degrees), 6)
        max_degree = max(undirected_degrees)
        max_row = max(
            degree_rows,
            key=lambda row: (row.undirected_degree, -row.agent_id.value),
        )
        max_degree_agent_id = max_row.agent_id
        isolated_count = sum(1 for value in undirected_degrees if value == 0)

    components = weak_components(world)
    sizes = [component.size for component in components]
    if sizes:
        largest_component_size = max(sizes)
        mean_component_size = round(fmean(sizes), 6)
    else:
        largest_component_size = 0
        mean_component_size = 0.0

    density = round((2 * undirected_edge_count) / (n * (n - 1)), 6) if n >= 2 else 0.0
    density_bps = max(0, min(10_000, round(density * 10_000)))

    return NetworkCensus(
        tick=world.tick,
        living_agent_count=n,
        directed_edge_count=directed_edge_count,
        undirected_edge_count=undirected_edge_count,
        reciprocal_pair_count=reciprocal_pair_count,
        reciprocity_rate=reciprocity_rate,
        reciprocity_bps=reciprocity_bps,
        mean_degree=mean_degree,
        max_degree=max_degree,
        max_degree_agent_id=max_degree_agent_id,
        isolated_count=isolated_count,
        component_count=len(components),
        largest_component_size=largest_component_size,
        mean_component_size=mean_component_size,
        density=density,
        density_bps=density_bps,
        strongest_tie=strongest_tie(world),
        degrees=degree_rows,
        components=components,
    )


__all__ = [
    "AgentDegree",
    "NetworkCensus",
    "NetworkComponent",
    "StrongestTie",
    "census_networks",
    "degrees",
    "directed_edges",
    "directed_strength",
    "strongest_tie",
    "undirected_neighbors",
    "weak_components",
]
