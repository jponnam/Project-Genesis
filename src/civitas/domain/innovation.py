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
    CAMP_AGRICULTURE,
    CAMP_ANATOMY,
    CAMP_ARCHITECTURE,
    CAMP_ASTRONOMY,
    CAMP_CABINETRY,
    CAMP_CARPENTRY,
    CAMP_CARTOGRAPHY,
    CAMP_CERAMICS,
    CAMP_CROP_ROTATION,
    CAMP_DYEING,
    CAMP_ENGINEERING,
    CAMP_FIRE,
    CAMP_FORESTRY,
    CAMP_GLASSMAKING,
    CAMP_GLAZING,
    CAMP_HYGIENE,
    CAMP_IRRIGATION,
    CAMP_JOINERY,
    CAMP_LOGIC,
    CAMP_MATHEMATICS,
    CAMP_MEDICINE,
    CAMP_METALLURGY,
    CAMP_MINING,
    CAMP_NAVIGATION,
    CAMP_OPTICS,
    CAMP_PHILOSOPHY,
    CAMP_PORCELAIN,
    CAMP_POTTERY,
    CAMP_RHETORIC,
    CAMP_SEAFARING,
    CAMP_SMITHING,
    CAMP_SURVEYING,
    CAMP_TANNING,
    CAMP_TEXTILES,
    CAMP_TOOLMAKING,
    CAMP_WRITING,
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
    SCRIBE = "scribe"
    ABACUS = "abacus"
    STAR_CHART = "star_chart"
    DIALECTIC = "dialectic"
    SYLLOGISM = "syllogism"
    ORATION = "oration"
    REMEDY = "remedy"
    DISSECTION = "dissection"
    ASEPSIS = "asepsis"
    PULLEY = "pulley"
    BLUEPRINT = "blueprint"
    PLUMB_LINE = "plumb_line"
    COMPASS = "compass"
    MAP = "map"
    SAIL = "sail"
    PLOW = "plow"
    FALLOW = "fallow"
    COPPICE = "coppice"
    LOOM = "loom"
    MORDANT = "mordant"
    TANNERY = "tannery"
    PICKAXE = "pickaxe"
    BELLOWS = "bellows"
    LATHE = "lathe"
    SAWMILL = "sawmill"
    PLANE = "plane"
    DOVETAIL = "dovetail"
    KILN = "kiln"
    GLAZE = "glaze"
    KAOLIN = "kaolin"
    BLOWPIPE = "blowpipe"
    LENS = "lens"


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

CAMP_SCRIBE: Innovation = Innovation.create(
    4,
    CAMP_WRITING.technology_id.value,
    "Camp Scribe",
    InnovationKind.SCRIBE,
    active=False,
)

CAMP_ABACUS: Innovation = Innovation.create(
    5,
    CAMP_MATHEMATICS.technology_id.value,
    "Camp Abacus",
    InnovationKind.ABACUS,
    active=False,
)

CAMP_STAR_CHART: Innovation = Innovation.create(
    6,
    CAMP_ASTRONOMY.technology_id.value,
    "Camp Star Chart",
    InnovationKind.STAR_CHART,
    active=False,
)

CAMP_DIALECTIC: Innovation = Innovation.create(
    7,
    CAMP_PHILOSOPHY.technology_id.value,
    "Camp Dialectic",
    InnovationKind.DIALECTIC,
    active=False,
)

CAMP_SYLLOGISM: Innovation = Innovation.create(
    8,
    CAMP_LOGIC.technology_id.value,
    "Camp Syllogism",
    InnovationKind.SYLLOGISM,
    active=False,
)

CAMP_ORATION: Innovation = Innovation.create(
    9,
    CAMP_RHETORIC.technology_id.value,
    "Camp Oration",
    InnovationKind.ORATION,
    active=False,
)

CAMP_REMEDY: Innovation = Innovation.create(
    10,
    CAMP_MEDICINE.technology_id.value,
    "Camp Remedy",
    InnovationKind.REMEDY,
    active=False,
)

CAMP_DISSECTION: Innovation = Innovation.create(
    11,
    CAMP_ANATOMY.technology_id.value,
    "Camp Dissection",
    InnovationKind.DISSECTION,
    active=False,
)

