"""Execute research campaigns into JSONL runs and aggregate compares."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from civitas.analytics.compare import (
    ComparisonReport,
    RunSnapshot,
    compare_many,
    snapshot_run,
)
from civitas.campaigns.loader import Campaign
from civitas.engine import SimulationEngine
from civitas.storage import write_events


@dataclass(frozen=True, slots=True)
class CampaignRunResult:
    """One seed member of a campaign execution."""

    seed: int
    path: str
    fingerprint: str
    event_count: int
    snapshot: RunSnapshot

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        payload = asdict(self)
        payload["snapshot"] = self.snapshot.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class CampaignReport:
    """Aggregate report for a completed campaign run."""

    campaign_id: str
    output_dir: str
    runs: tuple[CampaignRunResult, ...]
    comparisons: tuple[ComparisonReport, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "campaign_id": self.campaign_id,
            "output_dir": self.output_dir,
            "runs": [item.to_dict() for item in self.runs],
            "comparisons": [item.to_dict() for item in self.comparisons],
            "notes": list(self.notes),
        }


def run_campaign(
    campaign: Campaign,
    *,
    output_dir: Path | str,
    compare: bool = True,
) -> CampaignReport:
    """Execute every seed in ``campaign`` and optionally compare consecutive runs."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    engine = SimulationEngine()
    results: list[CampaignRunResult] = []
    notes: list[str] = [
        f"preset={campaign.preset}",
        f"ticks={campaign.ticks}",
        f"agents={campaign.agents}",
    ]

    for config in campaign.configs():
        path = root / f"{config.run_name}.jsonl"
        result = engine.run(config)
        write_events(path, result.events)
        snapshot = snapshot_run(path)
        results.append(
            CampaignRunResult(
                seed=int(config.seed),
                path=str(path),
                fingerprint=config.fingerprint(),
                event_count=len(result.events),
                snapshot=snapshot,
            )
        )

    comparisons: tuple[ComparisonReport, ...] = ()
    if compare and len(results) >= 2:
        comparisons = tuple(compare_many([item.path for item in results]))
        notes.append(f"pair_comparisons={len(comparisons)}")
    elif compare:
        notes.append("compare skipped: campaign has fewer than two seeds")

    return CampaignReport(
        campaign_id=campaign.id,
        output_dir=str(root),
        runs=tuple(results),
        comparisons=comparisons,
        notes=tuple(notes),
    )
