"""Action executor: apply selected actions to world state.

The executor mutates the world only through immutable ``World`` updates.
It does not call the needs, movement, gathering, or policy systems;
shared catalogs and domain helpers apply effects. Events include
``ActionCompleted`` and, when applicable, ``NeedDecayed``,
``ResourceConsumed``, ``ResourceGathered``, or ``AgentMoved``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    DEFAULT_GATHER_AMOUNT,
    DEFAULT_MOVE_ENERGY_COST,
    ActionChoice,
    ActionCompleted,
    ActionKind,
    AgentMoved,
    NeedDecayed,
    ResourceConsumed,
    ResourceGathered,
    apply_gather,
    relocate,
)
from civitas.domain.actions import ACTION_NEED_TARGET, ACTION_RESOURCE
from civitas.domain.numeric import clamp_unit
from civitas.domain.types import PositiveInt, UnitInterval

if TYPE_CHECKING:
    from collections.abc import Sequence

    from civitas.domain import Agent, World
    from civitas.engine.event_bus import EventBus


class ActionConfig(BaseModel):
    """Per-action need restoration amounts and MOVE/GATHER parameters."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    eat: UnitInterval = 0.25
    drink: UnitInterval = 0.30
    rest: UnitInterval = 0.20
    socialize: UnitInterval = 0.15
    seek_safety: UnitInterval = 0.10
    idle: UnitInterval = Field(default=0.0, ge=0.0, le=1.0)
    move_energy_cost: UnitInterval = DEFAULT_MOVE_ENERGY_COST
    gather_amount: PositiveInt = DEFAULT_GATHER_AMOUNT

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
        """Apply non-GATHER ``choice`` effects; return (agent, success)."""
        action = choice.action
        if action is ActionKind.IDLE:
            return agent, True
        if action is ActionKind.MOVE:
            return self._apply_move(agent, choice, world, bus)

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