CAMP_ASEPSIS: Innovation = Innovation.create(
    12,
    CAMP_HYGIENE.technology_id.value,
    "Camp Asepsis",
    InnovationKind.ASEPSIS,
    active=False,
)

CAMP_PULLEY: Innovation = Innovation.create(
    13,
    CAMP_ENGINEERING.technology_id.value,
    "Camp Pulley",
    InnovationKind.PULLEY,
    active=False,
)

CAMP_BLUEPRINT: Innovation = Innovation.create(
    14,
    CAMP_ARCHITECTURE.technology_id.value,
    "Camp Blueprint",
    InnovationKind.BLUEPRINT,
    active=False,
)

CAMP_PLUMB_LINE: Innovation = Innovation.create(
    15,
    CAMP_SURVEYING.technology_id.value,
    "Camp Plumb Line",
    InnovationKind.PLUMB_LINE,
    active=False,
)

CAMP_COMPASS: Innovation = Innovation.create(
    16,
    CAMP_NAVIGATION.technology_id.value,
    "Camp Compass",
    InnovationKind.COMPASS,
    active=False,
)

CAMP_MAP: Innovation = Innovation.create(
    17,
    CAMP_CARTOGRAPHY.technology_id.value,
    "Camp Map",
    InnovationKind.MAP,
    active=False,
)

CAMP_SAIL: Innovation = Innovation.create(
    18,
    CAMP_SEAFARING.technology_id.value,
    "Camp Sail",
    InnovationKind.SAIL,
    active=False,
)

CAMP_PLOW: Innovation = Innovation.create(
    19,
    CAMP_AGRICULTURE.technology_id.value,
    "Camp Plow",
    InnovationKind.PLOW,
    active=False,
)

CAMP_FALLOW: Innovation = Innovation.create(
    20,
    CAMP_CROP_ROTATION.technology_id.value,
    "Camp Fallow",
    InnovationKind.FALLOW,
    active=False,
)

CAMP_COPPICE: Innovation = Innovation.create(
    21,
    CAMP_FORESTRY.technology_id.value,
    "Camp Coppice",
    InnovationKind.COPPICE,
    active=False,
)

CAMP_LOOM: Innovation = Innovation.create(
    22,
    CAMP_TEXTILES.technology_id.value,
    "Camp Loom",
    InnovationKind.LOOM,
    active=False,
)

CAMP_MORDANT: Innovation = Innovation.create(
    23,
    CAMP_DYEING.technology_id.value,
    "Camp Mordant",
    InnovationKind.MORDANT,
    active=False,
)

CAMP_TANNERY: Innovation = Innovation.create(
    24,
    CAMP_TANNING.technology_id.value,
    "Camp Tannery",
    InnovationKind.TANNERY,
    active=False,
)

CAMP_PICKAXE: Innovation = Innovation.create(
    25,
    CAMP_MINING.technology_id.value,
    "Camp Pickaxe",
    InnovationKind.PICKAXE,
    active=False,
)

CAMP_BELLOWS: Innovation = Innovation.create(
    26,
    CAMP_SMITHING.technology_id.value,
    "Camp Bellows",
    InnovationKind.BELLOWS,
    active=False,
)

CAMP_LATHE: Innovation = Innovation.create(
    27,
    CAMP_TOOLMAKING.technology_id.value,
    "Camp Lathe",
    InnovationKind.LATHE,
    active=False,
)

CAMP_SAWMILL: Innovation = Innovation.create(
    28,
    CAMP_CARPENTRY.technology_id.value,
    "Camp Sawmill",
    InnovationKind.SAWMILL,
    active=False,
)

CAMP_PLANE: Innovation = Innovation.create(
    29,
    CAMP_JOINERY.technology_id.value,
    "Camp Plane",
    InnovationKind.PLANE,
    active=False,
)

CAMP_DOVETAIL: Innovation = Innovation.create(
    30,
    CAMP_CABINETRY.technology_id.value,
    "Camp Dovetail",
    InnovationKind.DOVETAIL,
    active=False,
)

