"""Scoped scenario/campaign execution under ``CIVITAS_RUNS_DIR``."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from civitas.api.catalog import default_runs_dir
from civitas.campaigns import CampaignReport, load_campaign, run_campaign
from civitas.engine import SimulationEngine
from civitas.scenarios import load_scenario
from civitas.storage import write_events

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


class InvalidExecutionIdError(ValueError):
    """Raised for unsafe manifest ids."""


class ExecutionNotFoundError(LookupError):
    """Raised when no persisted campaign report exists."""


def validate_manifest_id(value: str) -> str:
    """Return a safe manifest id or raise."""
    if not _SAFE_ID.fullmatch(value):
        raise InvalidExecutionIdError(f"invalid manifest id: {value}")
    return value


def _root() -> Path:
    root = default_runs_dir().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _under_runs(relative: Path) -> Path:
    root = _root()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise InvalidExecutionIdError("execution path escapes runs directory") from exc
    return candidate


def _execution_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def execute_scenario(scenario_id: str) -> dict[str, Any]:
    """Execute one scenario into a new top-level run artifact."""
    validate_manifest_id(scenario_id)
    scenario = load_scenario(scenario_id)
    config = scenario.to_config()
    execution_id = _execution_id()
    run_id = f"{config.run_name}_seed{config.seed}_{execution_id}"
    path = _under_runs(Path(f"{run_id}.jsonl"))
    if path.exists():
        raise FileExistsError(f"refusing to overwrite run: {run_id}")
    result = SimulationEngine().run(config)
    write_events(path, result.events)
    return {
        "scenario_id": scenario.id,
        "execution_id": execution_id,
        "run_id": run_id,
        "path": str(path),
        "fingerprint": config.fingerprint(),
        "event_count": len(result.events),
    }


def execute_campaign(campaign_id: str, *, compare: bool = True) -> dict[str, Any]:
    """Execute a campaign in a fresh confined directory and persist its report."""
    safe_id = validate_manifest_id(campaign_id)
    campaign = load_campaign(safe_id)
    execution_id = _execution_id()
    output_dir = _under_runs(Path("campaigns") / safe_id / execution_id)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite execution: {execution_id}")
    report = run_campaign(campaign, output_dir=output_dir, compare=compare)
    payload = report.to_dict()
    payload["execution_id"] = execution_id
    report_path = output_dir / "report.json"
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def list_campaign_executions(campaign_id: str) -> list[str]:
    """List persisted execution ids newest first."""
    safe_id = validate_manifest_id(campaign_id)
    root = _under_runs(Path("campaigns") / safe_id)
    if not root.is_dir():
        return []
    return sorted(
        (path.name for path in root.iterdir() if (path / "report.json").is_file()),
        reverse=True,
    )


def load_campaign_results(
    campaign_id: str,
    execution_id: str | None = None,
) -> dict[str, Any]:
    """Load a persisted campaign report without re-running simulations."""
    safe_id = validate_manifest_id(campaign_id)
    executions = list_campaign_executions(safe_id)
    selected = execution_id or (executions[0] if executions else None)
    if selected is None:
        raise ExecutionNotFoundError(f"no campaign results: {safe_id}")
    validate_manifest_id(selected)
    report_path = _under_runs(Path("campaigns") / safe_id / selected / "report.json")
    if not report_path.is_file():
        raise ExecutionNotFoundError(
            f"campaign execution not found: {safe_id}/{selected}"
        )
    return cast(
        "dict[str, Any]",
        json.loads(report_path.read_text(encoding="utf-8")),
    )


__all__ = [
    "CampaignReport",
    "ExecutionNotFoundError",
    "InvalidExecutionIdError",
    "execute_campaign",
    "execute_scenario",
    "list_campaign_executions",
    "load_campaign_results",
    "validate_manifest_id",
]
