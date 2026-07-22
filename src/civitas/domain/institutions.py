"""Institutions: durable organizations under governments.

Phase 5 Milestone 4 plus Phase 9 Milestone 4 budgets and Milestone 9
guilds, plus Phase 10 Milestone 2 archives, Milestone 6 bureaucracies,
and Milestone 8 academies, plus Phase 11 Milestone 3 temples,
Milestone 6 schools, and Milestone 8 lyceums, plus Phase 12 Milestone 3
hospitals, Milestone 6 apothecaries, and Milestone 8 collegia, plus
Phase 13 Milestone 3 workshops, Milestone 6 masons, and Milestone 8
architects, plus Phase 14 Milestone 3 caravans, Milestone 6
merchants, and Milestone 8 cartographers, plus Phase 15 Milestone 3
granaries, Milestone 6 husbandmen, and Milestone 8 agronomists.
Institutions are gov-attached civic organizations with a seat location
inside the government's jurisdiction, an optional officer, and an
integer budget funded from the parent government treasury. Councils,
guilds, archives, bureaucracies, academies, temples, schools, lyceums,
hospitals, apothecaries, collegia, workshops, masons, architects,
caravans, merchants, cartographers, granaries, husbandmen, and
agronomists coexist; this
package seeds a single ``COUNCIL``. Writing-gated archive creation is
a later milestone.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.governments import debit_government_treasury, government_by_id
from civitas.domain.ids import AgentId, GovernmentId, InstitutionId, LocationId
from civitas.domain.location import CAMP_LOCATION
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class InstitutionKind(StrEnum):
    """Supported institution kinds."""

    COUNCIL = "council"
    GUILD = "guild"
    ARCHIVE = "archive"
    BUREAUCRACY = "bureaucracy"
    ACADEMY = "academy"
    TEMPLE = "temple"
    SCHOOL = "school"
    LYCEUM = "lyceum"
    HOSPITAL = "hospital"
    APOTHECARY = "apothecary"
    COLLEGIUM = "collegium"
    WORKSHOP = "workshop"
    MASON = "mason"
    ARCHITECT = "architect"
    CARAVAN = "caravan"
    MERCHANT = "merchant"
    CARTOGRAPHER = "cartographer"
    GRANARY = "granary"
    HUSBANDMAN = "husbandman"
    AGRONOMIST = "agronomist"


class Institution(BaseModel):
    """One durable organization attached to a government."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    institution_id: InstitutionId
    government_id: GovernmentId
    location_id: LocationId
    name: NonEmptyStr
    kind: InstitutionKind
    active: bool = True
    officer_id: AgentId | None = None
    budget: NonNegativeInt = 0

    @classmethod
    def create(
        cls,
        institution_id: int,
        government_id: int,
        location_id: int,
        name: str,
        kind: InstitutionKind | str,
        *,
        active: bool = True,
        officer_id: int | None = None,
        budget: int = 0,
    ) -> Institution:
        """Construct a validated institution from primitive fields."""
        return cls(
            institution_id=InstitutionId(value=institution_id),
            government_id=GovernmentId(value=government_id),
            location_id=LocationId(value=location_id),
            name=name,
            kind=InstitutionKind(kind),
            active=active,
            officer_id=None if officer_id is None else AgentId(value=officer_id),
            budget=budget,
        )


# Canonical camp council seated at the camp under Camp Authority.
CAMP_COUNCIL: Institution = Institution.create(
    0,
    0,
    CAMP_LOCATION.location_id.value,
    "Camp Council",
    InstitutionKind.COUNCIL,
)


def default_institutions() -> tuple[Institution, ...]:
    """Return the canonical initial institution set."""
    return (CAMP_COUNCIL,)


