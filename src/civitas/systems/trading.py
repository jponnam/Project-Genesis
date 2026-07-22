"""Trading system: buyer-initiated resource purchases.

Owns trading as a first-class operation that emits ``ResourceTraded``.
Legality and world mutation live in domain helpers so the action executor
can apply TRADE without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    AgentId,
    ResourceTraded,
    TradeTerms,
    apply_trade,
    can_trade,
)
from civitas.domain.trading import DEFAULT_TRADE_PRICE, DEFAULT_TRADE_QUANTITY
from civitas.domain.types import NonNegativeInt, PositiveInt

if TYPE_CHECKING:
    from civitas.domain import World
    from civitas.engine.event_bus import EventBus


class TradingConfig(BaseModel):
    """Parameters controlling default trade size and price."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    quantity: PositiveInt = DEFAULT_TRADE_QUANTITY
    price: NonNegativeInt = DEFAULT_TRADE_PRICE


class TradingSystem:
    """Apply deterministic resource-for-money trades."""

    def __init__(self, config: TradingConfig | None = None) -> None:
        self._config = config if config is not None else TradingConfig()

    @property
    def config(self) -> TradingConfig:
        """Return the immutable trading configuration."""
        return self._config

    def can_trade(
        self,
        world: World,
        buyer_id: AgentId | int,
        seller_id: AgentId | int,
        resource: str,
        *,
        quantity: int | None = None,
        price: int | None = None,
    ) -> bool:
        """Return True when the described trade is legal right now."""
        terms = self._terms(buyer_id, seller_id, resource, quantity, price)
        return can_trade(world, terms)

    def trade(
        self,
        world: World,
        buyer_id: AgentId | int,
        seller_id: AgentId | int,
        resource: str,
        bus: EventBus | None = None,
        *,
        quantity: int | None = None,
        price: int | None = None,
    ) -> World:
        """Execute a trade when legal; emit ``ResourceTraded`` on success.

        Illegal trades leave the world unchanged.
        """
        terms = self._terms(buyer_id, seller_id, resource, quantity, price)
        updated = apply_trade(world, terms)
        if updated is None:
            return world
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
        return updated

    def _terms(
        self,
        buyer_id: AgentId | int,
        seller_id: AgentId | int,
        resource: str,
        quantity: int | None,
        price: int | None,
    ) -> TradeTerms:
        buyer = buyer_id if isinstance(buyer_id, AgentId) else AgentId(value=buyer_id)
        seller = (
            seller_id if isinstance(seller_id, AgentId) else AgentId(value=seller_id)
        )
        return TradeTerms(
            buyer_id=buyer,
            seller_id=seller,
            resource=resource,
            quantity=self._config.quantity if quantity is None else quantity,
            price=self._config.price if price is None else price,
        )
