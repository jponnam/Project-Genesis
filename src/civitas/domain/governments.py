"""Governments: polities with jurisdiction, treasury, and optional leader.

A government is a location-anchored public authority. Domain helpers own
lookups, treasury mutations, leader appointment, and censuses. Laws attach
to governments separately. Leaders may be appointed via ``set_leader`` or
filled by ``conduct_election`` (voting). Tax redirection to government
treasuries remains a later Phase 5 milestone.
"""

from __future__ import annotations

from statistics import fmean
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from civitas.domain.ids import AgentId, GovernmentId, LocationId
from civitas.domain.location import CAMP_LOCATION, default_world_map
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class Government(BaseModel):
    """A polity that rules a disjoint set of locations."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    government_id: GovernmentId
    name: NonEmptyStr
    seat_location_id: LocationId
    jurisdiction: tuple[LocationId, ...] = Field(
        description="Locations under this polity; seat must be included."
    )
    treasury: NonNegativeInt = 0
    leader_id: AgentId | None = None

    @model_validator(mode="after")
    def jurisdiction_must_be_valid(self) -> Self:
        """Reject empty, unsorted, duplicate, or seat-missing jurisdictions."""
        values = [location.value for location in self.jurisdiction]
        if not values:
            msg = "government jurisdiction must be non-empty"
            raise ValueError(msg)
        if len(values) != len(set(values)):
            msg = "government jurisdiction location ids must be unique"
            raise ValueError(msg)
        if values != sorted(values):
            msg = "government jurisdiction must be ordered by ascending location_id"
            raise ValueError(msg)
        if self.seat_location_id.value not in values:
            msg = "government seat_location_id must be inside jurisdiction"
            raise ValueError(msg)
        return self

    @classmethod
    def create(
        cls,
        government_id: int,
        name: str,
        seat_location_id: int,
        jurisdiction: tuple[int, ...],
        *,
        treasury: int = 0,
        leader_id: int | None = None,
    ) -> Government:
        """Construct a validated government from primitive fields."""
        return cls(
            government_id=GovernmentId(value=government_id),
            name=name,
            seat_location_id=LocationId(value=seat_location_id),
            jurisdiction=tuple(LocationId(value=value) for value in jurisdiction),
            treasury=treasury,
            leader_id=None if leader_id is None else AgentId(value=leader_id),
        )


# Canonical camp-centered authority covering the full default map.
CAMP_GOVERNMENT: Government = Government.create(
    0,
    "Camp Authority",
    CAMP_LOCATION.location_id.value,
    tuple(location.location_id.value for location in default_world_map()),
)


def default_governments() -> tuple[Government, ...]:
    """Return the canonical initial government set."""
    return (CAMP_GOVERNMENT,)


class GovernmentCensus(BaseModel):
    """Aggregate polity snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    government_count: NonNegativeInt
    covered_location_count: NonNegativeInt
    uncovered_location_count: NonNegativeInt
    total_treasury: NonNegativeInt
    led_count: NonNegativeInt = Field(
        description="Governments whose leader currently exists and is alive."
    )
    vacant_leader_count: NonNegativeInt
    living_subject_count: NonNegativeInt
    mean_subjects: float
    max_subjects: NonNegativeInt
    max_subjects_government_id: GovernmentId | None = None


def government_by_id(
    world: World,
    government_id: GovernmentId | int,
) -> Government | None:
    """Return the government with ``government_id``, or ``None``."""
    target = (
        government_id
        if isinstance(government_id, GovernmentId)
        else GovernmentId(value=government_id)
    )
    for government in world.governments:
        if government.government_id == target:
            return government
    return None


def government_at(
    world: World,
    location_id: LocationId | int,
) -> Government | None:
    """Return the government whose jurisdiction contains ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    for government in world.governments:
        if any(loc == target for loc in government.jurisdiction):
            return government
    return None


def living_subjects(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[Agent, ...]:
    """Return living agents located inside the government's jurisdiction."""
    government = government_by_id(world, government_id)
    if government is None:
        return ()
    covered = {location.value for location in government.jurisdiction}
    return tuple(
        agent for agent in world.alive_agents() if agent.location_id.value in covered
    )