class InstitutionCensus(BaseModel):
    """Aggregate institution snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    institution_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_institutions: NonNegativeInt
    staffed_count: NonNegativeInt
    vacant_officer_count: NonNegativeInt
    active_council_count: NonNegativeInt
    active_guild_count: NonNegativeInt = 0
    active_archive_count: NonNegativeInt = 0
    active_bureaucracy_count: NonNegativeInt = 0
    active_academy_count: NonNegativeInt = 0
    active_temple_count: NonNegativeInt = 0
    active_school_count: NonNegativeInt = 0
    active_lyceum_count: NonNegativeInt = 0
    active_hospital_count: NonNegativeInt = 0
    active_apothecary_count: NonNegativeInt = 0
    active_collegium_count: NonNegativeInt = 0
    active_workshop_count: NonNegativeInt = 0
    active_mason_count: NonNegativeInt = 0
    active_architect_count: NonNegativeInt = 0
    active_caravan_count: NonNegativeInt = 0
    active_merchant_count: NonNegativeInt = 0
    active_cartographer_count: NonNegativeInt = 0
    active_granary_count: NonNegativeInt = 0
    active_husbandman_count: NonNegativeInt = 0
    active_agronomist_count: NonNegativeInt = 0
    total_budget: NonNegativeInt = 0
    funded_count: NonNegativeInt = 0


def institution_by_id(
    world: World,
    institution_id: InstitutionId | int,
) -> Institution | None:
    """Return the institution with ``institution_id``, or ``None``."""
    target = (
        institution_id
        if isinstance(institution_id, InstitutionId)
        else InstitutionId(value=institution_id)
    )
    for institution in world.institutions:
        if institution.institution_id == target:
            return institution
    return None


def institutions_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[Institution, ...]:
    """Return institutions for ``government_id`` in ascending id order."""
    target = (
        government_id
        if isinstance(government_id, GovernmentId)
        else GovernmentId(value=government_id)
    )
    return tuple(
        institution
        for institution in world.institutions
        if institution.government_id == target
    )


def institution_at(
    world: World,
    location_id: LocationId | int,
) -> Institution | None:
    """Return the first active institution seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    for institution in world.institutions:
        if institution.active and institution.location_id == target:
            return institution
    return None


def active_institutions(world: World) -> tuple[Institution, ...]:
    """Return active institutions in ascending id order."""
    return tuple(
        institution for institution in world.institutions if institution.active
    )


def next_institution_id(world: World) -> InstitutionId:
    """Allocate the next unused ``InstitutionId`` (max existing + 1, or 0)."""
    if not world.institutions:
        return InstitutionId(value=0)
    highest = max(
        institution.institution_id.value for institution in world.institutions
    )
    return InstitutionId(value=highest + 1)


def officer_is_active(world: World, institution: Institution) -> bool:
    """Return True when the recorded officer exists and is alive."""
    if institution.officer_id is None:
        return False
    officer = world.agent_by_id(institution.officer_id)
    return officer is not None and officer.is_alive()


def _seat_in_jurisdiction(world: World, institution: Institution) -> bool:
    government = government_by_id(world, institution.government_id)
    if government is None:
        return False
    return any(
        location == institution.location_id for location in government.jurisdiction
    )


def _has_active_kind(
    world: World,
    government_id: GovernmentId,
    kind: InstitutionKind,
    *,
    excluding_institution_id: InstitutionId | None = None,
) -> bool:
    for institution in world.institutions:
        if (
            excluding_institution_id is not None
            and institution.institution_id == excluding_institution_id
        ):
            continue
        if (
            institution.active
            and institution.kind == kind
            and institution.government_id == government_id
        ):
            return True
    return False


