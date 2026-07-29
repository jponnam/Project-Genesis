"""Tests for campaign TOML loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from civitas.campaigns import (
    CampaignNotFoundError,
    default_campaigns_dir,
    list_campaigns,
    load_campaign,
)
from civitas.domain import WorldPreset

if TYPE_CHECKING:
    from pathlib import Path


def test_default_campaigns_dir_exists() -> None:
    """Repository campaigns directory is discoverable."""
    root = default_campaigns_dir()
    assert root.is_dir()
    assert any(root.glob("*.toml"))


def test_list_and_load_seed_sweep_demo() -> None:
    """Bundled seed_sweep_demo campaign loads with expected fields."""
    campaigns = list_campaigns()
    ids = {campaign.id for campaign in campaigns}
    assert "seed_sweep_demo" in ids
    campaign = load_campaign("seed_sweep_demo")
    assert campaign.seeds == (42, 7, 99)
    assert campaign.preset == WorldPreset.EARLY_CRAFT.value
    configs = campaign.configs()
    assert len(configs) == 3
    assert configs[0].fingerprint().endswith("|preset=early_craft")


def test_load_campaign_missing() -> None:
    """Unknown ids raise CampaignNotFoundError."""
    with pytest.raises(CampaignNotFoundError):
        load_campaign("not_a_real_campaign")


def test_invalid_campaign_missing_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed campaign files raise ValueError."""
    root = tmp_path / "campaigns"
    root.mkdir()
    (root / "bad.toml").write_text("id = 'bad'\n", encoding="utf-8")
    monkeypatch.setenv("CIVITAS_CAMPAIGNS_DIR", str(root))
    with pytest.raises(ValueError, match="missing keys"):
        list_campaigns()
