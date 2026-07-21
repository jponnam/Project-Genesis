"""Spatial location value objects for the simulation world.

Phase 2 introduces geography. Locations are immutable places with
coordinates and a kind; movement between them arrives in a later
milestone.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

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
    """An immutable place agents may occupy."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    location_id: LocationId
    name: NonEmptyStr
    coordinates: Coordinates
    kind: LocationKind = LocationKind.PLAIN
    capacity: PositiveInt = Field(
        default=32,
        description="Maximum agents that may occupy this location.",
    )

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
    ) -> Location:
        """Construct a validated location from primitive fields."""
        return cls(
            location_id=LocationId(value=location_id),
            name=name,
            coordinates=Coordinates(x=x, y=y),
            kind=kind,
            capacity=capacity,
        )


# Origin camp: all Phase 2 agents spawn here until movement exists.
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