def create_institution(world: World, institution: Institution) -> World | None:
    """Add ``institution`` to the world when legal."""
    if government_by_id(world, institution.government_id) is None:
        return None
    if world.location_by_id(institution.location_id) is None:
        return None
    if not _seat_in_jurisdiction(world, institution):
        return None
    if institution_by_id(world, institution.institution_id) is not None:
        return None
    if institution.officer_id is not None:
        officer = world.agent_by_id(institution.officer_id)
        if officer is None:
            return None
    if institution.active and _has_active_kind(
        world, institution.government_id, institution.kind
    ):
        return None
    institutions = tuple(
        sorted(
            (*world.institutions, institution),
            key=lambda item: item.institution_id.value,
        )
    )
    return world.model_copy(update={"institutions": institutions})


def set_institution_active(
    world: World,
    institution_id: InstitutionId | int,
    active: bool,
) -> World | None:
    """Activate or deactivate an existing institution when legal."""
    institution = institution_by_id(world, institution_id)
    if institution is None:
        return None
    if active and _has_active_kind(
        world,
        institution.government_id,
        institution.kind,
        excluding_institution_id=institution.institution_id,
    ):
        return None
    if institution.active == active:
        return world
    updated = institution.model_copy(update={"active": active})
    return world.with_institution(updated)


def dissolve_institution(
    world: World,
    institution_id: InstitutionId | int,
) -> World | None:
    """Deactivate ``institution_id`` (soft dissolve); ``None`` if missing."""
    return set_institution_active(world, institution_id, False)


def set_officer(
    world: World,
    institution_id: InstitutionId | int,
    officer_id: AgentId | int | None,
) -> World | None:
    """Appoint or clear an institution officer when legal.

    A non-``None`` officer must exist, be alive, and currently occupy a
    location inside the parent government's jurisdiction.
    """
    institution = institution_by_id(world, institution_id)
    if institution is None:
        return None
    government = government_by_id(world, institution.government_id)
    if government is None:
        return None

    if officer_id is None:
        updated = institution.model_copy(update={"officer_id": None})
        return world.with_institution(updated)

    target = (
        officer_id if isinstance(officer_id, AgentId) else AgentId(value=officer_id)
    )
    agent = world.agent_by_id(target)
    if agent is None or not agent.is_alive():
        return None
    covered = {location.value for location in government.jurisdiction}
    if agent.location_id.value not in covered:
        return None
    updated = institution.model_copy(update={"officer_id": target})
    return world.with_institution(updated)


def institution_budget_total(world: World) -> int:
    """Return the sum of all institution budget balances."""
    return sum(institution.budget for institution in world.institutions)


def credit_institution_budget(
    world: World,
    institution_id: InstitutionId | int,
    amount: int,
) -> World | None:
    """Add ``amount`` to an institution's budget when legal."""
    if amount <= 0:
        return None
    institution = institution_by_id(world, institution_id)
    if institution is None:
        return None
    updated = institution.model_copy(update={"budget": institution.budget + amount})
    return world.with_institution(updated)


def debit_institution_budget(
    world: World,
    institution_id: InstitutionId | int,
    amount: int,
) -> World | None:
    """Subtract ``amount`` from an institution's budget when affordable."""
    if amount <= 0:
        return None
    institution = institution_by_id(world, institution_id)
    if institution is None:
        return None
    if institution.budget < amount:
        return None
    updated = institution.model_copy(update={"budget": institution.budget - amount})
    return world.with_institution(updated)


def fund_institution_from_treasury(
    world: World,
    institution_id: InstitutionId | int,
    amount: int,
) -> World | None:
    """Move ``amount`` from the parent government treasury into the budget.

    Debits the institution's government treasury, then credits the
    institution budget. Returns ``None`` when the institution is missing,
    inactive, the parent government is missing, or the treasury cannot
    afford ``amount``.
    """
    if amount <= 0:
        return None
    institution = institution_by_id(world, institution_id)
    if institution is None or not institution.active:
        return None
    if government_by_id(world, institution.government_id) is None:
        return None
    debited = debit_government_treasury(world, institution.government_id, amount)
    if debited is None:
        return None
    credited = credit_institution_budget(debited, institution.institution_id, amount)
    if credited is None:
        return None
    return credited


