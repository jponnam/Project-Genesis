"""Load and validate demonstration scenario TOML files."""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class ScenarioNotFoundError(LookupError):
    """Raised when a scenario id cannot be resolved."""


@dataclass(frozen=True, slots=True)
class Scenario:
    """One data-driven demonstration scenario."""

    id: str
    title: str
    research_question: str
    seed: int
    ticks: int
    agents: int
    run_name: str
    command: str
    observable_signals: tuple[str, ...]
    limitations: tuple[str, ...]
    path: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


def default_scenarios_dir() -> Path:
    """Return the repository scenarios directory.

    Resolution order:
    1. ``CIVITAS_SCENARIOS_DIR`` environment variable
    2. ``./scenarios`` relative to the current working directory
    3. package-adjacent ``../../../scenarios`` from this file (editable installs)
    """
    import os

    configured = os.environ.get("CIVITAS_SCENARIOS_DIR")
    if configured:
        return Path(configured)
    cwd_candidate = Path.cwd() / "scenarios"
    if cwd_candidate.is_dir():
        return cwd_candidate
    repo_candidate = Path(__file__).resolve().parents[3] / "scenarios"
    return repo_candidate


def _parse_scenario(path: Path) -> Scenario:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    required = (
        "id",
        "title",
        "research_question",
        "seed",
        "ticks",
        "agents",
        "run_name",
        "command",
        "observable_signals",
        "limitations",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        msg = f"scenario {path} missing keys: {', '.join(missing)}"
        raise ValueError(msg)
    return Scenario(
        id=str(raw["id"]),
        title=str(raw["title"]),
        research_question=str(raw["research_question"]),
        seed=int(raw["seed"]),
        ticks=int(raw["ticks"]),
        agents=int(raw["agents"]),
        run_name=str(raw["run_name"]),
        command=str(raw["command"]),
        observable_signals=tuple(str(item) for item in raw["observable_signals"]),
        limitations=tuple(str(item) for item in raw["limitations"]),
        path=str(path),
    )


def list_scenarios(scenarios_dir: Path | None = None) -> tuple[Scenario, ...]:
    """Load all ``*.toml`` scenarios sorted by id."""
    root = default_scenarios_dir() if scenarios_dir is None else scenarios_dir
    if not root.is_dir():
        return ()
    scenarios = [_parse_scenario(path) for path in sorted(root.glob("*.toml"))]
    return tuple(sorted(scenarios, key=lambda item: item.id))


def load_scenario(scenario_id: str, scenarios_dir: Path | None = None) -> Scenario:
    """Load one scenario by id."""
    for scenario in list_scenarios(scenarios_dir=scenarios_dir):
        if scenario.id == scenario_id:
            return scenario
    raise ScenarioNotFoundError(f"scenario not found: {scenario_id}")
