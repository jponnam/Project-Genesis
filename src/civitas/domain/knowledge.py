"""Knowledge diffusion: agent facts for discovered technologies.

Phase 6 Milestone 4. Society discovery (technology/research/innovation)
settles first; this module bootstraps a living knower when no one knows a
discovered fact, then spreads facts peer-to-peer among co-located living
agents. Phase 8 Milestone 4 gates peer teaching on learner trust toward
the teacher.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.effects import effective_teachings_per_knower
from civitas.domain.ids import AgentId
from civitas.domain.laws import ethics_min_teach_trust_delta_for
from civitas.domain.numeric import clamp_unit
from civitas.domain.relationships import DEFAULT_TRUST, get_bond
from civitas.domain.technology import (
    Technology,
    TechnologyKind,
    discovered_technologies,
)
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

DEFAULT_TEACHINGS_PER_KNOWER: int = 1
DEFAULT_MIN_TEACH_TRUST: float = 0.5
FIRE_FACT: str = TechnologyKind.FIRE.value
POTTERY_FACT: str = TechnologyKind.POTTERY.value
IRRIGATION_FACT: str = TechnologyKind.IRRIGATION.value
METALLURGY_FACT: str = TechnologyKind.METALLURGY.value
WRITING_FACT: str = TechnologyKind.WRITING.value
MATHEMATICS_FACT: str = TechnologyKind.MATHEMATICS.value
ASTRONOMY_FACT: str = TechnologyKind.ASTRONOMY.value
PHILOSOPHY_FACT: str = TechnologyKind.PHILOSOPHY.value
LOGIC_FACT: str = TechnologyKind.LOGIC.value
RHETORIC_FACT: str = TechnologyKind.RHETORIC.value
MEDICINE_FACT: str = TechnologyKind.MEDICINE.value
ANATOMY_FACT: str = TechnologyKind.ANATOMY.value
HYGIENE_FACT: str = TechnologyKind.HYGIENE.value


class KnowledgeSource(StrEnum):
    """How an agent acquired a technology fact."""

    BOOTSTRAP = "bootstrap"
    PEER = "peer"
    BIRTH = "birth"


class KnowledgeCensus(BaseModel):
    """Aggregate knowledge snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_count: NonNegativeInt
    discovered_technology_count: NonNegativeInt
    fire_knower_count: NonNegativeInt
    pottery_knower_count: NonNegativeInt
    irrigation_knower_count: NonNegativeInt
    metallurgy_knower_count: NonNegativeInt = 0
    writing_knower_count: NonNegativeInt = 0
    mathematics_knower_count: NonNegativeInt = 0
    astronomy_knower_count: NonNegativeInt = 0
    philosophy_knower_count: NonNegativeInt = 0
    logic_knower_count: NonNegativeInt = 0
    rhetoric_knower_count: NonNegativeInt = 0
    medicine_knower_count: NonNegativeInt = 0
    anatomy_knower_count: NonNegativeInt = 0
    hygiene_knower_count: NonNegativeInt = 0
    total_fact_instances: NonNegativeInt
    coverage_bps: NonNegativeInt


@dataclass(frozen=True, slots=True)
class KnowledgeGain:
    """One fact learned during an apply pass."""

    agent_id: AgentId
    fact: str
    source: KnowledgeSource
    teacher_id: AgentId | None


def technology_fact(technology: Technology) -> str:
    """Return the canonical knowledge fact string for ``technology``."""
    return technology.kind.value


def agents_knowing(world: World, fact: str) -> tuple[Agent, ...]:
    """Return living agents who know ``fact``, in ascending id order."""
    return tuple(agent for agent in world.alive_agents() if agent.knowledge.knows(fact))


def grant_knowledge(
    world: World,
    agent_id: AgentId | int,
    fact: str,
) -> World | None:
    """Grant ``fact`` to ``agent_id`` when present and alive.

    Already-known facts return the same world. Missing/dead agents return
    ``None``.
    """
    agent = world.agent_by_id(agent_id)
    if agent is None or not agent.is_alive():
        return None
    if agent.knowledge.knows(fact):
        return world
    updated = agent.model_copy(update={"knowledge": agent.knowledge.learn(fact)})
    return world.with_agent(updated)


