"""Analytics layer: offline analysis of simulation traces.

Reads persisted event streams and produces research metrics. Analytics
never mutates simulation state and has no role in the tick loop.
"""

from __future__ import annotations

from civitas.analytics.engine import analyze_run, compute_metrics
from civitas.analytics.types import MetricResult, MetricsReport

__all__ = [
    "MetricResult",
    "MetricsReport",
    "analyze_run",
    "compute_metrics",
]
