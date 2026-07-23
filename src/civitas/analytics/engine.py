"""Analytics engine: compute the full offline metrics report for a run."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from civitas.analytics.metrics import ALL_METRICS
from civitas.analytics.types import MetricResult, MetricsReport
from civitas.storage.replay import load_events

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from civitas.domain import DomainEvent

    MetricFn = Callable[[tuple[DomainEvent, ...]], MetricResult]


def compute_metrics(
    events: Sequence[DomainEvent],
    *,
    path: str | None = None,
    metric_fns: Sequence[MetricFn] | None = None,
) -> MetricsReport:
    """Compute all (or selected) analytics metrics for ``events``.

    Metrics are evaluated in a stable order. Each metric handles empty and
    degenerate inputs itself.
    """
    ordered = tuple(events)
    selected = tuple(ALL_METRICS if metric_fns is None else metric_fns)
    results = tuple(metric_fn(ordered) for metric_fn in selected)
    return MetricsReport(path=path, event_count=len(ordered), metrics=results)


def analyze_run(path: Path | str) -> MetricsReport:
    """Load a JSONL run and compute the standard metrics report.

    Raises:
        civitas.storage.ReplayError: If the log cannot be loaded.
    """
    resolved = Path(path)
    events = load_events(resolved)
    return compute_metrics(events, path=str(resolved))
