"""Infrastructure: built capacity at settlement locations.

Phase 5 Milestone 6 plus Phase 9 Milestones 5-8, Phase 10
Milestones 3 and 9, Phase 11 Milestones 4 and 9, Phase 12
Milestones 4 and 9, Phase 13 Milestones 4 and 9, and Phase 14
Milestone 4. Infrastructure pieces attach to a city seat inside a
government jurisdiction. This package seeds a single ``WELL`` kind;
``STOREHOUSE``, ``ROAD``, ``SCRIPTORIUM``, ``STOA``, ``OBSERVATORY``,
``SHRINE``, ``CLINIC``, ``BATHHOUSE``, ``BRIDGE``, ``SCAFFOLD``, and
``WAYSTATION`` are available via free create or paid construction.
Governments pay via ``build_infrastructure``; institutions pay via
``build_infrastructure_from_institution``. Effect wiring applies WELL
drink restore, STOREHOUSE/WAYSTATION food gather (stacking), SCAFFOLD
wood gather, ROAD/BRIDGE move-energy discounts, SCRIPTORIUM/STOA
teachings-per-knower bonuses, OBSERVATORY retrieval-limit bonuses,
SHRINE/CLINIC drink restore (stacking with WELL), and BATHHOUSE rest
restore for colocated agents.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.cities import CAMP_CITY, city_by_id
from civitas.domain.governments import debit_government_treasury, government_by_id
from civitas.domain.ids import (
    CityId,
    GovernmentId,
    InfrastructureId,
    InstitutionId,
    LocationId,
)
from civitas.domain.institutions import debit_institution_budget, institution_by_id
from civitas.domain.location import CAMP_LOCATION
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class InfrastructureKind(StrEnum):
    """Supported infrastructure kinds."""

    WELL = "well"
    STOREHOUSE = "storehouse"
    ROAD = "road"
    SCRIPTORIUM = "scriptorium"
    STOA = "stoa"
    OBSERVATORY = "observatory"
    SHRINE = "shrine"
    CLINIC = "clinic"
    BATHHOUSE = "bathhouse"
    BRIDGE = "bridge"
    SCAFFOLD = "scaffold"
    WAYSTATION = "waystation"


# Canonical treasury cost to construct each infrastructure kind.
DEFAULT_WELL_BUILD_COST: int = 5
DEFAULT_STOREHOUSE_BUILD_COST: int = 8
DEFAULT_ROAD_BUILD_COST: int = 6
DEFAULT_SCRIPTORIUM_BUILD_COST: int = 10
DEFAULT_STOA_BUILD_COST: int = 10
DEFAULT_OBSERVATORY_BUILD_COST: int = 12
DEFAULT_SHRINE_BUILD_COST: int = 7
DEFAULT_CLINIC_BUILD_COST: int = 8
DEFAULT_BATHHOUSE_BUILD_COST: int = 12
DEFAULT_BRIDGE_BUILD_COST: int = 9
DEFAULT_SCAFFOLD_BUILD_COST: int = 10
DEFAULT_WAYSTATION_BUILD_COST: int = 8
INFRASTRUCTURE_BUILD_COSTS: dict[InfrastructureKind, int] = {
    InfrastructureKind.WELL: DEFAULT_WELL_BUILD_COST,
    InfrastructureKind.STOREHOUSE: DEFAULT_STOREHOUSE_BUILD_COST,
    InfrastructureKind.ROAD: DEFAULT_ROAD_BUILD_COST,
    InfrastructureKind.SCRIPTORIUM: DEFAULT_SCRIPTORIUM_BUILD_COST,
    InfrastructureKind.STOA: DEFAULT_STOA_BUILD_COST,
    InfrastructureKind.OBSERVATORY: DEFAULT_OBSERVATORY_BUILD_COST,
    InfrastructureKind.SHRINE: DEFAULT_SHRINE_BUILD_COST,
    InfrastructureKind.CLINIC: DEFAULT_CLINIC_BUILD_COST,
    InfrastructureKind.BATHHOUSE: DEFAULT_BATHHOUSE_BUILD_COST,
    InfrastructureKind.BRIDGE: DEFAULT_BRIDGE_BUILD_COST,
    InfrastructureKind.SCAFFOLD: DEFAULT_SCAFFOLD_BUILD_COST,
    InfrastructureKind.WAYSTATION: DEFAULT_WAYSTATION_BUILD_COST,
}


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
    active_storehouse_count: NonNegativeInt = 0
    active_road_count: NonNegativeInt = 0
    active_scriptorium_count: NonNegativeInt = 0
    active_stoa_count: NonNegativeInt = 0
    active_observatory_count: NonNegativeInt = 0
    active_shrine_count: NonNegativeInt = 0
    active_clinic_count: NonNegativeInt = 0
    active_bathhouse_count: NonNegativeInt = 0
    active_bridge_count: NonNegativeInt = 0
    active_scaffold_count: NonNegativeInt = 0
    active_waystation_count: NonNegativeInt = 0


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


def build_cost_for(kind: InfrastructureKind | str) -> int:
    """Return the canonical treasury cost to construct ``kind``."""
    return INFRASTRUCTURE_BUILD_COSTS[InfrastructureKind(kind)]


def build_infrastructure(
    world: World,
    item: Infrastructure,
    *,
    cost: int | None = None,
) -> World | None:
    """Debit the parent government treasury, then create ``item``.

    ``cost`` defaults to the catalog price for ``item.kind``. Returns
    ``None`` when cost is non-positive, construction would be illegal,
    or the government cannot afford the cost. Free seeding continues to
    use ``create_infrastructure``.
    """
    amount = build_cost_for(item.kind) if cost is None else cost
    if amount <= 0:
        return None
    if government_by_id(world, item.government_id) is None:
        return None
    if create_infrastructure(world, item) is None:
        return None
    debited = debit_government_treasury(world, item.government_id, amount)
    if debited is None:
        return None
    return create_infrastructure(debited, item)


def build_infrastructure_from_institution(
    world: World,
    item: Infrastructure,
    institution_id: InstitutionId | int,
    *,
    cost: int | None = None,
) -> World | None:
    """Debit an institution budget, then create ``item``.

    The institution must be active and share ``item.government_id``.
    ``cost`` defaults to the catalog price for ``item.kind``. Returns
    ``None`` when cost is non-positive, construction would be illegal,
    the institution is missing/inactive/mismatched, or the budget cannot
    afford the cost.
    """
    amount = build_cost_for(item.kind) if cost is None else cost
    if amount <= 0:
        return None
    institution = institution_by_id(world, institution_id)
    if institution is None or not institution.active:
        return None
    if institution.government_id != item.government_id:
        return None
    if create_infrastructure(world, item) is None:
        return None
    debited = debit_institution_budget(world, institution.institution_id, amount)
    if debited is None:
        return None
    return create_infrastructure(debited, item)


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
    active_storehouses = sum(
        1 for item in active if item.kind is InfrastructureKind.STOREHOUSE
    )
    active_roads = sum(1 for item in active if item.kind is InfrastructureKind.ROAD)
    active_scriptoria = sum(
        1 for item in active if item.kind is InfrastructureKind.SCRIPTORIUM
    )
    active_stoas = sum(1 for item in active if item.kind is InfrastructureKind.STOA)
    active_observatories = sum(
        1 for item in active if item.kind is InfrastructureKind.OBSERVATORY
    )
    active_shrines = sum(1 for item in active if item.kind is InfrastructureKind.SHRINE)
    active_clinics = sum(1 for item in active if item.kind is InfrastructureKind.CLINIC)
    active_bathhouses = sum(
        1 for item in active if item.kind is InfrastructureKind.BATHHOUSE
    )
    active_bridges = sum(1 for item in active if item.kind is InfrastructureKind.BRIDGE)
    active_scaffolds = sum(
        1 for item in active if item.kind is InfrastructureKind.SCAFFOLD
    )
    active_waystations = sum(
        1 for item in active if item.kind is InfrastructureKind.WAYSTATION
    )
    return InfrastructureCensus(
        tick=world.tick,
        infrastructure_count=len(items),
        active_count=len(active),
        inactive_count=len(items) - len(active),
        governments_with_infrastructure=len(governments),
        cities_with_infrastructure=len(cities),
        active_well_count=active_wells,
        active_storehouse_count=active_storehouses,
        active_road_count=active_roads,
        active_scriptorium_count=active_scriptoria,
        active_stoa_count=active_stoas,
        active_observatory_count=active_observatories,
        active_shrine_count=active_shrines,
        active_clinic_count=active_clinics,
        active_bathhouse_count=active_bathhouses,
        active_bridge_count=active_bridges,
        active_scaffold_count=active_scaffolds,
        active_waystation_count=active_waystations,
    )
