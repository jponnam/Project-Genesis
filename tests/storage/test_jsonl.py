"""Unit tests for JSONL event storage and replay."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from civitas.domain import (
    ActionSelected,
    AgentId,
    SimulationConfig,
    Tick,
    TickCompleted,
    TickStarted,
)
from civitas.engine import SimulationEngine
from civitas.storage import JsonlEventStore, write_events

if TYPE_CHECKING:
    from pathlib import Path


def _sample_events() -> tuple[TickStarted, ActionSelected, TickCompleted]:
    return (
        TickStarted(sequence=0, tick=Tick(value=1)),
        ActionSelected(
            sequence=1,
            tick=Tick(value=1),
            agent_id=AgentId(value=0),
            action="eat",
            utility=0.75,
        ),
        TickCompleted(sequence=2, tick=Tick(value=1)),
    )


def test_write_all_and_read_all_round_trip(tmp_path: Path) -> None:
    """Events survive a full JSONL write/read round-trip."""
    path = tmp_path / "events.jsonl"
    events = _sample_events()
    store = JsonlEventStore(path)
    store.write_all(events)
    assert store.exists()
    assert store.count() == 3
    assert store.read_all() == events


def test_append_and_append_many(tmp_path: Path) -> None:
    """append / append_many extend the store in order."""
    path = tmp_path / "run" / "events.jsonl"
    store = JsonlEventStore(path)
    first, second, third = _sample_events()
    store.append(first)
    store.append_many((second, third))
    assert store.read_all() == (first, second, third)


def test_encoding_is_deterministic(tmp_path: Path) -> None:
    """Identical event streams produce identical file bytes."""
    events = _sample_events()
    left = tmp_path / "a.jsonl"
    right = tmp_path / "b.jsonl"
    JsonlEventStore(left).write_all(events)
    JsonlEventStore(right).write_all(events)
    assert left.read_text(encoding="utf-8") == right.read_text(encoding="utf-8")
    assert '"event_type":"ActionSelected"' in left.read_text(encoding="utf-8")


def test_write_events_helper(tmp_path: Path) -> None:
    """write_events creates a store populated with the given events."""
    path = tmp_path / "out.jsonl"
    events = _sample_events()
    store = write_events(path, events)
    assert store.path == path
    assert store.read_all() == events


def test_iter_events_streams_in_order(tmp_path: Path) -> None:
    """iter_events yields the same sequence as read_all."""
    store = write_events(tmp_path / "events.jsonl", _sample_events())
    assert tuple(store.iter_events()) == store.read_all()


def test_read_all_requires_existing_file(tmp_path: Path) -> None:
    """Reading a missing store raises FileNotFoundError."""
    store = JsonlEventStore(tmp_path / "missing.jsonl")
    with pytest.raises(FileNotFoundError):
        store.read_all()


def test_invalid_json_line_raises(tmp_path: Path) -> None:
    """Corrupt JSON lines are rejected with line context."""
    path = tmp_path / "bad.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON at line 1"):
        JsonlEventStore(path).read_all()


def test_unknown_event_type_raises(tmp_path: Path) -> None:
    """Unknown event_type values fail during replay."""
    path = tmp_path / "unknown.jsonl"
    path.write_text(
        '{"event_type":"NotReal","sequence":0,"tick":{"value":0}}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid event at line 1"):
        JsonlEventStore(path).read_all()


def test_sequence_validation_detects_gaps(tmp_path: Path) -> None:
    """Contiguous sequence validation catches gaps."""
    path = tmp_path / "gap.jsonl"
    JsonlEventStore(path).write_all(
        (
            TickStarted(sequence=0, tick=Tick(value=1)),
            TickCompleted(sequence=2, tick=Tick(value=1)),
        )
    )
    with pytest.raises(ValueError, match="non-contiguous sequence"):
        JsonlEventStore(path).read_all(validate_sequence=True)
    # Validation can be disabled for forensic reads.
    events = JsonlEventStore(path).read_all(validate_sequence=False)
    assert events[1].sequence == 2


def test_clear_removes_file(tmp_path: Path) -> None:
    """clear deletes the store file."""
    store = write_events(tmp_path / "events.jsonl", _sample_events())
    assert store.exists()
    store.clear()
    assert not store.exists()
    assert store.count() == 0


def test_simulation_events_persist_and_replay(tmp_path: Path) -> None:
    """A seed-42 engine run can be persisted and replayed losslessly."""
    config = SimulationConfig(seed=42, ticks=2, agent_count=3)
    result = SimulationEngine().run(config)
    path = tmp_path / "seed42.jsonl"
    store = write_events(path, result.events)
    replayed = store.read_all()
    assert replayed == result.events
    # Second write is byte-identical (deterministic encoding).
    write_events(tmp_path / "seed42-b.jsonl", result.events)
    assert path.read_bytes() == (tmp_path / "seed42-b.jsonl").read_bytes()
