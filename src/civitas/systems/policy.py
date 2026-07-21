"""Utility-based action selection policy.

The policy scores candidate actions from agent needs, personality, and
goals, then picks the maximum utility. It never mutates the world and
never calls other systems — execution belongs to the action executor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    ACTION_CATALOG,
    ACTION_NEED_TARGET,
    ActionChoice,
    ActionKind,
    ActionSelected,
)
from civitas.domain.types import UnitInterval

if TYPE_CHECKING:
    from civitas.domain import Agent, World
    from civitas.engine.event_bus import EventBus


class PolicyConfig(BaseModel):
    """Weights controlling utility composition.

    Attributes:
        goal_weight: Multiplier applied to matching goal priorities.
        idle_weight: Scales idle utility by the least-satisfied need.
        personality_floor: Minimum personality multiplier (avoids zeros).
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    goal_weight: UnitInterval = 0.5
    idle_weight: UnitInterval = 0.15
    personality_floor: UnitInterval = Field(default=0.5, ge=0.0, le=1.0)


class UtilityPolicy:
    """Deterministic utility maximizer over the Phase 1 action catalog."""

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self._config = config if config is not None else PolicyConfig()

    @property
    def config(self) -> PolicyConfig:
        """Return the immutable policy configuration."""
        return self._config

    def score(self, agent: Agent, action: ActionKind | str) -> float:
        """Compute utility of ``action`` for ``agent``."""
        kind = ActionKind(action)
        need_component = self._need_utility(agent, kind)
        personality_component = self._personality_multiplier(agent, kind)
        goal_component = self._goal_bonus(agent, kind)
        raw = (need_component * personality_component) + goal_component
        return round(raw, 6)

    def select(self, agent: Agent) -> ActionChoice:
        """Select the highest-utility action for a living agent.

        Ties break by ascending action name for reproducibility.

        Raises:
            ValueError: If ``agent`` is not alive.
        """
        if not agent.is_alive():
            msg = f"cannot select actions for non-living agent {agent.agent_id}"
            raise ValueError(msg)

        best_action = ActionKind.IDLE
        best_utility = float("-inf")
        for action in ACTION_CATALOG:
            utility = self.score(agent, action)
            if utility > best_utility or (
                utility == best_utility and action.value < best_action.value
            ):
                best_action = action
                best_utility = utility
        return ActionChoice(
            agent_id=agent.agent_id,
            action=best_action,
            utility=best_utility,
        )

    def select_all(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> tuple[ActionChoice, ...]:
        """Select actions for all living agents in stable id order.

        Optionally publishes ``ActionSelected`` for each choice. The world
        is not modified.
        """
        choices: list[ActionChoice] = []
        for agent in world.alive_agents():
            choice = self.select(agent)
            choices.append(choice)
            if bus is not None:
                bus.publish(
                    ActionSelected(
                        tick=world.tick,
                        agent_id=choice.agent_id,
                        action=choice.action.value,
                        utility=choice.utility,
                    )
                )
        return tuple(choices)

    def score_all(self, agent: Agent) -> dict[str, float]:
        """Return a mapping of every catalog action to its utility."""
        return {action.value: self.score(agent, action) for action in ACTION_CATALOG}

    def _need_utility(self, agent: Agent, action: ActionKind) -> float:
        """Urgency-based utility from the action's target need."""
        target = ACTION_NEED_TARGET[action]
        needs = agent.needs.as_mapping()
        if target is None:
            least_satisfied = min(needs.values())
            return round(self._config.idle_weight * least_satisfied, 6)
        urgency = 1.0 - needs[target]
        return round(urgency, 6)

    def _personality_multiplier(self, agent: Agent, action: ActionKind) -> float:
        """Scale need utility by a relevant personality trait."""
        floor = self._config.personality_floor
        personality = agent.personality
        if action is ActionKind.SOCIALIZE:
            trait = personality.extraversion
        elif action is ActionKind.SEEK_SAFETY:
            trait = personality.neuroticism
        elif action in {ActionKind.EAT, ActionKind.DRINK, ActionKind.REST}:
            trait = personality.conscientiousness
        elif action is ActionKind.IDLE:
            trait = personality.agreeableness
        else:
            trait = 0.5
        return round(floor + ((1.0 - floor) * trait), 6)

    def _goal_bonus(self, agent: Agent, action: ActionKind) -> float:
        """Add priority-weighted bonus when a goal matches the action."""
        target = ACTION_NEED_TARGET[action]
        best = 0.0
        for goal in agent.goals.goals:
            matches_action = goal.kind == action.value
            matches_need = target is not None and goal.kind == f"satisfy_{target}"
            if matches_action or matches_need:
                best = max(best, goal.priority * self._config.goal_weight)
        return round(best, 6)
