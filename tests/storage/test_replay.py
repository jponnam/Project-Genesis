"""Tests for JSONL replay helpers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from civitas.domain import SimulationConfig
from civitas.engine import SimulationEngine
from civitas.storage import JsonlEventStore, ReplayError, replay_run, write_events
from civitas.storage.replay import (
    agent_ids_in_event,
    build_final_state_summary,
    filter_events,
    load_events,
    verify_metadata,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_mini_run(path: Path) -> Path:
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=2, agent_count=2, run_name="replay")
    )
    write_events(path, result.events)
    return path


def test_load_events_reads_contiguous_store(tmp_path: Path) -> None:
    """load_events returns the full validated event tuple."""
    path = _write_mini_run(tmp_path / "run.jsonl")
    events = load_events(path)
    assert events[0].event_type == "SimulationStarted"
    assert events[-1].event_type == "SimulationCompleted"
    assert len(events) == JsonlEventStore(path).count()


def test_load_events_missing_file(tmp_path: Path) -> None:
    """Missing files raise ReplayError."""
    with pytest.raises(ReplayError, match="not found"):
        load_events(tmp_path / "missing.jsonl")


def test_load_events_malformed_json(tmp_path: Path) -> None:
    """Invalid JSON lines raise ReplayError."""
    path = tmp_path / "bad.jsonl"
    path.write_text("{not-json\n", encoding="utf-8")
    with pytest.raises(ReplayError, match="malformed JSONL"):
        load_events(path)


def test_load_events_unknown_event_type(tmp_path: Path) -> None:
    """Unknown event_type values are reported as unsupported."""
    path = tmp_path / "unknown.jsonl"
    path.write_text(
        json.dumps(
            {
                "event_type": "NotARealEvent",
                "sequence": 0,
                "tick": {"value": 0},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReplayError, match="unsupported or unknown event type"):
        load_events(path)


def test_load_events_incomplete_sequence(tmp_path: Path) -> None:
    """Broken sequence continuity is treated as a corrupt/incomplete log."""
    good = _write_mini_run(tmp_path / "good.jsonl")
    # Break sequence continuity by rewriting the second line.
    lines = good.read_text(encoding="utf-8").strip().splitlines()
    second = json.loads(lines[1])
    second["sequence"] = 99
    lines[1] = json.dumps(second, sort_keys=True, separators=(",", ":"))
    bad = tmp_path / "gap.jsonl"
    bad.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ReplayError, match="incomplete or corrupt log"):
        load_events(bad)


def test_verify_metadata_flags_missing_completed(tmp_path: Path) -> None:
    """Truncated logs without SimulationCompleted produce verification notes."""
    path = _write_mini_run(tmp_path / "full.jsonl")
    events = list(load_events(path))
    truncated = tuple(e for e in events if e.event_type != "SimulationCompleted")
    write_events(tmp_path / "trunc.jsonl", truncated)
    result = replay_run(tmp_path / "trunc.jsonl", verify=True)
    assert result.metadata.has_completed is False
    assert any(
        "missing SimulationCompleted" in note for note in result.verification_notes
    )


def test_filter_by_tick_and_type(tmp_path: Path) -> None:
    """Tick and event-type filters narrow the matched stream."""
    path = _write_mini_run(tmp_path / "run.jsonl")
    events = load_events(path)
    filtered = filter_events(
        events,
        from_tick=1,
        to_tick=1,
        event_types=frozenset({"ActionSelected", "TickStarted"}),
    )
    assert filtered
    assert all(e.tick.value == 1 for e in filtered)
    assert {e.event_type for e in filtered} <= {"ActionSelected", "TickStarted"}


def test_filter_unknown_event_type_errors() -> None:
    """Unknown --event-type values fail before filtering."""
    with pytest.raises(ReplayError, match="unknown event type filter"):
        filter_events((), event_types=frozenset({"NopeEvent"}))


def test_filter_invalid_tick_range() -> None:
    """from_tick greater than to_tick is rejected."""
    with pytest.raises(ReplayError, match="invalid tick range"):
        filter_events((), from_tick=5, to_tick=1)


def test_agent_filter_matches_action_events(tmp_path: Path) -> None:
    """Agent filters keep events that reference the selected agent id."""
    path = _write_mini_run(tmp_path / "run.jsonl")
    events = load_events(path)
    action = next(e for e in events if e.event_type == "ActionSelected")
    agent_id = next(iter(agent_ids_in_event(action)))
    filtered = filter_events(events, agent_ids=frozenset({agent_id}))
    assert filtered
    assert all(agent_ids_in_event(e) & {agent_id} for e in filtered)


def test_final_state_summary_is_event_derived(tmp_path: Path) -> None:
    """Final-state summary uses spawn/death/action and observation fields."""
    path = _write_mini_run(tmp_path / "run.jsonl")
    events = load_events(path)
    summary = build_final_state_summary(events)
    assert summary.agents_spawned == 2
    assert summary.estimated_living == 2
    assert summary.last_population_alive == 2
    assert summary.last_wealth_total_money is not None
    assert "council" in summary.institutions_created
    assert "settlement" in summary.cities_created
    assert summary.actions


def test_replay_run_deterministic(tmp_path: Path) -> None:
    """replay_run on the same file yields identical matched sequences."""
    path = _write_mini_run(tmp_path / "run.jsonl")
    first = replay_run(path, include_final_state=True)
    second = replay_run(path, include_final_state=True)
    assert [e.sequence for e in first.events] == [e.sequence for e in second.events]
    assert first.type_counts == second.type_counts
    assert first.final_state == second.final_state
    assert first.verification_notes == ()


def test_verify_metadata_healthy_run(tmp_path: Path) -> None:
    """A complete seed-42 mini-run has no verification notes."""
    path = _write_mini_run(tmp_path / "run.jsonl")
    result = replay_run(path, verify=True)
    assert verify_metadata(result.metadata) == ()
    assert result.metadata.seed == 42
    assert result.metadata.run_name == "replay"
