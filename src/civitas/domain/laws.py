"""Laws: statutes attached to governments with optional fiscal effects.

Laws are first-class world aggregates. Domain helpers own enactment,
repeal, tax-schedule lookup, market-fee lookup, curriculum teaching
bonuses, calendar retrieval bonuses, ethics teach-trust deltas,
assembly socialize bonuses, sanitation drink bonuses, quarantine rest
bonuses, building-code move discounts, and passage move discounts.
Active ``TAX_SCHEDULE`` statutes override fallback levy parameters
when collecting taxes. Active ``MARKET_FEE`` statutes charge a flat
buyer fee on market listing fills (Phase 9 M10). Active ``CURRICULUM``
statutes grant living subjects +1 teachings-per-knower (Phase 10 M4).
Active ``CALENDAR`` statutes grant living subjects +1 retrieval limit
(Phase 10 M11). Active ``ETHICS`` statutes lower the peer teach-trust
threshold for living subject learners by 0.05 (Phase 11 M2).
Active ``ASSEMBLY`` statutes grant living subjects +0.05 SOCIALIZE
restore (Phase 11 M11). Active ``SANITATION`` statutes grant living
subjects +0.05 DRINK restore (Phase 12 M2). Active ``QUARANTINE``
statutes grant living subjects +0.05 REST restore (Phase 12 M11).
Active ``BUILDING_CODES`` statutes grant living subjects -0.02 MOVE
energy cost (Phase 13 M2). Active ``ZONING`` statutes grant living
subjects +0.05 EAT restore (Phase 13 M11). Active ``PASSAGE`` statutes
grant living subjects -0.02 MOVE energy cost (Phase 14 M2).
Elections (voting) are a separate Phase 5 aggregate, as are
institutions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.governments import government_at, government_by_id
from civitas.domain.ids import GovernmentId, LawId, LocationId
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World


class LawKind(StrEnum):
    """Supported statute kinds."""

    TAX_SCHEDULE = "tax_schedule"
    MARKET_FEE = "market_fee"
    CURRICULUM = "curriculum"
    CALENDAR = "calendar"
    ETHICS = "ethics"
    ASSEMBLY = "assembly"
    SANITATION = "sanitation"
    QUARANTINE = "quarantine"
    BUILDING_CODES = "building_codes"
    ZONING = "zoning"
    PASSAGE = "passage"


# Statute kinds that allow at most one active law per government.
_UNIQUE_ACTIVE_KINDS: frozenset[LawKind] = frozenset(
    {
        LawKind.TAX_SCHEDULE,
        LawKind.MARKET_FEE,
        LawKind.CURRICULUM,
        LawKind.CALENDAR,
        LawKind.ETHICS,
        LawKind.ASSEMBLY,
        LawKind.SANITATION,
        LawKind.QUARANTINE,
        LawKind.BUILDING_CODES,
        LawKind.ZONING,
        LawKind.PASSAGE,
    }
)

# Kind-only teachings bonus for living subjects under an active CURRICULUM.
CURRICULUM_TEACHINGS_PER_KNOWER_BONUS: int = 1

# Kind-only retrieval-limit bonus for living subjects under an active CALENDAR.
CALENDAR_RETRIEVAL_LIMIT_BONUS: int = 1

# Kind-only teach-trust delta for living subject learners under active ETHICS.
ETHICS_MIN_TEACH_TRUST_DELTA: float = -0.05

# Kind-only SOCIALIZE restore bonus for living subjects under active ASSEMBLY.
ASSEMBLY_SOCIALIZE_RESTORE_BONUS: float = 0.05

# Kind-only DRINK restore bonus for living subjects under active SANITATION.
SANITATION_DRINK_RESTORE_BONUS: float = 0.05

# Kind-only REST restore bonus for living subjects under active QUARANTINE.
QUARANTINE_REST_RESTORE_BONUS: float = 0.05

# Kind-only MOVE energy discount for living subjects under active BUILDING_CODES.
BUILDING_CODES_MOVE_ENERGY_DISCOUNT: float = 0.02

# Kind-only EAT restore bonus for living subjects under active ZONING.
ZONING_EAT_RESTORE_BONUS: float = 0.05

# Kind-only MOVE energy discount for living subjects under active PASSAGE.
PASSAGE_MOVE_ENERGY_DISCOUNT: float = 0.02


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
        description=(
            "TAX_SCHEDULE flat poll amount, or MARKET_FEE flat fill fee; "
            "ignored by CURRICULUM, CALENDAR, ETHICS, ASSEMBLY, SANITATION, "
            "QUARANTINE, BUILDING_CODES, ZONING, PASSAGE, and other kinds."
        ),
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
    active_market_fee_count: NonNegativeInt
    active_curriculum_count: NonNegativeInt
    active_calendar_count: NonNegativeInt
    active_ethics_count: NonNegativeInt
    active_assembly_count: NonNegativeInt
    active_sanitation_count: NonNegativeInt
    active_quarantine_count: NonNegativeInt
    active_building_codes_count: NonNegativeInt
    active_zoning_count: NonNegativeInt = 0
    active_passage_count: NonNegativeInt = 0


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


def active_market_fee_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active market-fee statute for ``government_id``, if any.

    When multiple active ``MARKET_FEE`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.MARKET_FEE:
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


def market_fee_for(world: World, location_id: LocationId | int) -> int:
    """Return the flat market fill fee at ``location_id``, or 0.

    Looks up the active ``MARKET_FEE`` law for ``government_at(location)``.
    """
    government = government_at(world, location_id)
    if government is None:
        return 0
    law = active_market_fee_law(world, government.government_id)
    if law is None:
        return 0
    return law.flat_amount


def active_curriculum_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active curriculum statute for ``government_id``, if any.

    When multiple active ``CURRICULUM`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.CURRICULUM:
            return law
    return None


def curriculum_teachings_bonus_for(world: World, agent: Agent) -> int:
    """Return +1 when ``agent`` is a living subject under active CURRICULUM.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0
    if active_curriculum_law(world, government.government_id) is None:
        return 0
    return CURRICULUM_TEACHINGS_PER_KNOWER_BONUS


