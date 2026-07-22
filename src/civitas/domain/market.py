"""Market venues and escrowed sell listings.

A market is anchored to a location. Sellers post listings that escrow
inventory onto the book; buyers fill listings by paying integer money.
Filled trades update per-resource last-trade prices used by the prices
layer. Domain helpers keep the market system aligned without systems
calling each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

from civitas.domain.economy import can_afford, credit_money, debit_money
from civitas.domain.ids import AgentId, ListingId, LocationId, MarketId
from civitas.domain.location import CAMP_LOCATION
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt, PositiveInt

if TYPE_CHECKING:
    from civitas.domain.world import World

DEFAULT_LISTING_QUANTITY: int = 1
DEFAULT_UNIT_PRICE: int = 1


class SellListing(BaseModel):
    """One escrowed sell offer on a market book."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    listing_id: ListingId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: PositiveInt
    unit_price: NonNegativeInt = DEFAULT_UNIT_PRICE


class LastTrade(BaseModel):
    """Most recent fill price for one resource on a market."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    resource: NonEmptyStr
    unit_price: NonNegativeInt


class Market(BaseModel):
    """A market venue with an ordered sell book and last-trade marks."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    market_id: MarketId
    location_id: LocationId
    name: NonEmptyStr
    listings: tuple[SellListing, ...] = ()
    last_trades: tuple[LastTrade, ...] = ()

    @model_validator(mode="after")
    def listings_and_trades_must_be_consistent(self) -> Self:
        """Reject duplicate/unsorted listings or last-trade resources."""
        ids = [listing.listing_id.value for listing in self.listings]
        if len(ids) != len(set(ids)):
            msg = "market listing ids must be unique"
            raise ValueError(msg)
        if ids != sorted(ids):
            msg = "market listings must be ordered by ascending listing_id"
            raise ValueError(msg)

        resources = [trade.resource for trade in self.last_trades]
        if len(resources) != len(set(resources)):
            msg = "market last_trades resources must be unique"
            raise ValueError(msg)
        if resources != sorted(resources):
            msg = "market last_trades must be ordered by resource name"
            raise ValueError(msg)
        return self

    @classmethod
    def create(
        cls,
        market_id: int,
        location_id: int,
        name: str,
        *,
        listings: tuple[SellListing, ...] = (),
        last_trades: tuple[LastTrade, ...] = (),
    ) -> Market:
        """Construct a validated market from primitive fields."""
        return cls(
            market_id=MarketId(value=market_id),
            location_id=LocationId(value=location_id),
            name=name,
            listings=listings,
            last_trades=last_trades,
        )

    def listing_by_id(self, listing_id: ListingId | int) -> SellListing | None:
        """Return the listing with ``listing_id``, or ``None``."""
        target = (
            listing_id
            if isinstance(listing_id, ListingId)
            else ListingId(value=listing_id)
        )
        for listing in self.listings:
            if listing.listing_id == target:
                return listing
        return None

    def last_trade_price(self, resource: str) -> int | None:
        """Return the last fill unit price for ``resource``, if any."""
        for trade in self.last_trades:
            if trade.resource == resource:
                return trade.unit_price
        return None

    def with_listings(self, listings: tuple[SellListing, ...]) -> Market:
        """Return this market with a replaced listing book."""
        return self.model_copy(update={"listings": listings})

    def with_last_trade(self, resource: str, unit_price: int) -> Market:
        """Return this market with an upserted last-trade mark."""
        if unit_price < 0:
            msg = f"unit_price must be >= 0, got {unit_price}"
            raise ValueError(msg)
        updated = [trade for trade in self.last_trades if trade.resource != resource]
        updated.append(LastTrade(resource=resource, unit_price=unit_price))
        updated.sort(key=lambda trade: trade.resource)
        return self.model_copy(update={"last_trades": tuple(updated)})


