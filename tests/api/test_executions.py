"""API coverage for scoped scenario/campaign execution."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from civitas.api.app import app

if TYPE_CHECKING:
    import pytest


def test_manifest_catalogs_and_scoped_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API lists manifests and creates only new artifacts under runs root."""
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setenv("CIVITAS_RUNS_DIR", str(root))
    existing = root / "existing.jsonl"
    existing.write_bytes(b"preserve-me\n")

    with TestClient(app) as client:
        scenarios = client.get("/scenarios")
        campaigns = client.get("/campaigns")
        assert scenarios.status_code == 200
        assert campaigns.status_code == 200
        assert any(item["id"] == "institutional_formation" for item in scenarios.json())
        assert any(item["id"] == "seed_sweep_demo" for item in campaigns.json())

        scenario = client.post("/scenarios/institutional_formation/run")
        assert scenario.status_code == 201, scenario.text
        scenario_body = scenario.json()
        scenario_path = Path(scenario_body["path"]).resolve()
        scenario_path.relative_to(root.resolve())
        assert scenario_path.is_file()

        campaign = client.post("/campaigns/seed_sweep_demo/run")
        assert campaign.status_code == 201, campaign.text
        campaign_body = campaign.json()
        assert len(campaign_body["runs"]) == 3
        assert len(campaign_body["comparisons"]) == 2
        execution_id = campaign_body["execution_id"]

        listed = client.get("/campaigns/seed_sweep_demo/executions")
        assert listed.status_code == 200
        assert execution_id in listed.json()
        results = client.get("/campaigns/seed_sweep_demo/results")
        assert results.status_code == 200
        assert results.json()["execution_id"] == execution_id

    assert existing.read_bytes() == b"preserve-me\n"
    for run in campaign_body["runs"]:
        Path(run["path"]).resolve().relative_to(root.resolve())


def test_invalid_execution_ids_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsafe manifest ids do not reach filesystem execution."""
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setenv("CIVITAS_RUNS_DIR", str(root))
    with TestClient(app) as client:
        response = client.post("/campaigns/%2E%2E%5Cescape/run")
        assert response.status_code in {400, 404}
