"""Unit tests for the TradingSystem and TRADE action integration."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    ActionKind,
    Agent,
    AgentId,
    Inventory,
    Needs,
    Personality,
    ResourceStack,
    ResourceTraded,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus
from civitas.systems import TradingSystem, UtilityPolicy


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
        agents=agents,
    )


def test_trading_system_emits_resource_traded() -> None:
    """TradingSystem.trade mutates balances and emits ResourceTraded."""
    world = _world(_with_food(0, 0, money=4), _with_food(1, 3, money=0))
    bus = EventBus()
    updated = TradingSystem().trade(world, 0, 1, "food", bus=bus, price=2)
    buyer = updated.agent_by_id(0)
    seller = updated.agent_by_id(1)
    assert buyer is not None and seller is not None
    assert buyer.inventory.quantity("food") == 1
    assert buyer.money == 2
    assert seller.inventory.quantity("food") == 2
    assert seller.money == 2
    events = [event for event in bus.history if isinstance(event, ResourceTraded)]
    assert len(events) == 1
    assert events[0].buyer_id.value == 0
    assert events[0].seller_id.value == 1
    assert events[0].price == 2


def test_trading_system_illegal_trade_is_noop() -> None:
    """Illegal trades leave the world and event bus unchanged."""
    world = _world(_with_food(0, 0, money=0), _with_food(1, 1, money=0))
    bus = EventBus()
    updated = TradingSystem().trade(world, 0, 1, "food", bus=bus)
    assert updated == world
    assert bus.history == ()


def test_policy_selects_trade_when_buyer_needs_seller_stock() -> None:
    """Hungry buyers with money select TRADE against a co-located seller."""
    buyer = _with_food(0, 0, money=5).model_copy(
        update={
            "needs": Needs(food=0.1, water=1.0, energy=1.0, social=1.0, safety=1.0),
            "personality": Personality(agreeableness=1.0, conscientiousness=0.0),
        }
    )
    seller = _with_food(1, 2, money=0)
    world = _world(buyer, seller)
    choice = UtilityPolicy().select(buyer, world=world)
    assert choice.action is ActionKind.TRADE
    assert choice.target_agent_id == AgentId(value=1)
    assert choice.target_resource == "food"
