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
    DEFAULT_DRINK_CONSUME_AMOUNT,
    DEFAULT_EAT_CONSUME_AMOUNT,
    DEFAULT_MOVE_ENERGY_COST,
    DEFAULT_TRUST,
    FOOD_RESOURCE,
    RESOURCE_NEED,
    WATER_RESOURCE,
    ActionChoice,
    ActionKind,
    ActionSelected,
    AgentId,
    TradeTerms,
    can_afford,
    can_rest,
    can_trade,
    enterable_neighbors,
    gatherable_resources,
    get_bond,
    occupancy,
    producible_recipes,
    recipe_by_id,
)
from civitas.domain.trading import DEFAULT_TRADE_PRICE, DEFAULT_TRADE_QUANTITY
from civitas.domain.types import NonNegativeInt, PositiveInt, UnitInterval

if TYPE_CHECKING:
    from civitas.domain import Agent, Location, LocationId, World
    from civitas.engine.event_bus import EventBus


class PolicyConfig(BaseModel):
    """Weights controlling utility composition.

    Attributes:
        goal_weight: Multiplier applied to matching goal priorities.
        retrieval_weight: Scales working-memory support for satisfy-need goals.
        idle_weight: Scales idle utility by the least-satisfied need.
        move_weight: Scales exploratory MOVE utility.
        gather_weight: Scales GATHER utility from need/inventory pressure.
        trade_weight: Scales TRADE utility from need/inventory pressure.
        produce_weight: Scales PRODUCE utility from output scarcity.
        resource_seek_weight: Bonus for MOVE toward resource-bearing cells.
        move_energy_cost: Minimum energy required to consider MOVE.
        trade_quantity: Units purchased by a selected TRADE.
        trade_price: Total money paid by the buyer for a selected TRADE.
        personality_floor: Minimum personality multiplier (avoids zeros).
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    goal_weight: UnitInterval = 0.5
    retrieval_weight: UnitInterval = 0.25
    idle_weight: UnitInterval = 0.15
    move_weight: UnitInterval = 0.35
    gather_weight: UnitInterval = 0.55
    trade_weight: UnitInterval = 0.60
    produce_weight: UnitInterval = 0.50
    resource_seek_weight: UnitInterval = 0.45
    move_energy_cost: UnitInterval = DEFAULT_MOVE_ENERGY_COST
    trade_quantity: PositiveInt = DEFAULT_TRADE_QUANTITY
    trade_price: NonNegativeInt = DEFAULT_TRADE_PRICE
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

        MOVE / GATHER / TRADE / PRODUCE / SOCIALIZE score their best legal
        target when ``world`` is set (PRODUCE only needs the agent).
        EAT/DRINK score 0.0 without inventory food/water. REST scores 0.0
        when energy is already full.
        """
        kind = ActionKind(action)
        if kind is ActionKind.MOVE:
            utility, _destination = self._best_move(agent, world)
            return utility
        if kind is ActionKind.GATHER:
            utility, _resource = self._best_gather(agent, world)
            return utility
        if kind is ActionKind.TRADE:
            utility, _seller, _resource = self._best_trade(agent, world)
            return utility
        if kind is ActionKind.PRODUCE:
            utility, _recipe = self._best_produce(agent)
            return utility
        if kind is ActionKind.SOCIALIZE:
            utility, _partner = self._best_socialize(agent, world)
            return utility
        if kind is ActionKind.EAT and not self._has_food(agent):
            return 0.0
        if kind is ActionKind.DRINK and not self._has_water(agent):
            return 0.0
        if kind is ActionKind.REST and not can_rest(agent):
            return 0.0
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

        Ties break by ascending action name for reproducibility.

        Raises:
            ValueError: If ``agent`` is not alive.
        """
        if not agent.is_alive():
            msg = f"cannot select actions for non-living agent {agent.agent_id}"
            raise ValueError(msg)

        best_action = ActionKind.IDLE
        best_utility = float("-inf")
        best_location: LocationId | None = None
        best_resource: str | None = None
        best_agent: AgentId | None = None
        for action in ACTION_CATALOG:
            if action is ActionKind.MOVE:
                utility, target_location = self._best_move(agent, world)
                if target_location is None:
                    continue
                target_resource = None
                target_agent = None
            elif action is ActionKind.GATHER:
                utility, target_resource = self._best_gather(agent, world)
                if target_resource is None:
                    continue
                target_location = None
                target_agent = None
            elif action is ActionKind.TRADE:
                utility, target_agent, target_resource = self._best_trade(agent, world)
                if target_agent is None or target_resource is None:
                    continue
                target_location = None
            elif action is ActionKind.SOCIALIZE:
                utility, target_agent = self._best_socialize(agent, world)
                if target_agent is None:
                    continue
                target_location = None
                target_resource = None
            elif action is ActionKind.PRODUCE:
                utility, target_resource = self._best_produce(agent)
                if target_resource is None:
                    continue
                target_location = None
                target_agent = None
            elif self._action_unavailable(action, agent):
                continue
            else:
                utility = self.score(agent, action, world=world)
                target_location = None
                target_resource = None
                target_agent = None
            if utility > best_utility or (
                utility == best_utility and action.value < best_action.value
            ):
                best_action = action
                best_utility = utility
                best_location = target_location
                best_resource = target_resource
                best_agent = target_agent
        return ActionChoice(
            agent_id=agent.agent_id,
            action=best_action,
            utility=best_utility,
            target_location_id=best_location,
            target_resource=best_resource,
            target_agent_id=best_agent,
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
                        target_resource=choice.target_resource,
                        target_agent_id=choice.target_agent_id,
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

        destination = min(
            candidates,
            key=lambda location: (
                -self._destination_appeal(agent, location),
                occupancy(world, location.location_id),
                location.location_id.value,
            ),
        )
        need_component = self._need_utility(agent, ActionKind.MOVE)
        personality_component = self._personality_multiplier(agent, ActionKind.MOVE)
        goal_component = self._goal_bonus(agent, ActionKind.MOVE)
        seek_bonus = round(
            self._destination_appeal(agent, destination)
            * self._config.resource_seek_weight,
            6,
        )
        utility = round(
            (need_component * personality_component) + goal_component + seek_bonus,
            6,
        )
        return utility, destination.location_id

    def _best_gather(
        self,
        agent: Agent,
        world: World | None,
    ) -> tuple[float, str | None]:
        """Return (utility, resource) for the best legal GATHER, if any."""
        if world is None:
            return 0.0, None
        location = world.location_by_id(agent.location_id)
        if location is None:
            return 0.0, None
        resources = gatherable_resources(location)
        if not resources:
            return 0.0, None

        best_resource: str | None = None
        best_utility = float("-inf")
        for resource in resources:
            utility = self._gather_utility(agent, resource)
            if utility > best_utility or (
                utility == best_utility
                and (best_resource is None or resource < best_resource)
            ):
                best_utility = utility
                best_resource = resource
        return best_utility, best_resource

    def _best_trade(
        self,
        agent: Agent,
        world: World | None,
    ) -> tuple[float, AgentId | None, str | None]:
        """Return (utility, seller, resource) for the best legal TRADE."""
        if world is None:
            return 0.0, None, None
        if not can_afford(agent, self._config.trade_price):
            return 0.0, None, None

        best_utility = float("-inf")
        best_seller: AgentId | None = None
        best_resource: str | None = None
        for seller in world.agents_at(agent.location_id):
            if seller.agent_id == agent.agent_id or not seller.is_alive():
                continue
            resources = sorted(
                {
                    stack.resource
                    for stack in seller.inventory.stacks
                    if stack.quantity >= self._config.trade_quantity
                }
            )
            for resource in resources:
                terms = TradeTerms(
                    buyer_id=agent.agent_id,
                    seller_id=seller.agent_id,
                    resource=resource,
                    quantity=self._config.trade_quantity,
                    price=self._config.trade_price,
                )
                if not can_trade(world, terms):
                    continue
                utility = self._trade_utility(agent, resource)
                candidate_key = (seller.agent_id.value, resource)
                best_key = (
                    (best_seller.value, best_resource)
                    if best_seller is not None and best_resource is not None
                    else None
                )
                if utility > best_utility or (
                    utility == best_utility
                    and (best_key is None or candidate_key < best_key)
                ):
                    best_utility = utility
                    best_seller = seller.agent_id
                    best_resource = resource
        if best_seller is None or best_resource is None:
            return 0.0, None, None
        return best_utility, best_seller, best_resource

    def _trade_utility(self, agent: Agent, resource: str) -> float:
        """Score buying ``resource`` from need urgency and inventory gap."""
        need_name = RESOURCE_NEED.get(resource)
        inventory_qty = agent.inventory.quantity(resource)
        scarcity = 1.0 / (1.0 + inventory_qty)
        if need_name is None:
            need_component = round(self._config.trade_weight * 0.25 * scarcity, 6)
        else:
            urgency = 1.0 - agent.needs.as_mapping()[need_name]
            need_component = round(
                self._config.trade_weight * urgency * scarcity,
                6,
            )
        personality_component = self._personality_multiplier(agent, ActionKind.TRADE)
        goal_component = self._trade_goal_bonus(agent, resource)
        return round((need_component * personality_component) + goal_component, 6)

    def _best_produce(self, agent: Agent) -> tuple[float, str | None]:
        """Return (utility, recipe_id) for the best legal PRODUCE, if any."""
        recipes = producible_recipes(agent)
        if not recipes:
            return 0.0, None

        best_recipe: str | None = None
        best_utility = float("-inf")
        for recipe in recipes:
            utility = self._produce_utility(agent, recipe.recipe_id)
            if utility > best_utility or (
                utility == best_utility
                and (best_recipe is None or recipe.recipe_id < best_recipe)
            ):
                best_utility = utility
                best_recipe = recipe.recipe_id
        return best_utility, best_recipe

    def _best_socialize(
        self,
        agent: Agent,
        world: World | None,
    ) -> tuple[float, AgentId | None]:
        """Return (utility, partner) for the best legal SOCIALIZE."""
        if world is None:
            return 0.0, None

        best_partner: AgentId | None = None
        best_key: tuple[float, float, int] | None = None
        for partner in world.agents_at(agent.location_id):
            if partner.agent_id == agent.agent_id or not partner.is_alive():
                continue
            bond = get_bond(agent, partner.agent_id)
            affinity = bond.affinity if bond is not None else 0.0
            trust = bond.trust if bond is not None else DEFAULT_TRUST
            # Prefer higher affinity, then higher trust, then lower id.
            key = (-affinity, -trust, partner.agent_id.value)
            if best_key is None or key < best_key:
                best_key = key
                best_partner = partner.agent_id
        if best_partner is None:
            return 0.0, None
        return self._socialize_utility(agent), best_partner

    def _socialize_utility(self, agent: Agent) -> float:
        """Score SOCIALIZE from social urgency and extraversion."""
        need_component = self._need_utility(agent, ActionKind.SOCIALIZE)
        personality_component = self._personality_multiplier(
            agent,
            ActionKind.SOCIALIZE,
        )
        goal_component = self._goal_bonus(agent, ActionKind.SOCIALIZE)
        return round((need_component * personality_component) + goal_component, 6)

    def _produce_utility(self, agent: Agent, recipe_id: str) -> float:
        """Score crafting ``recipe_id`` from output scarcity and needs."""
        recipe = recipe_by_id(recipe_id)
        if recipe is None:
            return 0.0
        scarcity_total = 0.0
        for stack in recipe.outputs:
            inventory_qty = agent.inventory.quantity(stack.resource)
            scarcity = 1.0 / (1.0 + inventory_qty)
            need_name = RESOURCE_NEED.get(stack.resource)
            if need_name is None:
                scarcity_total += 0.35 * scarcity
            else:
                urgency = 1.0 - agent.needs.as_mapping()[need_name]
                scarcity_total += urgency * scarcity
        need_component = round(
            self._config.produce_weight * scarcity_total / max(len(recipe.outputs), 1),
            6,
        )
        personality_component = self._personality_multiplier(agent, ActionKind.PRODUCE)
        goal_component = self._produce_goal_bonus(agent, recipe_id)
        return round((need_component * personality_component) + goal_component, 6)

    def _gather_utility(self, agent: Agent, resource: str) -> float:
        """Score gathering ``resource`` from need urgency and inventory gap.

        When a need-linked resource is absent from inventory and available
        underfoot, gathering slightly outranks the matching restorative
        action so agents stockpile before consuming.
        """
        need_name = RESOURCE_NEED.get(resource)
        inventory_qty = agent.inventory.quantity(resource)
        scarcity = 1.0 / (1.0 + inventory_qty)
        if need_name is None:
            need_component = round(self._config.gather_weight * 0.35 * scarcity, 6)
        else:
            urgency = 1.0 - agent.needs.as_mapping()[need_name]
            if inventory_qty == 0:
                need_component = round(urgency + 0.05, 6)
            else:
                need_component = round(
                    self._config.gather_weight * urgency * scarcity,
                    6,
                )
        personality_component = self._personality_multiplier(agent, ActionKind.GATHER)
        goal_component = self._gather_goal_bonus(agent, resource)
        return round((need_component * personality_component) + goal_component, 6)

    def _destination_appeal(self, agent: Agent, location: Location) -> float:
        """Return how attractive ``location`` is for resource seeking."""
        best = 0.0
        for resource in gatherable_resources(location):
            need_name = RESOURCE_NEED.get(resource)
            scarcity = 1.0 / (1.0 + agent.inventory.quantity(resource))
            if need_name is None:
                best = max(best, 0.2 * scarcity)
            else:
                urgency = 1.0 - agent.needs.as_mapping()[need_name]
                best = max(best, urgency * scarcity)
        return round(best, 6)

    def _has_food(self, agent: Agent) -> bool:
        """Return True when the agent holds enough food to eat."""
        return agent.inventory.quantity(FOOD_RESOURCE) >= DEFAULT_EAT_CONSUME_AMOUNT

    def _has_water(self, agent: Agent) -> bool:
        """Return True when the agent holds enough water to drink."""
        return agent.inventory.quantity(WATER_RESOURCE) >= DEFAULT_DRINK_CONSUME_AMOUNT

    def _action_unavailable(self, action: ActionKind, agent: Agent) -> bool:
        """Return True when EAT/DRINK/REST cannot run in the current state."""
        if action is ActionKind.EAT:
            return not self._has_food(agent)
        if action is ActionKind.DRINK:
            return not self._has_water(agent)
        if action is ActionKind.REST:
            return not can_rest(agent)
        return False

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
        elif action in {
            ActionKind.EAT,
            ActionKind.DRINK,
            ActionKind.REST,
            ActionKind.GATHER,
            ActionKind.PRODUCE,
        }:
            trait = personality.conscientiousness
        elif action is ActionKind.TRADE:
            trait = personality.agreeableness
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
        matched_need = False
        for goal in agent.goals.goals:
            matches_action = goal.kind == action.value
            matches_need = target is not None and goal.kind == f"satisfy_{target}"
            matches_explore = action is ActionKind.MOVE and goal.kind == "explore"
            if matches_action or matches_need or matches_explore:
                best = max(best, goal.priority * self._config.goal_weight)
                if matches_need:
                    matched_need = True
        if matched_need and target is not None:
            best += self._retrieval_support(agent, target)
        return round(best, 6)

    def _retrieval_support(self, agent: Agent, need: str) -> float:
        """Bonus when working memory holds records relevant to ``need``."""
        working = agent.working_memory
        if not working.records or working.query != need:
            return 0.0
        hits = sum(1 for record in working.records if need in record.content.lower())
        support = hits if hits > 0 else len(working.records)
        scale = float(self._config.retrieval_weight) / 0.25
        return round(min(0.15, 0.05 * support) * scale, 6)

    def _gather_goal_bonus(self, agent: Agent, resource: str) -> float:
        """Goal bonus for gathering a specific resource."""
        best = 0.0
        for goal in agent.goals.goals:
            matches = goal.kind in {ActionKind.GATHER.value, f"gather_{resource}"}
            if matches:
                best = max(best, goal.priority * self._config.goal_weight)
        return round(best, 6)

    def _trade_goal_bonus(self, agent: Agent, resource: str) -> float:
        """Goal bonus for buying a specific resource."""
        best = 0.0
        for goal in agent.goals.goals:
            matches = goal.kind in {
                ActionKind.TRADE.value,
                f"buy_{resource}",
                f"trade_{resource}",
            }
            if matches:
                best = max(best, goal.priority * self._config.goal_weight)
        return round(best, 6)

    def _produce_goal_bonus(self, agent: Agent, recipe_id: str) -> float:
        """Goal bonus for crafting a specific recipe."""
        best = 0.0
        for goal in agent.goals.goals:
            matches = goal.kind in {
                ActionKind.PRODUCE.value,
                f"produce_{recipe_id}",
                f"craft_{recipe_id}",
            }
            if matches:
                best = max(best, goal.priority * self._config.goal_weight)
        return round(best, 6)
