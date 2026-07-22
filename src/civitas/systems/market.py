"""Market system: escrowed listings and open-book observation.

Owns market mutations that emit listing events and tick-level book
censuses that emit ``MarketObserved``. Legality and world updates live
in domain helpers so other layers can reason about markets without
calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import (
    ListingCancelled,
    ListingFilled,
    ListingPosted,
    MarketObserved,
    can_cancel_listing,
    can_fill_listing,
    can_post_listing,
    cancel_listing,
    census_markets,
    fill_listing,
    market_by_id,
    post_listing,
)
from civitas.domain.market import DEFAULT_LISTING_QUANTITY, DEFAULT_UNIT_PRICE
from civitas.domain.types import NonNegativeInt, PositiveInt

if TYPE_CHECKING:
    from civitas.domain import AgentId, ListingId, MarketCensus, MarketId, World
    from civitas.engine.event_bus import EventBus


class MarketConfig(BaseModel):
    """Parameters controlling market observation and default listing size."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True
    default_quantity: PositiveInt = DEFAULT_LISTING_QUANTITY
    default_unit_price: NonNegativeInt = DEFAULT_UNIT_PRICE


class MarketSystem:
    """Post, fill, and cancel listings; observe open-book depth."""

    def __init__(self, config: MarketConfig | None = None) -> None:
        self._config = config if config is not None else MarketConfig()

    @property
    def config(self) -> MarketConfig:
        """Return the immutable market configuration."""
        return self._config

    def census(self, world: World) -> MarketCensus:
        """Return an open-book census for ``world``."""
        return census_markets(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe markets and optionally emit ``MarketObserved``.

        The world is never modified.
        """
        snap = census_markets(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                MarketObserved(
                    tick=snap.tick,
                    market_count=snap.market_count,
                    listing_count=snap.listing_count,
                    total_units=snap.total_units,
                    market_listings=snap.market_listings,
                )
            )
        return world

    def post_listing(
        self,
        world: World,
        market_id: MarketId | int,
        seller_id: AgentId | int,
        resource: str,
        bus: EventBus | None = None,
        *,
        quantity: int | None = None,
        unit_price: int | None = None,
    ) -> World:
        """Escrow a sell listing when legal; emit ``ListingPosted`` on success."""
        qty = self._config.default_quantity if quantity is None else quantity
        price = self._config.default_unit_price if unit_price is None else unit_price
        if not can_post_listing(world, market_id, seller_id, resource, qty, price):
            return world
        result = post_listing(
            world,
            market_id,
            seller_id,
            resource,
            quantity=qty,
            unit_price=price,
        )
        if result is None:
            return world
        world, listing = result
        if bus is not None and self._config.emit_events:
            market = market_by_id(world, market_id)
            if market is not None:
                bus.publish(
                    ListingPosted(
                        tick=world.tick,
                        market_id=market.market_id,
                        listing_id=listing.listing_id,
                        seller_id=listing.seller_id,
                        resource=listing.resource,
                        quantity=listing.quantity,
                        unit_price=listing.unit_price,
                    )
                )
        return world

    def fill_listing(
        self,
        world: World,
        market_id: MarketId | int,
        listing_id: ListingId | int,
        buyer_id: AgentId | int,
        bus: EventBus | None = None,
        *,
        quantity: int | None = None,
    ) -> World:
        """Fill a listing when legal; emit ``ListingFilled`` on success."""
        qty = self._config.default_quantity if quantity is None else quantity
        market = market_by_id(world, market_id)
        buyer = world.agent_by_id(buyer_id)
        listing = None if market is None else market.listing_by_id(listing_id)
        if market is None or buyer is None or listing is None:
            return world
        if not can_fill_listing(world, market_id, listing_id, buyer_id, qty):
            return world
        updated = fill_listing(world, market_id, listing_id, buyer_id, quantity=qty)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            bus.publish(
                ListingFilled(
                    tick=updated.tick,
                    market_id=market.market_id,
                    listing_id=listing.listing_id,
                    buyer_id=buyer.agent_id,
                    seller_id=listing.seller_id,
                    resource=listing.resource,
                    quantity=qty,
                    unit_price=listing.unit_price,
                    total_price=listing.unit_price * qty,
                )
            )
        return updated

    def cancel_listing(
        self,
        world: World,
        market_id: MarketId | int,
        listing_id: ListingId | int,
        seller_id: AgentId | int,
        bus: EventBus | None = None,
    ) -> World:
        """Cancel a listing when legal; emit ``ListingCancelled`` on success."""
        market = market_by_id(world, market_id)
        listing = None if market is None else market.listing_by_id(listing_id)
        if market is None or listing is None:
            return world
        if not can_cancel_listing(world, market_id, listing_id, seller_id):
            return world
        updated = cancel_listing(world, market_id, listing_id, seller_id)
        if updated is None:
            return world
        if bus is not None and self._config.emit_events:
            bus.publish(
                ListingCancelled(
                    tick=updated.tick,
                    market_id=market.market_id,
                    listing_id=listing.listing_id,
                    seller_id=listing.seller_id,
                    resource=listing.resource,
                    quantity=listing.quantity,
                )
            )
        return updated
