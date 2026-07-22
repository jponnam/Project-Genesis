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


class MarketId(BaseModel):
    """Unique market identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable market id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, MarketId):
            return self.value < other.value
        return NotImplemented


class ListingId(BaseModel):
    """Unique sell-listing identifier within a market."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable listing id within a market.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, ListingId):
            return self.value < other.value
        return NotImplemented


class GovernmentId(BaseModel):
    """Unique government / polity identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable government id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, GovernmentId):
            return self.value < other.value
        return NotImplemented


class LawId(BaseModel):
    """Unique law / statute identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable law id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, LawId):
            return self.value < other.value
        return NotImplemented


class ElectionId(BaseModel):
    """Unique election identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable election id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, ElectionId):
            return self.value < other.value
        return NotImplemented


class InstitutionId(BaseModel):
    """Unique institution identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable institution id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, InstitutionId):
            return self.value < other.value
        return NotImplemented


class CityId(BaseModel):
    """Unique city / settlement identifier within a simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    value: NonNegativeInt = Field(description="Stable city id for the run.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: object) -> Any:
        if isinstance(other, CityId):
            return self.value < other.value
        return NotImplemented
