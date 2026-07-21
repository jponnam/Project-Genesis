"""Deterministic in-process domain event bus.

The bus assigns a monotonic ``sequence`` to every published event,
appends it to an append-only history, and notifies subscribers in
subscription order. No threads, no wall-clock, no unseeded randomness.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from civitas.domain.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[E], None]
AnyEventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Synchronous, deterministic pub/sub bus for domain events.

    Dispatch order for each ``publish``:

    1. Exact-type handlers, in subscription order.
    2. Wildcard (``subscribe_any``) handlers, in subscription order.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[AnyEventHandler]] = {}
        self._any_handlers: list[AnyEventHandler] = []
        self._history: list[DomainEvent] = []
        self._next_sequence: int = 0

    @property
    def history(self) -> tuple[DomainEvent, ...]:
        """Return an immutable snapshot of published events in order."""
        return tuple(self._history)

    @property
    def next_sequence(self) -> int:
        """Sequence number that will be assigned to the next publish."""
        return self._next_sequence

    def subscribe(self, event_type: type[E], handler: EventHandler[E]) -> None:
        """Register ``handler`` for exact ``event_type`` publications."""
        handlers = self._handlers.setdefault(event_type, [])
        handlers.append(handler)  # type: ignore[arg-type]

    def subscribe_any(self, handler: AnyEventHandler) -> None:
        """Register ``handler`` for every published event."""
        self._any_handlers.append(handler)

    def publish(self, event: DomainEvent) -> DomainEvent:
        """Stamp ``sequence``, record history, and notify subscribers.

        Returns:
            The stamped event instance stored in history.
        """
        stamped = event.model_copy(update={"sequence": self._next_sequence})
        self._next_sequence += 1
        self._history.append(stamped)

        for handler in self._handlers.get(type(stamped), ()):
            handler(stamped)
        for handler in self._any_handlers:
            handler(stamped)
        return stamped

    def publish_many(self, events: list[DomainEvent]) -> tuple[DomainEvent, ...]:
        """Publish events in list order; return stamped results."""
        return tuple(self.publish(event) for event in events)

    def reset(self) -> None:
        """Clear history and sequence counter; keep subscriptions."""
        self._history.clear()
        self._next_sequence = 0
