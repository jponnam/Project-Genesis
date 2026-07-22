"""Technology: society-known catalog of discovered techniques.

Phase 6 Milestone 1. Technologies are world-level catalog rows with a
``discovered`` flag. This milestone seeds FIRE (known) and POTTERY
(unknown). Research (Milestone 2) advances progress toward undiscovered
entries. Innovation activates society adoptions of discovered techs.
Knowledge diffusion syncs facts onto agents. Effect wiring (Phase 8)
applies active-innovation bonuses. Phase 9 Milestone 1 adds prerequisite
trees that gate discovery and research advance.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, field_validator

from civitas.domain.ids import TechnologyId
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class TechnologyKind(StrEnum):
    """Supported technology kinds."""

    FIRE = "fire"
    POTTERY = "pottery"
    IRRIGATION = "irrigation"
    METALLURGY = "metallurgy"
    WRITING = "writing"
    MATHEMATICS = "mathematics"
    ASTRONOMY = "astronomy"
    PHILOSOPHY = "philosophy"
    LOGIC = "logic"
    RHETORIC = "rhetoric"
    MEDICINE = "medicine"
    ANATOMY = "anatomy"
    HYGIENE = "hygiene"
    ENGINEERING = "engineering"
    ARCHITECTURE = "architecture"
    SURVEYING = "surveying"


class Technology(BaseModel):
    """One society-level technology catalog entry."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    technology_id: TechnologyId
    name: NonEmptyStr
    kind: TechnologyKind
    discovered: bool = False
    prerequisite_ids: tuple[TechnologyId, ...] = ()

    @field_validator("prerequisite_ids")
    @classmethod
    def prerequisites_must_be_unique_and_sorted(
        cls,
        value: tuple[TechnologyId, ...],
    ) -> tuple[TechnologyId, ...]:
        """Reject duplicate or unsorted prerequisite ids."""
        values = [item.value for item in value]
        if len(values) != len(set(values)):
            msg = "prerequisite ids must be unique"
            raise ValueError(msg)
        if values != sorted(values):
            msg = "prerequisite ids must be ordered by ascending technology_id"
            raise ValueError(msg)
        return value

    @classmethod
    def create(
        cls,
        technology_id: int,
        name: str,
        kind: TechnologyKind | str,
        *,
        discovered: bool = False,
        prerequisite_ids: tuple[int, ...] = (),
    ) -> Technology:
        """Construct a validated technology from primitive fields."""
        prereqs = tuple(
            TechnologyId(value=item) for item in sorted(set(prerequisite_ids))
        )
        return cls(
            technology_id=TechnologyId(value=technology_id),
            name=name,
            kind=TechnologyKind(kind),
            discovered=discovered,
            prerequisite_ids=prereqs,
        )