def census_institutions(world: World) -> InstitutionCensus:
    """Build a deterministic institution census for ``world``."""
    institutions = world.institutions
    active = [institution for institution in institutions if institution.active]
    governments = {institution.government_id.value for institution in institutions}
    staffed = sum(
        1 for institution in institutions if officer_is_active(world, institution)
    )
    vacant = len(institutions) - staffed
    active_councils = sum(
        1 for institution in active if institution.kind is InstitutionKind.COUNCIL
    )
    active_guilds = sum(
        1 for institution in active if institution.kind is InstitutionKind.GUILD
    )
    active_archives = sum(
        1 for institution in active if institution.kind is InstitutionKind.ARCHIVE
    )
    active_bureaucracies = sum(
        1 for institution in active if institution.kind is InstitutionKind.BUREAUCRACY
    )
    active_academies = sum(
        1 for institution in active if institution.kind is InstitutionKind.ACADEMY
    )
    active_temples = sum(
        1 for institution in active if institution.kind is InstitutionKind.TEMPLE
    )
    active_schools = sum(
        1 for institution in active if institution.kind is InstitutionKind.SCHOOL
    )
    active_lyceums = sum(
        1 for institution in active if institution.kind is InstitutionKind.LYCEUM
    )
    active_hospitals = sum(
        1 for institution in active if institution.kind is InstitutionKind.HOSPITAL
    )
    active_apothecaries = sum(
        1 for institution in active if institution.kind is InstitutionKind.APOTHECARY
    )
    active_collegia = sum(
        1 for institution in active if institution.kind is InstitutionKind.COLLEGIUM
    )
    active_workshops = sum(
        1 for institution in active if institution.kind is InstitutionKind.WORKSHOP
    )
    active_masons = sum(
        1 for institution in active if institution.kind is InstitutionKind.MASON
    )
    active_architects = sum(
        1 for institution in active if institution.kind is InstitutionKind.ARCHITECT
    )
    active_caravans = sum(
        1 for institution in active if institution.kind is InstitutionKind.CARAVAN
    )
    active_merchants = sum(
        1 for institution in active if institution.kind is InstitutionKind.MERCHANT
    )
    active_cartographers = sum(
        1 for institution in active if institution.kind is InstitutionKind.CARTOGRAPHER
    )
    active_granaries = sum(
        1 for institution in active if institution.kind is InstitutionKind.GRANARY
    )
    active_husbandmen = sum(
        1 for institution in active if institution.kind is InstitutionKind.HUSBANDMAN
    )
    active_agronomists = sum(
        1 for institution in active if institution.kind is InstitutionKind.AGRONOMIST
    )
    total_budget = institution_budget_total(world)
    funded_count = sum(1 for institution in institutions if institution.budget > 0)
    return InstitutionCensus(
        tick=world.tick,
        institution_count=len(institutions),
        active_count=len(active),
        inactive_count=len(institutions) - len(active),
        governments_with_institutions=len(governments),
        staffed_count=staffed,
        vacant_officer_count=vacant,
        active_council_count=active_councils,
        active_guild_count=active_guilds,
        active_archive_count=active_archives,
        active_bureaucracy_count=active_bureaucracies,
        active_academy_count=active_academies,
        active_temple_count=active_temples,
        active_school_count=active_schools,
        active_lyceum_count=active_lyceums,
        active_hospital_count=active_hospitals,
        active_apothecary_count=active_apothecaries,
        active_collegium_count=active_collegia,
        active_workshop_count=active_workshops,
        active_mason_count=active_masons,
        active_architect_count=active_architects,
        active_caravan_count=active_caravans,
        active_merchant_count=active_merchants,
        active_cartographer_count=active_cartographers,
        active_granary_count=active_granaries,
        active_husbandman_count=active_husbandmen,
        active_agronomist_count=active_agronomists,
        total_budget=total_budget,
        funded_count=funded_count,
    )
