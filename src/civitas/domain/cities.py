"""Cities: settlement designations under governments.

Phase 5 Milestone 5. A city designates a location inside a government's
jurisdiction as a settlement, with an optional capital flag. Resident
counts are derived from living agents at the seat. Infrastructure is a
separate Phase 5 aggregate; extra city kinds remain later milestones.
"""

from __future__ import annotations

from enum import StrEnum
from statistics import fmean
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.governments import government_by_id
from civitas.domain.ids import CityId, GovernmentId, LocationId
from civitas.domain.location import CAMP_LOCATION
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class CityKind(StrEnum):
    """Supported city / settlement kinds."""

    SETTLEMENT = "settlement"


class City(BaseModel):
    """One settlement designation attached to a government location."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    city_id: CityId
    government_id: GovernmentId
    location_id: LocationId
    name: NonEmptyStr
    kind: CityKind
    active: bool = True
    is_capital: bool = False

    @classmethod
    def create(
        cls,
        city_id: int,
        government_id: int,
        location_id: int,
        name: str,
        kind: CityKind | str,
        *,
        active: bool = True,
        is_capital: bool = False,
    ) -> City:
        """Construct a validated city from primitive fields."""
        return cls(
            city_id=CityId(value=city_id),
            government_id=GovernmentId(value=government_id),
            location_id=LocationId(value=location_id),
            name=name,
            kind=CityKind(kind),
            active=active,
            is_capital=is_capital,
        )


# Canonical camp settlement / capital under Camp Authority.
CAMP_CITY: City = City.create(
    0,
    0,
    CAMP_LOCATION.location_id.value,
    "Camp City",
    CityKind.SETTLEMENT,
    is_capital=True,
)


def default_cities() -> tuple[City, ...]:
    """Return the canonical initial city set."""
    return (CAMP_CITY,)


class CityCensus(BaseModel):
    """Aggregate city snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    city_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_cities: NonNegativeInt
    capital_count: NonNegativeInt
    total_residents: NonNegativeInt
    mean_residents: float
    max_residents: NonNegativeInt
    max_residents_city_id: CityId | None = None
    active_settlement_count: NonNegativeInt


def city_by_id(world: World, city_id: CityId | int) -> City | None:
    """Return the city with ``city_id``, or ``None``."""
    target = city_id if isinstance(city_id, CityId) else CityId(value=city_id)
    for city in world.cities:
        if city.city_id == target:
            return city
    return None


def cities_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return cities for ``government_id`` in ascending id order."""
    target = (
        government_id
        if isinstance(government_id, GovernmentId)
        else GovernmentId(value=government_id)
    )
    return tuple(city for city in world.cities if city.government_id == target)


def city_at(world: World, location_id: LocationId | int) -> City | None:
    """Return the city seated at ``location_id``, or ``None``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    for city in world.cities:
        if city.location_id == target:
            return city
    return None


def active_cities(world: World) -> tuple[City, ...]:
    """Return active cities in ascending id order."""
    return tuple(city for city in world.cities if city.active)


def capital_for(
    world: World,
    government_id: GovernmentId | int,
) -> City | None:
    """Return the active capital for ``government_id``, or ``None``."""
    for city in cities_for(world, government_id):
        if city.active and city.is_capital:
            return city
    return None


def next_city_id(world: World) -> CityId:
    """Allocate the next unused ``CityId`` (max existing + 1, or 0)."""
    if not world.cities:
        return CityId(value=0)
    highest = max(city.city_id.value for city in world.cities)
    return CityId(value=highest + 1)


def residents(world: World, city_id: CityId | int) -> tuple[Agent, ...]:
    """Return living agents currently occupying the city's seat location."""
    city = city_by_id(world, city_id)
    if city is None:
        return ()
    return tuple(
        agent for agent in world.alive_agents() if agent.location_id == city.location_id
    )


def resident_count(world: World, city_id: CityId | int) -> int:
    """Return the count of living residents for ``city_id``."""
    return len(residents(world, city_id))


