"""Tests for resource stock censuses."""

from __future__ import annotations

from civitas.domain import (
    Inventory,
    ResourceStack,
    SimulationConfig,
    census_resources,
)
from civitas.engine import WorldFactory


def test_census_resources_empty_inventories() -> None:
    """Fresh worlds start with empty inventories and empty escrow."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3, ticks=1))
    snap = census_resources(world)
    assert snap.alive_count == 3
    assert snap.agent_holdings == ()
    assert snap.alive_totals == ()
    assert snap.escrow_totals == ()
    assert snap.stack_count == 0
    assert snap.distinct_resources == 0


def test_census_resources_sums_alive_stacks_deterministically() -> None:
    """Living agent stacks are sorted and totaled by resource."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2, ticks=1))
    agents = list(world.agents)
    agents[0] = agents[0].model_copy(
        update={
            "inventory": Inventory(stacks=(ResourceStack(resource="food", quantity=3),))
        }
    )
    agents[1] = agents[1].model_copy(
        update={
            "inventory": Inventory(
                stacks=(
                    ResourceStack(resource="water", quantity=2),
                    ResourceStack(resource="food", quantity=1),
                )
            )
        }
    )
    world = world.model_copy(update={"agents": tuple(agents)})
    snap = census_resources(world)
    assert snap.agent_holdings == (
        (0, "food", 3),
        (1, "food", 1),
        (1, "water", 2),
    )
    assert snap.alive_totals == (("food", 4), ("water", 2))
    assert snap.stack_count == 3
    assert snap.distinct_resources == 2
