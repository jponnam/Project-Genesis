"""Unit tests for the WaterSystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    APOTHECARY_DRINK_RESTORE_BONUS,
    CAMP_LOCATION,
    DEFAULT_DRINK_RESTORE,
    LAZARETTO_DRINK_RESTORE_BONUS,
    Agent,
    City,
    CityKind,
    Government,
    Institution,
    InstitutionKind,
    Inventory,
    Law,
    LawKind,
    NeedDecayed,
    Needs,
    ResourceConsumed,
    ResourceStack,
    SimulationConfig,
    World,
    default_world_map,
)
from civitas.engine import EventBus
from civitas.systems import WaterConfig, WaterSystem


def _world_with_water(quantity: int = 2) -> World:
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=0.5, energy=1.0, social=1.0, safety=1.0),
    ).model_copy(
        update={
            "inventory": Inventory(
                stacks=(ResourceStack(resource="water", quantity=quantity),)
            )
        }
    )
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )


def test_drink_emits_consume_and_need_events() -> None:
    """Successful drink publishes ResourceConsumed and water NeedDecayed."""
    world = _world_with_water()
    bus = EventBus()
    updated = WaterSystem().drink(world, 0, bus=bus)
    assert updated.agents[0].inventory.quantity("water") == 1
    assert updated.agents[0].needs.water == pytest.approx(0.80)
    assert any(
        isinstance(event, ResourceConsumed) and event.resource == "water"
        for event in bus.history
    )
    assert any(
        isinstance(event, NeedDecayed) and event.need == "water"
        for event in bus.history
    )


def test_drink_uses_sanitation_bonus() -> None:
    """WaterSystem drink restore includes SANITATION law bonuses."""
    world = _world_with_water(quantity=1).model_copy(
        update={
            "governments": (Government.create(0, "Camp", 0, (0,)),),
            "laws": (Law.create(0, 0, "Camp Sanitation", LawKind.SANITATION),),
        }
    )
    updated = WaterSystem().drink(world, 0)
    assert updated.agents[0].needs.water == pytest.approx(0.85)


def test_drink_uses_apothecary_bonus() -> None:
    """WaterSystem drink restore includes active apothecary seat bonuses."""
    world = _world_with_water(quantity=1).model_copy(
        update={
            "governments": (Government.create(0, "Camp", 0, (0,)),),
            "institutions": (
                Institution.create(
                    0, 0, 0, "Camp Apothecary", InstitutionKind.APOTHECARY
                ),
            ),
        }
    )
    updated = WaterSystem().drink(world, 0)
    assert updated.agents[0].needs.water == pytest.approx(
        0.5 + DEFAULT_DRINK_RESTORE + APOTHECARY_DRINK_RESTORE_BONUS
    )


def test_drink_uses_lazaretto_bonus() -> None:
    """WaterSystem drink restore includes active lazaretto city seat bonuses."""
    agent = _world_with_water(quantity=1).agents[0].model_copy(
        update={"location_id": default_world_map()[1].location_id}
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Lazaretto", CityKind.LAZARETTO),
        ),
        agents=(agent,),
    )
    updated = WaterSystem().drink(world, 0)
    assert updated.agents[0].needs.water == pytest.approx(
        0.5 + DEFAULT_DRINK_RESTORE + LAZARETTO_DRINK_RESTORE_BONUS
    )


def test_drink_without_water_is_noop() -> None:
    """Drinking with an empty inventory leaves the world unchanged."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    system = WaterSystem()
    assert system.can_drink(world, 0) is False
    assert system.drink(world, 0, bus=bus) == world
    assert bus.history == ()


def test_water_config_controls_restore_and_amount() -> None:
    """WaterConfig restore and consume_amount are applied."""
    world = _world_with_water(quantity=3)
    updated = WaterSystem(WaterConfig(restore=0.4, consume_amount=2)).drink(world, 0)
    assert updated.agents[0].inventory.quantity("water") == 1
    assert updated.agents[0].needs.water == pytest.approx(0.9)


def test_missing_agent_raises() -> None:
    """drink raises when the agent id is absent."""
    world = _world_with_water()
    with pytest.raises(ValueError, match="not found"):
        WaterSystem().drink(world, 9)
