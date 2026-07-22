"""Unit tests for domain event models and serialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentId,
    AgentMoved,
    AgentSpawned,
    DomainEvent,
    ListingFilled,
    ListingId,
    ListingPosted,
    LocationId,
    MarketCreated,
    MarketId,
    MarketObserved,
    MoneyTransferred,
    NeedDecayed,
    PopulationObserved,
    PriceObserved,
    ResourceConsumed,
    ResourceGathered,
    ResourceProduced,
    ResourceTraded,
    SimulationCompleted,
    SimulationStarted,
    TaxCollected,
    Tick,
    TickCompleted,
    TickStarted,
    WealthObserved,
    event_from_record,
)
from civitas.domain.events import CONCRETE_EVENT_TYPES, EVENT_TYPE_REGISTRY


def test_domain_event_exposes_event_type_name() -> None:
    """event_type matches the concrete class name."""
    event = TickStarted(tick=Tick(value=1))
    assert event.event_type == "TickStarted"
    assert isinstance(event, DomainEvent)


def test_events_are_frozen() -> None:
    """Domain events cannot be mutated in place."""
    event = TickCompleted(sequence=0, tick=Tick(value=2))
    with pytest.raises(ValidationError):
        event.sequence = 9  # type: ignore[misc]


def test_to_record_includes_event_type_and_round_trips() -> None:
    """Serialization includes event_type and deserializes losslessly."""
    original = ActionSelected(
        sequence=3,
        tick=Tick(value=4),
        agent_id=AgentId(value=1),
        action="eat",
        utility=0.75,
    )
    record = original.to_record()
    assert record["event_type"] == "ActionSelected"
    assert record["action"] == "eat"
    restored = event_from_record(record)
    assert restored == original
    assert isinstance(restored, ActionSelected)


def test_event_from_record_rejects_unknown_type() -> None:
    """Unknown event_type values are hard errors."""
    with pytest.raises(ValueError, match="unknown event_type"):
        event_from_record(
            {
                "event_type": "NotARealEvent",
                "sequence": 0,
                "tick": {"value": 0},
            }
        )


def test_event_from_record_requires_event_type() -> None:
    """Records without event_type are rejected."""
    with pytest.raises(ValueError, match="missing required key"):
        event_from_record({"sequence": 0, "tick": {"value": 0}})


def test_all_concrete_events_are_registered() -> None:
    """Every concrete event type is present in the registry."""
    assert len(CONCRETE_EVENT_TYPES) == len(EVENT_TYPE_REGISTRY)
    for event_cls in CONCRETE_EVENT_TYPES:
        assert EVENT_TYPE_REGISTRY[event_cls.__name__] is event_cls


def test_phase1_events_validate_payloads() -> None:
    """Representative Phase 1 events accept well-formed payloads."""
    tick = Tick(value=1)
    started = SimulationStarted(
        tick=Tick(value=0),
        seed=42,
        ticks=100,
        agent_count=10,
        run_name="default",
    )
    spawned = AgentSpawned(
        tick=tick,
        agent_id=AgentId(value=0),
        name="Ada",
        location_id=LocationId(value=0),
    )
    completed = ActionCompleted(
        tick=tick,
        agent_id=AgentId(value=0),
        action="rest",
        success=True,
    )
    consumed = ResourceConsumed(
        tick=tick,
        agent_id=AgentId(value=0),
        resource="food",
        amount=1,
    )
    decayed = NeedDecayed(
        tick=tick,
        agent_id=AgentId(value=0),
        need="food",
        previous=1.0,
        current=0.9,
    )
    finished = SimulationCompleted(tick=Tick(value=100), ticks_executed=100)
    assert started.run_name == "default"
    assert spawned.name == "Ada"
    assert completed.success is True
    assert consumed.amount == 1
    assert decayed.current == 0.9
    assert finished.ticks_executed == 100


def test_nested_ids_round_trip_through_record() -> None:
    """Nested AgentId/LocationId survive JSON record round-trips."""
    event = AgentSpawned(
        sequence=5,
        tick=Tick(value=0),
        agent_id=AgentId(value=9),
        name="Bea",
        location_id=LocationId(value=2),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentSpawned)
    assert restored.agent_id == AgentId(value=9)
    assert restored.location_id == LocationId(value=2)


def test_agent_moved_round_trips() -> None:
    """AgentMoved serializes nested location ids losslessly."""
    event = AgentMoved(
        sequence=2,
        tick=Tick(value=3),
        agent_id=AgentId(value=1),
        from_location_id=LocationId(value=0),
        to_location_id=LocationId(value=1),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentMoved)
    assert restored.from_location_id == LocationId(value=0)
    assert restored.to_location_id == LocationId(value=1)


def test_action_selected_optional_target_location() -> None:
    """ActionSelected accepts an optional MOVE destination."""
    event = ActionSelected(
        tick=Tick(value=1),
        agent_id=AgentId(value=0),
        action="move",
        utility=0.5,
        target_location_id=LocationId(value=3),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ActionSelected)
    assert restored.target_location_id == LocationId(value=3)


def test_resource_gathered_round_trips() -> None:
    """ResourceGathered serializes agent/location ids losslessly."""
    event = ResourceGathered(
        sequence=4,
        tick=Tick(value=2),
        agent_id=AgentId(value=1),
        location_id=LocationId(value=2),
        resource="wood",
        amount=1,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ResourceGathered)
    assert restored.resource == "wood"
    assert restored.location_id == LocationId(value=2)


def test_action_selected_optional_target_resource() -> None:
    """ActionSelected accepts an optional GATHER resource."""
    event = ActionSelected(
        tick=Tick(value=1),
        agent_id=AgentId(value=0),
        action="gather",
        utility=0.4,
        target_resource="water",
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ActionSelected)
    assert restored.target_resource == "water"


def test_population_observed_round_trips() -> None:
    """PopulationObserved serializes census fields losslessly."""
    event = PopulationObserved(
        sequence=7,
        tick=Tick(value=3),
        initial_count=10,
        total=10,
        alive=9,
        dead=1,
        location_counts=((0, 6), (1, 4)),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, PopulationObserved)
    assert restored.alive == 9
    assert restored.location_counts == ((0, 6), (1, 4))


def test_agent_born_round_trips() -> None:
    """AgentBorn serializes parent/child identity losslessly."""
    event = AgentBorn(
        sequence=4,
        tick=Tick(value=8),
        agent_id=AgentId(value=3),
        parent_id=AgentId(value=1),
        location_id=LocationId(value=0),
        name="Agent-3",
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentBorn)
    assert restored.agent_id == AgentId(value=3)
    assert restored.parent_id == AgentId(value=1)
    assert restored.name == "Agent-3"


def test_agent_died_round_trips() -> None:
    """AgentDied serializes cause and identity losslessly."""
    event = AgentDied(
        sequence=5,
        tick=Tick(value=9),
        agent_id=AgentId(value=2),
        location_id=LocationId(value=0),
        cause="starvation",
        name="Agent-2",
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentDied)
    assert restored.cause == "starvation"
    assert restored.agent_id == AgentId(value=2)


def test_money_transferred_round_trips() -> None:
    """MoneyTransferred serializes payer/payee/amount losslessly."""
    event = MoneyTransferred(
        sequence=6,
        tick=Tick(value=2),
        from_agent_id=AgentId(value=0),
        to_agent_id=AgentId(value=1),
        amount=4,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, MoneyTransferred)
    assert restored.amount == 4
    assert restored.from_agent_id == AgentId(value=0)


def test_resource_traded_round_trips() -> None:
    """ResourceTraded serializes trade terms losslessly."""
    event = ResourceTraded(
        sequence=7,
        tick=Tick(value=4),
        buyer_id=AgentId(value=0),
        seller_id=AgentId(value=2),
        resource="food",
        quantity=1,
        price=3,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ResourceTraded)
    assert restored.resource == "food"
    assert restored.price == 3
    assert restored.seller_id == AgentId(value=2)


def test_resource_produced_round_trips() -> None:
    """ResourceProduced serializes recipe outputs losslessly."""
    event = ResourceProduced(
        sequence=8,
        tick=Tick(value=5),
        agent_id=AgentId(value=1),
        recipe_id="tools",
        outputs=(("tools", 1),),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ResourceProduced)
    assert restored.recipe_id == "tools"
    assert restored.outputs == (("tools", 1),)
    assert restored.agent_id == AgentId(value=1)


def test_tax_collected_round_trips() -> None:
    """TaxCollected serializes levy amounts losslessly."""
    event = TaxCollected(
        sequence=9,
        tick=Tick(value=6),
        agent_id=AgentId(value=2),
        amount=3,
        treasury_after=11,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, TaxCollected)
    assert restored.amount == 3
    assert restored.treasury_after == 11
    assert restored.agent_id == AgentId(value=2)


def test_market_created_and_listing_events_round_trip() -> None:
    """Market venue and listing events serialize losslessly."""
    created = MarketCreated(
        sequence=1,
        tick=Tick(value=0),
        market_id=MarketId(value=0),
        location_id=LocationId(value=0),
        name="Camp Market",
    )
    assert isinstance(event_from_record(created.to_record()), MarketCreated)

    posted = ListingPosted(
        sequence=2,
        tick=Tick(value=1),
        market_id=MarketId(value=0),
        listing_id=ListingId(value=0),
        seller_id=AgentId(value=1),
        resource="food",
        quantity=2,
        unit_price=1,
    )
    restored_posted = event_from_record(posted.to_record())
    assert isinstance(restored_posted, ListingPosted)
    assert restored_posted.quantity == 2

    filled = ListingFilled(
        sequence=3,
        tick=Tick(value=2),
        market_id=MarketId(value=0),
        listing_id=ListingId(value=0),
        buyer_id=AgentId(value=2),
        seller_id=AgentId(value=1),
        resource="food",
        quantity=1,
        unit_price=1,
        total_price=1,
    )
    restored_filled = event_from_record(filled.to_record())
    assert isinstance(restored_filled, ListingFilled)
    assert restored_filled.total_price == 1


def test_market_observed_round_trips() -> None:
    """MarketObserved serializes open-book census fields losslessly."""
    event = MarketObserved(
        sequence=9,
        tick=Tick(value=3),
        market_count=1,
        listing_count=2,
        total_units=5,
        market_listings=((0, 2),),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, MarketObserved)
    assert restored.total_units == 5
    assert restored.market_listings == ((0, 2),)


def test_price_observed_round_trips() -> None:
    """PriceObserved serializes quote tuples losslessly."""
    event = PriceObserved(
        sequence=10,
        tick=Tick(value=4),
        quote_count=1,
        quotes=((0, "food", 3, 2, None, 1, 2, 3),),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, PriceObserved)
    assert restored.quote_count == 1
    assert restored.quotes[0][1] == "food"
    assert restored.quotes[0][2] == 3
    assert restored.quotes[0][4] is None


def test_wealth_observed_round_trips() -> None:
    """WealthObserved serializes census fields losslessly."""
    event = WealthObserved(
        sequence=8,
        tick=Tick(value=3),
        total=20,
        alive_total=15,
        dead_total=5,
        alive_count=3,
        mean_alive=5.0,
        min_alive=1,
        max_alive=9,
        treasury=4,
        society_total=24,
        treasury_share_bps=1666,
        median_alive=5,
        gini_bps=2000,
        top1_share_bps=6000,
        top10_share_bps=6000,
        zero_count=0,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, WealthObserved)
    assert restored.alive_total == 15
    assert restored.min_alive == 1
    assert restored.max_alive == 9
    assert restored.treasury == 4
    assert restored.society_total == 24
    assert restored.gini_bps == 2000
    assert restored.median_alive == 5
