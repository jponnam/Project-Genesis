"""Research: deterministic progress toward undiscovered technologies.

Phase 6 Milestone 2. Each undiscovered technology may have a progress
row. Each apply tick adds fixed integer points; when points reach the
threshold, ``discover_technology`` is called and the row is removed.
Innovation (Milestone 3) activates society adoptions after discovery.
Knowledge diffusion (Milestone 4) syncs facts onto agents afterward.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import TechnologyId
from civitas.domain.technology import (
    CAMP_POTTERY,
    discover_technology,
    prerequisites_met,
    technology_by_id,
)
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World

DEFAULT_POINTS_PER_TICK: int = 1
DEFAULT_POTTERY_THRESHOLD: int = 10


class ResearchProgress(BaseModel):
    """Progress toward discovering one technology."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    technology_id: TechnologyId
    points: NonNegativeInt = 0
    threshold: NonNegativeInt = Field(gt=0)

    @classmethod
    def create(
        cls,
        technology_id: int,
        *,
        points: int = 0,
        threshold: int = DEFAULT_POTTERY_THRESHOLD,
    ) -> ResearchProgress:
        """Construct a validated progress row from primitive fields."""
        return cls(
            technology_id=TechnologyId(value=technology_id),
            points=points,
            threshold=threshold,
        )


CAMP_POTTERY_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_POTTERY.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)


def default_research_progress() -> tuple[ResearchProgress, ...]:
    """Return the canonical initial research progress set."""
    return (CAMP_POTTERY_RESEARCH,)


class ResearchCensus(BaseModel):
    """Aggregate research snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    progress_count: NonNegativeInt
    total_points: NonNegativeInt
    total_threshold: NonNegativeInt
    total_remaining: NonNegativeInt
    completion_bps: NonNegativeInt


@dataclass(frozen=True, slots=True)
class ResearchAdvance:
    """One technology's outcome during an apply pass."""

    technology_id: TechnologyId
    points_before: int
    points_after: int
    threshold: int
    discovered: bool


def research_by_technology_id(
    world: World,
    technology_id: TechnologyId | int,
) -> ResearchProgress | None:
    """Return progress for ``technology_id``, or ``None``."""
    target = (
        technology_id
        if isinstance(technology_id, TechnologyId)
        else TechnologyId(value=technology_id)
    )
    for progress in world.research_progress:
        if progress.technology_id == target:
            return progress
    return None


def advance_research(
    world: World,
    *,
    points_per_tick: int = DEFAULT_POINTS_PER_TICK,
) -> tuple[World, tuple[ResearchAdvance, ...]]:
    """Advance all research rows by ``points_per_tick`` and discover when ready.

    Rows whose target is missing or already discovered are dropped.
    Progress rows are removed before discovery so world invariants hold.
    """
    if points_per_tick < 0:
        msg = f"points_per_tick must be >= 0, got {points_per_tick}"
        raise ValueError(msg)

    outcomes: list[ResearchAdvance] = []
    remaining: list[ResearchProgress] = []
    to_discover: list[TechnologyId] = []

    for progress in world.research_progress:
        technology = technology_by_id(world, progress.technology_id)
        if technology is None or technology.discovered:
            continue
        if not prerequisites_met(world, technology):
            # Locked by unmet prerequisites: preserve row, no progress.
            remaining.append(progress)
            continue

        points_before = progress.points
        points_after = min(points_before + points_per_tick, progress.threshold)
        discovered = points_after >= progress.threshold
        outcomes.append(
            ResearchAdvance(
                technology_id=progress.technology_id,
                points_before=points_before,
                points_after=points_after,
                threshold=progress.threshold,
                discovered=discovered,
            )
        )
        if discovered:
            to_discover.append(progress.technology_id)
        else:
            remaining.append(progress.model_copy(update={"points": points_after}))

    remaining_sorted = tuple(
        sorted(remaining, key=lambda item: item.technology_id.value)
    )
    world = world.model_copy(update={"research_progress": remaining_sorted})
    for technology_id in to_discover:
        updated = discover_technology(world, technology_id)
        if updated is not None:
            world = updated
    return world, tuple(outcomes)


def census_research(world: World) -> ResearchCensus:
    """Build a deterministic research census for ``world``."""
    rows = world.research_progress
    total_points = sum(row.points for row in rows)
    total_threshold = sum(row.threshold for row in rows)
    total_remaining = sum(max(row.threshold - row.points, 0) for row in rows)
    if total_threshold == 0:
        completion_bps = 0
    else:
        completion_bps = (total_points * 10_000) // total_threshold
    return ResearchCensus(
        tick=world.tick,
        progress_count=len(rows),
        total_points=total_points,
        total_threshold=total_threshold,
        total_remaining=total_remaining,
        completion_bps=completion_bps,
    )
