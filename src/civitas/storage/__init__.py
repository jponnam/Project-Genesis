"""Storage layer: durable persistence and replay.

Persists domain events as append-only JSONL for reproducibility and
offline analysis. Storage never contains simulation policy logic.
"""

from __future__ import annotations

from civitas.storage.jsonl import JsonlEventStore, write_events
from civitas.storage.projector import ProjectedState, project_events, project_run
from civitas.storage.replay import (
    FinalStateSummary,
    ReplayError,
    ReplayResult,
    RunMetadata,
    replay_run,
)
from civitas.storage.summary import RunInspection, build_inspection

__all__ = [
    "FinalStateSummary",
    "JsonlEventStore",
    "ProjectedState",
    "ReplayError",
    "ReplayResult",
    "RunInspection",
    "RunMetadata",
    "build_inspection",
    "project_events",
    "project_run",
    "replay_run",
    "write_events",
]
