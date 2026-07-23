"""FastAPI TestClient coverage for the research API."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from civitas import __version__
from civitas.api.app import app
from civitas.domain import SimulationConfig
from civitas.engine import SimulationEngine
from civitas.storage import write_events

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def runs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the API at an isolated temporary runs directory."""
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setenv("CIVITAS_RUNS_DIR", str(root))
    return root


@pytest.fixture
def sample_run(runs_dir: Path) -> str:
    """Write a deterministic JSONL run and return its run_id."""
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=3, agent_count=2, run_name="api")
    )
    path = runs_dir / "api_seed42.jsonl"
    write_events(path, result.events)
    return path.stem


@pytest.fixture
def client(runs_dir: Path) -> Iterator[TestClient]:
    """HTTP client bound to the FastAPI app."""
    assert os.environ["CIVITAS_RUNS_DIR"] == str(runs_dir)
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    """GET /health returns ok and package version."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_list_and_get_run(client: TestClient, sample_run: str) -> None:
    """Runs catalog lists the sample run and detail endpoint works."""
    listed = client.get("/runs")
    assert listed.status_code == 200
    payload = listed.json()
    assert any(item["run_id"] == sample_run for item in payload)

    detail = client.get(f"/runs/{sample_run}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["seed"] == 42
    assert body["run_name"] == "api"
    assert body["has_completed"] is True


def test_events_pagination_and_filter(client: TestClient, sample_run: str) -> None:
    """Events endpoint supports pagination and event_type filters."""
    response = client.get(
        f"/runs/{sample_run}/events",
        params={"limit": 5, "offset": 0, "event_type": "ActionSelected"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 5
    assert body["offset"] == 0
    assert body["total"] >= 0
    assert len(body["events"]) <= 5
    assert all(event["event_type"] == "ActionSelected" for event in body["events"])


def test_summary_metrics_emergence_agents_timeline(
    client: TestClient,
    sample_run: str,
) -> None:
    """Derived analysis endpoints return structured JSON."""
    summary = client.get(f"/runs/{sample_run}/summary")
    assert summary.status_code == 200
    assert summary.json()["seed"] == 42

    metrics = client.get(f"/runs/{sample_run}/metrics")
    assert metrics.status_code == 200
    assert "metrics" in metrics.json()

    emergence = client.get(f"/runs/{sample_run}/emergence")
    assert emergence.status_code == 200
    assert "rules_evaluated" in emergence.json()

    agents = client.get(f"/runs/{sample_run}/agents")
    assert agents.status_code == 200
    assert len(agents.json()["agents"]) >= 2

    timeline = client.get(f"/runs/{sample_run}/timeline")
    assert timeline.status_code == 200
    assert "entries" in timeline.json()


def test_missing_run_returns_404(client: TestClient) -> None:
    """Unknown run ids produce a 404 error payload."""
    response = client.get("/runs/does_not_exist")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_path_traversal_rejected(client: TestClient) -> None:
    """Run ids attempting directory traversal are rejected."""
    response = client.get("/runs/../secrets")
    assert response.status_code == 404


def test_openapi_available(client: TestClient) -> None:
    """OpenAPI schema is published for the research API."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Civitas Lab Research API"
    paths = schema["paths"]
    assert "/health" in paths
    assert "/runs/{run_id}/events" in paths


def test_api_is_read_only(client: TestClient, sample_run: str, runs_dir: Path) -> None:
    """No mutating routes are exposed; sample file bytes stay unchanged."""
    path = runs_dir / f"{sample_run}.jsonl"
    before = path.read_bytes()
    assert client.post("/runs").status_code in {404, 405, 401, 403}
    assert client.delete(f"/runs/{sample_run}").status_code in {404, 405, 401, 403}
    assert path.read_bytes() == before


def test_compare_endpoint(client: TestClient, sample_run: str, runs_dir: Path) -> None:
    """GET /compare returns a structured comparison payload."""
    other = SimulationEngine().run(
        SimulationConfig(seed=7, ticks=2, agent_count=2, run_name="other")
    )
    write_events(runs_dir / "other_seed7.jsonl", other.events)
    response = client.get(
        "/compare",
        params={"left": sample_run, "right": "other_seed7"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["identical_seeds"] is False
    assert body["left"]["seed"] == 42
    assert body["right"]["seed"] == 7
