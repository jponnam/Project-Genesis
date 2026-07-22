"""Society effect wiring from active innovations.

Phase 8 Milestone 1. Active innovations modify action outcomes through
pure domain helpers. ``FIRE_HEARTH`` boosts REST energy restore;
``POTTERY_CRAFT`` boosts water gather amount. The action executor reads
these helpers; ``EffectsSystem`` only observes coverage. Systems never
call each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.energy import DEFAULT_REST_RESTORE
from civitas.domain.innovation import InnovationKind, active_innovations
from civitas.domain.numeric import clamp_unit
from civitas.domain.resources import DEFAULT_GATHER_AMOUNT
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt
from civitas.domain.water import WATER_RESOURCE

if TYPE_CHECKING:
    from civitas.domain.world import World

FIRE_HEARTH_REST_BONUS: float = 0.05
POTTERY_WATER_GATHER_BONUS: int = 1


class EffectsCensus(BaseModel):
    """Aggregate society-effect snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    living_count: NonNegativeInt
    fire_hearth_active: NonNegativeInt
    pottery_craft_active: NonNegativeInt
    rest_restore_bps: NonNegativeInt
    water_gather_amount: NonNegativeInt


def innovation_kind_is_active(world: World, kind: InnovationKind | str) -> bool:
    """Return True when at least one active innovation matches ``kind``."""
    target = InnovationKind(kind)
    return any(item.kind is target for item in active_innovations(world))


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


def census_effects(world: World) -> EffectsCensus:
    """Build a deterministic society-effects census for ``world``."""
    restore = effective_rest_restore(world)
    water_amount = effective_gather_amount(world, WATER_RESOURCE)
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
    )
