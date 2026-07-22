"""Memory retrieval: surface relevant episodic context for action.

Phase 7 Milestone 4. After planning, each living agent retrieves a
bounded set of long-term memories into ``working_memory`` keyed by the
current satisfy-need query. The utility policy may read this context on
the following tick. Systems never call each other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.attributes import MemoryRecord, WorkingMemory
from civitas.domain.ids import AgentId
from civitas.domain.planning import priority_need_from_beliefs
from civitas.domain.reflection import dominant_need_name
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

DEFAULT_RETRIEVAL_LIMIT: int = 3
_VITAL_NEEDS: frozenset[str] = frozenset({"food", "water", "energy"})


class RetrievalCensus(BaseModel):
    """Aggregate retrieval snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_count: NonNegativeInt
    agents_with_context: NonNegativeInt
    total_retrieved: NonNegativeInt
    mean_retrieved_bps: NonNegativeInt


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    """One agent's retrieval result during an apply pass."""

    agent_id: AgentId
    query: str
    retrieved_count: int
    summary: str


def retrieval_query_for_agent(agent: Agent) -> str:
    """Return the need name used as the retrieval query for ``agent``."""
    for goal in agent.goals.goals:
        if goal.target in _VITAL_NEEDS:
            return goal.target
        if goal.kind.startswith("satisfy_"):
            need = goal.kind.removeprefix("satisfy_")
            if need in _VITAL_NEEDS:
                return need
    believed = priority_need_from_beliefs(agent)
    if believed is not None:
        return believed
    return dominant_need_name(agent)


def relevance_score(record: MemoryRecord, query: str) -> int:
    """Score ``record`` relevance to ``query`` (higher is better)."""
    score = record.tick.value
    if not query:
        return score
    content = record.content.lower()
    needle = query.lower()
    if needle in content:
        score += 100
    if f"{needle}=" in content:
        score += 50
    if record.kind == "reflection":
        score += 10
    return score


def retrieve_memories(
    agent: Agent,
    *,
    limit: int = DEFAULT_RETRIEVAL_LIMIT,
) -> tuple[MemoryRecord, ...]:
    """Return up to ``limit`` memories ranked by relevance then recency."""
    if limit <= 0 or not agent.memory.records:
        return ()
    query = retrieval_query_for_agent(agent)
    ranked = sorted(
        agent.memory.records,
        key=lambda record: (
            -relevance_score(record, query),
            -record.tick.value,
            record.kind,
            record.content,
        ),
    )
    return tuple(ranked[:limit])


def summarize_retrieved(records: tuple[MemoryRecord, ...]) -> str:
    """Build a deterministic short summary of retrieved records."""
    if not records:
        return "none"
    return "|".join(f"{record.kind}@{record.tick.value}" for record in records)


def apply_retrieval(
    world: World,
    *,
    limit: int = DEFAULT_RETRIEVAL_LIMIT,
) -> tuple[World, tuple[RetrievalHit, ...]]:
    """Refresh each living agent's working memory from long-term memory.

    When an active ARCHIVE sits at an agent's location, the effective
    retrieval limit includes the archive bonus from society effects.
    """
    # Local import avoids a module-level cycle with effects → retrieval.
    from civitas.domain.effects import effective_retrieval_limit

    hits: list[RetrievalHit] = []
    for agent in world.alive_agents():
        query = retrieval_query_for_agent(agent)
        agent_limit = effective_retrieval_limit(world, agent, base=limit)
        records = retrieve_memories(agent, limit=agent_limit)
        summary = summarize_retrieved(records)
        updated = agent.model_copy(
            update={"working_memory": WorkingMemory(query=query, records=records)}
        )
        world = world.with_agent(updated)
        hits.append(
            RetrievalHit(
                agent_id=agent.agent_id,
                query=query,
                retrieved_count=len(records),
                summary=summary,
            )
        )
    return world, tuple(hits)


def census_retrieval(world: World) -> RetrievalCensus:
    """Build a deterministic retrieval census for ``world``."""
    living = world.alive_agents()
    agents_with_context = 0
    total_retrieved = 0
    for agent in living:
        count = len(agent.working_memory.records)
        total_retrieved += count
        if count > 0:
            agents_with_context += 1
    living_count = len(living)
    mean_retrieved_bps = (
        0 if living_count == 0 else (total_retrieved * 10_000) // living_count
    )
    return RetrievalCensus(
        tick=world.tick,
        living_count=living_count,
        agents_with_context=agents_with_context,
        total_retrieved=total_retrieved,
        mean_retrieved_bps=mean_retrieved_bps,
    )
