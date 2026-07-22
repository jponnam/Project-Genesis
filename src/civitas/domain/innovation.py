"""Innovation: society adoption of discovered technologies.

Phase 6 Milestone 3. Each innovation links to one technology and becomes
``active`` when that technology is discovered. This milestone seeds an
active fire hearth and an inactive pottery craft. Knowledge diffusion
(Milestone 4) syncs facts onto agents. Effect wiring (Phase 8) applies
active-innovation bonuses to REST/GATHER outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain.ids import InnovationId, TechnologyId
from civitas.domain.technology import (
    CAMP_FIRE,
    CAMP_IRRIGATION,
    CAMP_METALLURGY,
    CAMP_POTTERY,
    technology_by_id,
)
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class InnovationKind(StrEnum):
    """Supported innovation kinds."""

    FIRE_HEARTH = "fire_hearth"
    POTTERY_CRAFT = "pottery_craft"
    IRRIGATION_CANAL = "irrigation_canal"
    FORGE = "forge"


class Innovation(BaseModel):
    """One society-level adoption of a discovered technology."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    innovation_id: InnovationId
    technology_id: TechnologyId
    name: NonEmptyStr
    kind: InnovationKind
    active: bool = False

    @classmethod
    def create(
        cls,
        innovation_id: int,
        technology_id: int,
        name: str,
        kind: InnovationKind | str,
        *,
        active: bool = False,
    ) -> Innovation:
        """Construct a validated innovation from primitive fields."""
        return cls(
            innovation_id=InnovationId(value=innovation_id),
            technology_id=TechnologyId(value=technology_id),
            name=name,
            kind=InnovationKind(kind),
            active=active,
        )


CAMP_FIRE_HEARTH: Innovation = Innovation.create(
    0,
    CAMP_FIRE.technology_id.value,
    "Camp Fire Hearth",
    InnovationKind.FIRE_HEARTH,
    active=True,
)

CAMP_POTTERY_CRAFT: Innovation = Innovation.create(
    1,
    CAMP_POTTERY.technology_id.value,
    "Camp Pottery Craft",
    InnovationKind.POTTERY_CRAFT,
    active=False,
)

CAMP_IRRIGATION_CANAL: Innovation = Innovation.create(
    2,
    CAMP_IRRIGATION.technology_id.value,
    "Camp Irrigation Canal",
    InnovationKind.IRRIGATION_CANAL,
    active=False,
)

CAMP_FORGE: Innovation = Innovation.create(
    3,
    CAMP_METALLURGY.technology_id.value,
    "Camp Forge",
    InnovationKind.FORGE,
    active=False,
)


def default_innovations() -> tuple[Innovation, ...]:
    """Return the canonical initial innovation set."""
    return (
        CAMP_FIRE_HEARTH,
        CAMP_POTTERY_CRAFT,
        CAMP_IRRIGATION_CANAL,
        CAMP_FORGE,
    )


