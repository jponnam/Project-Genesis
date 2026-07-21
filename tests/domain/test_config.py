"""Unit tests for simulation configuration models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import CANONICAL_SEED, SimulationConfig
from civitas.domain.config import SimulationConfig as ConfigDirect


def test_canonical_seed_is_forty_two() -> None:
    """Research reproducibility contract: canonical seed is 42."""
    assert CANONICAL_SEED == 42


def test_research_default_uses_canonical_seed() -> None:
    """research_default() must produce the canonical research configuration."""
    config = SimulationConfig.research_default()
    assert config.seed == CANONICAL_SEED
    assert config.ticks == 100
    assert config.agent_count == 10
    assert config.run_name == "default"


def test_default_construction_matches_research_default() -> None:
    """Bare SimulationConfig() must equal research_default()."""
    assert SimulationConfig() == SimulationConfig.research_default()


def test_config_is_frozen() -> None:
    """Configuration must be immutable after construction."""
    config = SimulationConfig()
    with pytest.raises(ValidationError):
        config.seed = 99  # type: ignore[misc]


def test_config_rejects_unknown_fields() -> None:
    """Extra fields are forbidden to prevent silent misconfiguration."""
    with pytest.raises(ValidationError):
        SimulationConfig.from_mapping({"seed": 1, "unknown": True})


def test_from_mapping_accepts_valid_overrides() -> None:
    """from_mapping must validate and apply provided overrides."""
    config = SimulationConfig.from_mapping(
        {
            "seed": 7,
            "ticks": 50,
            "agent_count": 3,
            "run_name": "experiment-a",
        }
    )
    assert config.seed == 7
    assert config.ticks == 50
    assert config.agent_count == 3
    assert config.run_name == "experiment-a"


def test_seed_must_be_non_negative() -> None:
    """Negative seeds are rejected."""
    with pytest.raises(ValidationError):
        SimulationConfig(seed=-1)


def test_ticks_must_be_positive() -> None:
    """Zero or negative tick counts are rejected."""
    with pytest.raises(ValidationError):
        SimulationConfig(ticks=0)
    with pytest.raises(ValidationError):
        SimulationConfig(ticks=-5)


def test_agent_count_must_be_positive() -> None:
    """Zero or negative agent counts are rejected."""
    with pytest.raises(ValidationError):
        SimulationConfig(agent_count=0)


def test_ticks_upper_bound_enforced() -> None:
    """Tick counts above the safety bound are rejected."""
    with pytest.raises(ValidationError):
        SimulationConfig(ticks=10_000_001)


def test_agent_count_upper_bound_enforced() -> None:
    """Agent counts above the safety bound are rejected."""
    with pytest.raises(ValidationError):
        SimulationConfig(agent_count=1_000_001)


def test_run_name_strips_whitespace() -> None:
    """Leading/trailing whitespace in run_name is stripped."""
    config = SimulationConfig(run_name="  trial-1  ")
    assert config.run_name == "trial-1"


def test_run_name_rejects_blank() -> None:
    """Blank or whitespace-only run names are rejected."""
    with pytest.raises(ValidationError):
        SimulationConfig(run_name="   ")
    with pytest.raises(ValidationError):
        SimulationConfig(run_name="")


def test_identical_configs_compare_equal() -> None:
    """Value equality holds for identical field sets."""
    left = SimulationConfig(seed=42, ticks=10, agent_count=2, run_name="x")
    right = SimulationConfig(seed=42, ticks=10, agent_count=2, run_name="x")
    assert left == right
    assert hash(left) == hash(right)


def test_fingerprint_is_stable_and_descriptive() -> None:
    """Fingerprint must encode all config fields stably."""
    config = SimulationConfig(seed=42, ticks=100, agent_count=10, run_name="default")
    assert config.fingerprint() == "seed=42|ticks=100|agents=10|name=default"


def test_different_seeds_produce_different_fingerprints() -> None:
    """Fingerprints must differ when seeds differ."""
    a = SimulationConfig(seed=1)
    b = SimulationConfig(seed=2)
    assert a.fingerprint() != b.fingerprint()


def test_domain_package_exports_config() -> None:
    """SimulationConfig must be exported from civitas.domain."""
    assert ConfigDirect is SimulationConfig
