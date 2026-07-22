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
    CAMP_AGRICULTURE,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASTRONOMY,
    CAMP_CARTOGRAPHY,
    CAMP_ENGINEERING,
    CAMP_HYGIENE,
    CAMP_IRRIGATION,
    CAMP_LOGIC,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_NAVIGATION,
    CAMP_PHILOSOPHY,
    CAMP_POTTERY,
    CAMP_RHETORIC,
    CAMP_SEAFARING,
    CAMP_SURVEYING,
    CAMP_WRITING,
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
CAMP_IRRIGATION_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_IRRIGATION.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_METALLURGY_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_METALLURGY.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_WRITING_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_WRITING.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_MATHEMATICS_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_MATHEMATICS.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_ASTRONOMY_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_ASTRONOMY.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_PHILOSOPHY_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_PHILOSOPHY.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_LOGIC_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_LOGIC.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_RHETORIC_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_RHETORIC.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_MEDICINE_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_MEDICINE.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_ANATOMY_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_ANATOMY.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_HYGIENE_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_HYGIENE.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_ENGINEERING_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_ENGINEERING.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_ARCHITECTURE_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_ARCHITECTURE.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_SURVEYING_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_SURVEYING.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_NAVIGATION_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_NAVIGATION.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_CARTOGRAPHY_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_CARTOGRAPHY.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_SEAFARING_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_SEAFARING.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)
CAMP_AGRICULTURE_RESEARCH: ResearchProgress = ResearchProgress.create(
    CAMP_AGRICULTURE.technology_id.value,
    points=0,
    threshold=DEFAULT_POTTERY_THRESHOLD,
)


def default_research_progress() -> tuple[ResearchProgress, ...]:
    """Return the canonical initial research progress set."""
    return tuple(
        sorted(
            (
                CAMP_POTTERY_RESEARCH,
                CAMP_IRRIGATION_RESEARCH,
                CAMP_METALLURGY_RESEARCH,
                CAMP_WRITING_RESEARCH,
                CAMP_MATHEMATICS_RESEARCH,
                CAMP_ASTRONOMY_RESEARCH,
                CAMP_PHILOSOPHY_RESEARCH,
                CAMP_LOGIC_RESEARCH,
                CAMP_RHETORIC_RESEARCH,
                CAMP_MEDICINE_RESEARCH,
                CAMP_ANATOMY_RESEARCH,
                CAMP_HYGIENE_RESEARCH,
                CAMP_ENGINEERING_RESEARCH,
                CAMP_ARCHITECTURE_RESEARCH,
                CAMP_SURVEYING_RESEARCH,
                CAMP_NAVIGATION_RESEARCH,
                CAMP_CARTOGRAPHY_RESEARCH,
                CAMP_SEAFARING_RESEARCH,
                CAMP_AGRICULTURE_RESEARCH,
            ),
            key=lambda item: item.technology_id.value,
        )
    )


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
    from civitas.domain.effects import effective_research_points_per_tick

    effective_points_per_tick = effective_research_points_per_tick(
        world,
        base=points_per_tick,
    )

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
        points_after = min(
            points_before + effective_points_per_tick,
            progress.threshold,
        )
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
