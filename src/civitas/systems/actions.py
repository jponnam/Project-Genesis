"""Action executor: apply selected actions to world state.

The executor mutates the world only through immutable ``World`` updates.
It does not call the needs system or utility policy; shared catalogs live
in the domain layer. Effects emit ``ActionCompleted``, and when applicable
``NeedDecayed`` / ``ResourceConsumed``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain import (
    ActionChoice,
    ActionCompleted,
    ActionKind,
    NeedDecayed,
    ResourceConsumed,
)
from civitas.domain.actions import ACTION_NEED_TARGET, ACTION_RESOURCE
from civitas.domain.numeric import clamp_unit
from civitas.domain.types import UnitInterval

if TYPE_CHECKING:
    from collections.abc import Sequence

    from civitas.domain import Agent, World
    from civitas.engine.event_bus import EventBus


class ActionConfig(BaseModel):
    """Per-action need restoration amounts on the unit interval."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    eat: UnitInterval = 0.25
    drink: UnitInterval = 0.30
    rest: UnitInterval = 0.20
    socialize: UnitInterval = 0.15
    seek_safety: UnitInterval = 0.10
    idle: UnitInterval = Field(default=0.0, ge=0.0, le=1.0)

    def restore_for(self, action: ActionKind) -> float:
        """Return the need restoration amount for ``action``."""
        mapping = {
            ActionKind.EAT: self.eat,
            ActionKind.DRINK: self.drink,
            ActionKind.REST: self.rest,
            ActionKind.SOCIALIZE: self.socialize,
            ActionKind.SEEK_SAFETY: self.seek_safety,
            ActionKind.IDLE: self.idle,
        }
        return mapping[action]


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

        updated_agent, success = self._apply(agent, choice.action, world, bus)
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
        action: ActionKind,
        world: World,
        bus: EventBus | None,
    ) -> tuple[Agent, bool]:
        """Apply ``action`` effects to ``agent``; return (agent, success)."""
        if action is ActionKind.IDLE:
            return agent, True

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
