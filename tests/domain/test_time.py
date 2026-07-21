"""Unit tests for discrete Tick value objects."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import Tick


def test_default_tick_is_zero() -> None:
    """The initial world state is tick 0."""
    assert Tick().value == 0


def test_tick_is_frozen() -> None:
    """Tick values are immutable."""
    tick = Tick(value=3)
    with pytest.raises(ValidationError):
        tick.value = 4  # type: ignore[misc]


def test_tick_rejects_negative_value() -> None:
    """Negative ticks are invalid."""
    with pytest.raises(ValidationError):
        Tick(value=-1)


def test_tick_next_advances_by_one() -> None:
    """next() returns a new Tick one step ahead."""
    assert Tick(value=0).next() == Tick(value=1)
    assert Tick(value=41).next() == Tick(value=42)


def test_tick_int_conversion() -> None:
    """Ticks convert cleanly to int."""
    assert int(Tick(value=7)) == 7


def test_tick_ordering() -> None:
    """Ticks compare by value against ticks and ints."""
    assert Tick(value=1) < Tick(value=2)
    assert Tick(value=2) <= 2
    assert Tick(value=3) < 4


def test_identical_ticks_are_equal_and_hashable() -> None:
    """Value equality and hashing support use in sets/maps."""
    left = Tick(value=5)
    right = Tick(value=5)
    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {Tick(value=5)}
