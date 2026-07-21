"""Pure numeric helpers shared across domain and systems."""

from __future__ import annotations


def clamp_unit(value: float) -> float:
    """Clamp ``value`` to ``[0.0, 1.0]`` with stable 6-decimal rounding."""
    return max(0.0, min(1.0, round(value, 6)))