class MarketCensus(BaseModel):
    """Immutable open-book snapshot across all markets."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    market_count: NonNegativeInt
    listing_count: NonNegativeInt
    total_units: NonNegativeInt
    # (market_id, listing_count) pairs in ascending market_id order.
    market_listings: tuple[tuple[int, int], ...] = ()


# Canonical camp market used by the world factory.
CAMP_MARKET: Market = Market.create(
    0,
    CAMP_LOCATION.location_id.value,
    "Camp Market",
)


def default_markets() -> tuple[Market, ...]:
    """Return the canonical initial market set."""
    return (CAMP_MARKET,)


def next_listing_id(market: Market) -> int:
    """Return the next unused listing id for ``market``."""
    if not market.listings:
        return 0
    return max(listing.listing_id.value for listing in market.listings) + 1


def market_by_id(world: World, market_id: MarketId | int) -> Market | None:
    """Return the market with ``market_id``, or ``None``."""
    target = market_id if isinstance(market_id, MarketId) else MarketId(value=market_id)
    for market in world.markets:
        if market.market_id == target:
            return market
    return None


def market_at(world: World, location_id: LocationId | int) -> Market | None:
    """Return the market at ``location_id``, or ``None`` if absent."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    for market in world.markets:
        if market.location_id == target:
            return market
    return None


def best_listing(
    market: Market,
    resource: str,
    *,
    max_unit_price: int | None = None,
) -> SellListing | None:
    """Return the cheapest listing for ``resource``, ties by listing id."""
    candidates = [
        listing
        for listing in market.listings
        if listing.resource == resource
        and (max_unit_price is None or listing.unit_price <= max_unit_price)
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda listing: (listing.unit_price, listing.listing_id.value),
    )


def can_post_listing(
    world: World,
    market_id: MarketId | int,
    seller_id: AgentId | int,
    resource: str,
    quantity: int,
    unit_price: int,
) -> bool:
    """Return True when the seller can escrow ``quantity`` onto the market."""
    if quantity < 1 or unit_price < 0:
        return False
    market = market_by_id(world, market_id)
    seller = world.agent_by_id(seller_id)
    if market is None or seller is None:
        return False
    if not seller.is_alive():
        return False
    if seller.location_id != market.location_id:
        return False
    return seller.inventory.quantity(resource) >= quantity


def post_listing(
    world: World,
    market_id: MarketId | int,
    seller_id: AgentId | int,
    resource: str,
    quantity: int = DEFAULT_LISTING_QUANTITY,
    unit_price: int = DEFAULT_UNIT_PRICE,
) -> tuple[World, SellListing] | None:
    """Escrow goods from the seller onto a new market listing."""
    if not can_post_listing(
        world, market_id, seller_id, resource, quantity, unit_price
    ):
        return None
    market = market_by_id(world, market_id)
    seller = world.agent_by_id(seller_id)
    if market is None or seller is None:
        return None
    try:
        new_inventory = seller.inventory.remove(resource, quantity)
    except ValueError:
        return None
    listing = SellListing(
        listing_id=ListingId(value=next_listing_id(market)),
        seller_id=seller.agent_id,
        resource=resource,
        quantity=quantity,
        unit_price=unit_price,
    )
    updated_seller = seller.model_copy(update={"inventory": new_inventory})
    updated_market = market.with_listings((*market.listings, listing))
    world = world.with_agent(updated_seller)
    return world.with_market(updated_market), listing


def can_fill_listing(
    world: World,
    market_id: MarketId | int,
    listing_id: ListingId | int,
    buyer_id: AgentId | int,
    quantity: int = DEFAULT_LISTING_QUANTITY,
) -> bool:
    """Return True when the buyer can purchase ``quantity`` from the listing."""
    if quantity < 1:
        return False
    market = market_by_id(world, market_id)
    buyer = world.agent_by_id(buyer_id)
    if market is None or buyer is None:
        return False
    listing = market.listing_by_id(listing_id)
    if listing is None:
        return False
    if not buyer.is_alive():
        return False
    if buyer.location_id != market.location_id:
        return False
    if buyer.agent_id == listing.seller_id:
        return False
    if listing.quantity < quantity:
        return False
    seller = world.agent_by_id(listing.seller_id)
    if seller is None or not seller.is_alive():
        return False
    total_price = listing.unit_price * quantity
    return can_afford(buyer, total_price)


