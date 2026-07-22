"""Action executor: apply selected actions to world state.

The executor mutates the world only through immutable ``World`` updates.
It does not call the needs, movement, gathering, food, water, energy,
production, relationship, or policy systems; shared catalogs and domain
helpers apply effects. Events include ``ActionCompleted`` and, when
applicable, ``NeedDecayed``, ``ResourceConsumed``, ``ResourceGathered``,
``ResourceProduced``, ``ResourceTraded``, ``RelationshipUpdated``, or
``AgentMoved``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    DEFAULT_AFFINITY_DELTA,
    DEFAULT_DRINK_CONSUME_AMOUNT,
    DEFAULT_DRINK_RESTORE,
    DEFAULT_EAT_CONSUME_AMOUNT,
    DEFAULT_EAT_RESTORE,
    DEFAULT_GATHER_AMOUNT,
    DEFAULT_MOVE_ENERGY_COST,
    DEFAULT_REST_RESTORE,
    DEFAULT_SOCIALIZE_RESTORE,
    DEFAULT_TRUST_DELTA,
    FOOD_RESOURCE,
    WATER_RESOURCE,
    ActionChoice,
    ActionCompleted,
    ActionKind,
    AgentMoved,
    NeedDecayed,
    RelationshipUpdated,
    ResourceConsumed,
    ResourceGathered,
    ResourceProduced,
    ResourceTraded,
    TradeTerms,
    apply_drink,
    apply_eat,
    apply_gather,
    apply_produce,
    apply_rest,
    apply_socialize,
    apply_trade,
    get_bond,
    recipe_by_id,
    relocate,
)
from civitas.domain.actions import ACTION_NEED_TARGET, ACTION_RESOURCE
from civitas.domain.numeric import clamp_unit
from civitas.domain.trading import DEFAULT_TRADE_PRICE, DEFAULT_TRADE_QUANTITY
from civitas.domain.types import NonNegativeInt, PositiveInt, UnitInterval

if TYPE_CHECKING:
    from collections.abc import Sequence

    from civitas.domain import Agent, World
    from civitas.engine.event_bus import EventBus


class ActionConfig(BaseModel):
    """Per-action need restoration amounts and MOVE/GATHER parameters."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    eat: UnitInterval = DEFAULT_EAT_RESTORE
    drink: UnitInterval = DEFAULT_DRINK_RESTORE
    rest: UnitInterval = DEFAULT_REST_RESTORE
    socialize: UnitInterval = DEFAULT_SOCIALIZE_RESTORE
    seek_safety: UnitInterval = 0.10
    idle: UnitInterval = Field(default=0.0, ge=0.0, le=1.0)
    move_energy_cost: UnitInterval = DEFAULT_MOVE_ENERGY_COST
    gather_amount: PositiveInt = DEFAULT_GATHER_AMOUNT
    eat_consume_amount: PositiveInt = DEFAULT_EAT_CONSUME_AMOUNT
    drink_consume_amount: PositiveInt = DEFAULT_DRINK_CONSUME_AMOUNT
    trade_quantity: PositiveInt = DEFAULT_TRADE_QUANTITY
    trade_price: NonNegativeInt = DEFAULT_TRADE_PRICE
    socialize_trust_delta: UnitInterval = DEFAULT_TRUST_DELTA
    socialize_affinity_delta: UnitInterval = DEFAULT_AFFINITY_DELTA

    def restore_for(self, action: ActionKind) -> float:
        """Return the need restoration amount for ``action``.

        Raises:
            ValueError: If ``action`` is not a restorative catalog action.
        """
        mapping = {
            ActionKind.EAT: self.eat,
            ActionKind.DRINK: self.drink,
            ActionKind.REST: self.rest,
            ActionKind.SOCIALIZE: self.socialize,
            ActionKind.SEEK_SAFETY: self.seek_safety,
            ActionKind.IDLE: self.idle,
        }
        try:
            return mapping[action]
        except KeyError as exc:
            msg = f"action {action.value} has no restoration amount"
            raise ValueError(msg) from exc


