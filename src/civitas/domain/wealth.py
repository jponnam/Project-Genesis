"""Wealth analytics: treasury-aware totals and inequality metrics.

Read-only helpers extend the basic agent-money census with society totals
(including ``World.treasury``) and integer inequality measures. Money math
stays integer-only via basis points.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.economy import wealth_alive_total, wealth_total
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from collections.abc import Sequence

    from civitas.domain.world import World

BPS_DENOMINATOR: int = 10_000


class WealthCensus(BaseModel):
    """Immutable wealth and inequality snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    total: NonNegativeInt = Field(description="Sum of money across the full roster.")
    alive_total: NonNegativeInt = Field(description="Sum of money among living agents.")
    dead_total: NonNegativeInt = Field(description="Sum of money among dead agents.")
    alive_count: NonNegativeInt
    mean_alive: float = Field(
        description="Mean money among living agents, or 0.0 when none are alive."
    )
    min_alive: NonNegativeInt | None = Field(
        default=None,
        description="Minimum living-agent money, or None when none are alive.",
    )
    max_alive: NonNegativeInt | None = Field(
        default=None,
        description="Maximum living-agent money, or None when none are alive.",
    )
    treasury: NonNegativeInt = Field(description="Public treasury balance.")
    society_total: NonNegativeInt = Field(
        description="Agent money total plus treasury."
    )
    treasury_share_bps: NonNegativeInt = Field(
        description="Treasury share of society_total in basis points."
    )
    median_alive: NonNegativeInt | None = Field(
        default=None,
        description="Median living-agent money, or None when none are alive.",
    )
    gini_bps: NonNegativeInt = Field(
        description="Gini coefficient of living balances in basis points."
    )
    top1_share_bps: NonNegativeInt = Field(
        description="Richest living agent's share of alive_total in basis points."
    )
    top10_share_bps: NonNegativeInt = Field(
        description="Top decile living share of alive_total in basis points."
    )
    zero_count: NonNegativeInt = Field(
        description="Count of living agents with zero money."
    )


def society_money_total(world: World) -> int:
    """Return agent money plus treasury (society-wide money stock)."""
    return wealth_total(world) + world.treasury


def share_bps(part: int, whole: int) -> int:
    """Return ``part / whole`` as integer basis points, or 0 when ``whole`` is 0."""
    if part < 0 or whole < 0:
        msg = f"share parts must be >= 0, got part={part} whole={whole}"
        raise ValueError(msg)
    if whole == 0:
        return 0
    return (part * BPS_DENOMINATOR) // whole


def median_int(sorted_values: Sequence[int]) -> int:
    """Return the integer median of a non-empty ascending sequence."""
    if not sorted_values:
        msg = "median_int requires a non-empty sequence"
        raise ValueError(msg)
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) // 2


def gini_bps(balances: Sequence[int]) -> int:
    """Return the Gini coefficient of ``balances`` in basis points.

    Uses the Brown formula on ascending balances. Equal balances (or fewer
    than two holders / zero total) yield 0. Result is clamped to
    ``[0, 10000]``.
    """
    if any(value < 0 for value in balances):
        msg = "gini_bps balances must be >= 0"
        raise ValueError(msg)
    ordered = tuple(sorted(balances))
    n = len(ordered)
    total = sum(ordered)
    if n < 2 or total == 0:
        return 0
    weighted = sum((index + 1) * value for index, value in enumerate(ordered))
    raw = ((2 * weighted - (n + 1) * total) * BPS_DENOMINATOR) // (n * total)
    return max(0, min(BPS_DENOMINATOR, raw))


def top_share_bps(balances: Sequence[int], fraction_numer: int = 1) -> int:
    """Return the richest ``ceil(n * fraction_numer / 10)`` share in bps.

    ``fraction_numer`` of 1 means top 10% (one decile). Always includes at
    least one richest agent when any living balances exist.
    """
    if fraction_numer < 1:
        msg = f"fraction_numer must be >= 1, got {fraction_numer}"
        raise ValueError(msg)
    ordered = tuple(sorted(balances))
    n = len(ordered)
    total = sum(ordered)
    if n == 0 or total == 0:
        return 0
    k = max(1, (n * fraction_numer + 9) // 10)
    top_sum = sum(ordered[-k:])
    return share_bps(top_sum, total)


def census_wealth(world: World) -> WealthCensus:
    """Build a deterministic wealth and inequality census for ``world``."""
    alive = world.alive_agents()
    total = wealth_total(world)
    alive_total = wealth_alive_total(world)
    alive_count = len(alive)
    treasury = world.treasury
    society_total = total + treasury
    balances = tuple(sorted(agent.money for agent in alive))

    if alive_count == 0:
        mean_alive = 0.0
        min_alive: int | None = None
        max_alive: int | None = None
        median_alive: int | None = None
        zero_count = 0
        gini = 0
        top1 = 0
        top10 = 0
    else:
        mean_alive = round(alive_total / alive_count, 6)
        min_alive = balances[0]
        max_alive = balances[-1]
        median_alive = median_int(balances)
        zero_count = sum(1 for value in balances if value == 0)
        gini = gini_bps(balances)
        top1 = share_bps(max_alive, alive_total)
        top10 = top_share_bps(balances, fraction_numer=1)

    return WealthCensus(
        tick=world.tick,
        total=total,
        alive_total=alive_total,
        dead_total=total - alive_total,
        alive_count=alive_count,
        mean_alive=mean_alive,
        min_alive=min_alive,
        max_alive=max_alive,
        treasury=treasury,
        society_total=society_total,
        treasury_share_bps=share_bps(treasury, society_total),
        median_alive=median_alive,
        gini_bps=gini,
        top1_share_bps=top1,
        top10_share_bps=top10,
        zero_count=zero_count,
    )
