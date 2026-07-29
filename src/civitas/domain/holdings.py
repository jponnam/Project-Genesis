"""Resource stock censuses: agent inventories and market escrow.

Phase 22 Milestone 4. Flow events (gather/consume/produce/trade) cannot
reconstruct holdings because production inputs and market escrow are not
fully ledgered. This module snapshots stocks from the live world so JSONL
consumers can recover the last known inventories honestly.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class ResourceCensus(BaseModel):
    """Immutable resource-stock snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    alive_count: NonNegativeInt
    # Living non-zero stacks: (agent_id, resource, quantity), sorted.
    agent_holdings: tuple[tuple[int, str, int], ...] = ()
    # Society totals among living agents: (resource, quantity), sorted.
    alive_totals: tuple[tuple[str, int], ...] = ()
    # Residual on dead agents: (resource, quantity), sorted.
    dead_totals: tuple[tuple[str, int], ...] = ()
    # Open-book escrow not in agent inventories: (resource, quantity).
    escrow_totals: tuple[tuple[str, int], ...] = ()
    stack_count: NonNegativeInt = Field(
        description="Number of non-zero living agent stacks.",
    )
    distinct_resources: NonNegativeInt = Field(
        description="Distinct resources among living agent stacks.",
    )


def _sorted_totals(counter: Counter[str]) -> tuple[tuple[str, int], ...]:
    return tuple(
        sorted((resource, int(amount)) for resource, amount in counter.items())
    )


def census_resources(world: World) -> ResourceCensus:
    """Return a deterministic resource-stock census for ``world``.

    Does not mutate the world. Money is intentionally omitted — use
    ``census_wealth`` / ``WealthObserved`` for monetary stocks.
    """
    alive_totals: Counter[str] = Counter()
    dead_totals: Counter[str] = Counter()
    holdings: list[tuple[int, str, int]] = []

    for agent in world.agents:
        living = agent.is_alive()
        target = alive_totals if living else dead_totals
        for stack in agent.inventory.stacks:
            quantity = int(stack.quantity)
            if quantity <= 0:
                continue
            resource = str(stack.resource)
            target[resource] += quantity
            if living:
                holdings.append((agent.agent_id.value, resource, quantity))

    holdings.sort(key=lambda item: (item[0], item[1]))

    escrow: Counter[str] = Counter()
    for market in world.markets:
        for listing in market.listings:
            escrow[str(listing.resource)] += int(listing.quantity)

    alive_sorted = _sorted_totals(alive_totals)
    return ResourceCensus(
        tick=world.tick,
        alive_count=len(world.alive_agents()),
        agent_holdings=tuple(holdings),
        alive_totals=alive_sorted,
        dead_totals=_sorted_totals(dead_totals),
        escrow_totals=_sorted_totals(escrow),
        stack_count=len(holdings),
        distinct_resources=len(alive_sorted),
    )