def subject_count(world: World, government_id: GovernmentId | int) -> int:
    """Return the count of living subjects for ``government_id``."""
    return len(living_subjects(world, government_id))


def leader_is_active(world: World, government: Government) -> bool:
    """Return True when the recorded leader exists and is alive."""
    if government.leader_id is None:
        return False
    leader = world.agent_by_id(government.leader_id)
    return leader is not None and leader.is_alive()


def credit_government_treasury(
    world: World,
    government_id: GovernmentId | int,
    amount: int,
) -> World | None:
    """Add ``amount`` to a government's treasury when legal."""
    if amount <= 0:
        return None
    government = government_by_id(world, government_id)
    if government is None:
        return None
    updated = government.model_copy(update={"treasury": government.treasury + amount})
    return world.with_government(updated)


def debit_government_treasury(
    world: World,
    government_id: GovernmentId | int,
    amount: int,
) -> World | None:
    """Subtract ``amount`` from a government's treasury when affordable."""
    if amount <= 0:
        return None
    government = government_by_id(world, government_id)
    if government is None:
        return None
    if government.treasury < amount:
        return None
    updated = government.model_copy(update={"treasury": government.treasury - amount})
    return world.with_government(updated)


def set_leader(
    world: World,
    government_id: GovernmentId | int,
    leader_id: AgentId | int | None,
) -> World | None:
    """Appoint or clear a government leader when legal.

    A non-``None`` leader must exist, be alive, and currently occupy a
    location inside the government's jurisdiction.
    """
    government = government_by_id(world, government_id)
    if government is None:
        return None
    if leader_id is None:
        updated = government.model_copy(update={"leader_id": None})
        return world.with_government(updated)

    target = leader_id if isinstance(leader_id, AgentId) else AgentId(value=leader_id)
    agent = world.agent_by_id(target)
    if agent is None or not agent.is_alive():
        return None
    covered = {location.value for location in government.jurisdiction}
    if agent.location_id.value not in covered:
        return None
    updated = government.model_copy(update={"leader_id": target})
    return world.with_government(updated)


def census_governments(world: World) -> GovernmentCensus:
    """Build a deterministic government census for ``world``."""
    governments = world.governments
    covered: set[int] = set()
    for government in governments:
        covered.update(location.value for location in government.jurisdiction)
    uncovered = len(world.locations) - len(covered)

    led_count = sum(
        1 for government in governments if leader_is_active(world, government)
    )
    vacant_leader_count = len(governments) - led_count
    subject_counts = [
        subject_count(world, government.government_id) for government in governments
    ]
    living_subject_count = sum(subject_counts)
    if subject_counts:
        mean_subjects = round(fmean(subject_counts), 6)
        max_subjects = max(subject_counts)
        max_gov = max(
            governments,
            key=lambda gov: (
                subject_count(world, gov.government_id),
                -gov.government_id.value,
            ),
        )
        max_subjects_government_id = max_gov.government_id
    else:
        mean_subjects = 0.0
        max_subjects = 0
        max_subjects_government_id = None

    return GovernmentCensus(
        tick=world.tick,
        government_count=len(governments),
        covered_location_count=len(covered),
        uncovered_location_count=max(0, uncovered),
        total_treasury=sum(government.treasury for government in governments),
        led_count=led_count,
        vacant_leader_count=vacant_leader_count,
        living_subject_count=living_subject_count,
        mean_subjects=mean_subjects,
        max_subjects=max_subjects,
        max_subjects_government_id=max_subjects_government_id,
    )


__all__ = [
    "CAMP_GOVERNMENT",
    "Government",
    "GovernmentCensus",
    "census_governments",
    "credit_government_treasury",
    "debit_government_treasury",
    "default_governments",
    "government_at",
    "government_by_id",
    "leader_is_active",
    "living_subjects",
    "set_leader",
    "subject_count",
]
