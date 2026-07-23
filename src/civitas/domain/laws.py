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
grant living subjects -0.02 MOVE energy cost (Phase 14 M2). Active
``CUSTOMS`` statutes grant living subjects -0.02 PRODUCE energy cost
(Phase 14 M11). Active ``LAND_TENURE`` statutes grant living subjects
+0.05 EAT restore (Phase 15 M2), stacking with zoning. Active
``CONSERVATION`` statutes grant living subjects +1 WOOD gather (Phase 15
M11), stacking with coppice society-wide and the scaffold seat. Active
``LABOR`` statutes grant living subjects -0.02 PRODUCE energy cost
(Phase 16 M2), stacking with guild, workshop, foundry, abacus, pulley,
customs, and loom. Active ``SUMPTUARY`` statutes lower the market fill
fee at the enacting government's markets by 1 (Phase 16 M11), stacking
with bureaucracy, harbor, merchant, dyer, warehouse, and mordant.
Active ``MINERAL_RIGHTS`` statutes grant living subjects +1 STONE gather
(Phase 17 M2), stacking with pickaxe and forge society-wide, the mason
seat, and the quarry city. Active ``SAFETY_CODES`` statutes grant living
subjects -0.02 PRODUCE energy cost (Phase 17 M11), stacking with guild,
workshop, weaver, smelter, foundry, fulling mill, forge works, mill
town, tannery, bellows, lathe, abacus, pulley, customs, labor, and loom.
Active ``TIMBER_RIGHTS`` statutes grant living subjects +1 WOOD gather
(Phase 18 M2), stacking with sawmill and coppice society-wide, the
scaffold seat, the conservation subject bonus, and the pastoral city.
Active ``FOREST_MANAGEMENT`` statutes grant living subjects +1 WOOD gather
(Phase 18 M11), stacking with sawmill and coppice society-wide, the
scaffold seat, the conservation and timber-rights subject bonuses, and the
pastoral city. Active ``FIRING_CODES`` statutes grant living subjects -0.02
PRODUCE energy cost (Phase 19 M2), stacking with guild, workshop, weaver,
smelter, joiner, foundry, fulling mill, forge works, sawpit, mill town,
ironworks, guildhall, tannery, bellows, lathe, plane, dovetail, kiln,
abacus, pulley, customs, labor, safety codes, and loom.
Active ``CLAY_CODES`` statutes grant living subjects -0.02 PRODUCE energy
cost (Phase 19 M11), stacking with guild, workshop, weaver, smelter,
joiner, foundry, fulling mill, forge works, sawpit, mill town, ironworks,
guildhall, tannery, bellows, lathe, plane, dovetail, kiln, glaze, kaolin,
clay pit, kiln yard, abacus, pulley, customs, labor, safety codes, firing
codes, and loom.
Elections (voting) are a separate Phase 5 aggregate, as are institutions.
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
    CUSTOMS = "customs"
    LAND_TENURE = "land_tenure"
    CONSERVATION = "conservation"
    LABOR = "labor"
    SUMPTUARY = "sumptuary"
    MINERAL_RIGHTS = "mineral_rights"
    SAFETY_CODES = "safety_codes"
    TIMBER_RIGHTS = "timber_rights"
    FOREST_MANAGEMENT = "forest_management"
    FIRING_CODES = "firing_codes"
    CLAY_CODES = "clay_codes"


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
        LawKind.CUSTOMS,
        LawKind.LAND_TENURE,
        LawKind.CONSERVATION,
        LawKind.LABOR,
        LawKind.SUMPTUARY,
        LawKind.MINERAL_RIGHTS,
        LawKind.SAFETY_CODES,
        LawKind.TIMBER_RIGHTS,
        LawKind.FOREST_MANAGEMENT,
        LawKind.FIRING_CODES,
        LawKind.CLAY_CODES,
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

# Kind-only PRODUCE energy discount for living subjects under active CUSTOMS.
CUSTOMS_PRODUCE_ENERGY_DISCOUNT: float = 0.02

# Kind-only EAT restore bonus for living subjects under active LAND_TENURE.
LAND_TENURE_EAT_RESTORE_BONUS: float = 0.05

# Kind-only WOOD gather bonus for living subjects under active CONSERVATION.
CONSERVATION_WOOD_GATHER_BONUS: int = 1

# Kind-only PRODUCE energy discount for living subjects under active LABOR.
LABOR_PRODUCE_ENERGY_DISCOUNT: float = 0.02