CAMP_FIRE: Technology = Technology.create(
    0, "Camp Fire", TechnologyKind.FIRE, discovered=True
)
CAMP_POTTERY: Technology = Technology.create(
    1,
    "Camp Pottery",
    TechnologyKind.POTTERY,
    discovered=False,
    prerequisite_ids=(0,),
)
CAMP_IRRIGATION: Technology = Technology.create(
    2,
    "Camp Irrigation",
    TechnologyKind.IRRIGATION,
    discovered=False,
    prerequisite_ids=(1,),
)
CAMP_METALLURGY: Technology = Technology.create(
    3,
    "Camp Metallurgy",
    TechnologyKind.METALLURGY,
    discovered=False,
    prerequisite_ids=(2,),
)
CAMP_WRITING: Technology = Technology.create(
    4,
    "Camp Writing",
    TechnologyKind.WRITING,
    discovered=False,
    prerequisite_ids=(3,),
)
CAMP_MATHEMATICS: Technology = Technology.create(
    5,
    "Camp Mathematics",
    TechnologyKind.MATHEMATICS,
    discovered=False,
    prerequisite_ids=(4,),
)
CAMP_ASTRONOMY: Technology = Technology.create(
    6,
    "Camp Astronomy",
    TechnologyKind.ASTRONOMY,
    discovered=False,
    prerequisite_ids=(5,),
)
CAMP_PHILOSOPHY: Technology = Technology.create(
    7,
    "Camp Philosophy",
    TechnologyKind.PHILOSOPHY,
    discovered=False,
    prerequisite_ids=(6,),
)
CAMP_LOGIC: Technology = Technology.create(
    8,
    "Camp Logic",
    TechnologyKind.LOGIC,
    discovered=False,
    prerequisite_ids=(7,),
)
CAMP_RHETORIC: Technology = Technology.create(
    9,
    "Camp Rhetoric",
    TechnologyKind.RHETORIC,
    discovered=False,
    prerequisite_ids=(8,),
)
CAMP_MEDICINE: Technology = Technology.create(
    10,
    "Camp Medicine",
    TechnologyKind.MEDICINE,
    discovered=False,
    prerequisite_ids=(9,),
)
CAMP_ANATOMY: Technology = Technology.create(
    11,
    "Camp Anatomy",
    TechnologyKind.ANATOMY,
    discovered=False,
    prerequisite_ids=(10,),
)
CAMP_HYGIENE: Technology = Technology.create(
    12,
    "Camp Hygiene",
    TechnologyKind.HYGIENE,
    discovered=False,
    prerequisite_ids=(11,),
)
CAMP_ENGINEERING: Technology = Technology.create(
    13,
    "Camp Engineering",
    TechnologyKind.ENGINEERING,
    discovered=False,
    prerequisite_ids=(12,),
)
CAMP_ARCHITECTURE: Technology = Technology.create(
    14,
    "Camp Architecture",
    TechnologyKind.ARCHITECTURE,
    discovered=False,
    prerequisite_ids=(13,),
)
CAMP_SURVEYING: Technology = Technology.create(
    15,
    "Camp Surveying",
    TechnologyKind.SURVEYING,
    discovered=False,
    prerequisite_ids=(14,),
)


def default_technologies() -> tuple[Technology, ...]:
    """Return the canonical initial technology catalog."""
    return (
        CAMP_FIRE,
        CAMP_POTTERY,
        CAMP_IRRIGATION,
        CAMP_METALLURGY,
        CAMP_WRITING,
        CAMP_MATHEMATICS,
        CAMP_ASTRONOMY,
        CAMP_PHILOSOPHY,
        CAMP_LOGIC,
        CAMP_RHETORIC,
        CAMP_MEDICINE,
        CAMP_ANATOMY,
        CAMP_HYGIENE,
        CAMP_ENGINEERING,
        CAMP_ARCHITECTURE,
        CAMP_SURVEYING,
    )


