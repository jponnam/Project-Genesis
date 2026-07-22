"""Tax system: per-tick levies into public treasuries.

Owns taxation as a first-class tick concern that emits ``TaxCollected``.
Due amounts and world mutation live in domain helpers so other layers can
reason about taxes without calling this system. Collections credit the
governing polity's treasury when the payer is under a government
jurisdiction, falling back to ``World.treasury`` otherwise.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import TaxCollected, collectable_tax, levy_taxes, resolve_tax_params
from civitas.domain.taxes import DEFAULT_FLAT_AMOUNT, DEFAULT_RATE_BPS
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain import AgentId, World
    from civitas.engine.event_bus import EventBus


class TaxConfig(BaseModel):
    """Parameters controlling system-driven tax collection.

    Taxes are disabled by default so research runs stay tax-free until a
    levy is explicitly enabled. When enabled, active ``TAX_SCHEDULE`` laws
    override ``flat_amount`` / ``rate_bps`` per agent's government.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    enabled: bool = False
    flat_amount: NonNegativeInt = DEFAULT_FLAT_AMOUNT
    rate_bps: NonNegativeInt = DEFAULT_RATE_BPS
    emit_events: bool = True


class TaxSystem:
    """Apply deterministic taxes after births settle each tick."""

    def __init__(self, config: TaxConfig | None = None) -> None:
        self._config = config if config is not None else TaxConfig()

    @property
    def config(self) -> TaxConfig:
        """Return the immutable tax configuration."""
        return self._config

    def tax_due(self, world: World, agent_id: AgentId | int) -> int:
        """Return the collectable tax for ``agent_id`` under laws/config."""
        agent = world.agent_by_id(agent_id)
        if agent is None:
            return 0
        flat_amount, rate_bps = resolve_tax_params(
            world,
            agent,
            flat_amount=self._config.flat_amount,
            rate_bps=self._config.rate_bps,
        )
        return collectable_tax(
            agent,
            flat_amount=flat_amount,
            rate_bps=rate_bps,
        )

    def apply_taxes(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Collect taxes from living agents; emit ``TaxCollected`` per payer.

        When disabled, the world is returned unchanged.
        """
        if not self._config.enabled:
            return world

        world, collections = levy_taxes(
            world,
            flat_amount=self._config.flat_amount,
            rate_bps=self._config.rate_bps,
        )
        if bus is not None and self._config.emit_events:
            for agent_id, amount, treasury_after, government_id in collections:
                bus.publish(
                    TaxCollected(
                        tick=world.tick,
                        agent_id=agent_id,
                        amount=amount,
                        treasury_after=treasury_after,
                        government_id=government_id,
                    )
                )
        return world
