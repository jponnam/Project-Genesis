"""Discrete simulation time value objects.

Civitas Lab uses integer ticks, not wall-clock time. Tick ``0`` denotes
the initial world state before any agent updates. Positive ticks denote
completed advances of the simulation clock.
"""

from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field

NonNegativeInt = Annotated[int, Field(ge=0)]


class Tick(BaseModel):
    """Immutable discrete time point in a simulation.

    Attributes:
        value: Non-negative tick index. ``0`` is the initial state.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_default=True,
    )

    value: NonNegativeInt = Field(
        default=0,
        description="Discrete tick index (0 = initial world state).",
    )

    def next(self) -> Self:
        """Return the immediately following tick."""
        return type(self)(value=self.value + 1)

    def __int__(self) -> int:
        """Allow ``int(tick)`` for indexing and arithmetic call sites."""
        return self.value

    def __lt__(self, other: object) -> Any:
        if isinstance(other, Tick):
            return self.value < other.value
        if isinstance(other, int):
            return self.value < other
        return NotImplemented

    def __le__(self, other: object) -> Any:
        if isinstance(other, Tick):
            return self.value <= other.value
        if isinstance(other, int):
            return self.value <= other
        return NotImplemented
