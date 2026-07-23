"""Analytics layer: offline analysis of simulation traces.

Reads persisted event streams and produces research metrics. Analytics
never mutates simulation state and has no role in the tick loop.
"""

from __future__ import annotations

from civitas.analytics.compare import (
    ComparisonReport,
    compare_many,
    compare_runs,
    snapshot_run,
)
from civitas.analytics.emergence import (
    EmergenceFinding,
    EmergenceReport,
    analyze_emergence,
    detect_emergence,
)
from civitas.analytics.engine import analyze_run, compute_metrics
from civitas.analytics.types import MetricResult, MetricsReport

__all__ = [
    "ComparisonReport",
    "EmergenceFinding",
    "EmergenceReport",
    "MetricResult",
    "MetricsReport",
    "analyze_emergence",
    "analyze_run",
    "compare_many",
    "compare_runs",
    "compute_metrics",
    "detect_emergence",
    "snapshot_run",
]
