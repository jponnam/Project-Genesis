"""Price quotes derived from market books and last trades.

Quotes are read-only observations: best ask from open listings, last
trade marks from fills, and a suggested listing price for sellers.
Systems must not invent floating-point prices — all values are integers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import MarketId
from civitas.domain.market import DEFAULT_UNIT_PRICE, best_listing
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.market import Market
    from civitas.domain.world import World


class PriceQuote(BaseModel):
    """Immutable price signal for one resource on one market."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    market_id: MarketId
    resource: NonEmptyStr
    best_ask: NonNegativeInt | None = Field(
        default=None,
        description="Lowest open listing unit price, or None if no asks.",
    )
    ask_quantity: NonNegativeInt = Field(
        description="Total units offered at the best ask price."
    )
    last_trade: NonNegativeInt | None = Field(
        default=None,
        description="Most recent fill unit price, or None if never traded.",
    )
    listing_count: NonNegativeInt
    total_units: NonNegativeInt
    suggested_unit_price: NonNegativeInt = Field(
        description="Seller guidance: last trade, else best ask, else default."
    )


class PriceCensus(BaseModel):
    """Immutable price snapshot across all markets and resources."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    quote_count: NonNegativeInt
    quotes: tuple[PriceQuote, ...] = ()


def suggested_unit_price(market: Market, resource: str) -> int:
    """Return seller guidance price for ``resource`` on ``market``.

    Preference order: last trade, then best ask, then ``DEFAULT_UNIT_PRICE``.
    """
    last = market.last_trade_price(resource)
    if last is not None:
        return last
    ask = best_listing(market, resource)
    if ask is not None:
        return ask.unit_price
    return DEFAULT_UNIT_PRICE


def quote_resource(market: Market, resource: str) -> PriceQuote:
    """Build a price quote for ``resource`` on ``market``."""
    resource_listings = [
        listing for listing in market.listings if listing.resource == resource
    ]
    ask = best_listing(market, resource)
    if ask is None:
        best_ask = None
        ask_quantity = 0
    else:
        best_ask = ask.unit_price
        ask_quantity = sum(
            listing.quantity
            for listing in resource_listings
            if listing.unit_price == ask.unit_price
        )
    return PriceQuote(
        market_id=market.market_id,
        resource=resource,
        best_ask=best_ask,
        ask_quantity=ask_quantity,
        last_trade=market.last_trade_price(resource),
        listing_count=len(resource_listings),
        total_units=sum(listing.quantity for listing in resource_listings),
        suggested_unit_price=suggested_unit_price(market, resource),
    )


def resources_with_prices(market: Market) -> tuple[str, ...]:
    """Return sorted resources that have listings or last-trade marks."""
    names = {listing.resource for listing in market.listings}
    names.update(trade.resource for trade in market.last_trades)
    return tuple(sorted(names))


def census_prices(world: World) -> PriceCensus:
    """Build a deterministic price census for every priced resource."""
    quotes: list[PriceQuote] = []
    for market in world.markets:
        for resource in resources_with_prices(market):
            quotes.append(quote_resource(market, resource))
    quotes.sort(key=lambda quote: (quote.market_id.value, quote.resource))
    return PriceCensus(
        tick=world.tick,
        quote_count=len(quotes),
        quotes=tuple(quotes),
    )
