"""Unit tests for the EconomySystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    MoneyTransferred,
    SimulationConfig,
    WealthObserved,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import EconomyConfig, EconomySystem


def test_observe_emits_wealth_observed_without_mutating_world() -> None:
    """observe publishes one wealth census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=4))
    bus = EventBus()
    updated = EconomySystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, WealthObserved)]
    assert len(events) == 1
    assert events[0].alive_count == 4
    assert events[0].total == sum(agent.money for agent in world.agents)
    assert events[0].dead_total == 0
    assert events[0].treasury == 0
    assert events[0].government_treasury == 0
    assert events[0].institution_budget == 0
    assert events[0].society_total == events[0].total
    assert events[0].median_alive is not None
    assert events[0].gini_bps >= 0


def test_observe_can_suppress_events() -> None:
    """EconomyConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A", money=3),),
    )
    bus = EventBus()
    EconomySystem(EconomyConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_transfer_emits_money_transferred() -> None:
    """Successful transfers mutate balances and emit MoneyTransferred."""
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(
            Agent.create(agent_id=0, name="A", money=7),
            Agent.create(agent_id=1, name="B", money=1),
        ),
    )
    bus = EventBus()
    updated = EconomySystem().transfer(world, 0, 1, 2, bus=bus)
    payer = updated.agent_by_id(0)
    payee = updated.agent_by_id(1)
    assert payer is not None and payee is not None
    assert payer.money == 5
    assert payee.money == 3
    events = [event for event in bus.history if isinstance(event, MoneyTransferred)]
    assert len(events) == 1
    assert events[0].from_agent_id.value == 0
    assert events[0].to_agent_id.value == 1
    assert events[0].amount == 2


def test_transfer_illegal_leaves_world_unchanged() -> None:
    """Failed transfers do not mutate the world or publish events."""
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(
            Agent.create(agent_id=0, name="A", money=1),
            Agent.create(agent_id=1, name="B", money=0),
        ),
    )
    bus = EventBus()
    updated = EconomySystem().transfer(world, 0, 1, 5, bus=bus)
    assert updated == world
    assert bus.history == ()
