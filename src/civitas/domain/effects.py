"""Society effect wiring from innovations and infrastructure.

Phase 8 Milestone 1 wired active innovations into REST/GATHER outcomes.
Milestone 2 adds location-scoped infrastructure effects: an active WELL
boosts DRINK restore for agents at that seat. The action executor reads
these helpers; ``EffectsSystem`` only observes coverage. Systems never
call each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.energy import DEFAULT_REST_RESTORE
from civitas.domain.ids import LocationId
from civitas.domain.infrastructure import InfrastructureKind, active_infrastructure
from civitas.domain.innovation import InnovationKind, active_innovations
from civitas.domain.numeric import clamp_unit
from civitas.domain.resources import DEFAULT_GATHER_AMOUNT
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt
from civitas.domain.water import DEFAULT_DRINK_RESTORE, WATER_RESOURCE

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.world import World

FIRE_HEARTH_REST_BONUS: float = 0.05
POTTERY_WATER_GATHER_BONUS: int = 1
WELL_DRINK_RESTORE_BONUS: float = 0.05


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


def rest_restore_bonus(world: World) -> float:
    """Return the REST restore bonus from active fire-hearth innovations."""
    if innovation_kind_is_active(world, InnovationKind.FIRE_HEARTH):
        return FIRE_HEARTH_REST_BONUS
    return 0.0


def gather_amount_bonus(world: World, resource: str) -> int:
    """Return the gather-amount bonus for ``resource`` from innovations."""
    if resource == WATER_RESOURCE and innovation_kind_is_active(
        world, InnovationKind.POTTERY_CRAFT
    ):
        return POTTERY_WATER_GATHER_BONUS
    return 0


def drink_restore_bonus(world: World, agent: Agent) -> float:
    """Return the DRINK restore bonus from a WELL at the agent's location."""
    if location_has_active_well(world, agent.location_id):
        return WELL_DRINK_RESTORE_BONUS
    return 0.0


def effective_rest_restore(
    world: World,
    *,
    base: float = DEFAULT_REST_RESTORE,
) -> float:
    """Return REST restore amount including society innovation bonuses."""
    return clamp_unit(base + rest_restore_bonus(world))


def effective_gather_amount(
    world: World,
    resource: str,
    *,
    base: int = DEFAULT_GATHER_AMOUNT,
) -> int:
    """Return gather amount for ``resource`` including innovation bonuses."""
    if base < 0:
        return 0
    return base + gather_amount_bonus(world, resource)


def effective_drink_restore(
    world: World,
    agent: Agent,
    *,
    base: float = DEFAULT_DRINK_RESTORE,
) -> float:
    """Return DRINK restore amount including well infrastructure bonuses."""
    return clamp_unit(base + drink_restore_bonus(world, agent))


def census_effects(world: World) -> EffectsCensus:
    """Build a deterministic society-effects census for ``world``."""
    restore = effective_rest_restore(world)
    water_amount = effective_gather_amount(world, WATER_RESOURCE)
    wells = tuple(
        item
        for item in active_infrastructure(world)
        if item.kind is InfrastructureKind.WELL
    )
    # Society drink potential at a well seat (bonus available when colocated).
    drink_at_well = clamp_unit(
        DEFAULT_DRINK_RESTORE + (WELL_DRINK_RESTORE_BONUS if wells else 0.0)
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
    )
