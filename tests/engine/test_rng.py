"""Unit tests for deterministic SeededRNG."""

from __future__ import annotations

import random

import pytest

from civitas.domain import CANONICAL_SEED, SimulationConfig
from civitas.engine import SeededRNG, mix_seed


def _take_floats(rng: SeededRNG, count: int) -> tuple[float, ...]:
    return tuple(rng.random() for _ in range(count))


def test_same_seed_produces_identical_sequences() -> None:
    """Identical seeds must yield identical draw sequences."""
    left = SeededRNG(CANONICAL_SEED)
    right = SeededRNG(CANONICAL_SEED)
    assert _take_floats(left, 32) == _take_floats(right, 32)


def test_different_seeds_diverge() -> None:
    """Different seeds must not produce the same sequence."""
    left = _take_floats(SeededRNG(1), 16)
    right = _take_floats(SeededRNG(2), 16)
    assert left != right


def test_from_config_uses_config_seed() -> None:
    """from_config binds to SimulationConfig.seed."""
    config = SimulationConfig(seed=99)
    rng = SeededRNG.from_config(config)
    assert rng.seed == 99
    assert _take_floats(rng, 8) == _take_floats(SeededRNG(99), 8)


def test_research_default_seed_is_canonical() -> None:
    """Research default config RNG uses seed 42."""
    rng = SeededRNG.from_config(SimulationConfig.research_default())
    assert rng.seed == CANONICAL_SEED == 42


def test_negative_seed_rejected() -> None:
    """Negative seeds are invalid."""
    with pytest.raises(ValueError, match="non-negative"):
        SeededRNG(-1)


def test_reset_restores_initial_sequence() -> None:
    """reset() replays the original sequence from the start."""
    rng = SeededRNG(7)
    first = _take_floats(rng, 10)
    rng.reset()
    assert rng.draw_count == 0
    second = _take_floats(rng, 10)
    assert first == second


def test_draw_count_tracks_public_draws() -> None:
    """Each public draw increments draw_count once."""
    rng = SeededRNG(3)
    assert rng.draw_count == 0
    rng.random()
    rng.randint(0, 3)
    rng.uniform(0.0, 1.0)
    rng.chance(0.5)
    rng.choice((1, 2, 3))
    rng.sample((1, 2, 3, 4), 2)
    rng.shuffled((1, 2, 3))
    rng.unit_interval()
    assert rng.draw_count == 8


def test_shuffled_is_deterministic_and_non_mutating() -> None:
    """shuffled is reproducible and never mutates the input sequence."""
    original = [1, 2, 3, 4, 5]
    snapshot = list(original)
    first = SeededRNG(11).shuffled(original)
    second = SeededRNG(11).shuffled(original)
    assert original == snapshot
    assert first == second
    assert sorted(first) == snapshot


def test_choice_rejects_empty_population() -> None:
    """choice on an empty population is an error."""
    with pytest.raises(ValueError, match="non-empty"):
        SeededRNG(1).choice(())


def test_randint_and_uniform_validate_bounds() -> None:
    """Inverted ranges are rejected."""
    rng = SeededRNG(1)
    with pytest.raises(ValueError, match="high must be >= low"):
        rng.randint(5, 1)
    with pytest.raises(ValueError, match="high must be >= low"):
        rng.uniform(2.0, 1.0)


def test_chance_bounds_and_extremes() -> None:
    """chance validates probability and respects 0/1 extremes."""
    rng = SeededRNG(5)
    with pytest.raises(ValueError, match="probability"):
        rng.chance(-0.1)
    with pytest.raises(ValueError, match="probability"):
        rng.chance(1.1)
    assert rng.chance(0.0) is False
    assert rng.chance(1.0) is True


def test_spawn_is_independent_of_parent_draws() -> None:
    """Child streams depend only on seed+stream_id, not parent state."""
    parent = SeededRNG(CANONICAL_SEED)
    child_before = parent.spawn(0)
    _ = parent.random()
    child_after = parent.spawn(0)
    assert _take_floats(child_before, 12) == _take_floats(child_after, 12)
    assert parent.draw_count == 1


def test_spawn_streams_differ_by_stream_id() -> None:
    """Different stream ids produce different child sequences."""
    parent = SeededRNG(CANONICAL_SEED)
    a = _take_floats(parent.spawn(0), 12)
    b = _take_floats(parent.spawn(1), 12)
    assert a != b


def test_mix_seed_is_stable() -> None:
    """mix_seed is pure and stable for the same inputs."""
    assert mix_seed(42, 0) == mix_seed(42, 0)
    assert mix_seed(42, 0) != mix_seed(42, 1)
    with pytest.raises(ValueError):
        mix_seed(-1, 0)
    with pytest.raises(ValueError):
        mix_seed(0, -1)


def test_does_not_consume_process_global_rng() -> None:
    """Using SeededRNG must not advance random module global state."""
    random.seed(12345)
    before = tuple(random.random() for _ in range(5))
    random.seed(12345)
    _ = _take_floats(SeededRNG(999), 50)
    after = tuple(random.random() for _ in range(5))
    assert before == after


def test_repr_includes_seed_and_draw_count() -> None:
    """repr supports debugging without exposing private fields oddly."""
    rng = SeededRNG(42)
    rng.random()
    text = repr(rng)
    assert "seed=42" in text
    assert "draw_count=1" in text
