"""Trading helpers for resource-for-money exchanges.

Trades are buyer-initiated: a living buyer pays integer money to a
co-located living seller for inventory stock. Domain helpers keep the
trading system and action executor aligned without systems calling each
other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

from civitas.domain.economy import can_afford, credit_money, debit_money
from civitas.domain.ids import AgentId
from civitas.domain.types import NonEmptyStr, NonNegativeInt, PositiveInt

if TYPE_CHECKING:
    from civitas.domain.world import World

DEFAULT_TRADE_QUANTITY: int = 1
DEFAULT_TRADE_PRICE: int = 1


class TradeTerms(BaseModel):
    """Immutable terms for one bilateral resource purchase."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    buyer_id: AgentId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: PositiveInt = DEFAULT_TRADE_QUANTITY
    price: NonNegativeInt = DEFAULT_TRADE_PRICE

    @model_validator(mode="after")
    def parties_must_differ(self) -> Self:
        """Reject self-dealing trade terms."""
        if self.buyer_id == self.seller_id:
            msg = "buyer_id and seller_id must differ"
            raise ValueError(msg)
        return self


def can_trade(world: World, terms: TradeTerms) -> bool:
    """Return True when ``terms`` can execute against ``world``."""
    buyer = world.agent_by_id(terms.buyer_id)
    seller = world.agent_by_id(terms.seller_id)
    if buyer is None or seller is None:
        return False
    if not buyer.is_alive() or not seller.is_alive():
        return False
    if buyer.location_id != seller.location_id:
        return False
    if seller.inventory.quantity(terms.resource) < terms.quantity:
        return False
    return can_afford(buyer, terms.price)


def apply_trade(world: World, terms: TradeTerms) -> World | None:
    """Execute ``terms`` when legal; return the updated world or ``None``.

    On success the seller loses ``quantity`` of ``resource``, the buyer
    gains it, and ``price`` money moves from buyer to seller.
    """
    if not can_trade(world, terms):
        return None

    buyer = world.agent_by_id(terms.buyer_id)
    seller = world.agent_by_id(terms.seller_id)
    if buyer is None or seller is None:
        return None

    paid = debit_money(buyer, terms.price)
    if paid is None:
        return None
    try:
        seller_inventory = seller.inventory.remove(terms.resource, terms.quantity)
    except ValueError:
        return None
    sold = seller.model_copy(update={"inventory": seller_inventory})
    paid_seller = credit_money(sold, terms.price)
    if paid_seller is None:
        return None
    buyer_inventory = paid.inventory.add(terms.resource, terms.quantity)
    paid_buyer = paid.model_copy(update={"inventory": buyer_inventory})

    world = world.with_agent(paid_buyer)
    return world.with_agent(paid_seller)