def active_calendar_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active calendar statute for ``government_id``, if any.

    When multiple active ``CALENDAR`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.CALENDAR:
            return law
    return None


def calendar_retrieval_bonus_for(world: World, agent: Agent) -> int:
    """Return +1 when ``agent`` is a living subject under active CALENDAR.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0
    if active_calendar_law(world, government.government_id) is None:
        return 0
    return CALENDAR_RETRIEVAL_LIMIT_BONUS


def active_ethics_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active ethics statute for ``government_id``, if any.

    When multiple active ``ETHICS`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.ETHICS:
            return law
    return None


def ethics_min_teach_trust_delta_for(world: World, learner: Agent) -> float:
    """Return -0.05 when ``learner`` is a living subject under active ETHICS.

    The statute kind alone enables the delta; ``flat_amount`` is ignored.
    Callers clamp ``base + delta`` into ``[0, 1]`` before teach checks.
    """
    if not learner.is_alive():
        return 0.0
    government = government_at(world, learner.location_id)
    if government is None:
        return 0.0
    if active_ethics_law(world, government.government_id) is None:
        return 0.0
    return ETHICS_MIN_TEACH_TRUST_DELTA


def active_assembly_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active assembly statute for ``government_id``, if any.

    When multiple active ``ASSEMBLY`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.ASSEMBLY:
            return law
    return None


def assembly_socialize_bonus_for(world: World, agent: Agent) -> float:
    """Return +0.05 when ``agent`` is a living subject under active ASSEMBLY.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_assembly_law(world, government.government_id) is None:
        return 0.0
    return ASSEMBLY_SOCIALIZE_RESTORE_BONUS


def active_sanitation_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active sanitation statute for ``government_id``, if any.

    When multiple active ``SANITATION`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.SANITATION:
            return law
    return None


def sanitation_drink_bonus_for(world: World, agent: Agent) -> float:
    """Return +0.05 when ``agent`` is a living subject under active SANITATION.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_sanitation_law(world, government.government_id) is None:
        return 0.0
    return SANITATION_DRINK_RESTORE_BONUS


def active_quarantine_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active quarantine statute for ``government_id``, if any.

    When multiple active ``QUARANTINE`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.QUARANTINE:
            return law
    return None


def quarantine_rest_bonus_for(world: World, agent: Agent) -> float:
    """Return +0.05 when ``agent`` is a living subject under active QUARANTINE.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_quarantine_law(world, government.government_id) is None:
        return 0.0
    return QUARANTINE_REST_RESTORE_BONUS


