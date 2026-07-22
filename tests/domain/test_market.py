"""Unit tests for domain market helpers."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_MARKET,
    Agent,
    City,
    CityKind,
    Government,
    Institution,
    InstitutionKind,
    Inventory,
    Law,
    LawKind,
    ResourceStack,
    SimulationConfig,
    World,
    best_listing,
    can_fill_listing,
    can_post_listing,
    cancel_listing,
    census_markets,
    effective_market_fee,
    fill_listing,
    market_fee_for,
    post_listing,
    society_money_total,
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


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (),
    laws: tuple[Law, ...] = (),
    institutions: tuple[Institution, ...] = (),
    cities: tuple[City, ...] = (),
    treasury: int = 0,
) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        markets=(CAMP_MARKET,),
        governments=governments,
        laws=laws,
        institutions=institutions,
        cities=cities,
        agents=agents,
        treasury=treasury,
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
    assert filled.markets[0].last_trade_price("food") == 2


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


def test_fill_listing_with_market_fee_credits_government() -> None:
    """Active MARKET_FEE debits buyer once per fill into the polity treasury."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1)
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=4),
        governments=(government,),
        laws=(fee,),
    )
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=2)
    assert posted is not None
    world, listing = posted
    initial = society_money_total(world)
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    seller = filled.agent_by_id(0)
    assert buyer is not None and seller is not None
    assert buyer.money == 1  # 4 - 2 price - 1 fee
    assert seller.money == 2
    assert filled.government_by_id(0).treasury == 1  # type: ignore[union-attr]
    assert filled.treasury == 0
    assert society_money_total(filled) == initial


def test_fill_listing_fails_when_buyer_cannot_afford_fee() -> None:
    """Fill fails when price + fee exceeds buyer money."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2)
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=2),
        governments=(government,),
        laws=(fee,),
    )
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=2)
    assert posted is not None
    world, listing = posted
    assert can_fill_listing(world, 0, listing.listing_id, 1, quantity=1) is False
    assert fill_listing(world, 0, listing.listing_id, 1, quantity=1) is None


def test_fill_listing_without_government_skips_fee() -> None:
    """Ungoverned markets charge no fee; world treasury stays put."""
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=3),
        treasury=5,
    )
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=1)
    assert posted is not None
    world, listing = posted
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    assert buyer is not None
    assert buyer.money == 2
    assert filled.treasury == 5


def test_bureaucracy_reduces_market_fee_on_fill() -> None:
    """Active bureaucracy at the market seat discounts the fill fee by 1."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2)
    bureaucracy = Institution.create(
        0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
    )
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=4),
        governments=(government,),
        laws=(fee,),
        institutions=(bureaucracy,),
    )
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 1
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=2)
    assert posted is not None
    world, listing = posted
    initial = society_money_total(world)
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    seller = filled.agent_by_id(0)
    assert buyer is not None and seller is not None
    assert buyer.money == 1  # 4 - 2 price - 1 discounted fee
    assert seller.money == 2
    assert filled.government_by_id(0).treasury == 1  # type: ignore[union-attr]
    assert society_money_total(filled) == initial


def test_bureaucracy_market_fee_discount_floors_at_zero() -> None:
    """Bureaucracy discount cannot drive the effective market fee below zero."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1)
    bureaucracy = Institution.create(
        0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
    )
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=3),
        governments=(government,),
        laws=(fee,),
        institutions=(bureaucracy,),
    )
    assert market_fee_for(world, 0) == 1
    assert effective_market_fee(world, 0) == 0
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=2)
    assert posted is not None
    world, listing = posted
    initial = society_money_total(world)
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    assert buyer is not None
    assert buyer.money == 1  # 3 - 2 price - 0 fee
    assert filled.government_by_id(0).treasury == 0  # type: ignore[union-attr]
    assert society_money_total(filled) == initial


def test_bureaucracy_without_market_fee_law_stays_zero() -> None:
    """Bureaucracy alone does not invent a negative or positive fee."""
    government = Government.create(0, "Camp", 0, (0,))
    bureaucracy = Institution.create(
        0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
    )
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=3),
        governments=(government,),
        institutions=(bureaucracy,),
    )
    assert market_fee_for(world, 0) == 0
    assert effective_market_fee(world, 0) == 0


def test_harbor_reduces_market_fee_on_fill() -> None:
    """Active harbor at the market seat discounts the fill fee by 1."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=2)
    harbor = City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR)
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=4),
        governments=(government,),
        laws=(fee,),
        cities=(harbor,),
    )
    assert market_fee_for(world, 0) == 2
    assert effective_market_fee(world, 0) == 1
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=2)
    assert posted is not None
    world, listing = posted
    initial = society_money_total(world)
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    seller = filled.agent_by_id(0)
    assert buyer is not None and seller is not None
    assert buyer.money == 1  # 4 - 2 price - 1 discounted fee
    assert seller.money == 2
    assert filled.government_by_id(0).treasury == 1  # type: ignore[union-attr]
    assert society_money_total(filled) == initial


def test_harbor_and_bureaucracy_stack_market_fee_on_fill() -> None:
    """Harbor and bureaucracy discounts stack on market fills."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=3)
    harbor = City.create(0, 0, 0, "Camp Harbor", CityKind.HARBOR)
    bureaucracy = Institution.create(
        0, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY
    )
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=5),
        governments=(government,),
        laws=(fee,),
        cities=(harbor,),
        institutions=(bureaucracy,),
    )
    assert market_fee_for(world, 0) == 3
    assert effective_market_fee(world, 0) == 1
    posted = post_listing(world, 0, 0, "food", quantity=1, unit_price=2)
    assert posted is not None
    world, listing = posted
    initial = society_money_total(world)
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    buyer = filled.agent_by_id(1)
    seller = filled.agent_by_id(0)
    assert buyer is not None and seller is not None
    assert buyer.money == 2  # 5 - 2 price - 1 stacked discounted fee
    assert seller.money == 2
    assert filled.government_by_id(0).treasury == 1  # type: ignore[union-attr]
    assert society_money_total(filled) == initial
