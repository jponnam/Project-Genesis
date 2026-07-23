"""Tests for JSONL run inspection summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from civitas.domain import SimulationConfig
from civitas.engine import SimulationEngine
from civitas.storage import ReplayError, build_inspection, write_events

if TYPE_CHECKING:
    from pathlib import Path


def _write_run(path: Path, *, ticks: int = 3, agents: int = 3) -> Path:
    result = SimulationEngine().run(
        SimulationConfig(
            seed=42,
            ticks=ticks,
            agent_count=agents,
            run_name="inspect",
        )
    )
    write_events(path, result.events)
    return path


def test_build_inspection_includes_core_fields(tmp_path: Path) -> None:
    """Inspection reports seed, counts, institutions, and event types."""
    path = _write_run(tmp_path / "run.jsonl")
    report = build_inspection(path)
    assert report.seed == 42
    assert report.run_name == "inspect"
    assert report.event_count > 0
    assert report.event_types["SimulationStarted"] == 1
    assert report.agents_spawned == 3
    assert any(item.startswith("council:") for item in report.institutions)
    assert any(item.startswith("settlement:") for item in report.cities)
    assert report.final_resource_holdings_available is False
    assert report.wealth is not None
    assert report.population is not None
    assert report.population.alive == report.estimated_living
    payload = report.to_dict()
    assert payload["seed"] == 42
    assert "event_types" in payload


def test_build_inspection_longer_run_can_include_births(tmp_path: Path) -> None:
    """A longer deterministic run surfaces births in notable events when present."""
    path = _write_run(tmp_path / "long.jsonl", ticks=10, agents=5)
    report = build_inspection(path)
    assert report.births >= 0
    assert report.deaths >= 0
    if report.births:
        assert any("birth" in item for item in report.notable_events)


def test_build_inspection_missing_file(tmp_path: Path) -> None:
    """Missing logs raise ReplayError."""
    with pytest.raises(ReplayError, match="not found"):
        build_inspection(tmp_path / "missing.jsonl")


def test_build_inspection_is_deterministic(tmp_path: Path) -> None:
    """Two inspections of the same file yield identical dictionaries."""
    path = _write_run(tmp_path / "run.jsonl")
    assert build_inspection(path).to_dict() == build_inspection(path).to_dict()
