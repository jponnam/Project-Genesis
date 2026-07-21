"""Deterministic seeded random number generator.

Civitas Lab forbids unseeded randomness. All stochastic draws go through
``SeededRNG``, which wraps ``random.Random`` and never touches the
process-global RNG module state.
"""

from __future__ import annotations

import hashlib
from random import Random
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from civitas.domain import SimulationConfig

T = TypeVar("T")


def mix_seed(seed: int, stream_id: int) -> int:
    """Derive a stable child seed from ``seed`` and ``stream_id``.

    Uses SHA-256 so the mapping is platform-independent and does not
    consume draws from a parent generator.
    """
    if seed < 0:
        msg = f"seed must be non-negative, got {seed}"
        raise ValueError(msg)
    if stream_id < 0:
        msg = f"stream_id must be non-negative, got {stream_id}"
        raise ValueError(msg)
    digest = hashlib.sha256(f"{seed}:{stream_id}".encode()).digest()
    # Keep within signed 63-bit positives for broad Random compatibility.
    return int.from_bytes(digest[:8], byteorder="big") >> 1


class SeededRNG:
    """Explicitly seeded RNG for reproducible simulations.

    Each public draw increments ``draw_count``. ``spawn`` creates an
    independent child stream without advancing the parent.
    """

    def __init__(self, seed: int) -> None:
        """Create an RNG bound to ``seed``.

        Raises:
            ValueError: If ``seed`` is negative.
        """
        if seed < 0:
            msg = f"seed must be non-negative, got {seed}"
            raise ValueError(msg)
        self._seed = seed
        self._rng = Random(seed)
        self._draw_count = 0

    @classmethod
    def from_config(cls, config: SimulationConfig) -> SeededRNG:
        """Construct an RNG using ``config.seed``."""
        return cls(seed=config.seed)

    @property
    def seed(self) -> int:
        """Original seed used to initialize this generator."""
        return self._seed

    @property
    def draw_count(self) -> int:
        """Number of draws taken since construction or last ``reset``."""
        return self._draw_count

    def reset(self) -> None:
        """Restore the generator to its initial seeded state."""
        self._rng.seed(self._seed)
        self._draw_count = 0

    def spawn(self, stream_id: int) -> SeededRNG:
        """Return an independent child RNG derived from this seed.

        Spawning does not advance ``draw_count`` or otherwise mutate this
        generator's state.
        """
        return SeededRNG(seed=mix_seed(self._seed, stream_id))

    def random(self) -> float:
        """Return the next float in ``[0.0, 1.0)``."""
        self._draw_count += 1
        return self._rng.random()

    def uniform(self, low: float, high: float) -> float:
        """Return the next float uniformly from ``[low, high]``.

        Raises:
            ValueError: If ``high`` is less than ``low``.
        """
        if high < low:
            msg = f"high must be >= low, got low={low}, high={high}"
            raise ValueError(msg)
        self._draw_count += 1
        return self._rng.uniform(low, high)

    def randint(self, low: int, high: int) -> int:
        """Return the next int uniformly from ``[low, high]`` inclusive.

        Raises:
            ValueError: If ``high`` is less than ``low``.
        """
        if high < low:
            msg = f"high must be >= low, got low={low}, high={high}"
            raise ValueError(msg)
        self._draw_count += 1
        return self._rng.randint(low, high)

    def chance(self, probability: float) -> bool:
        """Return True with the given probability in ``[0.0, 1.0]``.

        Raises:
            ValueError: If ``probability`` is outside ``[0.0, 1.0]``.
        """
        if probability < 0.0 or probability > 1.0:
            msg = f"probability must be in [0.0, 1.0], got {probability}"
            raise ValueError(msg)
        return self.random() < probability

    def choice(self, population: Sequence[T]) -> T:
        """Return one uniformly chosen element from ``population``.

        Raises:
            ValueError: If ``population`` is empty.
        """
        if not population:
            msg = "population must be non-empty"
            raise ValueError(msg)
        self._draw_count += 1
        return self._rng.choice(population)

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        """Return ``k`` unique elements chosen from ``population``.

        Raises:
            ValueError: If ``k`` is negative or larger than the population.
        """
        if k < 0:
            msg = f"k must be non-negative, got {k}"
            raise ValueError(msg)
        if k > len(population):
            msg = f"sample larger than population: k={k}, n={len(population)}"
            raise ValueError(msg)
        self._draw_count += 1
        return self._rng.sample(list(population), k)

    def shuffled(self, population: Sequence[T]) -> list[T]:
        """Return a new list with elements of ``population`` shuffled.

        The input sequence is never mutated.
        """
        items = list(population)
        self._draw_count += 1
        self._rng.shuffle(items)
        return items

    def unit_interval(self) -> float:
        """Alias for ``random()`` — a draw in ``[0.0, 1.0)``."""
        return self.random()

    def __repr__(self) -> str:
        return f"SeededRNG(seed={self._seed}, draw_count={self._draw_count})"
