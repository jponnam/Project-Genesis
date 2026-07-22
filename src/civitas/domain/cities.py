"""Cities: settlement designations under governments.

Phase 5 Milestone 5 introduced settlement capitals. Phase 9 Milestone 11
adds ``CityKind.OUTPOST`` for non-capital secondary seats that may share a
government with the capital but must occupy their own location. Phase 10
Milestone 5 adds ``CityKind.LIBRARY`` as another non-capital specialized
seat for record-keeping (living residents gain a retrieval-limit bonus).
Phase 10 Milestone 12 adds ``CityKind.FORUM`` as a non-capital specialized
seat for teaching (living residents gain a teachings-per-knower bonus).
Phase 11 Milestone 5 adds ``CityKind.SANCTUARY`` as a non-capital
specialized seat for reflective culture (living residents gain a REST
restore bonus). Phase 11 Milestone 12 adds ``CityKind.AGORA`` as a
non-capital specialized seat for civic social life (living residents gain
a SOCIALIZE restore bonus). Phase 12 Milestone 5 adds
``CityKind.INFIRMARY`` as a non-capital specialized seat for public
health recovery (living residents gain a REST restore bonus). Phase 12
Milestone 12 adds ``CityKind.LAZARETTO`` as a non-capital specialized
seat for quarantine care (living residents gain a DRINK restore bonus).
Phase 13 Milestone 5 adds ``CityKind.FOUNDRY`` as a non-capital
specialized seat for industrial production (living residents gain a
PRODUCE energy discount). Phase 13 Milestone 12 adds ``CityKind.QUARRY``
as a non-capital specialized seat for stone extraction (gatherers at the
seat gain a stone gather bonus). Phase 14 Milestone 5 adds
``CityKind.HARBOR`` as a non-capital specialized seat for trade routes
(markets at the seat gain a market-fee discount). Phase 14 Milestone 12
adds ``CityKind.ENTREPOT`` as a non-capital specialized seat for food
staging (gatherers at the seat gain a food gather bonus). Phase 15
Milestone 5 adds ``CityKind.FARMSTEAD`` as a non-capital specialized seat
for agriculture (gatherers at the seat gain a food gather bonus). Phase 15
Milestone 12 adds ``CityKind.PASTORAL`` as a non-capital specialized seat
for grazing land (gatherers at the seat gain a wood gather bonus). Phase 16
Milestone 5 adds ``CityKind.MILL_TOWN`` as a non-capital specialized seat
for craft production (living residents gain a PRODUCE energy discount).
Phase 16 Milestone 12 adds ``CityKind.EMPORIUM`` as a non-capital
specialized seat for trade (markets at the seat gain a market-fee
discount). Phase 17 Milestone 5 adds ``CityKind.MINING_CAMP`` as a
non-capital specialized seat for ore extraction (gatherers at the seat
gain a stone gather bonus). Phase 17 Milestone 12 adds
``CityKind.IRONWORKS`` as a non-capital specialized seat for metal
production (living residents gain a PRODUCE energy discount). Phase 18
Milestone 5 adds ``CityKind.TIMBER_TOWN`` as a non-capital specialized
seat for forestry (gatherers at the seat gain a wood gather bonus).
Resident
counts are derived from living agents at the seat. Infrastructure remains a
separate aggregate. Camp City stays the only seeded settlement capital;
libraries, forums, sanctuaries, agoras, infirmaries, lazarettos, foundries,
quarries, harbors, entrepots, farmsteads, pastorals, mill towns,
emporiums, mining camps, ironworks, and timber towns are not seeded.
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
    OUTPOST = "outpost"
    LIBRARY = "library"
    FORUM = "forum"
    SANCTUARY = "sanctuary"
    AGORA = "agora"
    INFIRMARY = "infirmary"
    LAZARETTO = "lazaretto"
    FOUNDRY = "foundry"
    QUARRY = "quarry"
    HARBOR = "harbor"
    ENTREPOT = "entrepot"
    FARMSTEAD = "farmstead"
    PASTORAL = "pastoral"
    MILL_TOWN = "mill_town"
    EMPORIUM = "emporium"
    MINING_CAMP = "mining_camp"
    IRONWORKS = "ironworks"
    TIMBER_TOWN = "timber_town"


# City kinds that may never be flagged as capital.
_NON_CAPITAL_KINDS: frozenset[CityKind] = frozenset(
    {
        CityKind.OUTPOST,
        CityKind.LIBRARY,
        CityKind.FORUM,
        CityKind.SANCTUARY,
        CityKind.AGORA,
        CityKind.INFIRMARY,
        CityKind.LAZARETTO,
        CityKind.FOUNDRY,
        CityKind.QUARRY,
        CityKind.HARBOR,
        CityKind.ENTREPOT,
        CityKind.FARMSTEAD,
        CityKind.PASTORAL,
        CityKind.MILL_TOWN,
        CityKind.EMPORIUM,
        CityKind.MINING_CAMP,
        CityKind.IRONWORKS,
        CityKind.TIMBER_TOWN,
    }
)


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
    active_outpost_count: NonNegativeInt = 0
    active_library_count: NonNegativeInt = 0
    active_forum_count: NonNegativeInt = 0
    active_sanctuary_count: NonNegativeInt = 0
    active_agora_count: NonNegativeInt = 0
    active_infirmary_count: NonNegativeInt = 0
    active_lazaretto_count: NonNegativeInt = 0
    active_foundry_count: NonNegativeInt = 0
    active_quarry_count: NonNegativeInt = 0
    active_harbor_count: NonNegativeInt = 0
    active_entrepot_count: NonNegativeInt = 0
    active_farmstead_count: NonNegativeInt = 0
    active_pastoral_count: NonNegativeInt = 0
    active_mill_town_count: NonNegativeInt = 0
    active_emporium_count: NonNegativeInt = 0
    active_mining_camp_count: NonNegativeInt = 0
    active_ironworks_count: NonNegativeInt = 0
    active_timber_town_count: NonNegativeInt = 0


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


def outposts_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return outpost cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.OUTPOST
    )


def libraries_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return library cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.LIBRARY
    )


def forums_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return forum cities for ``government_id`` in ascending id order."""
    return tuple(
        city for city in cities_for(world, government_id) if city.kind is CityKind.FORUM
    )