# Kind-only market fill-fee discount at markets under an active SUMPTUARY law.
SUMPTUARY_MARKET_FEE_DISCOUNT: int = 1

# Kind-only STONE gather bonus for living subjects under active MINERAL_RIGHTS.
MINERAL_RIGHTS_STONE_GATHER_BONUS: int = 1

# Kind-only PRODUCE energy discount for living subjects under SAFETY_CODES.
SAFETY_CODES_PRODUCE_ENERGY_DISCOUNT: float = 0.02

# Kind-only WOOD gather bonus for living subjects under active TIMBER_RIGHTS.
TIMBER_RIGHTS_WOOD_GATHER_BONUS: int = 1

# Kind-only WOOD gather bonus for living subjects under FOREST_MANAGEMENT.
FOREST_MANAGEMENT_WOOD_GATHER_BONUS: int = 1

# Kind-only PRODUCE energy discount for living subjects under FIRING_CODES.
FIRING_CODES_PRODUCE_ENERGY_DISCOUNT: float = 0.02

# Kind-only PRODUCE energy discount for living subjects under CLAY_CODES.
CLAY_CODES_PRODUCE_ENERGY_DISCOUNT: float = 0.02


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
            "QUARANTINE, BUILDING_CODES, ZONING, PASSAGE, CUSTOMS, "
            "LAND_TENURE, CONSERVATION, LABOR, SUMPTUARY, MINERAL_RIGHTS, "
            "SAFETY_CODES, TIMBER_RIGHTS, FOREST_MANAGEMENT, FIRING_CODES, "
            "CLAY_CODES, and other kinds."
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
    active_customs_count: NonNegativeInt = 0
    active_land_tenure_count: NonNegativeInt = 0
    active_conservation_count: NonNegativeInt = 0
    active_labor_count: NonNegativeInt = 0
    active_sumptuary_count: NonNegativeInt = 0
    active_mineral_rights_count: NonNegativeInt = 0
    active_safety_codes_count: NonNegativeInt = 0
    active_timber_rights_count: NonNegativeInt = 0
    active_forest_management_count: NonNegativeInt = 0
    active_firing_codes_count: NonNegativeInt = 0
    active_clay_codes_count: NonNegativeInt = 0


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


