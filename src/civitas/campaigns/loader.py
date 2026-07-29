"""Load and validate research campaign TOML manifests."""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from civitas.domain.config import SimulationConfig
from civitas.domain.presets import WorldPreset


class CampaignNotFoundError(LookupError):
    """Raised when a campaign id cannot be resolved."""


@dataclass(frozen=True, slots=True)
class Campaign:
    """One data-driven research campaign (seed x preset sweep)."""

    id: str
    title: str
    research_question: str
    seeds: tuple[int, ...]
    ticks: int
    agents: int
    preset: str
    run_name_prefix: str
    limitations: tuple[str, ...]
    path: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)

    def configs(self) -> tuple[SimulationConfig, ...]:
        """Build one ``SimulationConfig`` per seed in the campaign."""
        preset = WorldPreset(self.preset)
        return tuple(
            SimulationConfig(
                seed=seed,
                ticks=self.ticks,
                agent_count=self.agents,
                run_name=f"{self.run_name_prefix}_seed{seed}",
                preset=preset,
            )
            for seed in self.seeds
        )


def default_campaigns_dir() -> Path:
    """Return the repository campaigns directory.

    Resolution order:
    1. ``CIVITAS_CAMPAIGNS_DIR`` environment variable
    2. ``./campaigns`` relative to the current working directory
    3. package-adjacent ``../../../campaigns`` from this file
    """
    import os

    configured = os.environ.get("CIVITAS_CAMPAIGNS_DIR")
    if configured:
        return Path(configured)
    cwd_candidate = Path.cwd() / "campaigns"
    if cwd_candidate.is_dir():
        return cwd_candidate
    return Path(__file__).resolve().parents[3] / "campaigns"


def _parse_campaign(path: Path) -> Campaign:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    required = (
        "id",
        "title",
        "research_question",
        "seeds",
        "ticks",
        "agents",
        "run_name_prefix",
        "limitations",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        msg = f"campaign {path} missing keys: {', '.join(missing)}"
        raise ValueError(msg)
    seeds = tuple(int(item) for item in raw["seeds"])
    if not seeds:
        msg = f"campaign {path} requires at least one seed"
        raise ValueError(msg)
    return Campaign(
        id=str(raw["id"]),
        title=str(raw["title"]),
        research_question=str(raw["research_question"]),
        seeds=seeds,
        ticks=int(raw["ticks"]),
        agents=int(raw["agents"]),
        preset=str(raw.get("preset", "camp_minimal")),
        run_name_prefix=str(raw["run_name_prefix"]),
        limitations=tuple(str(item) for item in raw["limitations"]),
        path=str(path),
    )


def list_campaigns(campaigns_dir: Path | None = None) -> tuple[Campaign, ...]:
    """Load all ``*.toml`` campaigns sorted by id."""
    root = default_campaigns_dir() if campaigns_dir is None else campaigns_dir
    if not root.is_dir():
        return ()
    campaigns = [_parse_campaign(path) for path in sorted(root.glob("*.toml"))]
    return tuple(sorted(campaigns, key=lambda item: item.id))


def load_campaign(campaign_id: str, campaigns_dir: Path | None = None) -> Campaign:
    """Load one campaign by id."""
    for campaign in list_campaigns(campaigns_dir=campaigns_dir):
        if campaign.id == campaign_id:
            return campaign
    raise CampaignNotFoundError(f"campaign not found: {campaign_id}")