CAMP_KILN: Innovation = Innovation.create(
    31,
    CAMP_CERAMICS.technology_id.value,
    "Camp Kiln",
    InnovationKind.KILN,
    active=False,
)

CAMP_GLAZE: Innovation = Innovation.create(
    32,
    CAMP_GLAZING.technology_id.value,
    "Camp Glaze",
    InnovationKind.GLAZE,
    active=False,
)

CAMP_KAOLIN: Innovation = Innovation.create(
    33,
    CAMP_PORCELAIN.technology_id.value,
    "Camp Kaolin",
    InnovationKind.KAOLIN,
    active=False,
)

CAMP_BLOWPIPE: Innovation = Innovation.create(
    34,
    CAMP_GLASSMAKING.technology_id.value,
    "Camp Blowpipe",
    InnovationKind.BLOWPIPE,
    active=False,
)

CAMP_LENS: Innovation = Innovation.create(
    35,
    CAMP_OPTICS.technology_id.value,
    "Camp Lens",
    InnovationKind.LENS,
    active=False,
)


def default_innovations() -> tuple[Innovation, ...]:
    """Return the canonical initial innovation set."""
    return (
        CAMP_FIRE_HEARTH,
        CAMP_POTTERY_CRAFT,
        CAMP_IRRIGATION_CANAL,
        CAMP_FORGE,
        CAMP_SCRIBE,
        CAMP_ABACUS,
        CAMP_STAR_CHART,
        CAMP_DIALECTIC,
        CAMP_SYLLOGISM,
        CAMP_ORATION,
        CAMP_REMEDY,
        CAMP_DISSECTION,
        CAMP_ASEPSIS,
        CAMP_PULLEY,
        CAMP_BLUEPRINT,
        CAMP_PLUMB_LINE,
        CAMP_COMPASS,
        CAMP_MAP,
        CAMP_SAIL,
        CAMP_PLOW,
        CAMP_FALLOW,
        CAMP_COPPICE,
        CAMP_LOOM,
        CAMP_MORDANT,
        CAMP_TANNERY,
        CAMP_PICKAXE,
        CAMP_BELLOWS,
        CAMP_LATHE,
        CAMP_SAWMILL,
        CAMP_PLANE,
        CAMP_DOVETAIL,
        CAMP_KILN,
        CAMP_GLAZE,
        CAMP_KAOLIN,
        CAMP_BLOWPIPE,
        CAMP_LENS,
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
    active_scribe_count: NonNegativeInt = 0
    active_abacus_count: NonNegativeInt = 0
    active_star_chart_count: NonNegativeInt = 0
    active_dialectic_count: NonNegativeInt = 0
    active_syllogism_count: NonNegativeInt = 0
    active_oration_count: NonNegativeInt = 0
    active_remedy_count: NonNegativeInt = 0
    active_dissection_count: NonNegativeInt = 0
    active_asepsis_count: NonNegativeInt = 0
    active_pulley_count: NonNegativeInt = 0
    active_blueprint_count: NonNegativeInt = 0
    active_plumb_line_count: NonNegativeInt = 0
    active_compass_count: NonNegativeInt = 0
    active_map_count: NonNegativeInt = 0
    active_sail_count: NonNegativeInt = 0
    active_plow_count: NonNegativeInt = 0
    active_fallow_count: NonNegativeInt = 0
    active_coppice_count: NonNegativeInt = 0
    active_loom_count: NonNegativeInt = 0
    active_mordant_count: NonNegativeInt = 0
    active_tannery_count: NonNegativeInt = 0
    active_pickaxe_count: NonNegativeInt = 0
    active_bellows_count: NonNegativeInt = 0
    active_lathe_count: NonNegativeInt = 0
    active_sawmill_count: NonNegativeInt = 0
    active_plane_count: NonNegativeInt = 0
    active_dovetail_count: NonNegativeInt = 0
    active_kiln_count: NonNegativeInt = 0
    active_glaze_count: NonNegativeInt = 0
    active_kaolin_count: NonNegativeInt = 0
    active_blowpipe_count: NonNegativeInt = 0
    active_lens_count: NonNegativeInt = 0


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
    scribe = sum(1 for item in active if item.kind is InnovationKind.SCRIBE)
    abacus = sum(1 for item in active if item.kind is InnovationKind.ABACUS)
    star_chart = sum(1 for item in active if item.kind is InnovationKind.STAR_CHART)
    dialectic = sum(1 for item in active if item.kind is InnovationKind.DIALECTIC)
    syllogism = sum(1 for item in active if item.kind is InnovationKind.SYLLOGISM)
    oration = sum(1 for item in active if item.kind is InnovationKind.ORATION)
    remedy = sum(1 for item in active if item.kind is InnovationKind.REMEDY)
    dissection = sum(1 for item in active if item.kind is InnovationKind.DISSECTION)
    asepsis = sum(1 for item in active if item.kind is InnovationKind.ASEPSIS)
    pulley = sum(1 for item in active if item.kind is InnovationKind.PULLEY)
    blueprint = sum(1 for item in active if item.kind is InnovationKind.BLUEPRINT)
    plumb_line = sum(1 for item in active if item.kind is InnovationKind.PLUMB_LINE)
    compass = sum(1 for item in active if item.kind is InnovationKind.COMPASS)
    camp_map = sum(1 for item in active if item.kind is InnovationKind.MAP)
    sail = sum(1 for item in active if item.kind is InnovationKind.SAIL)
    plow = sum(1 for item in active if item.kind is InnovationKind.PLOW)
    fallow = sum(1 for item in active if item.kind is InnovationKind.FALLOW)
    coppice = sum(1 for item in active if item.kind is InnovationKind.COPPICE)
    loom = sum(1 for item in active if item.kind is InnovationKind.LOOM)
    mordant = sum(1 for item in active if item.kind is InnovationKind.MORDANT)
    tannery = sum(1 for item in active if item.kind is InnovationKind.TANNERY)
    pickaxe = sum(1 for item in active if item.kind is InnovationKind.PICKAXE)
    bellows = sum(1 for item in active if item.kind is InnovationKind.BELLOWS)
    lathe = sum(1 for item in active if item.kind is InnovationKind.LATHE)
    sawmill = sum(1 for item in active if item.kind is InnovationKind.SAWMILL)
    plane = sum(1 for item in active if item.kind is InnovationKind.PLANE)
    dovetail = sum(1 for item in active if item.kind is InnovationKind.DOVETAIL)
    kiln = sum(1 for item in active if item.kind is InnovationKind.KILN)
    glaze = sum(1 for item in active if item.kind is InnovationKind.GLAZE)
    kaolin = sum(1 for item in active if item.kind is InnovationKind.KAOLIN)
    blowpipe = sum(1 for item in active if item.kind is InnovationKind.BLOWPIPE)
    lens = sum(1 for item in active if item.kind is InnovationKind.LENS)
    return InnovationCensus(
        tick=world.tick,
        innovation_count=len(innovations),
        active_count=len(active),
        inactive_count=len(innovations) - len(active),
        active_fire_hearth_count=fire,
        active_pottery_craft_count=pottery,
        active_irrigation_canal_count=irrigation,
        active_forge_count=forge,
        active_scribe_count=scribe,
        active_abacus_count=abacus,
        active_star_chart_count=star_chart,
        active_dialectic_count=dialectic,
        active_syllogism_count=syllogism,
        active_oration_count=oration,
        active_remedy_count=remedy,
        active_dissection_count=dissection,
        active_asepsis_count=asepsis,
        active_pulley_count=pulley,
        active_blueprint_count=blueprint,
        active_plumb_line_count=plumb_line,
        active_compass_count=compass,
        active_map_count=camp_map,
        active_sail_count=sail,
        active_plow_count=plow,
        active_fallow_count=fallow,
        active_coppice_count=coppice,
        active_loom_count=loom,
        active_mordant_count=mordant,
        active_tannery_count=tannery,
        active_pickaxe_count=pickaxe,
        active_bellows_count=bellows,
        active_lathe_count=lathe,
        active_sawmill_count=sawmill,
        active_plane_count=plane,
        active_dovetail_count=dovetail,
        active_kiln_count=kiln,
        active_glaze_count=glaze,
        active_kaolin_count=kaolin,
        active_blowpipe_count=blowpipe,
        active_lens_count=lens,
    )
