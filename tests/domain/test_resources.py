"""Unit tests for domain resource deposits and gathering helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Location,
    LocationKind,
    ResourceKind,
    ResourceStack,
    SimulationConfig,
    World,
    apply_gather,
    default_world_map,
    deposits_for_kind,
    gatherable_resources,
    location_stock,
)


def test_camp_has_no_deposits() -> None:
    """Camp is a spawn hub without gatherable stock."""
    assert CAMP_LOCATION.deposits == ()
    assert deposits_for_kind(LocationKind.CAMP) == ()


def test_biome_deposits_are_deterministic() -> None:
    """Each location kind receives a fixed sorted deposit catalog."""
    forest = deposits_for_kind(LocationKind.FOREST)
    assert [stack.resource for stack in forest] == [
        ResourceKind.FOOD.value,
        ResourceKind.WOOD.value,
    ]
    assert forest[0].quantity == 24
    assert forest[1].quantity == 16
    river = deposits_for_kind(LocationKind.RIVER)
    assert [stack.resource for stack in river] == [ResourceKind.WATER.value]


def test_default_map_locations_carry_biome_stock() -> None:
    """Canonical map cells include deposits matching their kind."""
    locations = default_world_map()
    assert locations[0].deposits == ()
    assert gatherable_resources(locations[1]) == ("food",)  # plain
    assert "wood" in gatherable_resources(locations[2])  # forest
    assert gatherable_resources(locations[3]) == ("water",)  # river


def test_apply_gather_transfers_stock_to_inventory() -> None:
    """Gathering depletes the location and fills agent inventory."""
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    agent = Agent.create(agent_id=0, name="A", location_id=1)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(agent,),
    )
    updated = apply_gather(world, agent, "food", amount=1)
    assert updated is not None
    assert location_stock(updated.locations[1], "food") == 23
    assert updated.agents[0].inventory.quantity("food") == 1


def test_apply_gather_rejects_empty_stock() -> None:
    """Gathering fails when the deposit is exhausted."""
    plain = Location.create(
        1,
        "Plain",
        1,
        0,
        kind=LocationKind.PLAIN,
        deposits=(),
    )
    agent = Agent.create(agent_id=0, name="A", location_id=1)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(agent,),
    )
    assert apply_gather(world, agent, "food") is None


def test_world_with_location_replaces_deposit_state() -> None:
    """with_location updates deposits immutably."""
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    depleted = plain.model_copy(update={"deposits": ()})
    updated = world.with_location(depleted)
    assert updated.locations[1].deposits == ()
    assert world.locations[1].deposits != ()


def test_location_rejects_unsorted_deposits() -> None:
    """Deposit stacks must be ordered by resource name."""
    with pytest.raises(ValidationError):
        Location.create(
            1,
            "Bad",
            1,
            0,
            deposits=(
                ResourceStack(resource="wood", quantity=1),
                ResourceStack(resource="food", quantity=1),
            ),
        )