def bootstrap_discovered_knowledge(
    world: World,
) -> tuple[World, tuple[KnowledgeGain, ...]]:
    """Ensure each discovered tech has at least one living knower.

    When no living agent knows a discovered fact, grant it to the lowest
    living ``agent_id``.
    """
    gains: list[KnowledgeGain] = []
    living = world.alive_agents()
    if not living:
        return world, ()

    for technology in discovered_technologies(world):
        fact = technology_fact(technology)
        if any(agent.knowledge.knows(fact) for agent in living):
            continue
        target = living[0]
        updated = grant_knowledge(world, target.agent_id, fact)
        if updated is None:
            continue
        world = updated
        living = world.alive_agents()
        gains.append(
            KnowledgeGain(
                agent_id=target.agent_id,
                fact=fact,
                source=KnowledgeSource.BOOTSTRAP,
                teacher_id=None,
            )
        )
    return world, tuple(gains)


def learner_trust_in_teacher(learner: Agent, teacher: Agent) -> float:
    """Return learner→teacher trust, defaulting when no bond exists."""
    bond = get_bond(learner, teacher.agent_id)
    if bond is None:
        return DEFAULT_TRUST
    return float(bond.trust)


def can_learn_from_teacher(
    learner: Agent,
    teacher: Agent,
    *,
    min_trust: float = DEFAULT_MIN_TEACH_TRUST,
) -> bool:
    """Return True when ``learner`` trusts ``teacher`` enough to accept teaching."""
    if min_trust < 0.0 or min_trust > 1.0:
        msg = f"min_trust must be in [0, 1], got {min_trust}"
        raise ValueError(msg)
    return learner_trust_in_teacher(learner, teacher) >= min_trust


def diffuse_knowledge(
    world: World,
    *,
    teachings_per_knower: int = DEFAULT_TEACHINGS_PER_KNOWER,
    min_trust: float = DEFAULT_MIN_TEACH_TRUST,
) -> tuple[World, tuple[KnowledgeGain, ...]]:
    """Spread discovered-tech facts among co-located, trusting living agents.

    Candidates are ordered by ``(fact, teacher_id, learner_id)``. Each
    teacher may teach at most ``teachings_per_knower`` learners per apply.
    Learners must trust the teacher at least the effective minimum
    ``clamp_unit(min_trust + ethics_delta)`` (missing bonds use
    ``DEFAULT_TRUST``). Active ``ETHICS`` statutes lower that threshold
    for living subject learners.
    """
    if teachings_per_knower < 0:
        msg = f"teachings_per_knower must be >= 0, got {teachings_per_knower}"
        raise ValueError(msg)
    if min_trust < 0.0 or min_trust > 1.0:
        msg = f"min_trust must be in [0, 1], got {min_trust}"
        raise ValueError(msg)

    living = world.alive_agents()
    if not living:
        return world, ()
    agents_by_id = {agent.agent_id.value: agent for agent in living}
    if not any(
        effective_teachings_per_knower(world, base=teachings_per_knower, agent=agent)
        > 0
        for agent in living
    ):
        return world, ()

    candidates: list[tuple[str, int, int]] = []
    for technology in discovered_technologies(world):
        fact = technology_fact(technology)
        knowers = [agent for agent in living if agent.knowledge.knows(fact)]
        for teacher in knowers:
            for learner in living:
                if learner.agent_id == teacher.agent_id:
                    continue
                if learner.location_id != teacher.location_id:
                    continue
                if learner.knowledge.knows(fact):
                    continue
                effective_min_trust = clamp_unit(
                    min_trust + ethics_min_teach_trust_delta_for(world, learner)
                )
                if not can_learn_from_teacher(
                    learner,
                    teacher,
                    min_trust=effective_min_trust,
                ):
                    continue
                candidates.append(
                    (
                        fact,
                        teacher.agent_id.value,
                        learner.agent_id.value,
                    )
                )
    candidates.sort()

    taught_counts: dict[int, int] = {}
    learned: set[tuple[int, str]] = set()
    gains: list[KnowledgeGain] = []
    for fact, teacher_value, learner_value in candidates:
        teacher = agents_by_id[teacher_value]
        teaching_limit = effective_teachings_per_knower(
            world,
            base=teachings_per_knower,
            agent=teacher,
        )
        if taught_counts.get(teacher_value, 0) >= teaching_limit:
            continue
        if (learner_value, fact) in learned:
            continue
        updated = grant_knowledge(world, learner_value, fact)
        if updated is None:
            continue
        if updated is world:
            continue
        world = updated
        taught_counts[teacher_value] = taught_counts.get(teacher_value, 0) + 1
        learned.add((learner_value, fact))
        gains.append(
            KnowledgeGain(
                agent_id=AgentId(value=learner_value),
                fact=fact,
                source=KnowledgeSource.PEER,
                teacher_id=AgentId(value=teacher_value),
            )
        )
    return world, tuple(gains)


