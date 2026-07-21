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
    DEFAULT_MOVE_ENERGY_COST,
    ActionChoice,
    ActionKind,
    ActionSelected,
    enterable_neighbors,
    occupancy,
)
from civitas.domain.types import UnitInterval

if TYPE_CHECKING:
    from civitas.domain import Agent, LocationId, World
    from civitas.engine.event_bus import EventBus


class PolicyConfig(BaseModel):
    """Weights controlling utility composition.

    Attributes:
        goal_weight: Multiplier applied to matching goal priorities.
        idle_weight: Scales idle utility by the least-satisfied need.
        move_weight: Scales MOVE utility by energy and need satisfaction.
        move_energy_cost: Minimum energy required to consider MOVE.
        personality_floor: Minimum personality multiplier (avoids zeros).
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    goal_weight: UnitInterval = 0.5
    idle_weight: UnitInterval = 0.15
    move_weight: UnitInterval = 0.35
    move_energy_cost: UnitInterval = DEFAULT_MOVE_ENERGY_COST
    personality_floor: UnitInterval = Field(default=0.5, ge=0.0, le=1.0)


class UtilityPolicy:
    """Deterministic utility maximizer over the action catalog."""

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self._config = config if config is not None else PolicyConfig()

    @property
    def config(self) -> PolicyConfig:
        """Return the immutable policy configuration."""
        return self._config

    def score(
        self,
        agent: Agent,
        action: ActionKind | str,
        world: World | None = None,
    ) -> float:
        """Compute utility of ``action`` for ``agent``.

        MOVE scores the best enterable neighbor when ``world`` is provided;
        without a world (or without a legal destination) MOVE scores 0.0.
        """
        kind = ActionKind(action)
        if kind is ActionKind.MOVE:
            utility, _destination = self._best_move(agent, world)
            return utility
        need_component = self._need_utility(agent, kind)
        personality_component = self._personality_multiplier(agent, kind)
        goal_component = self._goal_bonus(agent, kind)
        raw = (need_component * personality_component) + goal_component
        return round(raw, 6)

    def select(
        self,
        agent: Agent,
        world: World | None = None,
    ) -> ActionChoice:
        """Select the highest-utility action for a living agent.

        Ties break by ascending action name for reproducibility. MOVE is
        only selectable when ``world`` exposes an enterable neighbor and
        the agent can afford the configured energy cost.

        Raises:
            ValueError: If ``agent`` is not alive.
        """
        if not agent.is_alive():
            msg = f"cannot select actions for non-living agent {agent.agent_id}"
            raise ValueError(msg)

        best_action = ActionKind.IDLE
        best_utility = float("-inf")
        best_target: LocationId | None = None
        for action in ACTION_CATALOG:
            if action is ActionKind.MOVE:
                utility, target = self._best_move(agent, world)
                if target is None:
                    continue
            else:
                utility = self.score(agent, action, world=world)
                target = None
            if utility > best_utility or (
                utility == best_utility and action.value < best_action.value
            ):
                best_action = action
                best_utility = utility
                best_target = target
        return ActionChoice(
            agent_id=agent.agent_id,
            action=best_action,
            utility=best_utility,
            target_location_id=best_target,
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
            choice = self.select(agent, world=world)
            choices.append(choice)
            if bus is not None:
                bus.publish(
                    ActionSelected(
                        tick=world.tick,
                        agent_id=choice.agent_id,
                        action=choice.action.value,
                        utility=choice.utility,
                        target_location_id=choice.target_location_id,
                    )
                )
        return tuple(choices)

    def score_all(self, agent: Agent, world: World | None = None) -> dict[str, float]:
        """Return a mapping of every catalog action to its utility."""
        return {
            action.value: self.score(agent, action, world=world)
            for action in ACTION_CATALOG
        }

    def _best_move(
        self,
        agent: Agent,
        world: World | None,
    ) -> tuple[float, LocationId | None]:
        """Return (utility, destination) for the best legal MOVE, if any."""
        if world is None:
            return 0.0, None
        if agent.needs.energy < self._config.move_energy_cost:
            return 0.0, None

        candidates = enterable_neighbors(world, agent.location_id)
        if not candidates:
            return 0.0, None

        # Prefer emptier destinations; tie-break by ascending location id.
        destination = min(
            candidates,
            key=lambda location: (
                occupancy(world, location.location_id),
                location.location_id.value,
            ),
        )
        need_component = self._need_utility(agent, ActionKind.MOVE)
        personality_component = self._personality_multiplier(agent, ActionKind.MOVE)
        goal_component = self._goal_bonus(agent, ActionKind.MOVE)
        utility = round(
            (need_component * personality_component) + goal_component,
            6,
        )
        return utility, destination.location_id

    def _need_utility(self, agent: Agent, action: ActionKind) -> float:
        """Urgency-based utility from the action's target need."""
        target = ACTION_NEED_TARGET[action]
        needs = agent.needs.as_mapping()
        if action is ActionKind.MOVE:
            least_satisfied = min(needs.values())
            return round(
                self._config.move_weight * agent.needs.energy * least_satisfied,
                6,
            )
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
        elif action is ActionKind.MOVE:
            trait = personality.openness
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
            matches_explore = action is ActionKind.MOVE and goal.kind == "explore"
            if matches_action or matches_need or matches_explore:
                best = max(best, goal.priority * self._config.goal_weight)
        return round(best, 6)
