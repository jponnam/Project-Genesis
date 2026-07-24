"""Named world presets / bootstrap overlays (Phase 22).

Presets deterministically enable *existing* catalog entities at world
construction. They must not introduce new ``*Kind`` enum values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from civitas.domain.attributes import Knowledge
from civitas.domain.cities import City, CityKind
from civitas.domain.infrastructure import Infrastructure, InfrastructureKind
from civitas.domain.innovation import Innovation, InnovationKind
from civitas.domain.institutions import Institution, InstitutionKind
from civitas.domain.laws import Law, LawKind
from civitas.domain.research import ResearchProgress
from civitas.domain.technology import Technology, TechnologyKind

# Fact strings mirror TechnologyKind values (avoid importing knowledge.py).
_FIRE_FACT = TechnologyKind.FIRE.value
_POTTERY_FACT = TechnologyKind.POTTERY.value
_IRRIGATION_FACT = TechnologyKind.IRRIGATION.value


class WorldPreset(StrEnum):
    """Named bootstrap depth for a simulation world."""

    CAMP_MINIMAL = "camp_minimal"
    EARLY_CRAFT = "early_craft"
    CIVIC_DENSE = "civic_dense"


@dataclass(frozen=True, slots=True)
class CatalogBundle:
    """Catalog tuples produced by default builders, after overlay."""

    technologies: tuple[Technology, ...]
    innovations: tuple[Innovation, ...]
    laws: tuple[Law, ...]
    institutions: tuple[Institution, ...]
    cities: tuple[City, ...]
    infrastructure: tuple[Infrastructure, ...]
    research_progress: tuple[ResearchProgress, ...]
    founder_knowledge: Knowledge


def parse_world_preset(value: str | WorldPreset) -> WorldPreset:
    """Parse a preset name; raises ``ValueError`` for unknown values."""
    if isinstance(value, WorldPreset):
        return value
    try:
        return WorldPreset(str(value).strip())
    except ValueError as exc:
        known = ", ".join(item.value for item in WorldPreset)
        msg = f"unknown world preset {value!r}; expected one of: {known}"
        raise ValueError(msg) from exc


def _discover(
    technologies: tuple[Technology, ...],
    kinds: frozenset[TechnologyKind],
) -> tuple[Technology, ...]:
    return tuple(
        tech.model_copy(update={"discovered": True}) if tech.kind in kinds else tech
        for tech in technologies
    )


def _activate(
    innovations: tuple[Innovation, ...],
    kinds: frozenset[InnovationKind],
) -> tuple[Innovation, ...]:
    return tuple(
        item.model_copy(update={"active": True}) if item.kind in kinds else item
        for item in innovations
    )


def _strip_research_for_discovered(
    research_progress: tuple[ResearchProgress, ...],
    technologies: tuple[Technology, ...],
) -> tuple[ResearchProgress, ...]:
    discovered_ids = {
        tech.technology_id.value for tech in technologies if tech.discovered
    }
    return tuple(
        row
        for row in research_progress
        if row.technology_id.value not in discovered_ids
    )


_EARLY_CRAFT_TECHS = frozenset(
    {
        TechnologyKind.FIRE,
        TechnologyKind.POTTERY,
        TechnologyKind.IRRIGATION,
    }
)
_EARLY_CRAFT_INNOVATIONS = frozenset(
    {
        InnovationKind.FIRE_HEARTH,
        InnovationKind.POTTERY_CRAFT,
        InnovationKind.IRRIGATION_CANAL,
    }
)
_EARLY_CRAFT_KNOWLEDGE = Knowledge(
    facts=frozenset({_FIRE_FACT, _POTTERY_FACT, _IRRIGATION_FACT})
)


def _civic_extra_laws() -> tuple[Law, ...]:
    return (
        Law.create(
            1,
            0,
            "Camp Market Fee",
            LawKind.MARKET_FEE,
            flat_amount=1,
            rate_bps=0,
            active=True,
        ),
        Law.create(
            2,
            0,
            "Camp Curriculum",
            LawKind.CURRICULUM,
            flat_amount=0,
            rate_bps=0,
            active=True,
        ),
        Law.create(
            3,
            0,
            "Camp Assembly",
            LawKind.ASSEMBLY,
            flat_amount=0,
            rate_bps=0,
            active=True,
        ),
    )


def _civic_extra_institutions() -> tuple[Institution, ...]:
    return (
        Institution.create(1, 0, 0, "Camp Guild", InstitutionKind.GUILD),
        Institution.create(2, 0, 0, "Camp Archive", InstitutionKind.ARCHIVE),
        Institution.create(3, 0, 0, "Camp Bureaucracy", InstitutionKind.BUREAUCRACY),
        Institution.create(4, 0, 0, "Camp Workshop", InstitutionKind.WORKSHOP),
    )


def _civic_extra_cities() -> tuple[City, ...]:
    return (
        City.create(1, 0, 1, "Camp Outpost", CityKind.OUTPOST, is_capital=False),
        City.create(2, 0, 2, "Camp Forum", CityKind.FORUM, is_capital=False),
    )


def _civic_extra_infrastructure() -> tuple[Infrastructure, ...]:
    return (
        Infrastructure.create(
            1,
            0,
            0,
            0,
            "Camp Storehouse",
            InfrastructureKind.STOREHOUSE,
        ),
        Infrastructure.create(
            2,
            0,
            0,
            0,
            "Camp Road",
            InfrastructureKind.ROAD,
        ),
    )


def apply_bootstrap_overlay(
    *,
    preset: WorldPreset | str,
    technologies: tuple[Technology, ...],
    innovations: tuple[Innovation, ...],
    laws: tuple[Law, ...],
    institutions: tuple[Institution, ...],
    cities: tuple[City, ...],
    infrastructure: tuple[Infrastructure, ...],
    research_progress: tuple[ResearchProgress, ...],
    founder_knowledge: Knowledge,
) -> CatalogBundle:
    """Apply a named preset overlay to default catalog tuples."""
    resolved = parse_world_preset(preset)

    if resolved is WorldPreset.CAMP_MINIMAL:
        return CatalogBundle(
            technologies=technologies,
            innovations=innovations,
            laws=laws,
            institutions=institutions,
            cities=cities,
            infrastructure=infrastructure,
            research_progress=research_progress,
            founder_knowledge=founder_knowledge,
        )

    techs = _discover(technologies, _EARLY_CRAFT_TECHS)
    innovs = _activate(innovations, _EARLY_CRAFT_INNOVATIONS)
    research = _strip_research_for_discovered(research_progress, techs)
    knowledge = _EARLY_CRAFT_KNOWLEDGE

    if resolved is WorldPreset.EARLY_CRAFT:
        return CatalogBundle(
            technologies=techs,
            innovations=innovs,
            laws=laws,
            institutions=institutions,
            cities=cities,
            infrastructure=infrastructure,
            research_progress=research,
            founder_knowledge=knowledge,
        )

    # civic_dense
    return CatalogBundle(
        technologies=techs,
        innovations=innovs,
        laws=laws + _civic_extra_laws(),
        institutions=institutions + _civic_extra_institutions(),
        cities=cities + _civic_extra_cities(),
        infrastructure=infrastructure + _civic_extra_infrastructure(),
        research_progress=research,
        founder_knowledge=knowledge,
    )