class TechnologyCensus(BaseModel):
    """Aggregate technology snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    technology_count: NonNegativeInt
    discovered_count: NonNegativeInt
    undiscovered_count: NonNegativeInt
    discovered_fire_count: NonNegativeInt
    discovered_pottery_count: NonNegativeInt
    discovered_irrigation_count: NonNegativeInt
    discovered_metallurgy_count: NonNegativeInt = 0
    discovered_writing_count: NonNegativeInt = 0
    discovered_mathematics_count: NonNegativeInt = 0
    discovered_astronomy_count: NonNegativeInt = 0
    discovered_philosophy_count: NonNegativeInt = 0
    discovered_logic_count: NonNegativeInt = 0
    discovered_rhetoric_count: NonNegativeInt = 0
    discovered_medicine_count: NonNegativeInt = 0
    discovered_anatomy_count: NonNegativeInt = 0
    discovered_hygiene_count: NonNegativeInt = 0
    discovered_engineering_count: NonNegativeInt = 0
    discovered_architecture_count: NonNegativeInt = 0
    discovered_surveying_count: NonNegativeInt = 0
    locked_count: NonNegativeInt
    researchable_count: NonNegativeInt


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


def prerequisites_met(world: World, technology: Technology) -> bool:
    """Return True when every prerequisite of ``technology`` is discovered."""
    for prerequisite_id in technology.prerequisite_ids:
        required = technology_by_id(world, prerequisite_id)
        if required is None or not required.discovered:
            return False
    return True


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
    for prerequisite_id in technology.prerequisite_ids:
        if prerequisite_id.value == technology.technology_id.value:
            return None
        if technology_by_id(world, prerequisite_id) is None:
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
    """Mark ``technology_id`` discovered when present and unlocked.

    Already-discovered technologies return the same world. Missing ids or
    unmet prerequisites return ``None``.
    """
    technology = technology_by_id(world, technology_id)
    if technology is None:
        return None
    if technology.discovered:
        return world
    if not prerequisites_met(world, technology):
        return None
    updated = technology.model_copy(update={"discovered": True})
    return world.with_technology(updated)


def census_technologies(world: World) -> TechnologyCensus:
    """Build a deterministic technology census for ``world``."""
    technologies = world.technologies
    discovered = [tech for tech in technologies if tech.discovered]
    undiscovered = [tech for tech in technologies if not tech.discovered]
    locked = [tech for tech in undiscovered if not prerequisites_met(world, tech)]
    researchable = [tech for tech in undiscovered if prerequisites_met(world, tech)]
    fire = sum(1 for tech in discovered if tech.kind is TechnologyKind.FIRE)
    pottery = sum(1 for tech in discovered if tech.kind is TechnologyKind.POTTERY)
    irrigation = sum(1 for tech in discovered if tech.kind is TechnologyKind.IRRIGATION)
    metallurgy = sum(1 for tech in discovered if tech.kind is TechnologyKind.METALLURGY)
    writing = sum(1 for tech in discovered if tech.kind is TechnologyKind.WRITING)
    mathematics = sum(
        1 for tech in discovered if tech.kind is TechnologyKind.MATHEMATICS
    )
    astronomy = sum(1 for tech in discovered if tech.kind is TechnologyKind.ASTRONOMY)
    philosophy = sum(1 for tech in discovered if tech.kind is TechnologyKind.PHILOSOPHY)
    logic = sum(1 for tech in discovered if tech.kind is TechnologyKind.LOGIC)
    rhetoric = sum(1 for tech in discovered if tech.kind is TechnologyKind.RHETORIC)
    medicine = sum(1 for tech in discovered if tech.kind is TechnologyKind.MEDICINE)
    anatomy = sum(1 for tech in discovered if tech.kind is TechnologyKind.ANATOMY)
    hygiene = sum(1 for tech in discovered if tech.kind is TechnologyKind.HYGIENE)
    engineering = sum(
        1 for tech in discovered if tech.kind is TechnologyKind.ENGINEERING
    )
    architecture = sum(
        1 for tech in discovered if tech.kind is TechnologyKind.ARCHITECTURE
    )
    surveying = sum(
        1 for tech in discovered if tech.kind is TechnologyKind.SURVEYING
    )
    return TechnologyCensus(
        tick=world.tick,
        technology_count=len(technologies),
        discovered_count=len(discovered),
        undiscovered_count=len(undiscovered),
        discovered_fire_count=fire,
        discovered_pottery_count=pottery,
        discovered_irrigation_count=irrigation,
        discovered_metallurgy_count=metallurgy,
        discovered_writing_count=writing,
        discovered_mathematics_count=mathematics,
        discovered_astronomy_count=astronomy,
        discovered_philosophy_count=philosophy,
        discovered_logic_count=logic,
        discovered_rhetoric_count=rhetoric,
        discovered_medicine_count=medicine,
        discovered_anatomy_count=anatomy,
        discovered_hygiene_count=hygiene,
        discovered_engineering_count=engineering,
        discovered_architecture_count=architecture,
        discovered_surveying_count=surveying,
        locked_count=len(locked),
        researchable_count=len(researchable),
    )
