"""Immutable simulation configuration models.

Configuration is a domain value object: pure data with validation and no I/O.
The engine and systems consume these settings; they never mutate them.

Determinism contract
--------------------
``seed`` is the sole source of stochasticity for a run. Identical
``SimulationConfig`` values must produce identical simulations once the
engine and systems are fully wired (Phase 1 completion).
"""

from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from civitas.domain.types import NonEmptyStr, NonNegativeInt

# Canonical seed used across research reproducibility tests.
CANONICAL_SEED: int = 42

BoundedTicks = Annotated[int, Field(ge=1, le=10_000_000)]
BoundedAgentCount = Annotated[int, Field(ge=1, le=1_000_000)]


class SimulationConfig(BaseModel):
    """Validated parameters for a single deterministic simulation run.

    Attributes:
        seed: Non-negative integer seed for the simulation RNG.
        ticks: Number of discrete ticks to advance the clock.
        agent_count: Initial agent population created by the world factory.
        run_name: Human-readable label for the run (not used in RNG).
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )

    seed: NonNegativeInt = Field(
        default=CANONICAL_SEED,
        description="RNG seed. Identical seeds must yield identical simulations.",
    )
    ticks: BoundedTicks = Field(
        default=100,
        description="Number of ticks to execute.",
    )
    agent_count: BoundedAgentCount = Field(
        default=10,
        description="Initial number of agents in the world.",
    )
    run_name: NonEmptyStr = Field(
        default="default",
        description="Label for the run; does not affect determinism.",
    )

    @field_validator("run_name")
    @classmethod
    def run_name_must_be_nonblank(cls, value: str) -> str:
        """Reject names that are empty after whitespace stripping."""
        if not value:
            msg = "run_name must not be blank"
            raise ValueError(msg)
        return value

    @classmethod
    def research_default(cls) -> Self:
        """Return the canonical research configuration (seed 42)."""
        return cls()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> Self:
        """Build a config from a plain mapping (e.g. CLI options or JSON)."""
        return cls.model_validate(data)

    def fingerprint(self) -> str:
        """Return a stable string identifying this configuration.

        The fingerprint includes every field that affects simulation
        outcomes. ``run_name`` is included for operator traceability but
        does not influence RNG behavior.
        """
        return (
            f"seed={self.seed}"
            f"|ticks={self.ticks}"
            f"|agents={self.agent_count}"
            f"|name={self.run_name}"
        )
