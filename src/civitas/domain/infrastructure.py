"""Infrastructure: built capacity at settlement locations.

Phase 5 Milestone 6. Infrastructure pieces attach to a city seat inside a
government jurisdiction. This milestone seeds a single ``WELL`` kind as
declarative water capacity. Tech trees, build costs, roads, storehouses,
and build costs remain later milestones. Effect wiring (Phase 8) applies
WELL drink-restore bonuses for colocated agents.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.cities import CAMP_CITY, city_by_id
from civitas.domain.governments import government_by_id
from civitas.domain.ids import CityId, GovernmentId, InfrastructureId, LocationId
from civitas.domain.location import CAMP_LOCATION
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class InfrastructureKind(StrEnum):
    """Supported infrastructure kinds."""

    WELL = "well"


class Infrastructure(BaseModel):
    """One built capacity piece attached to a city seat."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    infrastructure_id: InfrastructureId
    government_id: GovernmentId
    city_id: CityId
    location_id: LocationId
    name: NonEmptyStr
    kind: InfrastructureKind
    active: bool = True

    @classmethod
    def create(
        cls,
        infrastructure_id: int,
        government_id: int,
        city_id: int,
        location_id: int,
        name: str,
        kind: InfrastructureKind | str,
        *,
        active: bool = True,
    ) -> Infrastructure:
        """Construct a validated infrastructure piece from primitive fields."""
        return cls(
            infrastructure_id=InfrastructureId(value=infrastructure_id),
            government_id=GovernmentId(value=government_id),
            city_id=CityId(value=city_id),
            location_id=LocationId(value=location_id),
            name=name,
            kind=InfrastructureKind(kind),
            active=active,
        )


# Canonical camp well at Camp City under Camp Authority.
CAMP_WELL: Infrastructure = Infrastructure.create(
    0,
    0,
    CAMP_CITY.city_id.value,
    CAMP_LOCATION.location_id.value,
    "Camp Well",
    InfrastructureKind.WELL,
)


def default_infrastructure() -> tuple[Infrastructure, ...]:
    """Return the canonical initial infrastructure set."""
    return (CAMP_WELL,)


class InfrastructureCensus(BaseModel):
    """Aggregate infrastructure snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    infrastructure_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_infrastructure: NonNegativeInt
    cities_with_infrastructure: NonNegativeInt
    active_well_count: NonNegativeInt


def infrastructure_by_id(
    world: World,
    infrastructure_id: InfrastructureId | int,
) -> Infrastructure | None:
    """Return the infrastructure with ``infrastructure_id``, or ``None``."""
    target = (
        infrastructure_id
        if isinstance(infrastructure_id, InfrastructureId)
        else InfrastructureId(value=infrastructure_id)
    )
    for item in world.infrastructure:
        if item.infrastructure_id == target:
            return item
    return None


def infrastructure_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[Infrastructure, ...]:
    """Return infrastructure for ``government_id`` in ascending id order."""
    target = (
        government_id
        if isinstance(government_id, GovernmentId)
        else GovernmentId(value=government_id)
    )
    return tuple(item for item in world.infrastructure if item.government_id == target)


def infrastructure_for_city(
    world: World,
    city_id: CityId | int,
) -> tuple[Infrastructure, ...]:
    """Return infrastructure for ``city_id`` in ascending id order."""
    target = city_id if isinstance(city_id, CityId) else CityId(value=city_id)
    return tuple(item for item in world.infrastructure if item.city_id == target)


def infrastructure_at(
    world: World,
    location_id: LocationId | int,
) -> tuple[Infrastructure, ...]:
    """Return active infrastructure seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return tuple(
        item
        for item in world.infrastructure
        if item.active and item.location_id == target
    )


def active_infrastructure(world: World) -> tuple[Infrastructure, ...]:
    """Return active infrastructure in ascending id order."""
    return tuple(item for item in world.infrastructure if item.active)


def next_infrastructure_id(world: World) -> InfrastructureId:
    """Allocate the next unused ``InfrastructureId`` (max existing + 1, or 0)."""
    if not world.infrastructure:
        return InfrastructureId(value=0)
    highest = max(item.infrastructure_id.value for item in world.infrastructure)
    return InfrastructureId(value=highest + 1)


def _links_are_consistent(world: World, item: Infrastructure) -> bool:
    government = government_by_id(world, item.government_id)
    if government is None:
        return False
    if world.location_by_id(item.location_id) is None:
        return False
    city = city_by_id(world, item.city_id)
    if city is None:
        return False
    if city.government_id != item.government_id:
        return False
    if city.location_id != item.location_id:
        return False
    return any(location == item.location_id for location in government.jurisdiction)


def _has_active_kind_at_location(
    world: World,
    location_id: LocationId,
    kind: InfrastructureKind,
    *,
    excluding_infrastructure_id: InfrastructureId | None = None,
) -> bool:
    for item in world.infrastructure:
        if (
            excluding_infrastructure_id is not None
            and item.infrastructure_id == excluding_infrastructure_id
        ):
            continue
        if item.active and item.kind == kind and item.location_id == location_id:
            return True
    return False


def create_infrastructure(
    world: World,
    item: Infrastructure,
) -> World | None:
    """Add ``item`` to the world when legal."""
    if not _links_are_consistent(world, item):
        return None
    if infrastructure_by_id(world, item.infrastructure_id) is not None:
        return None
    if item.active and _has_active_kind_at_location(world, item.location_id, item.kind):
        return None
    infrastructure = tuple(
        sorted(
            (*world.infrastructure, item),
            key=lambda entry: entry.infrastructure_id.value,
        )
    )
    return world.model_copy(update={"infrastructure": infrastructure})


def set_infrastructure_active(
    world: World,
    infrastructure_id: InfrastructureId | int,
    active: bool,
) -> World | None:
    """Activate or deactivate existing infrastructure when legal."""
    item = infrastructure_by_id(world, infrastructure_id)
    if item is None:
        return None
    if active and _has_active_kind_at_location(
        world,
        item.location_id,
        item.kind,
        excluding_infrastructure_id=item.infrastructure_id,
    ):
        return None
    if item.active == active:
        return world
    updated = item.model_copy(update={"active": active})
    return world.with_infrastructure(updated)


def dissolve_infrastructure(
    world: World,
    infrastructure_id: InfrastructureId | int,
) -> World | None:
    """Deactivate ``infrastructure_id`` (soft dissolve); ``None`` if missing."""
    return set_infrastructure_active(world, infrastructure_id, False)


def census_infrastructure(world: World) -> InfrastructureCensus:
    """Build a deterministic infrastructure census for ``world``."""
    items = world.infrastructure
    active = [item for item in items if item.active]
    governments = {item.government_id.value for item in items}
    cities = {item.city_id.value for item in items}
    active_wells = sum(1 for item in active if item.kind is InfrastructureKind.WELL)
    return InfrastructureCensus(
        tick=world.tick,
        infrastructure_count=len(items),
        active_count=len(active),
        inactive_count=len(items) - len(active),
        governments_with_infrastructure=len(governments),
        cities_with_infrastructure=len(cities),
        active_well_count=active_wells,
    )