class InnovationCensus(BaseModel):
    """Aggregate innovation snapshot at a world tick."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    innovation_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    active_fire_hearth_count: NonNegativeInt
    active_pottery_craft_count: NonNegativeInt
    active_irrigation_canal_count: NonNegativeInt
    active_forge_count: NonNegativeInt = 0


@dataclass(frozen=True, slots=True)
class InnovationActivation:
    """One innovation activated during an apply pass."""

    innovation_id: InnovationId
    technology_id: TechnologyId
    name: str
    kind: InnovationKind


def innovation_by_id(
    world: World,
    innovation_id: InnovationId | int,
) -> Innovation | None:
    """Return the innovation with ``innovation_id``, or ``None``."""
    target = (
        innovation_id
        if isinstance(innovation_id, InnovationId)
        else InnovationId(value=innovation_id)
    )
    for innovation in world.innovations:
        if innovation.innovation_id == target:
            return innovation
    return None


def innovation_by_kind(
    world: World,
    kind: InnovationKind | str,
) -> Innovation | None:
    """Return the innovation with ``kind``, or ``None``."""
    target = InnovationKind(kind)
    for innovation in world.innovations:
        if innovation.kind is target:
            return innovation
    return None


def innovation_for_technology(
    world: World,
    technology_id: TechnologyId | int,
) -> Innovation | None:
    """Return the innovation linked to ``technology_id``, or ``None``."""
    target = (
        technology_id
        if isinstance(technology_id, TechnologyId)
        else TechnologyId(value=technology_id)
    )
    for innovation in world.innovations:
        if innovation.technology_id == target:
            return innovation
    return None


def active_innovations(world: World) -> tuple[Innovation, ...]:
    """Return active innovations in ascending id order."""
    return tuple(item for item in world.innovations if item.active)


def next_innovation_id(world: World) -> InnovationId:
    """Return the next unused innovation id."""
    if not world.innovations:
        return InnovationId(value=0)
    highest = max(item.innovation_id.value for item in world.innovations)
    return InnovationId(value=highest + 1)


def create_innovation(world: World, innovation: Innovation) -> World | None:
    """Insert ``innovation`` when ids/kinds/tech links are unique and legal.

    Returns ``None`` when the innovation cannot be added.
    """
    if innovation_by_id(world, innovation.innovation_id) is not None:
        return None
    if innovation_by_kind(world, innovation.kind) is not None:
        return None
    if innovation_for_technology(world, innovation.technology_id) is not None:
        return None
    technology = technology_by_id(world, innovation.technology_id)
    if technology is None:
        return None
    if innovation.active and not technology.discovered:
        return None
    innovations = tuple(
        sorted(
            (*world.innovations, innovation),
            key=lambda item: item.innovation_id.value,
        )
    )
    return world.model_copy(update={"innovations": innovations})


def activate_innovation(
    world: World,
    innovation_id: InnovationId | int,
) -> World | None:
    """Activate ``innovation_id`` when its technology is discovered.

    Already-active innovations return the same world. Missing ids or
    undiscovered technologies return ``None``.
    """
    innovation = innovation_by_id(world, innovation_id)
    if innovation is None:
        return None
    if innovation.active:
        return world
    technology = technology_by_id(world, innovation.technology_id)
    if technology is None or not technology.discovered:
        return None
    updated = innovation.model_copy(update={"active": True})
    return world.with_innovation(updated)


def activate_due_innovations(
    world: World,
) -> tuple[World, tuple[InnovationActivation, ...]]:
    """Activate every inactive innovation whose technology is discovered."""
    activations: list[InnovationActivation] = []
    for innovation in world.innovations:
        if innovation.active:
            continue
        technology = technology_by_id(world, innovation.technology_id)
        if technology is None or not technology.discovered:
            continue
        updated = activate_innovation(world, innovation.innovation_id)
        if updated is None:
            continue
        world = updated
        activations.append(
            InnovationActivation(
                innovation_id=innovation.innovation_id,
                technology_id=innovation.technology_id,
                name=innovation.name,
                kind=innovation.kind,
            )
        )
    return world, tuple(activations)


def census_innovations(world: World) -> InnovationCensus:
    """Build a deterministic innovation census for ``world``."""
    innovations = world.innovations
    active = [item for item in innovations if item.active]
    fire = sum(1 for item in active if item.kind is InnovationKind.FIRE_HEARTH)
    pottery = sum(1 for item in active if item.kind is InnovationKind.POTTERY_CRAFT)
    irrigation = sum(
        1 for item in active if item.kind is InnovationKind.IRRIGATION_CANAL
    )
    forge = sum(1 for item in active if item.kind is InnovationKind.FORGE)
    return InnovationCensus(
        tick=world.tick,
        innovation_count=len(innovations),
        active_count=len(active),
        inactive_count=len(innovations) - len(active),
        active_fire_hearth_count=fire,
        active_pottery_craft_count=pottery,
        active_irrigation_canal_count=irrigation,
        active_forge_count=forge,
    )
