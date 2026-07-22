"""Unit tests for domain price quote helpers."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_MARKET,
    Agent,
    Inventory,
    ResourceStack,
    SimulationConfig,
    World,
    census_prices,
    fill_listing,
    post_listing,
    quote_resource,
    suggested_unit_price,
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


def test_quote_resource_reports_best_ask_and_suggestion() -> None:
    """Open listings drive best ask, depth, and suggested price."""
    world = _world(_with_food(0, 3, money=0))
    posted = post_listing(world, 0, 0, "food", quantity=2, unit_price=3)
    assert posted is not None
    world, _listing = posted
    quote = quote_resource(world.markets[0], "food")
    assert quote.best_ask == 3
    assert quote.ask_quantity == 2
    assert quote.last_trade is None
    assert quote.listing_count == 1
    assert quote.total_units == 2
    assert quote.suggested_unit_price == 3
    assert suggested_unit_price(world.markets[0], "food") == 3


def test_fill_updates_last_trade_and_suggestion() -> None:
    """Successful fills stamp last-trade marks used by suggestions."""
    world = _world(_with_food(0, 2, money=0), _with_food(1, 0, money=10))
    posted = post_listing(world, 0, 0, "food", quantity=2, unit_price=4)
    assert posted is not None
    world, listing = posted
    filled = fill_listing(world, 0, listing.listing_id, 1, quantity=1)
    assert filled is not None
    market = filled.markets[0]
    assert market.last_trade_price("food") == 4
    quote = quote_resource(market, "food")
    assert quote.last_trade == 4
    assert quote.best_ask == 4
    assert quote.suggested_unit_price == 4
    assert census_prices(filled).quote_count == 1


def test_suggested_price_falls_back_to_default() -> None:
    """Empty books without last trades suggest the default unit price."""
    world = _world(_with_food(0, 0, money=0))
    assert suggested_unit_price(world.markets[0], "stone") == 1
    assert census_prices(world).quotes == ()
