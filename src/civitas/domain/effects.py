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
academy/scriptorium/curriculum/scribe). The action executor,
retrieval path, market fills, and knowledge diffusion read
these helpers; ``EffectsSystem`` only observes coverage.
Systems never call each other.
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
    calendar_retrieval_bonus_for,
    curriculum_teachings_bonus_for,
    market_fee_for,
)
from civitas.domain.numeric import clamp_unit
from civitas.domain.production import DEFAULT_PRODUCE_ENERGY_COST
from civitas.domain.resources import DEFAULT_GATHER_AMOUNT, ResourceKind
from civitas.domain.retrieval import DEFAULT_RETRIEVAL_LIMIT
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt
from civitas.domain.water import DEFAULT_DRINK_RESTORE, WATER_RESOURCE

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

FIRE_HEARTH_REST_BONUS: float = 0.05
POTTERY_WATER_GATHER_BONUS: int = 1
IRRIGATION_WATER_GATHER_BONUS: int = 1
METALLURGY_STONE_GATHER_BONUS: int = 1
WRITING_TEACHINGS_PER_KNOWER_BONUS: int = 1
SCRIPTORIUM_TEACHINGS_PER_KNOWER_BONUS: int = 1
ACADEMY_TEACHINGS_PER_KNOWER_BONUS: int = 1
FORUM_TEACHINGS_PER_KNOWER_BONUS: int = 1
WELL_DRINK_RESTORE_BONUS: float = 0.05
STOREHOUSE_FOOD_GATHER_BONUS: int = 1
ROAD_MOVE_ENERGY_DISCOUNT: float = 0.02
GUILD_PRODUCE_ENERGY_DISCOUNT: float = 0.02
MATHEMATICS_PRODUCE_ENERGY_DISCOUNT: float = 0.02
ARCHIVE_RETRIEVAL_LIMIT_BONUS: int = 1
LIBRARY_RETRIEVAL_LIMIT_BONUS: int = 1
OBSERVATORY_RETRIEVAL_LIMIT_BONUS: int = 1
ASTRONOMY_RETRIEVAL_LIMIT_BONUS: int = 1
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


def rest_restore_bonus(world: World) -> float:
    """Return the REST restore bonus from active fire-hearth innovations."""
    if innovation_kind_is_active(world, InnovationKind.FIRE_HEARTH):
        return FIRE_HEARTH_REST_BONUS
    return 0.0


def teachings_per_knower_bonus(world: World) -> int:
    """Return peer-teaching capacity bonus from an active scribe innovation."""
    if innovation_kind_is_active(world, InnovationKind.SCRIBE):
        return WRITING_TEACHINGS_PER_KNOWER_BONUS
    return 0


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
    """Return the DRINK restore bonus from a WELL at the agent's location."""
    if location_has_active_well(world, agent.location_id):
        return WELL_DRINK_RESTORE_BONUS
    return 0.0


def move_energy_discount(world: World, agent: Agent) -> float:
    """Return MOVE energy discount from a ROAD at the agent's location."""
    if location_has_active_road(world, agent.location_id):
        return ROAD_MOVE_ENERGY_DISCOUNT
    return 0.0


def produce_energy_discount(world: World, agent: Agent) -> float:
    """Return PRODUCE energy discount from guild seat and abacus innovation.

    An active GUILD at the agent's location contributes
    ``GUILD_PRODUCE_ENERGY_DISCOUNT``. An active ABACUS innovation
    contributes ``MATHEMATICS_PRODUCE_ENERGY_DISCOUNT`` society-wide.
    Both stack when present.
    """
    discount = 0.0
    if location_has_active_guild(world, agent.location_id):
        discount += GUILD_PRODUCE_ENERGY_DISCOUNT
    if innovation_kind_is_active(world, InnovationKind.ABACUS):
        discount += MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
    return discount


def retrieval_limit_bonus(world: World, agent: Agent) -> int:
    """Return retrieval-limit bonuses for the agent.

    Active ARCHIVE institutions, LIBRARY city seats, and OBSERVATORY
    infrastructure each contribute ``+1`` when present at the agent's
    location. An active STAR_CHART innovation contributes
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
) -> float:
    """Return REST restore amount including society innovation bonuses."""
    return clamp_unit(base + rest_restore_bonus(world))


def effective_teachings_per_knower(
    world: World,
    *,
    base: int = 1,
    location_id: LocationId | int | None = None,
    agent: Agent | None = None,
) -> int:
    """Return teachings-per-knower including scribe, seats, curriculum, forum.

    The scribe innovation bonus is society-wide. The scriptorium, academy,
    and forum bonuses apply only when ``location_id`` or ``agent`` places
    the knower at an active SCRIPTORIUM, ACADEMY, or FORUM seat. The
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
    if seat is not None and location_has_active_academy(world, seat):
        bonus += ACADEMY_TEACHINGS_PER_KNOWER_BONUS
    if seat is not None and location_has_active_forum(world, seat):
        bonus += FORUM_TEACHINGS_PER_KNOWER_BONUS
    if agent is not None:
        bonus += curriculum_teachings_bonus_for(world, agent)
    return base + bonus


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
    """Return DRINK restore amount including well infrastructure bonuses."""
    return clamp_unit(base + drink_restore_bonus(world, agent))


def effective_move_energy_cost(
    world: World,
    agent: Agent,
    *,
    base: float = DEFAULT_MOVE_ENERGY_COST,
) -> float:
    """Return MOVE energy cost including road discounts at the origin seat."""
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
    """Return PRODUCE energy cost including guild and abacus discounts."""
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
    # Society drink potential at a well seat (bonus available when colocated).
    drink_at_well = clamp_unit(
        DEFAULT_DRINK_RESTORE + (WELL_DRINK_RESTORE_BONUS if wells else 0.0)
    )
    # Food gather potential at a storehouse seat.
    food_at_storehouse = effective_gather_amount(
        world,
        FOOD_RESOURCE,
        location_id=storehouses[0].location_id if storehouses else None,
    )
    # Move cost potential at a road seat.
    move_at_road = clamp_unit(
        max(
            0.0,
            DEFAULT_MOVE_ENERGY_COST - (ROAD_MOVE_ENERGY_DISCOUNT if roads else 0.0),
        )
    )
    # Produce cost potential at a guild seat, plus society abacus discount.
    produce_discount = GUILD_PRODUCE_ENERGY_DISCOUNT if guilds else 0.0
    if innovation_kind_is_active(world, InnovationKind.ABACUS):
        produce_discount += MATHEMATICS_PRODUCE_ENERGY_DISCOUNT
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
