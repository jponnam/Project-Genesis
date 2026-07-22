"""Unit tests for the MarketSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_MARKET,
    Agent,
    Government,
    Inventory,
    Law,
    LawKind,
    ListingCancelled,
    ListingFilled,
    ListingPosted,
    MarketFeeCollected,
    MarketObserved,
    ResourceStack,
    SimulationConfig,
    World,
    society_money_total,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import MarketConfig, MarketSystem


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
) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        markets=(CAMP_MARKET,),
        governments=governments,
        laws=laws,
        agents=agents,
    )


def test_observe_emits_market_observed() -> None:
    """observe publishes one open-book census without mutating the world."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = MarketSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, MarketObserved)]
    assert len(events) == 1
    assert events[0].market_count == 1
    assert events[0].listing_count == 0


def test_post_fill_cancel_emit_listing_events() -> None:
    """MarketSystem listing ops emit posted/filled/cancelled events."""
    system = MarketSystem()
    bus = EventBus()
    world = _world(_with_food(0, 2, money=0), _with_food(1, 0, money=4))
    world = system.post_listing(world, 0, 0, "food", bus=bus, quantity=2, unit_price=1)
    posted = [event for event in bus.history if isinstance(event, ListingPosted)]
    assert len(posted) == 1
    listing_id = posted[0].listing_id

    world = system.fill_listing(world, 0, listing_id, 1, bus=bus, quantity=1)
    filled = [event for event in bus.history if isinstance(event, ListingFilled)]
    assert len(filled) == 1
    assert filled[0].total_price == 1

    world = system.cancel_listing(world, 0, listing_id, 0, bus=bus)
    cancelled = [event for event in bus.history if isinstance(event, ListingCancelled)]
    assert len(cancelled) == 1
    seller = world.agent_by_id(0)
    assert seller is not None
    assert seller.inventory.quantity("food") == 1


def test_observe_can_suppress_events() -> None:
    """MarketConfig.emit_events=False skips publishing."""
    world = WorldFactory().create(SimulationConfig(seed=1, agent_count=1))
    bus = EventBus()
    MarketSystem(MarketConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_fill_emits_market_fee_collected() -> None:
    """MarketSystem emits MarketFeeCollected when a MARKET_FEE applies."""
    government = Government.create(0, "Camp", 0, (0,))
    fee = Law.create(0, 0, "Stall Fee", LawKind.MARKET_FEE, flat_amount=1)
    system = MarketSystem()
    bus = EventBus()
    world = _world(
        _with_food(0, 1, money=0),
        _with_food(1, 0, money=4),
        governments=(government,),
        laws=(fee,),
    )
    world = system.post_listing(world, 0, 0, "food", bus=bus, quantity=1, unit_price=2)
    listing_id = world.markets[0].listings[0].listing_id
    initial = society_money_total(world)
    world = system.fill_listing(world, 0, listing_id, 1, bus=bus, quantity=1)
    fees = [event for event in bus.history if isinstance(event, MarketFeeCollected)]
    assert len(fees) == 1
    assert fees[0].amount == 1
    assert fees[0].treasury_after == 1
    assert fees[0].government_id == government.government_id
    assert world.government_by_id(0).treasury == 1  # type: ignore[union-attr]
    assert society_money_total(world) == initial
