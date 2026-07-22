"""Agent reflection: LLM-assisted belief updates from episodic state.

Phase 7 Milestone 2. After episode encoding, each living agent builds a
prompt, completes it through an injected language-model port, stores a
reflection memory, and upserts a priority belief. Planning and retrieval
remain later milestones.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from civitas.domain.attributes import Belief, MemoryRecord
from civitas.domain.ids import AgentId
from civitas.domain.memory import MemoryKind
from civitas.llm.protocol import LanguageModel, LanguageModelRequest

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


@dataclass(frozen=True, slots=True)
class ReflectionOutcome:
    """One agent's reflection result during an apply pass."""

    agent_id: AgentId
    proposition: str
    confidence: float
    model_name: str
    response_text: str


def dominant_need_name(agent: Agent) -> str:
    """Return the lowest vital need name (ties broken alphabetically)."""
    candidates = (
        ("energy", agent.needs.energy),
        ("food", agent.needs.food),
        ("water", agent.needs.water),
    )
    return min(candidates, key=lambda item: (item[1], item[0]))[0]


def build_reflection_prompt(agent: Agent) -> str:
    """Build a deterministic reflection prompt for ``agent``."""
    latest = agent.memory.records[-1].content if agent.memory.records else "none"
    need = dominant_need_name(agent)
    return f"agent={agent.agent_id.value};need={need};episode={latest}"


def belief_from_reflection(
    agent: Agent,
    response_text: str,
) -> Belief:
    """Derive a priority belief from agent needs and model response text."""
    need = dominant_need_name(agent)
    level = getattr(agent.needs, need)
    # Higher deficit → higher confidence; salt with response length parity.
    base = 1.0 - float(level)
    salt = 0.01 if len(response_text) % 2 else 0.0
    confidence = min(0.99, max(0.01, base + salt))
    return Belief(proposition=f"priority:{need}", confidence=confidence)


def apply_reflections(
    world: World,
    language_model: LanguageModel,
    *,
    seed: int,
) -> tuple[World, tuple[ReflectionOutcome, ...]]:
    """Reflect for each living agent using ``language_model``."""
    outcomes: list[ReflectionOutcome] = []
    for agent in world.alive_agents():
        prompt = build_reflection_prompt(agent)
        response = language_model.complete(
            LanguageModelRequest(prompt=prompt, seed=seed)
        )
        belief = belief_from_reflection(agent, response.text)
        reflection_record = MemoryRecord(
            tick=world.tick,
            kind=MemoryKind.REFLECTION.value,
            content=response.text,
        )
        # Re-read agent after possible prior updates in this pass.
        current = world.agent_by_id(agent.agent_id)
        if current is None or not current.is_alive():
            continue
        updated_agent = current.model_copy(
            update={
                "beliefs": current.beliefs.upsert(belief),
                "memory": current.memory.remember(reflection_record),
            }
        )
        world = world.with_agent(updated_agent)
        outcomes.append(
            ReflectionOutcome(
                agent_id=agent.agent_id,
                proposition=belief.proposition,
                confidence=float(belief.confidence),
                model_name=response.model_name,
                response_text=response.text,
            )
        )
    return world, tuple(outcomes)
