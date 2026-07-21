"""Unit tests for the deterministic EventBus."""

from __future__ import annotations

from civitas.domain import (
    ActionSelected,
    AgentId,
    Tick,
    TickCompleted,
    TickStarted,
)
from civitas.engine import EventBus


def test_publish_assigns_monotonic_sequence() -> None:
    """Published events receive increasing sequence numbers."""
    bus = EventBus()
    first = bus.publish(TickStarted(tick=Tick(value=1)))
    second = bus.publish(TickCompleted(tick=Tick(value=1)))
    assert first.sequence == 0
    assert second.sequence == 1
    assert bus.next_sequence == 2
    assert bus.history == (first, second)


def test_exact_handlers_run_in_subscription_order() -> None:
    """Exact-type subscribers are invoked in registration order."""
    bus = EventBus()
    seen: list[str] = []

    bus.subscribe(TickStarted, lambda _event: seen.append("a"))
    bus.subscribe(TickStarted, lambda _event: seen.append("b"))
    bus.publish(TickStarted(tick=Tick(value=1)))
    assert seen == ["a", "b"]


def test_subscribe_any_runs_after_exact_handlers() -> None:
    """Wildcard handlers run after exact-type handlers."""
    bus = EventBus()
    seen: list[str] = []

    bus.subscribe_any(lambda _event: seen.append("any"))
    bus.subscribe(TickStarted, lambda _event: seen.append("exact"))
    bus.publish(TickStarted(tick=Tick(value=1)))
    assert seen == ["exact", "any"]


def test_handlers_do_not_receive_other_event_types() -> None:
    """Exact subscriptions ignore non-matching event types."""
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe(TickStarted, lambda _event: seen.append("started"))
    bus.publish(TickCompleted(tick=Tick(value=1)))
    assert seen == []


def test_publish_many_preserves_order() -> None:
    """publish_many stamps and records events in list order."""
    bus = EventBus()
    stamped = bus.publish_many(
        [
            TickStarted(tick=Tick(value=1)),
            TickCompleted(tick=Tick(value=1)),
        ]
    )
    assert [event.sequence for event in stamped] == [0, 1]
    assert [event.event_type for event in stamped] == [
        "TickStarted",
        "TickCompleted",
    ]


def test_reset_clears_history_and_sequence_keeps_subscriptions() -> None:
    """reset() clears history/sequence but leaves handlers registered."""
    bus = EventBus()
    seen: list[int] = []
    bus.subscribe(TickStarted, lambda event: seen.append(event.sequence))
    bus.publish(TickStarted(tick=Tick(value=1)))
    bus.reset()
    assert bus.history == ()
    assert bus.next_sequence == 0
    bus.publish(TickStarted(tick=Tick(value=1)))
    assert seen == [0, 0]


def test_dispatch_is_deterministic_for_identical_publishes() -> None:
    """Identical publish sequences yield identical histories."""

    def run() -> tuple[str, ...]:
        bus = EventBus()
        bus.publish(TickStarted(tick=Tick(value=1)))
        bus.publish(
            ActionSelected(
                tick=Tick(value=1),
                agent_id=AgentId(value=0),
                action="eat",
                utility=0.5,
            )
        )
        bus.publish(TickCompleted(tick=Tick(value=1)))
        return tuple(event.event_type for event in bus.history)

    assert run() == run()
