"""Shared types for offline analytics metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class MetricResult:
    """One deterministic metric computed from an event stream.

    Attributes:
        name: Stable metric identifier (snake_case).
        definition: Precise human-readable definition.
        value: Primary scalar or structured value (JSON-serializable).
        status: ``ok``, ``empty``, or ``undefined`` for degenerate inputs.
        details: Optional supporting values (series, counts, notes).
    """

    name: str
    definition: str
    value: Any
    status: str = "ok"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MetricsReport:
    """Bundle of metrics for one simulation run."""

    path: str | None
    event_count: int
    metrics: tuple[MetricResult, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "path": self.path,
            "event_count": self.event_count,
            "metrics": [metric.to_dict() for metric in self.metrics],
        }

    def by_name(self) -> dict[str, MetricResult]:
        """Index metrics by name."""
        return {metric.name: metric for metric in self.metrics}
