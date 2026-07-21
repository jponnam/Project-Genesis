"""Needs system: homeostatic decay and satisfaction.

This system owns need-level updates only. It does not select actions or
call other systems; callers apply results and observe ``NeedDecayed``
events through the event bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import NeedDecayed, Needs
from civitas.domain.numeric import clamp_unit
from civitas.domain.types import UnitInterval

if TYPE_CHECKING:
    from civitas.domain import Agent, AgentId, World
    from civitas.engine.event_bus import EventBus

NEED_NAMES: tuple[str, ...] = ("food", "water", "energy", "social", "safety")


class NeedsConfig(BaseModel):
    """Per-tick decay rates for each homeostatic need.

    Rates are subtracted from current satisfaction each tick and clamped
    to the unit interval. Defaults are mild so short Phase 1 runs remain
    informative without instantly depleting agents.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    food: UnitInterval = 0.02
    water: UnitInterval = 0.03
    energy: UnitInterval = 0.025
    social: UnitInterval = 0.01
    safety: UnitInterval = 0.005

    def rate_for(self, need: str) -> float:
        """Return the decay rate for ``need``.

        Raises:
            ValueError: If ``need`` is not a known need name.
        """
        rates = self.as_mapping()
        try:
            return rates[need]
        except KeyError as exc:
            msg = f"unknown need: {need}"
            raise ValueError(msg) from exc

    def as_mapping(self) -> dict[str, float]:
        """Return need name → per-tick decay rate."""
        return {
            "food": self.food,
            "water": self.water,
            "energy": self.energy,
            "social": self.social,
            "safety": self.safety,
        }


class NeedsSystem:
    """Apply deterministic need decay and satisfaction to a world."""

    def __init__(self, config: NeedsConfig | None = None) -> None:
        self._config = config if config is not None else NeedsConfig()

    @property
    def config(self) -> NeedsConfig:
        """Return the immutable needs configuration."""
        return self._config

    def apply_decay(self, world: World, bus: EventBus | None = None) -> World:
        """Decay needs for every living agent at ``world.tick``.

        Dead agents are left unchanged. ``NeedDecayed`` events are emitted
        in ascending agent-id order, then need-name order, only when a
        value actually changes.
        """
        updated_agents: list[Agent] = []
        for agent in world.agents:
            if not agent.is_alive():
                updated_agents.append(agent)
                continue
            new_needs, changes = self._decay_needs(agent.needs)
            if not changes:
                updated_agents.append(agent)
                continue
            updated_agents.append(agent.model_copy(update={"needs": new_needs}))
            if bus is not None:
                for need_name, previous, current in changes:
                    bus.publish(
                        NeedDecayed(
                            tick=world.tick,
                            agent_id=agent.agent_id,
                            need=need_name,
                            previous=previous,
                            current=current,
                        )
                    )
        return world.model_copy(update={"agents": tuple(updated_agents)})

    def satisfy(
        self,
        world: World,
        agent_id: AgentId | int,
        need: str,
        amount: float,
        bus: EventBus | None = None,
    ) -> World:
        """Increase ``need`` for one agent by ``amount`` (clamped to 1.0).

        Raises:
            ValueError: If the agent is missing, ``need`` is unknown, or
                ``amount`` is not positive.
        """
        if amount <= 0.0:
            msg = f"satisfy amount must be positive, got {amount}"
            raise ValueError(msg)
        if need not in NEED_NAMES:
            msg = f"unknown need: {need}"
            raise ValueError(msg)

        agent = world.agent_by_id(agent_id)
        if agent is None:
            msg = f"agent id {agent_id} not found in world"
            raise ValueError(msg)

        previous = agent.needs.as_mapping()[need]
        current = clamp_unit(previous + amount)
        if current == previous:
            return world

        new_needs = agent.needs.model_copy(update={need: current})
        updated = world.with_agent(agent.model_copy(update={"needs": new_needs}))
        if bus is not None:
            bus.publish(
                NeedDecayed(
                    tick=world.tick,
                    agent_id=agent.agent_id,
                    need=need,
                    previous=previous,
                    current=current,
                )
            )
        return updated

    def _decay_needs(
        self,
        needs: Needs,
    ) -> tuple[Needs, list[tuple[str, float, float]]]:
        """Return updated needs and the list of (name, previous, current)."""
        updates: dict[str, float] = {}
        changes: list[tuple[str, float, float]] = []
        rates = self._config.as_mapping()
        current_values = needs.as_mapping()
        for name in NEED_NAMES:
            previous = current_values[name]
            current = clamp_unit(previous - rates[name])
            updates[name] = current
            if current != previous:
                changes.append((name, previous, current))
        return Needs(**updates), changes