def _seat_in_jurisdiction(world: World, city: City) -> bool:
    government = government_by_id(world, city.government_id)
    if government is None:
        return False
    return any(location == city.location_id for location in government.jurisdiction)


def _has_active_capital(
    world: World,
    government_id: GovernmentId,
    *,
    excluding_city_id: CityId | None = None,
) -> bool:
    for city in world.cities:
        if excluding_city_id is not None and city.city_id == excluding_city_id:
            continue
        if city.active and city.is_capital and city.government_id == government_id:
            return True
    return False


def create_city(world: World, city: City) -> World | None:
    """Add ``city`` to the world when legal."""
    if government_by_id(world, city.government_id) is None:
        return None
    if world.location_by_id(city.location_id) is None:
        return None
    if not _seat_in_jurisdiction(world, city):
        return None
    if city_by_id(world, city.city_id) is not None:
        return None
    if city_at(world, city.location_id) is not None:
        return None
    if (
        city.active
        and city.is_capital
        and _has_active_capital(world, city.government_id)
    ):
        return None
    cities = tuple(sorted((*world.cities, city), key=lambda item: item.city_id.value))
    return world.model_copy(update={"cities": cities})


def set_city_active(
    world: World,
    city_id: CityId | int,
    active: bool,
) -> World | None:
    """Activate or deactivate an existing city when legal."""
    city = city_by_id(world, city_id)
    if city is None:
        return None
    if (
        active
        and city.is_capital
        and _has_active_capital(
            world,
            city.government_id,
            excluding_city_id=city.city_id,
        )
    ):
        return None
    if city.active == active:
        return world
    updated = city.model_copy(update={"active": active})
    return world.with_city(updated)


def dissolve_city(world: World, city_id: CityId | int) -> World | None:
    """Deactivate ``city_id`` (soft dissolve); ``None`` if missing."""
    return set_city_active(world, city_id, False)


def set_capital(
    world: World,
    city_id: CityId | int,
    is_capital: bool,
) -> World | None:
    """Set or clear the capital flag for ``city_id`` when legal.

    Setting capital on an active city clears any other active capital for
    the same government. Inactive cities cannot become capital.
    """
    city = city_by_id(world, city_id)
    if city is None:
        return None
    if is_capital and not city.active:
        return None
    if city.is_capital == is_capital:
        return world

    if not is_capital:
        updated = city.model_copy(update={"is_capital": False})
        return world.with_city(updated)

    # Clear other capitals for this government, then set this city.
    working = world
    for other in cities_for(working, city.government_id):
        if other.city_id == city.city_id:
            continue
        if other.is_capital:
            cleared = other.model_copy(update={"is_capital": False})
            working = working.with_city(cleared)
    updated = city.model_copy(update={"is_capital": True})
    return working.with_city(updated)


def census_cities(world: World) -> CityCensus:
    """Build a deterministic city census for ``world``."""
    cities = world.cities
    active = [city for city in cities if city.active]
    governments = {city.government_id.value for city in cities}
    capitals = [city for city in active if city.is_capital]
    resident_counts = [resident_count(world, city.city_id) for city in active]
    total_residents = sum(resident_counts)
    if resident_counts:
        mean_residents = float(fmean(resident_counts))
        max_residents = max(resident_counts)
        max_city = active[resident_counts.index(max_residents)]
        max_residents_city_id = max_city.city_id
    else:
        mean_residents = 0.0
        max_residents = 0
        max_residents_city_id = None
    active_settlements = sum(1 for city in active if city.kind is CityKind.SETTLEMENT)
    return CityCensus(
        tick=world.tick,
        city_count=len(cities),
        active_count=len(active),
        inactive_count=len(cities) - len(active),
        governments_with_cities=len(governments),
        capital_count=len(capitals),
        total_residents=total_residents,
        mean_residents=mean_residents,
        max_residents=max_residents,
        max_residents_city_id=max_residents_city_id,
        active_settlement_count=active_settlements,
    )