def apply_knowledge_diffusion(
    world: World,
    *,
    teachings_per_knower: int = DEFAULT_TEACHINGS_PER_KNOWER,
    min_trust: float = DEFAULT_MIN_TEACH_TRUST,
) -> tuple[World, tuple[KnowledgeGain, ...]]:
    """Bootstrap missing knowers, then run one peer-diffusion pass."""
    world, bootstrap_gains = bootstrap_discovered_knowledge(world)
    world, peer_gains = diffuse_knowledge(
        world,
        teachings_per_knower=teachings_per_knower,
        min_trust=min_trust,
    )
    return world, bootstrap_gains + peer_gains


def census_knowledge(world: World) -> KnowledgeCensus:
    """Build a deterministic knowledge census for ``world``."""
    living = world.alive_agents()
    discovered = discovered_technologies(world)
    discovered_facts = {technology_fact(tech) for tech in discovered}
    fire_knowers = sum(1 for agent in living if agent.knowledge.knows(FIRE_FACT))
    pottery_knowers = sum(1 for agent in living if agent.knowledge.knows(POTTERY_FACT))
    irrigation_knowers = sum(
        1 for agent in living if agent.knowledge.knows(IRRIGATION_FACT)
    )
    metallurgy_knowers = sum(
        1 for agent in living if agent.knowledge.knows(METALLURGY_FACT)
    )
    writing_knowers = sum(1 for agent in living if agent.knowledge.knows(WRITING_FACT))
    mathematics_knowers = sum(
        1 for agent in living if agent.knowledge.knows(MATHEMATICS_FACT)
    )
    astronomy_knowers = sum(
        1 for agent in living if agent.knowledge.knows(ASTRONOMY_FACT)
    )
    philosophy_knowers = sum(
        1 for agent in living if agent.knowledge.knows(PHILOSOPHY_FACT)
    )
    logic_knowers = sum(1 for agent in living if agent.knowledge.knows(LOGIC_FACT))
    rhetoric_knowers = sum(
        1 for agent in living if agent.knowledge.knows(RHETORIC_FACT)
    )
    medicine_knowers = sum(
        1 for agent in living if agent.knowledge.knows(MEDICINE_FACT)
    )
    anatomy_knowers = sum(1 for agent in living if agent.knowledge.knows(ANATOMY_FACT))
    hygiene_knowers = sum(1 for agent in living if agent.knowledge.knows(HYGIENE_FACT))
    total_fact_instances = 0
    for agent in living:
        total_fact_instances += sum(
            1 for fact in discovered_facts if agent.knowledge.knows(fact)
        )
    living_count = len(living)
    discovered_count = len(discovered)
    if living_count == 0 or discovered_count == 0:
        coverage_bps = 0
    else:
        coverage_bps = (total_fact_instances * 10_000) // (
            living_count * discovered_count
        )
    return KnowledgeCensus(
        tick=world.tick,
        living_count=living_count,
        discovered_technology_count=discovered_count,
        fire_knower_count=fire_knowers,
        pottery_knower_count=pottery_knowers,
        irrigation_knower_count=irrigation_knowers,
        metallurgy_knower_count=metallurgy_knowers,
        writing_knower_count=writing_knowers,
        mathematics_knower_count=mathematics_knowers,
        astronomy_knower_count=astronomy_knowers,
        philosophy_knower_count=philosophy_knowers,
        logic_knower_count=logic_knowers,
        rhetoric_knower_count=rhetoric_knowers,
        medicine_knower_count=medicine_knowers,
        anatomy_knower_count=anatomy_knowers,
        hygiene_knower_count=hygiene_knowers,
        total_fact_instances=total_fact_instances,
        coverage_bps=coverage_bps,
    )
