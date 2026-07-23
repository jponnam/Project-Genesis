"""Tests for server-rendered observatory pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from civitas.api.app import app
from civitas.domain import SimulationConfig
from civitas.engine import SimulationEngine
from civitas.storage import write_events

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def runs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated runs directory for UI tests."""
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setenv("CIVITAS_RUNS_DIR", str(root))
    return root


@pytest.fixture
def sample_run(runs_dir: Path) -> str:
    """Create a deterministic sample run."""
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=3, agent_count=2, run_name="ui")
    )
    path = runs_dir / "ui_seed42.jsonl"
    write_events(path, result.events)
    return path.stem


@pytest.fixture
def client(runs_dir: Path) -> Iterator[TestClient]:
    """HTTP client for observatory routes."""
    with TestClient(app) as test_client:
        yield test_client


def test_ui_home_lists_runs(client: TestClient, sample_run: str) -> None:
    """Observatory home renders the run selector."""
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Run selector" in response.text
    assert sample_run in response.text
    assert "Civitas Observatory" in response.text


def test_ui_run_dashboard(client: TestClient, sample_run: str) -> None:
    """Run dashboard includes overview sections and unavailable labels."""
    response = client.get(f"/ui/runs/{sample_run}")
    assert response.status_code == 200
    assert "Event-type frequency" in response.text
    assert "Emergence findings" in response.text
    assert "Final per-agent holdings unavailable" in response.text
    assert "Agents" in response.text


def test_ui_agent_detail(client: TestClient, sample_run: str) -> None:
    """Agent detail page renders for a known agent id."""
    response = client.get(f"/ui/runs/{sample_run}/agents/0")
    assert response.status_code == 200
    assert "Agent 0" in response.text
    assert "Events involving this agent" in response.text


def test_ui_compare_page(client: TestClient, sample_run: str, runs_dir: Path) -> None:
    """Compare page can render a side-by-side summary for two runs."""
    second = SimulationEngine().run(
        SimulationConfig(seed=7, ticks=2, agent_count=2, run_name="other")
    )
    write_events(runs_dir / "other_seed7.jsonl", second.events)
    response = client.get(
        "/ui/compare",
        params={"left": sample_run, "right": "other_seed7"},
    )
    assert response.status_code == 200
    assert sample_run in response.text
    assert "other_seed7" in response.text
    assert "Seed / run comparison" in response.text


def test_ui_static_assets(client: TestClient) -> None:
    """CSS and JS assets are served."""
    css = client.get("/ui/static/styles.css")
    js = client.get("/ui/static/app.js")
    assert css.status_code == 200
    assert "--accent" in css.text
    assert js.status_code == 200
    assert "bar-fill" in js.text


def test_root_redirects_to_ui(client: TestClient) -> None:
    """API root redirects browsers to the observatory."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/"
