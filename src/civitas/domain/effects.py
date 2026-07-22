"""Society effect wiring from innovations and infrastructure.

Phase 8 wired active innovations into REST/GATHER outcomes and WELL
drink-restore bonuses. Phase 9 adds location-scoped STOREHOUSE food-gather
bonuses, ROAD move-energy discounts, and GUILD produce-energy discounts.
Phase 10 adds ARCHIVE retrieval-limit bonuses, SCRIPTORIUM
teachings-per-knower bonuses, CURRICULUM law teachings bonuses
(stacking with the global scribe innovation), LIBRARY city
retrieval-limit bonuses (stacking with archive), BUREAUCRACY
market-fee discounts, a global ABACUS produce-energy discount
(stacking with guild seat discounts), ACADEMY
teachings-per-knower bonuses (stacking with scribe/scriptorium/
curriculum), OBSERVATORY retrieval-limit bonuses (stacking with
archive and library), a global STAR_CHART retrieval-limit
bonus (stacking with archive, library, and observatory),
CALENDAR law retrieval-limit bonuses for living subjects
(stacking with archive, library, observatory, and star chart),
and FORUM city teachings-per-knower bonuses (stacking with
academy/scriptorium/curriculum/scribe), plus a global DIALECTIC
teachings-per-knower bonus (stacking with scribe). Phase 11 adds
TEMPLE REST restore bonuses (stacking with the global fire-hearth
innovation), SHRINE DRINK restore bonuses (stacking with WELL),
SANCTUARY city REST restore bonuses (stacking with fire hearth and
temple), SCHOOL teachings-per-knower bonuses (stacking with
scribe/scriptorium/stoa/curriculum/academy/forum/dialectic), a global
SYLLOGISM research-points bonus, LYCEUM retrieval-limit bonuses
(stacking with archive/library/observatory/star-chart/calendar), a
global ORATION SOCIALIZE restore bonus, and ASSEMBLY law SOCIALIZE
restore bonuses for living subjects (stacking with oration), and AGORA
city SOCIALIZE restore bonuses for agents at the city seat (stacking with
oration and assembly). Phase 12 adds a global REMEDY REST restore bonus
(stacking with fire hearth, temple, and sanctuary), SANITATION law
DRINK restore bonuses for living subjects (stacking with well and shrine),
HOSPITAL REST restore bonuses (stacking with fire hearth, remedy, temple,
and sanctuary), CLINIC DRINK restore bonuses (stacking with well,
shrine, and sanitation), INFIRMARY city REST restore bonuses (stacking
with fire hearth, remedy, temple, sanctuary, and hospital), and BATHHOUSE
REST restore bonuses (stacking with every prior REST source).
Phase 12 Milestone 6 adds APOTHECARY DRINK restore bonuses (stacking with
well, shrine, clinic, and sanitation). Phase 12 Milestone 7 adds a global
DISSECTION research-points bonus (stacking with syllogism). Phase 12
Milestone 8 adds COLLEGIUM teachings-per-knower bonuses (stacking with
scribe/dialectic/scriptorium/academy/forum/school/stoa/curriculum).
Phase 12 Milestone 10 adds a global ASEPSIS DRINK restore bonus (stacking
with well, shrine, clinic, apothecary, and sanitation). Phase 12 Milestone
11 adds QUARANTINE law REST restore bonuses for living subjects (stacking
with every prior REST source). Phase 12 Milestone 12 adds LAZARETTO city
DRINK restore bonuses (stacking with every prior DRINK source). Phase 13
Milestone 1 adds a global PULLEY produce-energy discount (stacking with
guild seat and abacus discounts). Phase 13 Milestone 2 adds BUILDING_CODES
law MOVE energy discounts for living subjects (stacking with ROAD seats).
Phase 13 Milestone 3 adds WORKSHOP produce-energy discounts at the
institution seat (stacking with guild, abacus, and pulley). Phase 13
Milestone 4 adds BRIDGE MOVE energy discounts at the infrastructure seat
(stacking with ROAD and BUILDING_CODES). The action executor, retrieval
path, market fills, knowledge diffusion, and research progression read
these helpers; ``EffectsSystem`` only observes coverage. Systems never
call each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.cities import CityKind, city_at
from civitas.domain.energy import DEFAULT_REST_RESTORE
from civitas.domain.food import FOOD_RESOURCE
from civitas.domain.geography import DEFAULT_MOVE_ENERGY_COST
from civitas.domain.ids import LocationId
from civitas.domain.infrastructure import InfrastructureKind, active_infrastructure
from civitas.domain.innovation import InnovationKind, active_innovations
from civitas.domain.institutions import InstitutionKind, active_institutions
from civitas.domain.laws import (
    assembly_socialize_bonus_for,
    building_codes_move_discount_for,
    calendar_retrieval_bonus_for,
    curriculum_teachings_bonus_for,
    market_fee_for,
    quarantine_rest_bonus_for,
    sanitation_drink_bonus_for,
)
from civitas.domain.numeric import clamp_unit
from civitas.domain.production import DEFAULT_PRODUCE_ENERGY_COST
from civitas.domain.relationships import DEFAULT_SOCIALIZE_RESTORE
from civitas.domain.research import DEFAULT_POINTS_PER_TICK
from civitas.domain.resources import DEFAULT_GATHER_AMOUNT, ResourceKind
from civitas.domain.retrieval import DEFAULT_RETRIEVAL_LIMIT
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt
from civitas.domain.water import DEFAULT_DRINK_RESTORE, WATER_RESOURCE

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

FIRE_HEARTH_REST_BONUS: float = 0.05
MEDICINE_REST_RESTORE_BONUS: float = 0.05
TEMPLE_REST_RESTORE_BONUS: float = 0.05
SANCTUARY_REST_RESTORE_BONUS: float = 0.05
HOSPITAL_REST_RESTORE_BONUS: float = 0.05
INFIRMARY_REST_RESTORE_BONUS: float = 0.05
BATHHOUSE_REST_RESTORE_BONUS: float = 0.05
POTTERY_WATER_GATHER_BONUS: int = 1
IRRIGATION_WATER_GATHER_BONUS: int = 1
METALLURGY_STONE_GATHER_BONUS: int = 1
WRITING_TEACHINGS_PER_KNOWER_BONUS: int = 1
SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS: int = 1
STOA_TEACHINGS_PER_KNOWER_BONUS: int = 1
ACADEMY_TEACHINGS_PER_KNOWER_BONUS: int = 1
FORUM_TEACHINGS_PER_KNOWER_BONUS: int = 1
SCHOOL_TEACHINGS_PER_KNOWER_BONUS: int = 1
COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS: int = 1
PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS: int = 1
LOGIC_RESEARCH_POINTS_BONUS: int = 1
ANATOMY_RESEARCH_POINTS_BONUS: int = 1
RHETORIC_SOCIALIZE_RESTORE_BONUS: float = 0.05
AGORA_SOCIALIZE_RESTORE_BONUS: float = 0.05
WELL_DRINK_RESTORE_BONUS: float = 0.05
SHRINE_DRINK_RESTORE_BONUS: float = 0.05
CLINIC_DRINK_RESTORE_BONUS: float = 0.05
APOTHECARY_DRINK_RESTORE_BONUS: float = 0.05
HYGIENE_DRINK_RESTORE_BONUS: float = 0.05
LAZARETTO_DRINK_RESTORE_BONUS: float = 0.05
STOREHOUSE_FOOD_GATHER_BONUS: int = 1
ROAD_MOVE_ENERGY_DISCOUNT: float = 0.02
BRIDGE_MOVE_ENERGY_DISCOUNT: float = 0.02
GUILD_PRODUCE_ENERGY_DISCOUNT: float = 0.02
WORKSHOP_PRODUCE_ENERGY_DISCOUNT: float = 0.02
MATHEMATICS_PRODUCE_ENERGY_DISCOUNT: float = 0.02
ENGINEERING_PRODUCE_ENERGY_DISCOUNT: float = 0.02
ARCHIVE_RETRIEVAL_LIMIT_BONUS: int = 1
LIBRARY_RETRIEVAL_LIMIT_BONUS: int = 1
OBSERVATORY_RETRIEVAL_LIMIT_BONUS: int = 1
ASTRONOMY_RETRIEVAL_LIMIT_BONUS: int = 1
LYCEUM_RETRIEVAL_LIMIT_BONUS: int = 1
BUREAUCRACY_MARKET_FEE_DISCOUNT: int = 1


class EffectsCensus(BaseModel):
    """Aggregate society-effect snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_count: NonNegativeInt
    fire_hearth_active: NonNegativeInt
    pottery_craft_active: NonNegativeInt
    rest_restore_bps: NonNegativeInt
    water_gather_amount: NonNegativeInt
    active_well_count: NonNegativeInt
    drink_restore_bps: NonNegativeInt
    active_storehouse_count: NonNegativeInt = 0
    food_gather_amount: NonNegativeInt = DEFAULT_GATHER_AMOUNT
    active_road_count: NonNegativeInt = 0
    move_energy_cost_bps: NonNegativeInt = round(DEFAULT_MOVE_ENERGY_COST * 10_000)
    active_guild_count: NonNegativeInt = 0
    produce_energy_cost_bps: NonNegativeInt = round(
        DEFAULT_PRODUCE_ENERGY_COST * 10_000
    )