def active_customs_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active customs statute for ``government_id``, if any.

    When multiple active ``CUSTOMS`` laws exist (should not under uniqueness
    rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.CUSTOMS:
            return law
    return None


def customs_produce_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 PRODUCE cost when ``agent`` is under active CUSTOMS.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_customs_law(world, government.government_id) is None:
        return 0.0
    return CUSTOMS_PRODUCE_ENERGY_DISCOUNT


def active_land_tenure_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active land-tenure statute for ``government_id``, if any.

    When multiple active ``LAND_TENURE`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.LAND_TENURE:
            return law
    return None


def land_tenure_eat_bonus_for(world: World, agent: Agent) -> float:
    """Return +0.05 when ``agent`` is a living subject under LAND_TENURE.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_land_tenure_law(world, government.government_id) is None:
        return 0.0
    return LAND_TENURE_EAT_RESTORE_BONUS


def active_conservation_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active conservation statute for ``government_id``, if any.

    When multiple active ``CONSERVATION`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.CONSERVATION:
            return law
    return None


def conservation_wood_bonus_for(world: World, agent: Agent) -> int:
    """Return +1 when ``agent`` is a living subject under CONSERVATION.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0
    if active_conservation_law(world, government.government_id) is None:
        return 0
    return CONSERVATION_WOOD_GATHER_BONUS


def active_labor_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active labor statute for ``government_id``, if any.

    When multiple active ``LABOR`` laws exist (should not under uniqueness
    rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.LABOR:
            return law
    return None


def labor_produce_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 PRODUCE cost when ``agent`` is under active LABOR.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_labor_law(world, government.government_id) is None:
        return 0.0
    return LABOR_PRODUCE_ENERGY_DISCOUNT


def active_sumptuary_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active sumptuary statute for ``government_id``, if any.

    When multiple active ``SUMPTUARY`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.SUMPTUARY:
            return law
    return None


def sumptuary_market_discount_for(
    world: World,
    location_id: LocationId | int,
) -> int:
    """Return the SUMPTUARY market fill-fee discount at ``location_id``, or 0.

    Market fees are location-scoped, so the government is resolved via
    ``government_at(location)``, mirroring ``market_fee_for``. The statute
    kind alone enables the discount; ``flat_amount`` is ignored.
    """
    government = government_at(world, location_id)
    if government is None:
        return 0
    if active_sumptuary_law(world, government.government_id) is None:
        return 0
    return SUMPTUARY_MARKET_FEE_DISCOUNT


def active_mineral_rights_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active mineral-rights statute for ``government_id``, if any.

    When multiple active ``MINERAL_RIGHTS`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.MINERAL_RIGHTS:
            return law
    return None


def mineral_rights_stone_bonus_for(world: World, agent: Agent) -> int:
    """Return +1 when ``agent`` is a living subject under MINERAL_RIGHTS.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0
    if active_mineral_rights_law(world, government.government_id) is None:
        return 0
    return MINERAL_RIGHTS_STONE_GATHER_BONUS


def active_safety_codes_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active safety-codes statute for ``government_id``, if any.

    When multiple active ``SAFETY_CODES`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.SAFETY_CODES:
            return law
    return None


def safety_codes_produce_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 PRODUCE cost when ``agent`` is under active SAFETY_CODES.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_safety_codes_law(world, government.government_id) is None:
        return 0.0
    return SAFETY_CODES_PRODUCE_ENERGY_DISCOUNT


def active_timber_rights_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active timber-rights statute for ``government_id``, if any.

    When multiple active ``TIMBER_RIGHTS`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.TIMBER_RIGHTS:
            return law
    return None


def timber_rights_wood_bonus_for(world: World, agent: Agent) -> int:
    """Return +1 when ``agent`` is a living subject under TIMBER_RIGHTS.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0
    if active_timber_rights_law(world, government.government_id) is None:
        return 0
    return TIMBER_RIGHTS_WOOD_GATHER_BONUS


def active_forest_management_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active forest-management statute for ``government_id``, if any.

    When multiple active ``FOREST_MANAGEMENT`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.FOREST_MANAGEMENT:
            return law
    return None


def forest_management_wood_bonus_for(world: World, agent: Agent) -> int:
    """Return +1 when ``agent`` is a living subject under FOREST_MANAGEMENT.

    The statute kind alone enables the bonus; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0
    if active_forest_management_law(world, government.government_id) is None:
        return 0
    return FOREST_MANAGEMENT_WOOD_GATHER_BONUS


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



def active_firing_codes_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active firing-codes statute for ``government_id``, if any.

    When multiple active ``FIRING_CODES`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.FIRING_CODES:
            return law
    return None


def firing_codes_produce_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 PRODUCE cost when ``agent`` is under active FIRING_CODES.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_firing_codes_law(world, government.government_id) is None:
        return 0.0
    return FIRING_CODES_PRODUCE_ENERGY_DISCOUNT


def active_clay_codes_law(
    world: World,
    government_id: GovernmentId | int,
) -> Law | None:
    """Return the active clay-codes statute for ``government_id``, if any.

    When multiple active ``CLAY_CODES`` laws exist (should not under
    uniqueness rules), the lowest ``law_id`` wins.
    """
    for law in active_laws(world, government_id):
        if law.kind == LawKind.CLAY_CODES:
            return law
    return None


def clay_codes_produce_discount_for(world: World, agent: Agent) -> float:
    """Return -0.02 PRODUCE cost when ``agent`` is under active CLAY_CODES.

    The statute kind alone enables the discount; ``flat_amount`` is ignored.
    """
    if not agent.is_alive():
        return 0.0
    government = government_at(world, agent.location_id)
    if government is None:
        return 0.0
    if active_clay_codes_law(world, government.government_id) is None:
        return 0.0
    return CLAY_CODES_PRODUCE_ENERGY_DISCOUNT


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
    active_customs = sum(1 for law in active if law.kind == LawKind.CUSTOMS)
    active_land_tenure = sum(1 for law in active if law.kind == LawKind.LAND_TENURE)
    active_conservation = sum(
        1 for law in active if law.kind == LawKind.CONSERVATION
    )
    active_labor = sum(1 for law in active if law.kind == LawKind.LABOR)
    active_sumptuary = sum(1 for law in active if law.kind == LawKind.SUMPTUARY)
    active_mineral_rights = sum(
        1 for law in active if law.kind == LawKind.MINERAL_RIGHTS
    )
    active_safety_codes = sum(
        1 for law in active if law.kind == LawKind.SAFETY_CODES
    )
    active_timber_rights = sum(
        1 for law in active if law.kind == LawKind.TIMBER_RIGHTS
    )
    active_forest_management = sum(
        1 for law in active if law.kind == LawKind.FOREST_MANAGEMENT
    )
    active_firing_codes = sum(
        1 for law in active if law.kind == LawKind.FIRING_CODES
    )
    active_clay_codes = sum(
        1 for law in active if law.kind == LawKind.CLAY_CODES
    )
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
        active_customs_count=active_customs,
        active_land_tenure_count=active_land_tenure,
        active_conservation_count=active_conservation,
        active_labor_count=active_labor,
        active_sumptuary_count=active_sumptuary,
        active_mineral_rights_count=active_mineral_rights,
        active_safety_codes_count=active_safety_codes,
        active_timber_rights_count=active_timber_rights,
        active_forest_management_count=active_forest_management,
        active_firing_codes_count=active_firing_codes,
        active_clay_codes_count=active_clay_codes,
    )


__all__ = [
    "ASSEMBLY_SOCIALIZE_RESTORE_BONUS",
    "BUILDING_CODES_MOVE_ENERGY_DISCOUNT",
    "CALENDAR_RETRIEVAL_LIMIT_BONUS",
    "CAMP_POLL_TAX_LAW",
    "CLAY_CODES_PRODUCE_ENERGY_DISCOUNT",
    "CONSERVATION_WOOD_GATHER_BONUS",
    "CURRICULUM_TEACHINGS_PER_KNOWER_BONUS",
    "CUSTOMS_PRODUCE_ENERGY_DISCOUNT",
    "ETHICS_MIN_TEACH_TRUST_DELTA",
    "FIRING_CODES_PRODUCE_ENERGY_DISCOUNT",
    "FOREST_MANAGEMENT_WOOD_GATHER_BONUS",
    "LABOR_PRODUCE_ENERGY_DISCOUNT",
    "LAND_TENURE_EAT_RESTORE_BONUS",
    "MINERAL_RIGHTS_STONE_GATHER_BONUS",
    "PASSAGE_MOVE_ENERGY_DISCOUNT",
    "QUARANTINE_REST_RESTORE_BONUS",
    "SAFETY_CODES_PRODUCE_ENERGY_DISCOUNT",
    "SANITATION_DRINK_RESTORE_BONUS",
    "SUMPTUARY_MARKET_FEE_DISCOUNT",
    "TIMBER_RIGHTS_WOOD_GATHER_BONUS",
    "ZONING_EAT_RESTORE_BONUS",
    "Law",
    "LawCensus",
    "LawKind",
    "active_assembly_law",
    "active_building_codes_law",
    "active_calendar_law",
    "active_clay_codes_law",
    "active_conservation_law",
    "active_curriculum_law",
    "active_customs_law",
    "active_ethics_law",
    "active_firing_codes_law",
    "active_forest_management_law",
    "active_labor_law",
    "active_land_tenure_law",
    "active_laws",
    "active_market_fee_law",
    "active_mineral_rights_law",
    "active_passage_law",
    "active_quarantine_law",
    "active_safety_codes_law",
    "active_sanitation_law",
    "active_sumptuary_law",
    "active_tax_schedule",
    "active_timber_rights_law",
    "active_zoning_law",
    "assembly_socialize_bonus_for",
    "building_codes_move_discount_for",
    "calendar_retrieval_bonus_for",
    "census_laws",
    "clay_codes_produce_discount_for",
    "conservation_wood_bonus_for",
    "curriculum_teachings_bonus_for",
    "customs_produce_discount_for",
    "default_laws",
    "enact_law",
    "ethics_min_teach_trust_delta_for",
    "firing_codes_produce_discount_for",
    "forest_management_wood_bonus_for",
    "labor_produce_discount_for",
    "land_tenure_eat_bonus_for",
    "law_by_id",
    "laws_for",
    "market_fee_for",
    "mineral_rights_stone_bonus_for",
    "passage_move_discount_for",
    "quarantine_rest_bonus_for",
    "repeal_law",
    "safety_codes_produce_discount_for",
    "sanitation_drink_bonus_for",
    "set_law_active",
    "sumptuary_market_discount_for",
    "tax_schedule_for_agent",
    "timber_rights_wood_bonus_for",
    "zoning_eat_bonus_for",
]