class ActionExecutor:
    """Apply ``ActionChoice`` results to agents in deterministic order."""

    def __init__(self, config: ActionConfig | None = None) -> None:
        self._config = config if config is not None else ActionConfig()

    @property
    def config(self) -> ActionConfig:
        """Return the immutable executor configuration."""
        return self._config

    def execute(
        self,
        world: World,
        choice: ActionChoice,
        bus: EventBus | None = None,
    ) -> World:
        """Execute a single choice and return the updated world."""
        agent = world.agent_by_id(choice.agent_id)
        if agent is None:
            msg = f"agent id {choice.agent_id.value} not found in world"
            raise ValueError(msg)

        if not agent.is_alive():
            if bus is not None:
                bus.publish(
                    ActionCompleted(
                        tick=world.tick,
                        agent_id=choice.agent_id,
                        action=choice.action.value,
                        success=False,
                    )
                )
            return world

        if choice.action is ActionKind.GATHER:
            world, success = self._apply_gather(world, agent, choice, bus)
        elif choice.action is ActionKind.TRADE:
            world, success = self._apply_trade(world, agent, choice, bus)
        elif choice.action is ActionKind.SOCIALIZE:
            world, success = self._apply_socialize(world, agent, choice, bus)
        else:
            updated_agent, success = self._apply(agent, choice, world, bus)
            if success and updated_agent is not agent:
                world = world.with_agent(updated_agent)

        if bus is not None:
            bus.publish(
                ActionCompleted(
                    tick=world.tick,
                    agent_id=choice.agent_id,
                    action=choice.action.value,
                    success=success,
                )
            )
        return world

    def execute_all(
        self,
        world: World,
        choices: Sequence[ActionChoice],
        bus: EventBus | None = None,
    ) -> World:
        """Execute choices in ascending agent-id order."""
        ordered = sorted(choices, key=lambda choice: choice.agent_id.value)
        for choice in ordered:
            world = self.execute(world, choice, bus=bus)
        return world

    def _apply(
        self,
        agent: Agent,
        choice: ActionChoice,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply non-GATHER/TRADE/SOCIALIZE choice effects; return (agent, success)."""
        action = choice.action
        if action is ActionKind.IDLE:
            return agent, True
        if action is ActionKind.MOVE:
            return self._apply_move(agent, choice, world, bus)
        if action is ActionKind.EAT:
            return self._apply_eat(agent, world, bus)
        if action is ActionKind.DRINK:
            return self._apply_drink(agent, world, bus)
        if action is ActionKind.REST:
            return self._apply_rest(agent, world, bus)
        if action is ActionKind.PRODUCE:
            return self._apply_produce(agent, choice, world, bus)

        need_name = ACTION_NEED_TARGET[action]
        if need_name is None:
            msg = f"action {action.value} has no need target"
            raise ValueError(msg)

        restore = self._config.restore_for(action)
        previous = agent.needs.as_mapping()[need_name]
        current = clamp_unit(previous + restore)
        updated = agent

        if current != previous:
            new_needs = agent.needs.model_copy(update={need_name: current})
            updated = updated.model_copy(update={"needs": new_needs})
            if bus is not None:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=agent.agent_id,
                        need=need_name,
                        previous=previous,
                        current=current,
                    )
                )

        resource = ACTION_RESOURCE[action]
        if resource is not None and updated.inventory.quantity(resource) > 0:
            new_inventory = updated.inventory.remove(resource, 1)
            updated = updated.model_copy(update={"inventory": new_inventory})
            if bus is not None:
                bus.publish(
                    ResourceConsumed(
                        tick=world.tick,
                        agent_id=agent.agent_id,
                        resource=resource,
                        amount=1,
                    )
                )

        return updated, True

    def _apply_eat(
        self,
        agent: Agent,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply inventory-backed EAT; emit consume/need events on success."""
        previous_food = agent.needs.food
        updated = apply_eat(
            agent,
            restore=self._config.eat,
            amount=self._config.eat_consume_amount,
        )
        if updated is None:
            return agent, False

        if bus is not None:
            bus.publish(
                ResourceConsumed(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    resource=FOOD_RESOURCE,
                    amount=self._config.eat_consume_amount,
                )
            )
            if updated.needs.food != previous_food:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=agent.agent_id,
                        need="food",
                        previous=previous_food,
                        current=updated.needs.food,
                    )
                )
        return updated, True

    def _apply_drink(
        self,
        agent: Agent,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply inventory-backed DRINK; emit consume/need events on success."""
        previous_water = agent.needs.water
        updated = apply_drink(
            agent,
            restore=self._config.drink,
            amount=self._config.drink_consume_amount,
        )
        if updated is None:
            return agent, False

        if bus is not None:
            bus.publish(
                ResourceConsumed(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    resource=WATER_RESOURCE,
                    amount=self._config.drink_consume_amount,
                )
            )
            if updated.needs.water != previous_water:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=agent.agent_id,
                        need="water",
                        previous=previous_water,
                        current=updated.needs.water,
                    )
                )
        return updated, True

    def _apply_rest(
        self,
        agent: Agent,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply REST energy recovery; emit NeedDecayed on success."""
        previous_energy = agent.needs.energy
        updated = apply_rest(agent, restore=self._config.rest)
        if updated is None:
            return agent, False

        if bus is not None and updated.needs.energy != previous_energy:
            bus.publish(
                NeedDecayed(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    need="energy",
                    previous=previous_energy,
                    current=updated.needs.energy,
                )
            )
        return updated, True

    def _apply_produce(
        self,
        agent: Agent,
        choice: ActionChoice,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply PRODUCE via domain helper; emit ResourceProduced on success."""
        if choice.target_resource is None:
            return agent, False

        recipe = recipe_by_id(choice.target_resource)
        previous_energy = agent.needs.energy
        updated = apply_produce(agent, choice.target_resource)
        if updated is None or recipe is None:
            return agent, False

        if bus is not None:
            bus.publish(
                ResourceProduced(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    recipe_id=recipe.recipe_id,
                    outputs=tuple(
                        (stack.resource, stack.quantity) for stack in recipe.outputs
                    ),
                )
            )
            if updated.needs.energy != previous_energy:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=agent.agent_id,
                        need="energy",
                        previous=previous_energy,
                        current=updated.needs.energy,
                    )
                )
        return updated, True

    def _apply_move(
        self,
        agent: Agent,
        choice: ActionChoice,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply MOVE using domain relocation; emit AgentMoved on success."""
        if choice.target_location_id is None:
            return agent, False

        from_location_id = agent.location_id
        previous_energy = agent.needs.energy
        updated = relocate(
            world,
            agent,
            choice.target_location_id,
            energy_cost=self._config.move_energy_cost,
        )
        if updated is None:
            return agent, False

        if bus is not None:
            if updated.needs.energy != previous_energy:
                bus.publish(
                    NeedDecayed(
                        tick=world.tick,
                        agent_id=agent.agent_id,
                        need="energy",
                        previous=previous_energy,
                        current=updated.needs.energy,
                    )
                )
            bus.publish(
                AgentMoved(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    from_location_id=from_location_id,
                    to_location_id=updated.location_id,
                )
            )
        return updated, True

    def _apply_gather(
        self,
        world: World,
        agent: Agent,
        choice: ActionChoice,
        bus: EventBus | None,
    ) -> tuple[World, bool]:
        """Apply GATHER via domain helper; emit ResourceGathered on success."""
        if choice.target_resource is None:
            return world, False

        updated = apply_gather(
            world,
            agent,
            choice.target_resource,
            amount=self._config.gather_amount,
        )
        if updated is None:
            return world, False

        if bus is not None:
            bus.publish(
                ResourceGathered(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    location_id=agent.location_id,
                    resource=choice.target_resource,
                    amount=self._config.gather_amount,
                )
            )
        return updated, True

    def _apply_trade(
        self,
        world: World,
        agent: Agent,
        choice: ActionChoice,
        bus: EventBus | None,
    ) -> tuple[World, bool]:
        """Apply TRADE via domain helper; emit ResourceTraded on success."""
        if choice.target_resource is None or choice.target_agent_id is None:
            return world, False

        terms = TradeTerms(
            buyer_id=agent.agent_id,
            seller_id=choice.target_agent_id,
            resource=choice.target_resource,
            quantity=self._config.trade_quantity,
            price=self._config.trade_price,
        )
        updated = apply_trade(world, terms)
        if updated is None:
            return world, False

        if bus is not None:
            bus.publish(
                ResourceTraded(
                    tick=updated.tick,
                    buyer_id=terms.buyer_id,
                    seller_id=terms.seller_id,
                    resource=terms.resource,
                    quantity=terms.quantity,
                    price=terms.price,
                )
            )
        return updated, True

    def _apply_socialize(
        self,
        world: World,
        agent: Agent,
        choice: ActionChoice,
        bus: EventBus | None,
    ) -> tuple[World, bool]:
        """Apply SOCIALIZE via domain helper; emit bond/need events."""
        if choice.target_agent_id is None:
            return world, False

        partner_id = choice.target_agent_id
        partner_before = world.agent_by_id(partner_id)
        actor_created = get_bond(agent, partner_id) is None
        partner_created = (
            partner_before is None or get_bond(partner_before, agent.agent_id) is None
        )
        previous_social = agent.needs.social

        updated = apply_socialize(
            world,
            agent.agent_id,
            partner_id,
            trust_delta=self._config.socialize_trust_delta,
            affinity_delta=self._config.socialize_affinity_delta,
            restore=self._config.socialize,
        )
        if updated is None:
            return world, False

        if bus is not None:
            actor_after = updated.agent_by_id(agent.agent_id)
            partner_after = updated.agent_by_id(partner_id)
            if actor_after is not None and actor_after.needs.social != previous_social:
                bus.publish(
                    NeedDecayed(
                        tick=updated.tick,
                        agent_id=agent.agent_id,
                        need="social",
                        previous=previous_social,
                        current=actor_after.needs.social,
                    )
                )
            actor_bond = (
                get_bond(actor_after, partner_id) if actor_after is not None else None
            )
            if actor_after is not None and actor_bond is not None:
                bus.publish(
                    RelationshipUpdated(
                        tick=updated.tick,
                        from_agent_id=actor_after.agent_id,
                        to_agent_id=actor_bond.other_id,
                        affinity=actor_bond.affinity,
                        trust=actor_bond.trust,
                        created=actor_created,
                    )
                )
            partner_bond = (
                get_bond(partner_after, agent.agent_id)
                if partner_after is not None
                else None
            )
            if partner_after is not None and partner_bond is not None:
                bus.publish(
                    RelationshipUpdated(
                        tick=updated.tick,
                        from_agent_id=partner_after.agent_id,
                        to_agent_id=partner_bond.other_id,
                        affinity=partner_bond.affinity,
                        trust=partner_bond.trust,
                        created=partner_created,
                    )
                )
        return updated, True
