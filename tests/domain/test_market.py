"""Unit tests for domain market helpers."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_MARKET,
    Agent,
    Inventory,
    ResourceStack,
    SimulationConfig,
    World,
    best_listing,
    can_fill_listing,
    can_post_listing,
    cancel_listing,
    census_markets,
    fill_listing,
    post_listing,
)


def _with_food(agent_id: int, quantity: int, *, money: int = 0) -> Agent:
    agent = Agent.create(agent_id=agent_id, name=f"A-{agent_id}", money=money)
    if quantity <= 0:
        return agent
    return agent.model_copy(
        update={
            "inventory": Inventory(
                stacks=(ResourceStack(resource="food", quantity=quantity),)
            )
        }
    )


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        markets=(CAMP_MARKET,),
        agents=agents,
    )


def test_post_listing_escrows_inventory() -> None:
    """Posting removes goods from the seller and opens a listing."""
    world = _world(_with_food(0, 3, money=0))
    assert can_post_listing(world, 0, 0, "food", 2, 1) is True
    result = post_listing(world, 0, 0, "food", quantity=2, unit_price=1)
    assert result is not None
    updated, listing = result
    seller = updated.agent_by_id(0)
    assert seller is not None
    assert seller.inventory.quantity("food") == 1
    assert listing.quantity == 2
    assert updated.markets[0].listings == (listing,)


def test_fill_listing_transfers_goods_and_money() -> None:
    """Filling pays the seller and restocks the buyer from escrow."""
    world = _world(_with_food(0, 2, money=0), _with_food(1, 0, money=5))
    posted = post_listing(world, 0, 0, "food", quantity=2, unit_price=2)
    assert posted is not None
    world, listing = posted
    assert can_fill_listing(world, 0, listing.listing_id, 1, quantity=1) is True
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    seller = filled.agent_by_id(0)
    assert buyer is not None and seller is not None
    assert buyer.inventory.quantity("food") == 1
    assert buyer.money == 3
    assert seller.money == 2
    assert filled.markets[0].listings[0].quantity == 1


def test_fill_listing_removes_exhausted_offer() -> None:
    """Buying the last units removes the listing from the book."""
    world = _world(_with_food(0, 1, money=0), _with_food(1, 0, money=3))
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=1)
    assert posted is not None
    world, listing = posted
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    assert filled.markets[0].listings == ()


def test_cancel_listing_returns_escrow() -> None:
    """Cancelling restores escrowed goods to the seller."""
    world = _world(_with_food(0, 2, money=0))
    posted = post_listing(world, 0, 0, "food", quantity=2, unit_price=1)
    assert posted is not None
    world, listing = posted
    cancelled = cancel_listing(world, 0, listing.listing_id, 0)
    assert cancelled is not None
    seller = cancelled.agent_by_id(0)
    assert seller is not None
    assert seller.inventory.quantity("food") == 2
    assert cancelled.markets[0].listings == ()


def test_best_listing_prefers_lowest_unit_price() -> None:
    """Cheapest listing wins; ties break by listing id."""
    world = _world(_with_food(0, 5, money=0))
    first = post_listing(world, 0, 0, "food", quantity=1, unit_price=3)
    assert first is not None
    world, _listing_a = first
    second = post_listing(world, 0, 0, "food", quantity=1, unit_price=1)
    assert second is not None
    world, listing_b = second
    assert best_listing(world.markets[0], "food") == listing_b


def test_census_markets_counts_open_book() -> None:
    """Market census reports venue and listing depth."""
    world = _world(_with_food(0, 2, money=0))
    posted = post_listing(world, 0, 0, "food", quantity=2, unit_price=1)
    assert posted is not None
    world, _listing = posted
    snap = census_markets(world)
    assert snap.market_count == 1
    assert snap.listing_count == 1
    assert snap.total_units == 2
    assert snap.market_listings == ((0, 1),)
