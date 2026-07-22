"""Unit tests for domain trading helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentId,
    AgentStatus,
    Health,
    Inventory,
    Location,
    LocationKind,
    ResourceStack,
    SimulationConfig,
    TradeTerms,
    World,
    apply_trade,
    can_trade,
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
        agents=agents,
    )


def test_trade_terms_reject_self_deal() -> None:
    """Buyer and seller must be distinct."""
    with pytest.raises(ValidationError):
        TradeTerms(
            buyer_id=AgentId(value=0),
            seller_id=AgentId(value=0),
            resource="food",
        )


def test_can_trade_and_apply_trade_success() -> None:
    """Legal trades move resource to the buyer and money to the seller."""
    buyer = _with_food(0, 0, money=5)
    seller = _with_food(1, 2, money=1)
    world = _world(buyer, seller)
    terms = TradeTerms(
        buyer_id=AgentId(value=0),
        seller_id=AgentId(value=1),
        resource="food",
        quantity=1,
        price=2,
    )
    assert can_trade(world, terms) is True
    updated = apply_trade(world, terms)
    assert updated is not None
    new_buyer = updated.agent_by_id(0)
    new_seller = updated.agent_by_id(1)
    assert new_buyer is not None and new_seller is not None
    assert new_buyer.inventory.quantity("food") == 1
    assert new_buyer.money == 3
    assert new_seller.inventory.quantity("food") == 1
    assert new_seller.money == 3


def test_can_trade_rejects_illegal_cases() -> None:
    """Distance, poverty, missing stock, and death block trades."""
    buyer = _with_food(0, 0, money=1)
    seller = _with_food(1, 1, money=0)
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    elsewhere = seller.model_copy(update={"location_id": plain.location_id})
    distant_world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(buyer, elsewhere),
    )
    base_terms = TradeTerms(
        buyer_id=AgentId(value=0),
        seller_id=AgentId(value=1),
        resource="food",
        quantity=1,
        price=1,
    )
    assert can_trade(distant_world, base_terms) is False

    same_place = _world(buyer, seller)
    assert can_trade(same_place, base_terms.model_copy(update={"price": 5})) is False
    assert (
        can_trade(same_place, base_terms.model_copy(update={"resource": "water"}))
        is False
    )

    dead_seller = seller.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_trade(_world(buyer, dead_seller), base_terms) is False
    assert apply_trade(same_place, base_terms.model_copy(update={"price": 5})) is None