def fill_listing(
    world: World,
    market_id: MarketId | int,
    listing_id: ListingId | int,
    buyer_id: AgentId | int,
    quantity: int = DEFAULT_LISTING_QUANTITY,
) -> World | None:
    """Fill ``quantity`` from a listing; pay the seller and restock the buyer."""
    if not can_fill_listing(world, market_id, listing_id, buyer_id, quantity):
        return None
    market = market_by_id(world, market_id)
    buyer = world.agent_by_id(buyer_id)
    if market is None or buyer is None:
        return None
    listing = market.listing_by_id(listing_id)
    if listing is None:
        return None
    seller = world.agent_by_id(listing.seller_id)
    if seller is None:
        return None

    total_price = listing.unit_price * quantity
    paid_buyer = debit_money(buyer, total_price)
    if paid_buyer is None:
        return None
    paid_seller = credit_money(seller, total_price)
    if paid_seller is None:
        return None
    stocked_buyer = paid_buyer.model_copy(
        update={"inventory": paid_buyer.inventory.add(listing.resource, quantity)}
    )

    remaining = listing.quantity - quantity
    if remaining == 0:
        new_listings = tuple(
            item for item in market.listings if item.listing_id != listing.listing_id
        )
    else:
        reduced = listing.model_copy(update={"quantity": remaining})
        new_listings = tuple(
            reduced if item.listing_id == listing.listing_id else item
            for item in market.listings
        )

    world = world.with_agent(stocked_buyer)
    world = world.with_agent(paid_seller)
    updated_market = market.with_listings(new_listings).with_last_trade(
        listing.resource,
        listing.unit_price,
    )
    return world.with_market(updated_market)


def can_cancel_listing(
    world: World,
    market_id: MarketId | int,
    listing_id: ListingId | int,
    seller_id: AgentId | int,
) -> bool:
    """Return True when the seller may cancel their own open listing."""
    market = market_by_id(world, market_id)
    seller = world.agent_by_id(seller_id)
    if market is None or seller is None:
        return False
    listing = market.listing_by_id(listing_id)
    if listing is None:
        return False
    if listing.seller_id != seller.agent_id:
        return False
    return seller.is_alive()


def cancel_listing(
    world: World,
    market_id: MarketId | int,
    listing_id: ListingId | int,
    seller_id: AgentId | int,
) -> World | None:
    """Cancel a listing and return escrowed goods to the living seller."""
    if not can_cancel_listing(world, market_id, listing_id, seller_id):
        return None
    market = market_by_id(world, market_id)
    seller = world.agent_by_id(seller_id)
    if market is None or seller is None:
        return None
    listing = market.listing_by_id(listing_id)
    if listing is None:
        return None
    restored = seller.model_copy(
        update={"inventory": seller.inventory.add(listing.resource, listing.quantity)}
    )
    new_listings = tuple(
        item for item in market.listings if item.listing_id != listing.listing_id
    )
    world = world.with_agent(restored)
    return world.with_market(market.with_listings(new_listings))


def census_markets(world: World) -> MarketCensus:
    """Build a deterministic open-book census for ``world``."""
    listing_count = 0
    total_units = 0
    market_listings: list[tuple[int, int]] = []
    for market in world.markets:
        count = len(market.listings)
        listing_count += count
        total_units += sum(listing.quantity for listing in market.listings)
        market_listings.append((market.market_id.value, count))
    return MarketCensus(
        tick=world.tick,
        market_count=len(world.markets),
        listing_count=listing_count,
        total_units=total_units,
        market_listings=tuple(market_listings),
    )
