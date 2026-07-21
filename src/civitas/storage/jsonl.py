"""Append-only JSONL persistence for domain events.

Each line is one JSON object produced by ``DomainEvent.to_record()``.
Encoding is deterministic (``sort_keys=True``, compact separators) so the
same event stream always yields the same file bytes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from civitas.domain import DomainEvent, event_from_record

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence


class JsonlEventStore:
    """File-backed store for replaying simulation event streams.

    The store never interprets policy or world state — it only serializes
    and deserializes ``DomainEvent`` records.
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Return the JSONL file path."""
        return self._path

    def exists(self) -> bool:
        """Return True when the store file exists on disk."""
        return self._path.is_file()

    def append(self, event: DomainEvent) -> None:
        """Append a single event as one JSON line."""
        self._ensure_parent()
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(self._encode(event))
            handle.write("\n")

    def append_many(self, events: Sequence[DomainEvent]) -> None:
        """Append events in order as JSON lines."""
        if not events:
            return
        self._ensure_parent()
        with self._path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(self._encode(event))
                handle.write("\n")

    def write_all(self, events: Sequence[DomainEvent]) -> None:
        """Replace the store contents with ``events`` (atomic run dump)."""
        self._ensure_parent()
        payload = "".join(self._encode(event) + "\n" for event in events)
        self._path.write_text(payload, encoding="utf-8")

    def read_all(self, *, validate_sequence: bool = True) -> tuple[DomainEvent, ...]:
        """Load every event from the store in file order.

        Args:
            validate_sequence: When True, require ``sequence`` values to be
                contiguous integers starting at 0.

        Raises:
            FileNotFoundError: If the store file does not exist.
            ValueError: If a line is invalid JSON/event data, or sequence
                validation fails.
        """
        return tuple(self.iter_events(validate_sequence=validate_sequence))

    def iter_events(
        self,
        *,
        validate_sequence: bool = True,
    ) -> Iterator[DomainEvent]:
        """Yield events one-by-one for streaming replay."""
        if not self.exists():
            msg = f"event store not found: {self._path}"
            raise FileNotFoundError(msg)

        expected_sequence = 0
        with self._path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                event = self._decode_line(line, line_number=line_number)
                if validate_sequence and event.sequence != expected_sequence:
                    msg = (
                        f"non-contiguous sequence at line {line_number}: "
                        f"expected {expected_sequence}, got {event.sequence}"
                    )
                    raise ValueError(msg)
                expected_sequence += 1
                yield event

    def count(self) -> int:
        """Return the number of non-empty event lines in the store."""
        if not self.exists():
            return 0
        total = 0
        with self._path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                if raw_line.strip():
                    total += 1
        return total

    def clear(self) -> None:
        """Delete the store file if it exists."""
        if self.exists():
            self._path.unlink()

    def _ensure_parent(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _encode(event: DomainEvent) -> str:
        return json.dumps(
            event.to_record(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _decode_line(line: str, *, line_number: int) -> DomainEvent:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            msg = f"invalid JSON at line {line_number}: {exc.msg}"
            raise ValueError(msg) from exc
        if not isinstance(record, dict):
            msg = f"event record at line {line_number} must be a JSON object"
            raise ValueError(msg)
        try:
            return event_from_record(record)
        except (ValueError, TypeError) as exc:
            msg = f"invalid event at line {line_number}: {exc}"
            raise ValueError(msg) from exc


def write_events(path: Path | str, events: Iterable[DomainEvent]) -> JsonlEventStore:
    """Write ``events`` to ``path`` and return the store handle."""
    store = JsonlEventStore(path)
    store.write_all(tuple(events))
    return store
