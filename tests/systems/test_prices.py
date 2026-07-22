"""Unit tests for the PriceSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_MARKET,
    Agent,
    Inventory,
    PriceObserved,
    ResourceStack,
    SimulationConfig,
    World,
    post_listing,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import PriceConfig, PriceSystem


def test_observe_emits_price_observed_without_mutating_world() -> None:
    """Empty books emit a zero-quote census and leave the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    bus = EventBus()
    updated = PriceSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, PriceObserved)]
    assert len(events) == 1
    assert events[0].quote_count == 0
    assert events[0].quotes == ()


def test_observe_includes_quotes_for_open_listings() -> None:
    """Posted listings appear in PriceObserved quote tuples."""
    seller = Agent.create(agent_id=0, name="S", money=0).model_copy(
        update={
            "inventory": Inventory(stacks=(ResourceStack(resource="food", quantity=2),))
        }
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        markets=(CAMP_MARKET,),
        agents=(seller,),
    )
    posted = post_listing(world, 0, 0, "food", quantity=2, unit_price=5)
    assert posted is not None
    world, _listing = posted
    bus = EventBus()
    PriceSystem().observe(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, PriceObserved)]
    assert events[0].quote_count == 1
    market_id, resource, best_ask, ask_qty, last, count, units, suggested = events[
        0
    ].quotes[0]
    assert market_id == 0
    assert resource == "food"
    assert best_ask == 5
    assert ask_qty == 2
    assert last is None
    assert count == 1
    assert units == 2
    assert suggested == 5


def test_observe_can_suppress_events() -> None:
    """PriceConfig.emit_events=False skips publishing."""
    world = WorldFactory().create(SimulationConfig(seed=1, agent_count=1))
    bus = EventBus()
    PriceSystem(PriceConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()
