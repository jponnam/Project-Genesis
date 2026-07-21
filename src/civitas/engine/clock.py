"""Deterministic discrete simulation clock.

The clock is the sole authority for simulation time. It advances one
tick at a time and never consults wall-clock time or unseeded RNG.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from civitas.domain.time import Tick

if TYPE_CHECKING:
    from collections.abc import Iterator

    from civitas.domain import SimulationConfig


class ClockError(Exception):
    """Raised when a clock operation violates the simulation schedule."""


class SimulationClock:
    """Mutable tick clock for a single simulation run.

    Semantics
    ---------
    * Starts at tick ``0`` (initial world state, no advances yet).
    * ``duration`` is the number of advances to perform (from
      ``SimulationConfig.ticks``).
    * Each successful ``advance()`` moves to the next tick and returns it.
    * After ``duration`` advances, ``current_tick.value == duration`` and
      ``is_finished`` is ``True``.

    The clock is intentionally stateful. Tick values themselves remain
    immutable domain objects.
    """

    def __init__(self, duration: int) -> None:
        """Create a clock that will advance exactly ``duration`` times.

        Args:
            duration: Positive number of ticks to execute.

        Raises:
            ClockError: If ``duration`` is less than 1.
        """
        if duration < 1:
            msg = f"duration must be >= 1, got {duration}"
            raise ClockError(msg)
        self._duration = duration
        self._current = Tick(value=0)

    @classmethod
    def from_config(cls, config: SimulationConfig) -> Self:
        """Construct a clock from a validated simulation configuration."""
        return cls(duration=config.ticks)

    @property
    def duration(self) -> int:
        """Total number of advances scheduled for this run."""
        return self._duration

    @property
    def current_tick(self) -> Tick:
        """Current discrete time point (immutable snapshot)."""
        return self._current

    @property
    def remaining(self) -> int:
        """Number of advances still allowed before the clock finishes."""
        return self._duration - self._current.value

    @property
    def is_finished(self) -> bool:
        """True when no further advances are permitted."""
        return self._current.value >= self._duration

    def advance(self) -> Tick:
        """Advance exactly one tick and return the new current tick.

        Raises:
            ClockError: If the clock has already reached ``duration``.
        """
        if self.is_finished:
            msg = (
                f"cannot advance past duration "
                f"(current={self._current.value}, duration={self._duration})"
            )
            raise ClockError(msg)
        self._current = self._current.next()
        return self._current

    def run(self) -> Iterator[Tick]:
        """Yield each tick from ``1`` through ``duration``, advancing.

        This is the canonical iteration protocol for the future engine
        loop: one yield per agent-update cycle.
        """
        while not self.is_finished:
            yield self.advance()

    def reset(self) -> None:
        """Return the clock to tick ``0`` without changing ``duration``."""
        self._current = Tick(value=0)

    def __repr__(self) -> str:
        return (
            f"SimulationClock(current={self._current.value}, duration={self._duration})"
        )
