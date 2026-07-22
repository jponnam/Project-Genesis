"""Episodic memory encoding for agent cognition.

Phase 7 Milestone 1. Each apply tick appends a deterministic episode
record to living agents. LLM reflection, planning, and retrieval remain
later milestones.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.attributes import MemoryRecord
from civitas.domain.ids import AgentId
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

EPISODE_KIND: str = "episode"


class MemoryKind(StrEnum):
    """Supported memory record kinds."""

    EPISODE = "episode"


class MemoryCensus(BaseModel):
    """Aggregate episodic memory snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_count: NonNegativeInt
    total_records: NonNegativeInt
    agents_with_memory: NonNegativeInt
    episode_records: NonNegativeInt
    mean_records_bps: NonNegativeInt


@dataclass(frozen=True, slots=True)
class MemoryWrite:
    """One memory record written during an apply pass."""

    agent_id: AgentId
    kind: str
    content: str


def encode_agent_episode(agent: Agent, tick: Tick) -> MemoryRecord:
    """Build a deterministic episode record for ``agent`` at ``tick``."""
    facts = ",".join(sorted(agent.knowledge.facts))
    content = (
        f"loc={agent.location_id.value}"
        f"|food={agent.needs.food:.3f}"
        f"|water={agent.needs.water:.3f}"
        f"|energy={agent.needs.energy:.3f}"
        f"|facts={facts}"
    )
    return MemoryRecord(tick=tick, kind=MemoryKind.EPISODE.value, content=content)


def record_memory(world: World, agent_id: AgentId | int, record: MemoryRecord) -> World:
    """Append ``record`` to ``agent_id`` memory when the agent exists.

    Raises:
        ValueError: If ``agent_id`` is missing from the world.
    """
    agent = world.agent_by_id(agent_id)
    if agent is None:
        target = agent_id if isinstance(agent_id, int) else agent_id.value
        msg = f"agent id {target} not found in world"
        raise ValueError(msg)
    updated = agent.model_copy(update={"memory": agent.memory.remember(record)})
    return world.with_agent(updated)


def apply_memory_encoding(
    world: World,
) -> tuple[World, tuple[MemoryWrite, ...]]:
    """Encode one episode memory for each living agent in id order."""
    writes: list[MemoryWrite] = []
    for agent in world.alive_agents():
        record = encode_agent_episode(agent, world.tick)
        world = record_memory(world, agent.agent_id, record)
        writes.append(
            MemoryWrite(
                agent_id=agent.agent_id,
                kind=record.kind,
                content=record.content,
            )
        )
    return world, tuple(writes)


def census_memory(world: World) -> MemoryCensus:
    """Build a deterministic memory census for ``world``."""
    living = world.alive_agents()
    total_records = 0
    agents_with_memory = 0
    episode_records = 0
    for agent in living:
        count = len(agent.memory.records)
        total_records += count
        if count > 0:
            agents_with_memory += 1
        episode_records += sum(
            1 for record in agent.memory.records if record.kind == EPISODE_KIND
        )
    living_count = len(living)
    mean_records_bps = (
        0 if living_count == 0 else (total_records * 10_000) // living_count
    )
    return MemoryCensus(
        tick=world.tick,
        living_count=living_count,
        total_records=total_records,
        agents_with_memory=agents_with_memory,
        episode_records=episode_records,
        mean_records_bps=mean_records_bps,
    )
