"""Tests for deterministic run comparison."""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.analytics import compare_runs
from civitas.domain import SimulationConfig
from civitas.engine import SimulationEngine
from civitas.storage import write_events

if TYPE_CHECKING:
    from pathlib import Path


def _write(
    path: Path,
    *,
    seed: int,
    ticks: int = 3,
    agents: int = 2,
    name: str = "c",
) -> Path:
    result = SimulationEngine().run(
        SimulationConfig(seed=seed, ticks=ticks, agent_count=agents, run_name=name)
    )
    write_events(path, result.events)
    return path


def test_compare_identical_runs_has_no_deltas(tmp_path: Path) -> None:
    """Two byte-identical seed-42 runs compare with no field deltas."""
    left = _write(tmp_path / "a.jsonl", seed=42, name="same")
    right = _write(tmp_path / "b.jsonl", seed=42, name="same")
    report = compare_runs(left, right)
    assert report.identical_seeds is True
    assert report.identical_event_counts is True
    assert report.deltas == ()
    assert report.to_dict()["left"]["seed"] == 42


def test_compare_different_seeds_is_deterministic(tmp_path: Path) -> None:
    """Different seeds produce stable delta reports."""
    left = _write(tmp_path / "a.jsonl", seed=42, name="a")
    right = _write(tmp_path / "b.jsonl", seed=7, name="b")
    first = compare_runs(left, right)
    second = compare_runs(left, right)
    assert first.to_dict() == second.to_dict()
    assert first.identical_seeds is False
    fields = {delta.field for delta in first.deltas}
    assert "seed" in fields
    assert any("Seeds differ" in note for note in first.notes)
