"""Unit tests for location geography models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_LOCATION,
    Coordinates,
    Location,
    LocationKind,
    default_world_map,
)


def test_camp_location_is_origin() -> None:
    """The canonical camp sits at (0, 0) with id 0."""
    assert CAMP_LOCATION.location_id.value == 0
    assert CAMP_LOCATION.coordinates == Coordinates(x=0, y=0)
    assert CAMP_LOCATION.kind is LocationKind.CAMP


def test_default_world_map_is_three_by_three() -> None:
    """Factory map is a fixed 3x3 grid with unique ids and coordinates."""
    locations = default_world_map()
    assert len(locations) == 9
    assert locations[0] == CAMP_LOCATION
    assert [loc.location_id.value for loc in locations] == list(range(9))
    coords = {(loc.coordinates.x, loc.coordinates.y) for loc in locations}
    assert coords == {(x, y) for x in range(3) for y in range(3)}


def test_default_world_map_is_stable() -> None:
    """The canonical map does not depend on RNG and is identical every call."""
    assert default_world_map() == default_world_map()


def test_manhattan_distance() -> None:
    """Manhattan distance is |dx| + |dy|."""
    origin = Coordinates(x=0, y=0)
    assert origin.manhattan_distance(Coordinates(x=2, y=3)) == 5


def test_location_create_and_frozen() -> None:
    """Location.create builds validated immutable locations."""
    location = Location.create(4, "Forest-1-1", 1, 1, kind=LocationKind.FOREST)
    assert location.name == "Forest-1-1"
    assert location.kind is LocationKind.FOREST
    with pytest.raises(ValidationError):
        location.name = "X"  # type: ignore[misc]


def test_location_rejects_non_positive_capacity() -> None:
    """Capacity must be at least 1."""
    with pytest.raises(ValidationError):
        Location.create(1, "Bad", 1, 0, capacity=0)
