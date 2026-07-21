"""Spatial location value objects for the simulation world.

Locations are immutable places with coordinates, a kind, and optional
resource deposits. Agents move between them and may gather deposit stock
into inventory.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from civitas.domain.attributes import ResourceStack
from civitas.domain.ids import LocationId
from civitas.domain.types import NonEmptyStr, PositiveInt


class LocationKind(StrEnum):
    """Coarse biome / site classification for a location."""

    CAMP = "camp"
    PLAIN = "plain"
    FOREST = "forest"
    RIVER = "river"
    HILL = "hill"


class Coordinates(BaseModel):
    """Integer grid coordinates on the world map."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    x: int = Field(description="East-west grid coordinate.")
    y: int = Field(description="North-south grid coordinate.")

    def manhattan_distance(self, other: Coordinates) -> int:
        """Return the Manhattan distance to ``other``."""
        return abs(self.x - other.x) + abs(self.y - other.y)


class Location(BaseModel):
    """An immutable place agents may occupy and gather from."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    location_id: LocationId
    name: NonEmptyStr
    coordinates: Coordinates
    kind: LocationKind = LocationKind.PLAIN
    capacity: PositiveInt = Field(
        default=32,
        description="Maximum agents that may occupy this location.",
    )
    deposits: tuple[ResourceStack, ...] = ()

    @model_validator(mode="after")
    def deposits_must_be_unique_and_sorted(self) -> Self:
        """Reject duplicate or unsorted deposit resource names."""
        names = [stack.resource for stack in self.deposits]
        if len(names) != len(set(names)):
            msg = "location deposits must have unique resource names"
            raise ValueError(msg)
        if names != sorted(names):
            msg = "location deposits must be ordered by resource name"
            raise ValueError(msg)
        return self

    @property
    def id(self) -> LocationId:
        """Shorthand for ``location_id``."""
        return self.location_id

    @classmethod
    def create(
        cls,
        location_id: int,
        name: str,
        x: int,
        y: int,
        *,
        kind: LocationKind = LocationKind.PLAIN,
        capacity: int = 32,
        deposits: tuple[ResourceStack, ...] | None = None,
    ) -> Location:
        """Construct a validated location from primitive fields.

        When ``deposits`` is omitted, the canonical stock for ``kind`` is
        used.
        """
        if deposits is None:
            # Lazy import avoids a location <-> resources circular import.
            from civitas.domain.resources import deposits_for_kind

            stock = deposits_for_kind(kind)
        else:
            stock = deposits
        return cls(
            location_id=LocationId(value=location_id),
            name=name,
            coordinates=Coordinates(x=x, y=y),
            kind=kind,
            capacity=capacity,
            deposits=stock,
        )


# Origin camp: spawn point with no gatherable deposits.
CAMP_LOCATION: Location = Location.create(
    0,
    "Camp",
    0,
    0,
    kind=LocationKind.CAMP,
    capacity=64,
)

# Deterministic 3x3 research map (ids 0..8). No RNG - layout is fixed.
_DEFAULT_KIND_GRID: tuple[tuple[LocationKind, ...], ...] = (
    (LocationKind.CAMP, LocationKind.PLAIN, LocationKind.FOREST),
    (LocationKind.RIVER, LocationKind.PLAIN, LocationKind.HILL),
    (LocationKind.FOREST, LocationKind.RIVER, LocationKind.HILL),
)


def default_world_map() -> tuple[Location, ...]:
    """Return the canonical 3x3 location map used by the world factory."""
    locations: list[Location] = []
    for y, row in enumerate(_DEFAULT_KIND_GRID):
        for x, kind in enumerate(row):
            location_id = y * 3 + x
            if location_id == 0:
                locations.append(CAMP_LOCATION)
                continue
            name = f"{kind.value.title()}-{x}-{y}"
            locations.append(
                Location.create(location_id, name, x, y, kind=kind, capacity=32)
            )
    return tuple(locations)
