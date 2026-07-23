"""Deterministic comparison of two or more JSONL simulation runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from civitas.analytics.emergence import EmergenceReport, analyze_emergence
from civitas.analytics.engine import analyze_run
from civitas.analytics.types import MetricsReport
from civitas.storage.replay import ReplayError, load_events
from civitas.storage.summary import RunInspection, build_inspection


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    """Compact comparable view of one run."""

    path: str
    run_name: str | None
    seed: int | None
    ticks_configured: int | None
    ticks_executed: int | None
    agent_count_configured: int | None
    event_count: int
    actions: dict[str, int]
    births: int
    deaths: int
    estimated_living: int
    trades: int
    wealth_gini_bps: int | None
    wealth_top1_share_bps: int | None
    institutions: tuple[str, ...]
    cities: tuple[str, ...]
    technologies_discovered: tuple[str, ...]
    emergence_patterns: tuple[str, ...]
    action_diversity_entropy: float | None
    relationship_network_density_bps: int | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ComparisonDelta:
    """One named difference between left and right runs."""

    field: str
    left: Any
    right: Any
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    """Structured comparison across two runs."""

    left: RunSnapshot
    right: RunSnapshot
    deltas: tuple[ComparisonDelta, ...]
    identical_seeds: bool
    identical_event_counts: bool
    shared_emergence: tuple[str, ...]
    unique_left_emergence: tuple[str, ...]
    unique_right_emergence: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "deltas": [delta.to_dict() for delta in self.deltas],
            "identical_seeds": self.identical_seeds,
            "identical_event_counts": self.identical_event_counts,
            "shared_emergence": list(self.shared_emergence),
            "unique_left_emergence": list(self.unique_left_emergence),
            "unique_right_emergence": list(self.unique_right_emergence),
            "notes": list(self.notes),
        }


def _metric_value(report: MetricsReport, name: str) -> Any:
    metric = report.by_name().get(name)
    if metric is None or metric.status != "ok":
        return None
    return metric.value


def snapshot_run(path: Path | str) -> RunSnapshot:
    """Build a comparable snapshot for one JSONL path."""
    resolved = Path(path)
    inspection = build_inspection(resolved)
    metrics = analyze_run(resolved)
    emergence = analyze_emergence(resolved)
    wealth = inspection.wealth
    return RunSnapshot(
        path=str(resolved),
        run_name=inspection.run_name,
        seed=inspection.seed,
        ticks_configured=inspection.ticks_configured,
        ticks_executed=inspection.ticks_executed,
        agent_count_configured=inspection.agent_count_configured,
        event_count=inspection.event_count,
        actions=dict(inspection.actions),
        births=inspection.births,
        deaths=inspection.deaths,
        estimated_living=inspection.estimated_living,
        trades=inspection.trades,
        wealth_gini_bps=None if wealth is None else int(wealth.gini_bps),
        wealth_top1_share_bps=(None if wealth is None else int(wealth.top1_share_bps)),
        institutions=inspection.institutions,
        cities=inspection.cities,
        technologies_discovered=inspection.technologies_discovered,
        emergence_patterns=tuple(
            sorted({finding.pattern for finding in emergence.findings})
        ),
        action_diversity_entropy=_metric_value(metrics, "action_diversity_entropy"),
        relationship_network_density_bps=_metric_value(
            metrics,
            "relationship_network_density",
        ),
    )


def _delta(
    field_name: str,
    left: Any,
    right: Any,
    *,
    note: str = "",
) -> ComparisonDelta | None:
    if left == right:
        return None
    return ComparisonDelta(field=field_name, left=left, right=right, note=note)


def compare_runs(left_path: Path | str, right_path: Path | str) -> ComparisonReport:
    """Compare two runs and return a deterministic report.

    Raises:
        ReplayError: If either log cannot be loaded.
    """
    # Touch-load to surface malformed logs early with ReplayError.
    load_events(left_path)
    load_events(right_path)
    left = snapshot_run(left_path)
    right = snapshot_run(right_path)

    deltas: list[ComparisonDelta] = []
    for field_name in (
        "seed",
        "run_name",
        "ticks_configured",
        "ticks_executed",
        "agent_count_configured",
        "event_count",
        "births",
        "deaths",
        "estimated_living",
        "trades",
        "wealth_gini_bps",
        "wealth_top1_share_bps",
        "action_diversity_entropy",
        "relationship_network_density_bps",
        "actions",
        "institutions",
        "cities",
        "technologies_discovered",
    ):
        item = _delta(
            field_name,
            getattr(left, field_name),
            getattr(right, field_name),
        )
        if item is not None:
            deltas.append(item)

    left_patterns = set(left.emergence_patterns)
    right_patterns = set(right.emergence_patterns)
    shared = tuple(sorted(left_patterns & right_patterns))
    only_left = tuple(sorted(left_patterns - right_patterns))
    only_right = tuple(sorted(right_patterns - left_patterns))
    notes: list[str] = []
    if left.seed == right.seed and left.event_count != right.event_count:
        notes.append(
            "Same seed but different event counts; configs or code versions may differ."
        )
    if left.seed != right.seed:
        notes.append("Seeds differ; outcome differences are expected.")

    return ComparisonReport(
        left=left,
        right=right,
        deltas=tuple(deltas),
        identical_seeds=left.seed == right.seed,
        identical_event_counts=left.event_count == right.event_count,
        shared_emergence=shared,
        unique_left_emergence=only_left,
        unique_right_emergence=only_right,
        notes=tuple(notes),
    )


def compare_many(paths: list[Path | str]) -> list[ComparisonReport]:
    """Compare consecutive pairs in ``paths`` (A-B, B-C, ...)."""
    if len(paths) < 2:
        raise ReplayError("compare requires at least two run paths")
    reports: list[ComparisonReport] = []
    for index in range(len(paths) - 1):
        reports.append(compare_runs(paths[index], paths[index + 1]))
    return reports


# Re-export types used by callers/tests.
__all__ = [
    "ComparisonDelta",
    "ComparisonReport",
    "EmergenceReport",
    "MetricsReport",
    "RunInspection",
    "RunSnapshot",
    "compare_many",
    "compare_runs",
    "snapshot_run",
]
