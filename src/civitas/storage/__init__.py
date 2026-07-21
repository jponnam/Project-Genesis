"""Storage layer: durable persistence and replay.

Persists domain events as append-only JSONL for reproducibility and
offline analysis. Storage never contains simulation policy logic.
"""

from __future__ import annotations

from civitas.storage.jsonl import JsonlEventStore, write_events

__all__ = [
    "JsonlEventStore",
    "write_events",
]
