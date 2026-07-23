"""Tests for scenario TOML loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from civitas.scenarios import (
    ScenarioNotFoundError,
    default_scenarios_dir,
    list_scenarios,
    load_scenario,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_default_scenarios_dir_exists() -> None:
    """Repository scenarios directory is discoverable."""
    root = default_scenarios_dir()
    assert root.is_dir()
    assert any(root.glob("*.toml"))


def test_list_scenarios_contains_expected_ids() -> None:
    """Bundled scenarios load with required metadata."""
    scenarios = list_scenarios()
    ids = {scenario.id for scenario in scenarios}
    assert "wealth_concentration" in ids
    assert "technological_diffusion" in ids
    assert "scarcity_and_cooperation" in ids
    for scenario in scenarios:
        assert scenario.command.startswith("civitas run")
        assert scenario.observable_signals
        assert scenario.limitations
        assert scenario.seed >= 0
        assert scenario.ticks >= 1
        assert scenario.agents >= 1


def test_load_scenario_round_trip() -> None:
    """load_scenario returns the matching id."""
    scenario = load_scenario("institutional_formation")
    assert scenario.id == "institutional_formation"
    joined = " ".join(scenario.observable_signals)
    assert "InstitutionCreated" in joined or "council" in joined.lower()


def test_load_scenario_missing() -> None:
    """Unknown ids raise ScenarioNotFoundError."""
    with pytest.raises(ScenarioNotFoundError):
        load_scenario("not_a_real_scenario")


def test_invalid_toml_missing_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed scenario files raise ValueError."""
    root = tmp_path / "scenarios"
    root.mkdir()
    (root / "bad.toml").write_text("id = 'bad'\n", encoding="utf-8")
    monkeypatch.setenv("CIVITAS_SCENARIOS_DIR", str(root))
    with pytest.raises(ValueError, match="missing keys"):
        list_scenarios()
