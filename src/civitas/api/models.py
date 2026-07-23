"""Pydantic response models for the read-only research API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Liveness payload."""

    model_config = ConfigDict(extra="forbid")

    status: str
    version: str


class RunListItem(BaseModel):
    """One discovered JSONL run file."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    path: str
    size_bytes: int
    seed: int | None = None
    run_name: str | None = None
    ticks_configured: int | None = None
    ticks_executed: int | None = None
    agent_count: int | None = None
    event_count: int | None = None


class RunDetail(RunListItem):
    """Run metadata with verification notes."""

    has_started: bool
    has_completed: bool
    verification_notes: list[str] = Field(default_factory=list)


class EventPage(BaseModel):
    """Paginated event listing."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    total: int
    offset: int
    limit: int
    events: list[dict[str, Any]]


class AgentSummary(BaseModel):
    """Agent facts reconstructed from lifecycle/action events."""

    model_config = ConfigDict(extra="forbid")

    agent_id: int
    name: str | None = None
    spawned: bool = False
    born: bool = False
    died: bool = False
    death_cause: str | None = None
    action_counts: dict[str, int] = Field(default_factory=dict)
    last_location_id: int | None = None


class AgentListResponse(BaseModel):
    """Collection of agent summaries for a run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    agents: list[AgentSummary]


class TimelineResponse(BaseModel):
    """Notable timeline entries for a run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    entries: list[str]


class ErrorResponse(BaseModel):
    """Standard API error body."""

    model_config = ConfigDict(extra="forbid")

    detail: str
