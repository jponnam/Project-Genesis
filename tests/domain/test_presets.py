"""Tests for Phase 22 world presets / bootstrap overlays."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    InnovationKind,
    SimulationConfig,
    TechnologyKind,
    WorldPreset,
    apply_bootstrap_overlay,
    default_cities,
    default_infrastructure,
    default_innovations,
    default_institutions,
    default_laws,
    default_research_progress,
    default_technologies,
    parse_world_preset,
)
from civitas.domain.attributes import Knowledge
from civitas.engine import WorldFactory


def _bundle(preset: WorldPreset):
    return apply_bootstrap_overlay(
        preset=preset,
        technologies=default_technologies(),
        innovations=default_innovations(),
        laws=default_laws(),
        institutions=default_institutions(),
        cities=default_cities(),
        infrastructure=default_infrastructure(),
        research_progress=default_research_progress(),
        founder_knowledge=Knowledge(facts=frozenset({"fire"})),
    )


def test_parse_world_preset_accepts_known_values() -> None:
    """Known preset names parse to WorldPreset."""
    assert parse_world_preset("early_craft") is WorldPreset.EARLY_CRAFT
    assert parse_world_preset(WorldPreset.CIVIC_DENSE) is WorldPreset.CIVIC_DENSE


def test_parse_world_preset_rejects_unknown() -> None:
    """Unknown presets raise ValueError with known names."""
    with pytest.raises(ValueError, match="camp_minimal"):
        parse_world_preset("glass_town")


def test_camp_minimal_is_identity_overlay() -> None:
    """camp_minimal leaves default catalogs unchanged."""
    bundle = _bundle(WorldPreset.CAMP_MINIMAL)
    assert bundle.technologies == default_technologies()
    assert bundle.innovations == default_innovations()
    assert bundle.laws == default_laws()
    assert bundle.institutions == default_institutions()
    assert bundle.cities == default_cities()
    assert bundle.infrastructure == default_infrastructure()
    assert bundle.research_progress == default_research_progress()


def test_early_craft_unlocks_pottery_and_irrigation() -> None:
    """early_craft discovers pottery/irrigation and activates crafts."""
    bundle = _bundle(WorldPreset.EARLY_CRAFT)
    discovered = {tech.kind for tech in bundle.technologies if tech.discovered}
    assert TechnologyKind.FIRE in discovered
    assert TechnologyKind.POTTERY in discovered
    assert TechnologyKind.IRRIGATION in discovered
    active = {item.kind for item in bundle.innovations if item.active}
    assert InnovationKind.POTTERY_CRAFT in active
    assert InnovationKind.IRRIGATION_CANAL in active
    discovered_ids = {
        tech.technology_id.value for tech in bundle.technologies if tech.discovered
    }
    assert all(
        row.technology_id.value not in discovered_ids
        for row in bundle.research_progress
    )
    assert "pottery" in bundle.founder_knowledge.facts
    assert "irrigation" in bundle.founder_knowledge.facts


def test_civic_dense_adds_existing_civic_entities() -> None:
    """civic_dense adds only existing law/institution/city/infra kinds."""
    bundle = _bundle(WorldPreset.CIVIC_DENSE)
    assert len(bundle.laws) == 4
    assert len(bundle.institutions) == 5
    assert len(bundle.cities) == 3
    assert len(bundle.infrastructure) == 3
    assert {law.kind.value for law in bundle.laws} == {
        "tax_schedule",
        "market_fee",
        "curriculum",
        "assembly",
    }
    assert {city.kind.value for city in bundle.cities} == {
        "settlement",
        "outpost",
        "forum",
    }


def test_config_rejects_unknown_preset() -> None:
    """SimulationConfig validation rejects unknown presets."""
    with pytest.raises(ValidationError, match="unknown world preset"):
        SimulationConfig(preset="not_a_preset")


def test_fingerprint_includes_preset() -> None:
    """Different presets produce different fingerprints."""
    a = SimulationConfig(preset=WorldPreset.CAMP_MINIMAL)
    b = SimulationConfig(preset=WorldPreset.EARLY_CRAFT)
    assert a.fingerprint().endswith("|preset=camp_minimal")
    assert b.fingerprint().endswith("|preset=early_craft")
    assert a.fingerprint() != b.fingerprint()


def test_same_seed_and_preset_produce_identical_worlds() -> None:
    """Identical seed+preset ⇒ identical worlds."""
    config = SimulationConfig(
        seed=42,
        ticks=20,
        agent_count=4,
        preset=WorldPreset.EARLY_CRAFT,
    )
    factory = WorldFactory()
    assert factory.create(config) == factory.create(config)


def test_different_presets_produce_different_worlds() -> None:
    """Changing only the preset must change the world catalogs."""
    factory = WorldFactory()
    minimal = factory.create(SimulationConfig(seed=42, preset=WorldPreset.CAMP_MINIMAL))
    craft = factory.create(SimulationConfig(seed=42, preset=WorldPreset.EARLY_CRAFT))
    dense = factory.create(SimulationConfig(seed=42, preset=WorldPreset.CIVIC_DENSE))
    assert minimal != craft
    assert craft != dense
    assert any(
        tech.kind is TechnologyKind.POTTERY and tech.discovered
        for tech in craft.technologies
    )
    assert len(dense.cities) > len(craft.cities)