def active_building_codes_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active building-code statute for ``government_id``, if any.

    When multiple active ``BUILDING_CODES`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.BUILDING_CODES:
            return law
    return None


def building_codes_move_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 MOVE cost when ``agent`` is under active BUILDING_CODES.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_building_codes_law(world, government.government_id) is None:
        return 0.0
    return BUILDING_CODES_MOVE_ENERGY_DISCOUNT


def active_zoning_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active zoning statute for ``government_id``, if any.

    When multiple active ``ZONING`` laws exist (should not under uniqueness
    rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.ZONING:
            return law
    return None


def zoning_eat_bonus_for(world: World, agent: Agent) -> float:
    """Return +0.05 when ``agent`` is a living subject under active ZONING.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_zoning_law(world, government.government_id) is None:
        return 0.0
    return ZONING_EAT_RESTORE_BONUS


def active_passage_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active passage statute for ``government_id``, if any.

    When multiple active ``PASSAGE`` laws exist (should not under uniqueness
    rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.PASSAGE:
            return law
    return None


def passage_move_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 MOVE cost when ``agent`` is under active PASSAGE.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_passage_law(world, government.government_id) is None:
        return 0.0
    return PASSAGE_MOVE_ENERGY_DISCOUNT


def _has_active_kind(
    world: World,
    government_id: GovernmentId,
    kind: LawKind,
    *,
    excluding_law_id: LawId | None = None,
) -> bool:
    for law in world.laws:
        if excluding_law_id is not None and law.law_id == excluding_law_id:
            continue
        if law.active and law.kind == kind and law.government_id == government_id:
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
        and law.kind in _UNIQUE_ACTIVE_KINDS
        and _has_active_kind(world, law.government_id, law.kind)
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
        and law.kind in _UNIQUE_ACTIVE_KINDS
        and _has_active_kind(
            world,
            law.government_id,
            law.kind,
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
    active_fee = sum(1 for law in active if law.kind == LawKind.MARKET_FEE)
    active_curriculum = sum(1 for law in active if law.kind == LawKind.CURRICULUM)
    active_calendar = sum(1 for law in active if law.kind == LawKind.CALENDAR)
    active_ethics = sum(1 for law in active if law.kind == LawKind.ETHICS)
    active_assembly = sum(1 for law in active if law.kind == LawKind.ASSEMBLY)
    active_sanitation = sum(1 for law in active if law.kind == LawKind.SANITATION)
    active_quarantine = sum(1 for law in active if law.kind == LawKind.QUARANTINE)
    active_building_codes = sum(
        1 for law in active if law.kind == LawKind.BUILDING_CODES
    )
    active_zoning = sum(1 for law in active if law.kind == LawKind.ZONING)
    active_passage = sum(1 for law in active if law.kind == LawKind.PASSAGE)
    return LawCensus(
        tick=world.tick,
        law_count=len(laws),
        active_count=len(active),
        inactive_count=len(laws) - len(active),
        governments_with_active_laws=len(governments_with_active),
        active_tax_schedule_count=active_tax,
        active_market_fee_count=active_fee,
        active_curriculum_count=active_curriculum,
        active_calendar_count=active_calendar,
        active_ethics_count=active_ethics,
        active_assembly_count=active_assembly,
        active_sanitation_count=active_sanitation,
        active_quarantine_count=active_quarantine,
        active_building_codes_count=active_building_codes,
        active_zoning_count=active_zoning,
        active_passage_count=active_passage,
    )


__all__ = [
    "ASSEMBLY_SOCIALIZE_RESTORE_BONUS",
    "BUILDING_CODES_MOVE_ENERGY_DISCOUNT",
    "CALENDAR_RETRIEVAL_LIMIT_BONUS",
    "CAMP_POLL_TAX_LAW",
    "CURRICULUM_TEACHINGS_PER_KNOWER_BONUS",
    "ETHICS_MIN_TEACH_TRUST_DELTA",
    "PASSAGE_MOVE_ENERGY_DISCOUNT",
    "QUARANTINE_REST_RESTORE_BONUS",
    "SANITATION_DRINK_RESTORE_BONUS",
    "ZONING_EAT_RESTORE_BONUS",
    "Law",
    "LawCensus",
    "LawKind",
    "active_assembly_law",
    "active_building_codes_law",
    "active_calendar_law",
    "active_curriculum_law",
    "active_ethics_law",
    "active_laws",
    "active_market_fee_law",
    "active_passage_law",
    "active_quarantine_law",
    "active_sanitation_law",
    "active_tax_schedule",
    "active_zoning_law",
    "assembly_socialize_bonus_for",
    "building_codes_move_discount_for",
    "calendar_retrieval_bonus_for",
    "census_laws",
    "curriculum_teachings_bonus_for",
    "default_laws",
    "enact_law",
    "ethics_min_teach_trust_delta_for",
    "law_by_id",
    "laws_for",
    "market_fee_for",
    "passage_move_discount_for",
    "quarantine_rest_bonus_for",
    "repeal_law",
    "sanitation_drink_bonus_for",
    "set_law_active",
    "tax_schedule_for_agent",
    "zoning_eat_bonus_for",
]
