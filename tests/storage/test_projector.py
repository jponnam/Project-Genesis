"""Tests for the deterministic partial world projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from civitas.domain import ResourcesObserved, SimulationConfig, Tick
from civitas.engine import SimulationEngine
from civitas.storage import ReplayError, project_events, project_run, write_events

if TYPE_CHECKING:
    from pathlib import Path


def test_project_run_is_deterministic(tmp_path: Path) -> None:
    """Identical JSONL yields identical projected state."""
    path = tmp_path / "run.jsonl"
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=3, agent_count=3, run_name="proj")
    )
    write_events(path, result.events)
    first = project_run(path)
    second = project_run(path)
    assert first == second
    assert first.seed == 42
    assert first.resource_holdings_available is True
    assert "full_world_identity" in first.unavailable
    assert "per_agent_money_vector" in first.unavailable
    assert first.to_dict()["event_count"] == first.event_count


def test_project_events_tracks_holdings_from_resources_observed() -> None:
    """Projector copies last ResourcesObserved holdings without inventing stocks."""
    state = project_events(
        (
            ResourcesObserved(
                sequence=0,
                tick=Tick(value=0),
                alive_count=2,
                agent_holdings=((0, "food", 4),),
                alive_totals=(("food", 4),),
                stack_count=1,
                distinct_resources=1,
            ),
        )
    )
    assert state.resource_holdings_available is True
    assert state.resource_alive_totals == (("food", 4),)
    assert state.resource_agent_holdings == ((0, "food", 4),)
    assert "resource_holdings" not in state.unavailable


def test_project_run_missing_file(tmp_path: Path) -> None:
    """Missing JSONL raises ReplayError."""
    with pytest.raises(ReplayError):
        project_run(tmp_path / "missing.jsonl")
