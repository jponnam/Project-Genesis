"""Typed identifiers for domain entities.

Integer identifiers are assigned by the world factory (later milestone)
so that seeded construction remains deterministic.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.types import NonNegativeInt


class AgentId(BaseModel):
    """Unique agent identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable agent id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, AgentId):
            return self.value < other.value
        return NotImplemented


class LocationId(BaseModel):
    """Unique location identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable location id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, LocationId):
            return self.value < other.value
        return NotImplemented