def innovation_kind_is_active(world: World, kind: InnovationKind | str) -> bool:
    """Return True when at least one active innovation matches ``kind``."""
    target = InnovationKind(kind)
    return any(item.kind is target for item in active_innovations(world))


def location_has_active_well(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active WELL stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.WELL and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_storehouse(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active STOREHOUSE stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.STOREHOUSE and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_road(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active ROAD stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.ROAD and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_bridge(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active BRIDGE stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.BRIDGE and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_scriptorium(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active SCRIPTORIUM stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.SCRIPTORIUM and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_stoa(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active STOA stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.STOA and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_observatory(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active OBSERVATORY stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.OBSERVATORY and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_shrine(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active SHRINE stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.SHRINE and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_clinic(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active CLINIC stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.CLINIC and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_bathhouse(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active BATHHOUSE stands at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InfrastructureKind.BATHHOUSE and item.location_id == target
        for item in active_infrastructure(world)
    )


def location_has_active_guild(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active GUILD is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.GUILD and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_workshop(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active WORKSHOP is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.WORKSHOP and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_archive(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active ARCHIVE is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.ARCHIVE and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_bureaucracy(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active BUREAUCRACY is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.BUREAUCRACY and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_academy(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active ACADEMY is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.ACADEMY and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_temple(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active TEMPLE is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.TEMPLE and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_hospital(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active HOSPITAL is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.HOSPITAL and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_apothecary(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active APOTHECARY is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.APOTHECARY and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_collegium(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active COLLEGIUM is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.COLLEGIUM and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_school(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active SCHOOL is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.SCHOOL and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_lyceum(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active LYCEUM is seated at ``location_id``."""
    target = (
        location_id
        if isinstance(location_id, LocationId)
        else LocationId(value=location_id)
    )
    return any(
        item.kind is InstitutionKind.LYCEUM and item.location_id == target
        for item in active_institutions(world)
    )


def location_has_active_library(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active LIBRARY city is seated at ``location_id``."""
    city = city_at(world, location_id)
    return city is not None and city.active and city.kind is CityKind.LIBRARY


def location_has_active_forum(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active FORUM city is seated at ``location_id``."""
    city = city_at(world, location_id)
    return city is not None and city.active and city.kind is CityKind.FORUM


def location_has_active_sanctuary(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active SANCTUARY city is seated at ``location_id``."""
    city = city_at(world, location_id)
    return city is not None and city.active and city.kind is CityKind.SANCTUARY


def location_has_active_agora(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active AGORA city is seated at ``location_id``."""
    city = city_at(world, location_id)
    return city is not None and city.active and city.kind is CityKind.AGORA


def location_has_active_infirmary(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active INFIRMARY city is seated at ``location_id``."""
    city = city_at(world, location_id)
    return city is not None and city.active and city.kind is CityKind.INFIRMARY


def location_has_active_lazaretto(
    world: World,
    location_id: LocationId | int,
) -> bool:
    """Return True when an active LAZARETTO city is seated at ``location_id``."""
    city = city_at(world, location_id)
    return city is not None and city.active and city.kind is CityKind.LAZARETTO


def rest_restore_bonus(
    world: World,
    *,
    location_id: LocationId | int | None = None,
    agent: Agent | None = None,
) -> float:
    """Return the REST restore bonus from hearth, remedy, laws, and rest seats.

    An active FIRE_HEARTH innovation contributes ``FIRE_HEARTH_REST_BONUS``
    society-wide. An active REMEDY innovation contributes
    ``MEDICINE_REST_RESTORE_BONUS`` society-wide. An active ``QUARANTINE``
    statute contributes for living subjects when ``agent`` is provided. An
    active TEMPLE at ``location_id`` or the agent's location contributes
    ``TEMPLE_REST_RESTORE_BONUS``. An active SANCTUARY city seat contributes
    ``SANCTUARY_REST_RESTORE_BONUS``. An active HOSPITAL seat contributes
    ``HOSPITAL_REST_RESTORE_BONUS``. An active INFIRMARY city seat contributes
    ``INFIRMARY_REST_RESTORE_BONUS``. An active BATHHOUSE contributes
    ``BATHHOUSE_REST_RESTORE_BONUS``. All stack.
    """
    bonus = 0.0
    if innovation_kind_is_active(world, InnovationKind.FIRE_HEARTH):
        bonus += FIRE_HEARTH_REST_BONUS
    if innovation_kind_is_active(world, InnovationKind.REMEDY):
        bonus += MEDICINE_REST_RESTORE_BONUS
    if agent is not None:
        bonus += quarantine_rest_bonus_for(world, agent)
    seat = (
        location_id
        if location_id is not None
        else (None if agent is None else agent.location_id)
    )
    if seat is not None and location_has_active_temple(world, seat):
        bonus += TEMPLE_REST_RESTORE_BONUS
    if seat is not None and location_has_active_sanctuary(world, seat):
        bonus += SANCTUARY_REST_RESTORE_BONUS
    if seat is not None and location_has_active_hospital(world, seat):
        bonus += HOSPITAL_REST_RESTORE_BONUS
    if seat is not None and location_has_active_infirmary(world, seat):
        bonus += INFIRMARY_REST_RESTORE_BONUS
    if seat is not None and location_has_active_bathhouse(world, seat):
        bonus += BATHHOUSE_REST_RESTORE_BONUS
    return bonus


def teachings_per_knower_bonus(world: World) -> int:
    """Return peer-teaching capacity bonus from society-wide innovations.

    An active SCRIBE contributes ``WRITING_TEACHINGS_PER_KNOWER_BONUS``.
    An active DIALECTIC contributes ``PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS``.
    Both stack when active.
    """
    bonus = 0
    if innovation_kind_is_active(world, InnovationKind.SCRIBE):
        bonus += WRITING_TEACHINGS_PER_KNOWER_BONUS
    if innovation_kind_is_active(world, InnovationKind.DIALECTIC):
        bonus += PHILOSOPHY_TEACHINGS_PER_KNOWER_BONUS
    return bonus


def research_points_bonus(world: World) -> int:
    """Return per-tick research point bonus from active research innovations."""
    bonus = 0
    if innovation_kind_is_active(world, InnovationKind.SYLLOGISM):
        bonus += LOGIC_RESEARCH_POINTS_BONUS
    if innovation_kind_is_active(world, InnovationKind.DISSECTION):
        bonus += ANATOMY_RESEARCH_POINTS_BONUS
    return bonus


def socialize_restore_bonus(
    world: World,
    *,
    agent: Agent | None = None,
) -> float:
    """Return SOCIALIZE restore bonuses from active oration, assembly, and agora.

    An active ORATION innovation contributes society-wide. An active
    ``ASSEMBLY`` statute contributes for living subjects when ``agent`` is
    provided. An active AGORA city contributes at the agent's seat. All stack.
    """
    bonus = 0.0
    if innovation_kind_is_active(world, InnovationKind.ORATION):
        bonus += RHETORIC_SOCIALIZE_RESTORE_BONUS
    if agent is not None:
        bonus += assembly_socialize_bonus_for(world, agent)
        if location_has_active_agora(world, agent.location_id):
            bonus += AGORA_SOCIALIZE_RESTORE_BONUS
    return bonus


def gather_amount_bonus(
    world: World,
    resource: str,
    *,
    location_id: LocationId | int | None = None,
) -> int:
    """Return gather-amount bonuses for ``resource``.

    Water and stone bonuses come from society innovations. Food bonuses come
    from an active STOREHOUSE at ``location_id`` when provided.
    """
    bonus = 0
    if resource == WATER_RESOURCE:
        if innovation_kind_is_active(world, InnovationKind.POTTERY_CRAFT):
            bonus += POTTERY_WATER_GATHER_BONUS
        if innovation_kind_is_active(world, InnovationKind.IRRIGATION_CANAL):
            bonus += IRRIGATION_WATER_GATHER_BONUS
    elif resource == ResourceKind.STONE.value:
        if innovation_kind_is_active(world, InnovationKind.FORGE):
            bonus += METALLURGY_STONE_GATHER_BONUS
    elif resource == FOOD_RESOURCE and location_id is not None:
        if location_has_active_storehouse(world, location_id):
            bonus += STOREHOUSE_FOOD_GATHER_BONUS
    return bonus


def drink_restore_bonus(world: World, agent: Agent) -> float:
    """Return the DRINK restore bonus from seats, sanitation, and asepsis.

    An active WELL contributes ``WELL_DRINK_RESTORE_BONUS``. An active
    SHRINE contributes ``SHRINE_DRINK_RESTORE_BONUS``. An active
    CLINIC contributes ``CLINIC_DRINK_RESTORE_BONUS``. An active
    APOTHECARY contributes ``APOTHECARY_DRINK_RESTORE_BONUS``. An active
    LAZARETTO city contributes ``LAZARETTO_DRINK_RESTORE_BONUS``. An active
    ``SANITATION`` statute contributes for living subjects. An active ASEPSIS
    innovation contributes society-wide. All stack.
    """
    bonus = 0.0
    if innovation_kind_is_active(world, InnovationKind.ASEPSIS):
        bonus += HYGIENE_DRINK_RESTORE_BONUS
    if location_has_active_well(world, agent.location_id):
        bonus += WELL_DRINK_RESTORE_BONUS
    if location_has_active_shrine(world, agent.location_id):
        bonus += SHRINE_DRINK_RESTORE_BONUS
    if location_has_active_clinic(world, agent.location_id):
        bonus += CLINIC_DRINK_RESTORE_BONUS
    if location_has_active_apothecary(world, agent.location_id):
        bonus += APOTHECARY_DRINK_RESTORE_BONUS
    if location_has_active_lazaretto(world, agent.location_id):
        bonus += LAZARETTO_DRINK_RESTORE_BONUS
    bonus += sanitation_drink_bonus_for(world, agent)
    return bonus


def move_energy_discount(world: World, agent: Agent) -> float:
    """Return MOVE energy discount from road/bridge seats and building codes.

    An active ROAD at the agent's location contributes
    ``ROAD_MOVE_ENERGY_DISCOUNT``. An active BRIDGE at the agent's
    location contributes ``BRIDGE_MOVE_ENERGY_DISCOUNT``. An active
    ``BUILDING_CODES`` statute contributes its subject discount. All
    stack when present.
    """
    discount = 0.0
    if location_has_active_road(world, agent.location_id):
        discount += ROAD_MOVE_ENERGY_DISCOUNT
    if location_has_active_bridge(world, agent.location_id):
        discount += BRIDGE_MOVE_ENERGY_DISCOUNT
    discount += building_codes_move_discount_for(world, agent)
    return discount


def produce_energy_discount(world: World, agent: Agent) -> float:
    """Return PRODUCE energy discount from guild, workshop, abacus, and pulley.

    An active GUILD at the agent's location contributes
    ``GUILD_PRODUCE_ENERGY_DISCOUNT``. An active WORKSHOP at the agent's
    location contributes ``WORKSHOP_PRODUCE_ENERGY_DISCOUNT``. An active
    ABACUS innovation contributes ``MATHEMATICS_PRODUCE_ENERGY_DISCOUNT``
    society-wide. An active PULLEY innovation contributes
    ``ENGINEERING_PRODUCE_ENERGY_DISCOUNT`` society-wide. All stack when
    present.
    """
    discount = 0.0
    if location_has_active_guild(world, agent.location_id):
        discount += GUILD_PRODUCE_ENERGY_DISCOUNT
    if location_has_active_workshop(world, agent.location_id):
        discount += WORKSHOP_PRODUCE_ENERGY_DISCOUNT
    if innovation_kind_is_active(world, InnovationKind.ABACUS):
        discount += MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
    if innovation_kind_is_active(world, InnovationKind.PULLEY):
        discount += ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    return discount


def retrieval_limit_bonus(world: World, agent: Agent) -> int:
    """Return retrieval-limit bonuses for the agent.

    Active ARCHIVE and LYCEUM institutions, LIBRARY city seats, and
    OBSERVATORY infrastructure each contribute ``+1`` when present at
    the agent's location. An active STAR_CHART innovation contributes
    ``ASTRONOMY_RETRIEVAL_LIMIT_BONUS`` society-wide. An active
    ``CALENDAR`` statute contributes ``+1`` for living subjects of that
    government. All stack.
    """
    bonus = 0
    if location_has_active_archive(world, agent.location_id):
        bonus += ARCHIVE_RETRIEVAL_LIMIT_BONUS
    if location_has_active_library(world, agent.location_id):
        bonus += LIBRARY_RETRIEVAL_LIMIT_BONUS
    if location_has_active_observatory(world, agent.location_id):
        bonus += OBSERVATORY_RETRIEVAL_LIMIT_BONUS
    if location_has_active_lyceum(world, agent.location_id):
        bonus += LYCEUM_RETRIEVAL_LIMIT_BONUS
    if innovation_kind_is_active(world, InnovationKind.STAR_CHART):
        bonus += ASTRONOMY_RETRIEVAL_LIMIT_BONUS
    bonus += calendar_retrieval_bonus_for(world, agent)
    return bonus


def market_fee_discount(world: World, location_id: LocationId | int) -> int:
    """Return market-fee discount from a BUREAUCRACY at ``location_id``."""
    if location_has_active_bureaucracy(world, location_id):
        return BUREAUCRACY_MARKET_FEE_DISCOUNT
    return 0


def effective_market_fee(world: World, location_id: LocationId | int) -> int:
    """Return market fill fee after bureaucracy discount (floor at 0).

    ``effective_market_fee = max(0, market_fee_for(...) - discount)`` where
    an active bureaucracy at the market location contributes a discount of
    ``BUREAUCRACY_MARKET_FEE_DISCOUNT`` (1).
    """
    base = market_fee_for(world, location_id)
    return max(0, base - market_fee_discount(world, location_id))


def effective_rest_restore(
    world: World,
    *,
    base: float = DEFAULT_REST_RESTORE,
    location_id: LocationId | int | None = None,
    agent: Agent | None = None,
) -> float:
    """Return REST restore amount including hearth, remedy, laws, and rest seats.

    Fire-hearth and remedy are society-wide. Quarantine applies only for
    living subjects when ``agent`` is provided. Temple, sanctuary, hospital,
    infirmary, and bathhouse bonuses apply only when ``location_id`` or
    ``agent`` places the resting agent at an active TEMPLE, SANCTUARY,
    HOSPITAL, INFIRMARY, or BATHHOUSE seat. All stack via
    ``rest_restore_bonus``.
    """
    return clamp_unit(
        base + rest_restore_bonus(world, location_id=location_id, agent=agent)
    )


def effective_teachings_per_knower(
    world: World,
    *,
    base: int = 1,
    location_id: LocationId | int | None = None,
    agent: Agent | None = None,
) -> int:
    """Return teachings-per-knower including scribe, dialectic, seats, laws.

    The scribe and dialectic innovation bonuses are society-wide. The
    scriptorium, stoa, academy, forum, school, and collegium bonuses apply
    only when ``location_id`` or ``agent`` places the knower at an active
    SCRIPTORIUM, STOA, ACADEMY, FORUM, SCHOOL, or COLLEGIUM seat. The
    curriculum law bonus applies when ``agent`` is a living subject of a
    government with an active ``CURRICULUM`` statute. All bonuses stack.
    """
    if base < 0:
        return 0
    seat = (
        location_id
        if location_id is not None
        else (None if agent is None else agent.location_id)
    )
    bonus = teachings_per_knower_bonus(world)
    if seat is not None and location_has_active_scriptorium(world, seat):
        bonus += SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS
    if seat is not None and location_has_active_stoa(world, seat):
        bonus += STOA_TEACHINGS_PER_KNOWER_BONUS
    if seat is not None and location_has_active_academy(world, seat):
        bonus += ACADEMY_TEACHINGS_PER_KNOWER_BONUS
    if seat is not None and location_has_active_forum(world, seat):
        bonus += FORUM_TEACHINGS_PER_KNOWER_BONUS
    if seat is not None and location_has_active_school(world, seat):
        bonus += SCHOOL_TEACHINGS_PER_KNOWER_BONUS
    if seat is not None and location_has_active_collegium(world, seat):
        bonus += COLLEGIUM_TEACHINGS_PER_KNOWER_BONUS
    if agent is not None:
        bonus += curriculum_teachings_bonus_for(world, agent)
    return base + bonus


def effective_research_points_per_tick(
    world: World,
    *,
    base: int = DEFAULT_POINTS_PER_TICK,
) -> int:
    """Return research points per tick including active research bonuses."""
    if base < 0:
        return 0
    return base + research_points_bonus(world)


def effective_socialize_restore(
    world: World,
    *,
    base: float = DEFAULT_SOCIALIZE_RESTORE,
    agent: Agent | None = None,
) -> float:
    """Return SOCIALIZE restore amount including active oration/assembly/agora."""
    return clamp_unit(base + socialize_restore_bonus(world, agent=agent))


def effective_gather_amount(
    world: World,
    resource: str,
    *,
    base: int = DEFAULT_GATHER_AMOUNT,
    location_id: LocationId | int | None = None,
    agent: Agent | None = None,
) -> int:
    """Return gather amount for ``resource`` including effect bonuses."""
    if base < 0:
        return 0
    seat = (
        location_id
        if location_id is not None
        else (None if agent is None else agent.location_id)
    )
    return base + gather_amount_bonus(world, resource, location_id=seat)


def effective_drink_restore(
    world: World,
    agent: Agent,
    *,
    base: float = DEFAULT_DRINK_RESTORE,
) -> float:
    """Return DRINK restore amount including drink seats, sanitation, and asepsis.

    ``effective_drink_restore = clamp_unit(base + drink_restore_bonus(...))``.
    """
    return clamp_unit(base + drink_restore_bonus(world, agent))


def effective_move_energy_cost(
    world: World,
    agent: Agent,
    *,
    base: float = DEFAULT_MOVE_ENERGY_COST,
) -> float:
    """Return MOVE cost including road, bridge, and building-code discounts."""
    if base < 0:
        return 0.0
    discounted = base - move_energy_discount(world, agent)
    return clamp_unit(max(0.0, discounted))


def effective_produce_energy_cost(
    world: World,
    agent: Agent,
    *,
    base: float,
) -> float:
    """Return PRODUCE energy cost including guild, abacus, and pulley discounts."""
    if base < 0:
        return 0.0
    discounted = base - produce_energy_discount(world, agent)
    return clamp_unit(max(0.0, discounted))


def effective_retrieval_limit(
    world: World,
    agent: Agent,
    *,
    base: int = DEFAULT_RETRIEVAL_LIMIT,
) -> int:
    """Return memory retrieval limit including location/star-chart/calendar bonuses."""
    if base < 0:
        return 0
    return base + retrieval_limit_bonus(world, agent)


def census_effects(world: World) -> EffectsCensus:
    """Build a deterministic society-effects census for ``world``."""
    restore = effective_rest_restore(world)
    water_amount = effective_gather_amount(world, WATER_RESOURCE)
    wells = tuple(
        item
        for item in active_infrastructure(world)
        if item.kind is InfrastructureKind.WELL
    )
    storehouses = tuple(
        item
        for item in active_infrastructure(world)
        if item.kind is InfrastructureKind.STOREHOUSE
    )
    roads = tuple(
        item
        for item in active_infrastructure(world)
        if item.kind is InfrastructureKind.ROAD
    )
    guilds = tuple(
        item
        for item in active_institutions(world)
        if item.kind is InstitutionKind.GUILD
    )
    workshops = tuple(
        item
        for item in active_institutions(world)
        if item.kind is InstitutionKind.WORKSHOP
    )
    # Society drink potential at a well seat (bonus available when colocated).
    drink_bonus = WELL_DRINK_RESTORE_BONUS if wells else 0.0
    if innovation_kind_is_active(world, InnovationKind.ASEPSIS):
        drink_bonus += HYGIENE_DRINK_RESTORE_BONUS
    drink_at_well = clamp_unit(DEFAULT_DRINK_RESTORE + drink_bonus)
    # Food gather potential at a storehouse seat.
    food_at_storehouse = effective_gather_amount(
        world,
        FOOD_RESOURCE,
        location_id=storehouses[0].location_id if storehouses else None,
    )
    bridges = tuple(
        item
        for item in active_infrastructure(world)
        if item.kind is InfrastructureKind.BRIDGE
    )
    # Move cost potential at a road/bridge seat.
    move_discount = ROAD_MOVE_ENERGY_DISCOUNT if roads else 0.0
    if bridges:
        move_discount += BRIDGE_MOVE_ENERGY_DISCOUNT
    move_at_road = clamp_unit(
        max(
            0.0,
            DEFAULT_MOVE_ENERGY_COST - move_discount,
        )
    )
    # Produce cost potential at guild/workshop seats, plus society-wide discounts.
    produce_discount = GUILD_PRODUCE_ENERGY_DISCOUNT if guilds else 0.0
    if workshops:
        produce_discount += WORKSHOP_PRODUCE_ENERGY_DISCOUNT
    if innovation_kind_is_active(world, InnovationKind.ABACUS):
        produce_discount += MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
    if innovation_kind_is_active(world, InnovationKind.PULLEY):
        produce_discount += ENGINEERING_PRODUCE_ENERGY_DISCOUNT
    produce_at_guild = clamp_unit(
        max(
            0.0,
            DEFAULT_PRODUCE_ENERGY_COST - produce_discount,
        )
    )
    return EffectsCensus(
        tick=world.tick,
        living_count=len(world.alive_agents()),
        fire_hearth_active=int(
            innovation_kind_is_active(world, InnovationKind.FIRE_HEARTH)
        ),
        pottery_craft_active=int(
            innovation_kind_is_active(world, InnovationKind.POTTERY_CRAFT)
        ),
        rest_restore_bps=round(restore * 10_000),
        water_gather_amount=water_amount,
        active_well_count=len(wells),
        drink_restore_bps=round(drink_at_well * 10_000),
        active_storehouse_count=len(storehouses),
        food_gather_amount=food_at_storehouse,
        active_road_count=len(roads),
        move_energy_cost_bps=round(move_at_road * 10_000),
        active_guild_count=len(guilds),
        produce_energy_cost_bps=round(produce_at_guild * 10_000),
    )
