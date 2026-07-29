"""Tests for campaign execution."""

from __future__ import annotations

from pathlib import Path

from civitas.campaigns import load_campaign, run_campaign


def test_run_campaign_writes_jsonl_and_comparisons(tmp_path: Path) -> None:
    """Campaign runner executes all seeds and builds pair comparisons."""
    campaign = load_campaign("seed_sweep_demo")
    report = run_campaign(campaign, output_dir=tmp_path / "out", compare=True)
    assert report.campaign_id == "seed_sweep_demo"
    assert len(report.runs) == 3
    assert len(report.comparisons) == 2
    for item in report.runs:
        assert Path(item.path).is_file()
        assert item.event_count > 0
    payload = report.to_dict()
    assert payload["campaign_id"] == "seed_sweep_demo"
    assert len(payload["comparisons"]) == 2
