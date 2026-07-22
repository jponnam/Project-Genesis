"""Technology: society-known catalog of discovered techniques.

Phase 6 Milestone 1. Technologies are world-level catalog rows with a
``discovered`` flag. This milestone seeds FIRE (known) and POTTERY
(unknown). Research (Milestone 2) advances progress toward undiscovered
entries. Innovation activates society adoptions of discovered techs.
Prereq trees, agent knowledge sync, and effect wiring remain later
Phase 6 milestones.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.ids import TechnologyId
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class TechnologyKind(StrEnum):
    """Supported technology kinds."""

    FIRE = "fire"
    POTTERY = "pottery"


class Technology(BaseModel):
    """One society-level technology catalog entry."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    technology_id: TechnologyId
    name: NonEmptyStr
    kind: TechnologyKind
    discovered: bool = False

    @classmethod
    def create(
        cls,
        technology_id: int,
        name: str,
        kind: TechnologyKind | str,
        *,
        discovered: bool = False,
    ) -> Technology:
        """Construct a validated technology from primitive fields."""
        return cls(
            technology_id=TechnologyId(value=technology_id),
            name=name,
            kind=TechnologyKind(kind),
            discovered=discovered,
        )


CAMP_FIRE: Technology = Technology.create(
    0, "Camp Fire", TechnologyKind.FIRE, discovered=True
)
CAMP_POTTERY: Technology = Technology.create(
    1, "Camp Pottery", TechnologyKind.POTTERY, discovered=False
)


def default_technologies() -> tuple[Technology, ...]:
    """Return the canonical initial technology catalog."""
    return (CAMP_FIRE, CAMP_POTTERY)


class TechnologyCensus(BaseModel):
    """Aggregate technology snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    technology_count: NonNegativeInt
    discovered_count: NonNegativeInt
    undiscovered_count: NonNegativeInt
    discovered_fire_count: NonNegativeInt
    discovered_pottery_count: NonNegativeInt


def technology_by_id(
    world: World,
    technology_id: TechnologyId | int,
) -> Technology | None:
    """Return the technology with ``technology_id``, or ``None``."""
    target = (
        technology_id
        if isinstance(technology_id, TechnologyId)
        else TechnologyId(value=technology_id)
    )
    for technology in world.technologies:
        if technology.technology_id == target:
            return technology
    return None


def technology_by_kind(
    world: World,
    kind: TechnologyKind | str,
) -> Technology | None:
    """Return the technology with ``kind``, or ``None``."""
    target = kind if isinstance(kind, TechnologyKind) else TechnologyKind(kind)
    for technology in world.technologies:
        if technology.kind is target:
            return technology
    return None


def discovered_technologies(world: World) -> tuple[Technology, ...]:
    """Return discovered technologies in ascending id order."""
    return tuple(tech for tech in world.technologies if tech.discovered)


def next_technology_id(world: World) -> TechnologyId:
    """Allocate the next unused ``TechnologyId`` (max existing + 1, or 0)."""
    if not world.technologies:
        return TechnologyId(value=0)
    highest = max(tech.technology_id.value for tech in world.technologies)
    return TechnologyId(value=highest + 1)


def create_technology(world: World, technology: Technology) -> World | None:
    """Add ``technology`` to the catalog when legal."""
    if technology_by_id(world, technology.technology_id) is not None:
        return None
    if technology_by_kind(world, technology.kind) is not None:
        return None
    technologies = tuple(
        sorted(
            (*world.technologies, technology),
            key=lambda item: item.technology_id.value,
        )
    )
    return world.model_copy(update={"technologies": technologies})


def discover_technology(
    world: World,
    technology_id: TechnologyId | int,
) -> World | None:
    """Mark ``technology_id`` discovered when present.

    Already-discovered technologies return the same world. Missing ids
    return ``None``.
    """
    technology = technology_by_id(world, technology_id)
    if technology is None:
        return None
    if technology.discovered:
        return world
    updated = technology.model_copy(update={"discovered": True})
    return world.with_technology(updated)


def census_technologies(world: World) -> TechnologyCensus:
    """Build a deterministic technology census for ``world``."""
    technologies = world.technologies
    discovered = [tech for tech in technologies if tech.discovered]
    fire = sum(1 for tech in discovered if tech.kind is TechnologyKind.FIRE)
    pottery = sum(1 for tech in discovered if tech.kind is TechnologyKind.POTTERY)
    return TechnologyCensus(
        tick=world.tick,
        technology_count=len(technologies),
        discovered_count=len(discovered),
        undiscovered_count=len(technologies) - len(discovered),
        discovered_fire_count=fire,
        discovered_pottery_count=pottery,
    )
