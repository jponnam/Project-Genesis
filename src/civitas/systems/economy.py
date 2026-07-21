"""Economy system: money transfers and wealth observation.

Owns economic mutations that emit ``MoneyTransferred`` and tick-level
wealth censuses that emit ``WealthObserved``. Transfer legality and
census math live in domain helpers so other layers can reason about
money without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    MoneyTransferred,
    WealthObserved,
    census_wealth,
    transfer_money,
)

if TYPE_CHECKING:
    from civitas.domain import AgentId, WealthCensus, World
    from civitas.engine.event_bus import EventBus


class EconomyConfig(BaseModel):
    """Parameters controlling economy observation and transfers."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class EconomySystem:
    """Apply money transfers and emit deterministic wealth censuses."""

    def __init__(self, config: EconomyConfig | None = None) -> None:
        self._config = config if config is not None else EconomyConfig()

    @property
    def config(self) -> EconomyConfig:
        """Return the immutable economy configuration."""
        return self._config

    def census(self, world: World) -> WealthCensus:
        """Return a wealth census for ``world``."""
        return census_wealth(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe wealth and optionally emit ``WealthObserved``.

        The world is never modified.
        """
        snap = census_wealth(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                WealthObserved(
                    tick=snap.tick,
                    total=snap.total,
                    alive_total=snap.alive_total,
                    dead_total=snap.dead_total,
                    alive_count=snap.alive_count,
                    mean_alive=snap.mean_alive,
                    min_alive=snap.min_alive,
                    max_alive=snap.max_alive,
                )
            )
        return world

    def transfer(
        self,
        world: World,
        payer_id: AgentId | int,
        payee_id: AgentId | int,
        amount: int,
        bus: EventBus | None = None,
    ) -> World:
        """Transfer ``amount`` from payer to payee when legal.

        Emits ``MoneyTransferred`` on success. Illegal transfers leave the
        world unchanged.
        """
        updated = transfer_money(world, payer_id, payee_id, amount)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            payer = world.agent_by_id(payer_id)
            payee = world.agent_by_id(payee_id)
            if payer is not None and payee is not None:
                bus.publish(
                    MoneyTransferred(
                        tick=updated.tick,
                        from_agent_id=payer.agent_id,
                        to_agent_id=payee.agent_id,
                        amount=amount,
                    )
                )
        return updated
