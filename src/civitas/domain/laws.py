"""Laws: statutes attached to governments with optional tax effects.

Laws are first-class world aggregates. Domain helpers own enactment,
repeal, and tax-schedule lookup. Active ``TAX_SCHEDULE`` statutes override
fallback levy parameters when collecting taxes. Voting and other statute
kinds are later Phase 5 milestones.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.governments import government_at, government_by_id
from civitas.domain.ids import GovernmentId, LawId
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class LawKind(StrEnum):
    """Supported statute kinds."""

    TAX_SCHEDULE = "tax_schedule"


class Law(BaseModel):
    """One statute enacted by a government."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    law_id: LawId
    government_id: GovernmentId
    name: NonEmptyStr
    kind: LawKind
    active: bool = True
    flat_amount: NonNegativeInt = Field(
        default=0,
        description="TAX_SCHEDULE flat poll amount; ignored by other kinds.",
    )
    rate_bps: NonNegativeInt = Field(
        default=0,
        description="TAX_SCHEDULE wealth rate in basis points.",
    )

    @classmethod
    def create(
        cls,
        law_id: int,
        government_id: int,
        name: str,
        kind: LawKind | str,
        *,
        active: bool = True,
        flat_amount: int = 0,
        rate_bps: int = 0,
    ) -> Law:
        """Construct a validated law from primitive fields."""
        return cls(
            law_id=LawId(value=law_id),
            government_id=GovernmentId(value=government_id),
            name=name,
            kind=LawKind(kind),
            active=active,
            flat_amount=flat_amount,
            rate_bps=rate_bps,
        )


# Canonical camp poll-tax statute (matches default TaxConfig flat amount).
CAMP_POLL_TAX_LAW: Law = Law.create(
    0,
    0,
    "Camp Poll Tax",
    LawKind.TAX_SCHEDULE,
    flat_amount=1,
    rate_bps=0,
    active=True,
)


def default_laws() -> tuple[Law, ...]:
    """Return the canonical initial law set."""
    return (CAMP_POLL_TAX_LAW,)


class LawCensus(BaseModel):
    """Aggregate statute snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    law_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_active_laws: NonNegativeInt
    active_tax_schedule_count: NonNegativeInt


def law_by_id(world: World, law_id: LawId | int) -> Law | None:
    """Return the law with ``law_id``, or ``None``."""
    target = law_id if isinstance(law_id, LawId) else LawId(value=law_id)
    for law in world.laws:
        if law.law_id == target:
            return law
    return None


def laws_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[Law, ...]:
    """Return all statutes for ``government_id`` in ascending law id order."""
    target = (
        government_id
        if isinstance(government_id, GovernmentId)
        else GovernmentId(value=government_id)
    )
    return tuple(law for law in world.laws if law.government_id == target)


def active_laws(
    world: World,
    government_id: GovernmentId | int | None = None,
) -> tuple[Law, ...]:
    """Return active statutes, optionally filtered by government."""
    laws = world.laws if government_id is None else laws_for(world, government_id)
    return tuple(law for law in laws if law.active)


def active_tax_schedule(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active tax schedule for ``government_id``, if any."""
    for law in active_laws(world, government_id):
        if law.kind == LawKind.TAX_SCHEDULE:
            return law
    return None


def tax_schedule_for_agent(
    world: World,
    agent: Agent,
) -> tuple[int, int] | None:
    """Return ``(flat_amount, rate_bps)`` from the agent's polity tax law."""
    government = government_at(world, agent.location_id)
    if government is None:
        return None
    law = active_tax_schedule(world, government.government_id)
    if law is None:
        return None
    return (law.flat_amount, law.rate_bps)


def _has_active_tax_schedule(
    world: World,
    government_id: GovernmentId,
    *,
    excluding_law_id: LawId | None = None,
) -> bool:
    for law in world.laws:
        if excluding_law_id is not None and law.law_id == excluding_law_id:
            continue
        if (
            law.active
            and law.kind == LawKind.TAX_SCHEDULE
            and law.government_id == government_id
        ):
            return True
    return False


def enact_law(world: World, law: Law) -> World | None:
    """Add ``law`` to the world when legal."""
    if government_by_id(world, law.government_id) is None:
        return None
    if law_by_id(world, law.law_id) is not None:
        return None
    if (
        law.active
        and law.kind == LawKind.TAX_SCHEDULE
        and _has_active_tax_schedule(world, law.government_id)
    ):
        return None
    laws = tuple(sorted((*world.laws, law), key=lambda item: item.law_id.value))
    return world.model_copy(update={"laws": laws})


def set_law_active(
    world: World,
    law_id: LawId | int,
    active: bool,
) -> World | None:
    """Activate or deactivate an existing law when legal."""
    law = law_by_id(world, law_id)
    if law is None:
        return None
    if (
        active
        and law.kind == LawKind.TAX_SCHEDULE
        and _has_active_tax_schedule(
            world,
            law.government_id,
            excluding_law_id=law.law_id,
        )
    ):
        return None
    if law.active == active:
        return world
    updated = law.model_copy(update={"active": active})
    return world.with_law(updated)


def repeal_law(world: World, law_id: LawId | int) -> World | None:
    """Deactivate ``law_id`` (soft repeal); returns ``None`` if missing."""
    return set_law_active(world, law_id, False)


def census_laws(world: World) -> LawCensus:
    """Build a deterministic law census for ``world``."""
    laws = world.laws
    active = [law for law in laws if law.active]
    governments_with_active = {law.government_id.value for law in active}
    active_tax = sum(1 for law in active if law.kind == LawKind.TAX_SCHEDULE)
    return LawCensus(
        tick=world.tick,
        law_count=len(laws),
        active_count=len(active),
        inactive_count=len(laws) - len(active),
        governments_with_active_laws=len(governments_with_active),
        active_tax_schedule_count=active_tax,
    )


__all__ = [
    "CAMP_POLL_TAX_LAW",
    "Law",
    "LawCensus",
    "LawKind",
    "active_laws",
    "active_tax_schedule",
    "census_laws",
    "default_laws",
    "enact_law",
    "law_by_id",
    "laws_for",
    "repeal_law",
    "set_law_active",
    "tax_schedule_for_agent",
]
