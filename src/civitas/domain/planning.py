"""Agent planning: translate reflection beliefs into actionable goals.

Phase 7 Milestone 3. Each apply tick sets a single ``satisfy_<need>``
goal from the agent's priority belief (or dominant need). Memory
retrieval remains a later milestone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.attributes import Goal, GoalSet
from civitas.domain.ids import AgentId
from civitas.domain.reflection import dominant_need_name
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class PlanCensus(BaseModel):
    """Aggregate planning snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_count: NonNegativeInt
    agents_with_plans: NonNegativeInt
    satisfy_food_count: NonNegativeInt
    satisfy_water_count: NonNegativeInt
    satisfy_energy_count: NonNegativeInt


@dataclass(frozen=True, slots=True)
class PlanUpdate:
    """One agent's planned goal during an apply pass."""

    agent_id: AgentId
    goal_kind: str
    priority: float
    target: str | None


def priority_need_from_beliefs(agent: Agent) -> str | None:
    """Return the need named by a ``priority:*`` belief, if present."""
    for belief in agent.beliefs.entries:
        if belief.proposition.startswith("priority:"):
            need = belief.proposition.split(":", 1)[1]
            if need in {"food", "water", "energy"}:
                return need
    return None


def plan_goal_for_agent(agent: Agent) -> Goal:
    """Build the deterministic satisfy-need goal for ``agent``."""
    need = priority_need_from_beliefs(agent)
    if need is None:
        need = dominant_need_name(agent)
        priority = 0.5
    else:
        confidence = agent.beliefs.confidence_in(f"priority:{need}")
        priority = 0.5 if confidence is None else float(confidence)
    return Goal(kind=f"satisfy_{need}", priority=priority, target=need)


def apply_planning(world: World) -> tuple[World, tuple[PlanUpdate, ...]]:
    """Replace each living agent's goals with one planned satisfy-need goal."""
    updates: list[PlanUpdate] = []
    for agent in world.alive_agents():
        goal = plan_goal_for_agent(agent)
        updated = agent.model_copy(update={"goals": GoalSet(goals=(goal,))})
        world = world.with_agent(updated)
        updates.append(
            PlanUpdate(
                agent_id=agent.agent_id,
                goal_kind=goal.kind,
                priority=float(goal.priority),
                target=goal.target,
            )
        )
    return world, tuple(updates)


def census_plans(world: World) -> PlanCensus:
    """Build a deterministic planning census for ``world``."""
    living = world.alive_agents()
    agents_with_plans = 0
    food = 0
    water = 0
    energy = 0
    for agent in living:
        if not agent.goals.goals:
            continue
        agents_with_plans += 1
        for goal in agent.goals.goals:
            if goal.kind == "satisfy_food":
                food += 1
            elif goal.kind == "satisfy_water":
                water += 1
            elif goal.kind == "satisfy_energy":
                energy += 1
    return PlanCensus(
        tick=world.tick,
        living_count=len(living),
        agents_with_plans=agents_with_plans,
        satisfy_food_count=food,
        satisfy_water_count=water,
        satisfy_energy_count=energy,
    )