def sanctuaries_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return sanctuary cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.SANCTUARY
    )


def agoras_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return agora cities for ``government_id`` in ascending id order."""
    return tuple(
        city for city in cities_for(world, government_id) if city.kind is CityKind.AGORA
    )


def infirmaries_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return infirmary cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.INFIRMARY
    )


def lazarettos_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return lazaretto cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.LAZARETTO
    )


def foundries_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return foundry cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.FOUNDRY
    )


def quarries_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return quarry cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.QUARRY
    )


def harbors_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return harbor cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.HARBOR
    )


def entrepots_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return entrepot cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.ENTREPOT
    )


def farmsteads_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return farmstead cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.FARMSTEAD
    )


def pastorals_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return pastoral cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.PASTORAL
    )


def mill_towns_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return mill town cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.MILL_TOWN
    )


def emporiums_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return emporium cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.EMPORIUM
    )


def mining_camps_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return mining camp cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.MINING_CAMP
    )


def ironworks_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return ironworks cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.IRONWORKS
    )


def timber_towns_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[City, ...]:
    """Return timber town cities for ``government_id`` in ascending id order."""
    return tuple(
        city
        for city in cities_for(world, government_id)
        if city.kind is CityKind.TIMBER_TOWN
    )


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
    """Add ``city`` to the world when legal.

    Outposts, libraries, forums, sanctuaries, agoras, infirmaries,
    lazarettos, foundries, quarries, harbors, entrepots, farmsteads,
    pastorals, mill towns, emporiums, mining camps, ironworks, and
    timber towns cannot be capitals.
    Settlement capital uniqueness is unchanged:
    at most one active capital per government. Every city still needs a unique
    seat location inside its government jurisdiction.
    """
    if city.kind in _NON_CAPITAL_KINDS and city.is_capital:
        return None
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
    if is_capital and city.kind in _NON_CAPITAL_KINDS:
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
    active_outposts = sum(1 for city in active if city.kind is CityKind.OUTPOST)
    active_libraries = sum(1 for city in active if city.kind is CityKind.LIBRARY)
    active_forums = sum(1 for city in active if city.kind is CityKind.FORUM)
    active_sanctuaries = sum(1 for city in active if city.kind is CityKind.SANCTUARY)
    active_agoras = sum(1 for city in active if city.kind is CityKind.AGORA)
    active_infirmaries = sum(1 for city in active if city.kind is CityKind.INFIRMARY)
    active_lazarettos = sum(1 for city in active if city.kind is CityKind.LAZARETTO)
    active_foundries = sum(1 for city in active if city.kind is CityKind.FOUNDRY)
    active_quarries = sum(1 for city in active if city.kind is CityKind.QUARRY)
    active_harbors = sum(1 for city in active if city.kind is CityKind.HARBOR)
    active_entrepots = sum(1 for city in active if city.kind is CityKind.ENTREPOT)
    active_farmsteads = sum(1 for city in active if city.kind is CityKind.FARMSTEAD)
    active_pastorals = sum(1 for city in active if city.kind is CityKind.PASTORAL)
    active_mill_towns = sum(1 for city in active if city.kind is CityKind.MILL_TOWN)
    active_emporiums = sum(1 for city in active if city.kind is CityKind.EMPORIUM)
    active_mining_camps = sum(
        1 for city in active if city.kind is CityKind.MINING_CAMP
    )
    active_ironworks = sum(1 for city in active if city.kind is CityKind.IRONWORKS)
    active_timber_towns = sum(
        1 for city in active if city.kind is CityKind.TIMBER_TOWN
    )
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
        active_outpost_count=active_outposts,
        active_library_count=active_libraries,
        active_forum_count=active_forums,
        active_sanctuary_count=active_sanctuaries,
        active_agora_count=active_agoras,
        active_infirmary_count=active_infirmaries,
        active_lazaretto_count=active_lazarettos,
        active_foundry_count=active_foundries,
        active_quarry_count=active_quarries,
        active_harbor_count=active_harbors,
        active_entrepot_count=active_entrepots,
        active_farmstead_count=active_farmsteads,
        active_pastoral_count=active_pastorals,
        active_mill_town_count=active_mill_towns,
        active_emporium_count=active_emporiums,
        active_mining_camp_count=active_mining_camps,
        active_ironworks_count=active_ironworks,
        active_timber_town_count=active_timber_towns,
    )
