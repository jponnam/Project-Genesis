"""Unit tests for the deterministic SimulationClock."""

from __future__ import annotations

import pytest

from civitas.domain import SimulationConfig, Tick
from civitas.engine import ClockError, SimulationClock


def test_clock_starts_at_tick_zero() -> None:
    """A new clock begins at the initial world state."""
    clock = SimulationClock(duration=10)
    assert clock.current_tick == Tick(value=0)
    assert clock.duration == 10
    assert clock.remaining == 10
    assert not clock.is_finished


def test_from_config_uses_config_ticks() -> None:
    """from_config must schedule exactly config.ticks advances."""
    config = SimulationConfig(ticks=25)
    clock = SimulationClock.from_config(config)
    assert clock.duration == 25


def test_advance_moves_forward_one_tick() -> None:
    """Each advance increments the current tick by one."""
    clock = SimulationClock(duration=3)
    assert clock.advance() == Tick(value=1)
    assert clock.advance() == Tick(value=2)
    assert clock.current_tick == Tick(value=2)
    assert clock.remaining == 1


def test_clock_finishes_after_duration_advances() -> None:
    """After duration advances, the clock is finished at tick=duration."""
    clock = SimulationClock(duration=3)
    clock.advance()
    clock.advance()
    final = clock.advance()
    assert final == Tick(value=3)
    assert clock.is_finished
    assert clock.remaining == 0


def test_advance_past_duration_raises() -> None:
    """Advancing a finished clock is a hard error."""
    clock = SimulationClock(duration=1)
    clock.advance()
    with pytest.raises(ClockError, match="cannot advance past duration"):
        clock.advance()


def test_duration_must_be_positive() -> None:
    """Zero or negative durations are rejected at construction."""
    with pytest.raises(ClockError, match="duration must be >= 1"):
        SimulationClock(duration=0)
    with pytest.raises(ClockError, match="duration must be >= 1"):
        SimulationClock(duration=-3)


def test_run_yields_ticks_one_through_duration() -> None:
    """run() yields ticks 1..duration in order and finishes the clock."""
    clock = SimulationClock(duration=4)
    ticks = list(clock.run())
    assert ticks == [Tick(value=1), Tick(value=2), Tick(value=3), Tick(value=4)]
    assert clock.is_finished


def test_run_is_deterministic_across_resets() -> None:
    """The same duration always produces the same tick sequence."""
    clock = SimulationClock(duration=5)
    first = list(clock.run())
    clock.reset()
    second = list(clock.run())
    assert first == second
    assert first == [Tick(value=n) for n in range(1, 6)]


def test_reset_returns_to_tick_zero() -> None:
    """reset() restores the initial state without changing duration."""
    clock = SimulationClock(duration=8)
    list(clock.run())
    assert clock.is_finished
    clock.reset()
    assert clock.current_tick == Tick(value=0)
    assert clock.duration == 8
    assert not clock.is_finished


def test_repr_includes_current_and_duration() -> None:
    """repr supports debugging without exposing private fields oddly."""
    clock = SimulationClock(duration=9)
    clock.advance()
    text = repr(clock)
    assert "current=1" in text
    assert "duration=9" in text


def test_research_default_config_clock_runs_one_hundred_ticks() -> None:
    """Canonical research config schedules 100 advances."""
    clock = SimulationClock.from_config(SimulationConfig.research_default())
    ticks = list(clock.run())
    assert len(ticks) == 100
    assert ticks[0] == Tick(value=1)
    assert ticks[-1] == Tick(value=100)
