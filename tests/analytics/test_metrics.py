"""Tests for offline analytics metrics and engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from civitas.analytics import analyze_run, compute_metrics
from civitas.analytics.metrics import (
    action_diversity_entropy,
    agent_activity_distribution,
    birth_and_death_rates,
    event_frequency_by_type,
    final_resource_holdings,
    money_alive_series,
    repeated_behavior_entropy,
    resource_holdings_series,
    resource_inequality,
    wealth_gini_bps,
    wealth_volatility,
)
from civitas.domain import (
    ActionSelected,
    AgentId,
    ResourcesObserved,
    SimulationCompleted,
    SimulationConfig,
    SimulationStarted,
    Tick,
    WealthObserved,
)
from civitas.engine import SimulationEngine
from civitas.storage import ReplayError, write_events

if TYPE_CHECKING:
    from pathlib import Path


def _action(
    sequence: int,
    tick: int,
    agent: int,
    action: str,
) -> ActionSelected:
    return ActionSelected(
        sequence=sequence,
        tick=Tick(value=tick),
        agent_id=AgentId(value=agent),
        action=action,
        utility=0.5,
    )


def test_event_frequency_empty() -> None:
    """Empty streams return empty status."""
    result = event_frequency_by_type(())
    assert result.status == "empty"
    assert result.value == {}


def test_agent_activity_distribution_shares_sum_to_one() -> None:
    """Activity shares are normalized probabilities."""
    events = (
        _action(0, 1, 0, "move"),
        _action(1, 1, 0, "rest"),
        _action(2, 1, 1, "move"),
    )
    result = agent_activity_distribution(events)
    assert result.status == "ok"
    assert result.value["0"] == pytest.approx(2 / 3)
    assert result.value["1"] == pytest.approx(1 / 3)


def test_action_diversity_entropy_known_value() -> None:
    """Two equiprobable actions yield entropy of 1 bit."""
    events = (
        _action(0, 1, 0, "move"),
        _action(1, 1, 0, "rest"),
    )
    result = action_diversity_entropy(events)
    assert result.status == "ok"
    assert result.value == pytest.approx(1.0)


def test_wealth_gini_uses_last_observation() -> None:
    """Primary gini value is the final WealthObserved.gini_bps."""
    events = (
        WealthObserved(
            sequence=0,
            tick=Tick(value=0),
            total=10,
            alive_total=10,
            dead_total=0,
            alive_count=2,
            mean_alive=5.0,
            gini_bps=1000,
            top1_share_bps=6000,
        ),
        WealthObserved(
            sequence=1,
            tick=Tick(value=1),
            total=12,
            alive_total=12,
            dead_total=0,
            alive_count=2,
            mean_alive=6.0,
            gini_bps=2500,
            top1_share_bps=7000,
        ),
    )
    result = wealth_gini_bps(events)
    assert result.status == "ok"
    assert result.value == 2500
    assert result.details["series"] == [(0, 1000), (1, 2500)]


def test_wealth_volatility_undefined_for_single_observation() -> None:
    """Volatility requires at least two wealth censuses."""
    events = (
        WealthObserved(
            sequence=0,
            tick=Tick(value=0),
            total=10,
            alive_total=10,
            dead_total=0,
            alive_count=1,
            mean_alive=10.0,
            gini_bps=0,
        ),
    )
    result = wealth_volatility(events)
    assert result.status == "undefined"
    assert result.value is None


def test_final_resource_holdings_uses_last_census() -> None:
    """final_resource_holdings primary value is last alive_totals."""
    events = (
        ResourcesObserved(
            sequence=0,
            tick=Tick(value=0),
            alive_count=2,
            alive_totals=(("food", 1),),
            stack_count=1,
            distinct_resources=1,
        ),
        ResourcesObserved(
            sequence=1,
            tick=Tick(value=1),
            alive_count=2,
            agent_holdings=((0, "food", 3), (1, "water", 1)),
            alive_totals=(("food", 3), ("water", 1)),
            escrow_totals=(("wood", 2),),
            stack_count=2,
            distinct_resources=2,
        ),
    )
    result = final_resource_holdings(events)
    assert result.status == "ok"
    assert result.value == {"food": 3, "water": 1}
    assert result.details["escrow_totals"] == {"wood": 2}
    series = resource_holdings_series(events)
    assert series.status == "ok"
    assert series.value["1"]["food"] == 3


def test_resource_inequality_from_agent_holdings() -> None:
    """resource_inequality computes gini from per-agent stock totals."""
    events = (
        ResourcesObserved(
            sequence=0,
            tick=Tick(value=0),
            alive_count=2,
            agent_holdings=((0, "food", 9), (1, "food", 1)),
            alive_totals=(("food", 10),),
            stack_count=2,
            distinct_resources=1,
        ),
    )
    result = resource_inequality(events)
    assert result.status == "ok"
    assert result.value == 4000  # gini_bps for [1, 9]
    assert result.details["top1_share_bps"] == 9000


def test_money_alive_series_tracks_wealth_census() -> None:
    """money_alive_series uses WealthObserved.alive_total."""
    events = (
        WealthObserved(
            sequence=0,
            tick=Tick(value=0),
            total=4,
            alive_total=4,
            dead_total=0,
            alive_count=2,
            mean_alive=2.0,
            gini_bps=0,
        ),
        WealthObserved(
            sequence=1,
            tick=Tick(value=2),
            total=7,
            alive_total=7,
            dead_total=0,
            alive_count=2,
            mean_alive=3.5,
            gini_bps=0,
        ),
    )
    result = money_alive_series(events)
    assert result.status == "ok"
    assert result.value == 7
    assert result.details["series"] == [(0, 4), (2, 7)]


def test_stock_metrics_empty_without_resources_observed() -> None:
    """Stock metrics are empty when ResourcesObserved is absent."""
    assert final_resource_holdings(()).status == "empty"
    assert resource_holdings_series(()).status == "empty"
    assert resource_inequality(()).status == "empty"
    assert money_alive_series(()).status == "empty"


def test_repeated_behavior_entropy_low_for_repetition() -> None:
    """Repeated identical actions produce zero bigram entropy."""
    events = (
        _action(0, 1, 0, "move"),
        _action(1, 2, 0, "move"),
        _action(2, 3, 0, "move"),
    )
    result = repeated_behavior_entropy(events)
    assert result.status == "ok"
    assert result.value == pytest.approx(0.0)


def test_birth_and_death_rates_on_live_run(tmp_path: Path) -> None:
    """Live engine runs produce finite birth/death rate metrics."""
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=5, agent_count=3, run_name="m")
    )
    metric = birth_and_death_rates(result.events)
    assert metric.status == "ok"
    assert metric.value is not None
    assert metric.details["ticks_executed"] == 5


def test_compute_metrics_and_analyze_run(tmp_path: Path) -> None:
    """Engine computes the full report and analyze_run loads JSONL."""
    path = tmp_path / "run.jsonl"
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=3, agent_count=2, run_name="metrics")
    )
    write_events(path, result.events)
    report = analyze_run(path)
    assert report.event_count == len(result.events)
    assert report.path == str(path)
    names = {metric.name for metric in report.metrics}
    assert "event_frequency_by_type" in names
    assert "wealth_gini_bps" in names
    assert "action_diversity_entropy" in names
    assert "final_resource_holdings" in names
    assert "resource_inequality" in names
    assert "money_alive_series" in names
    assert report.by_name()["final_resource_holdings"].status == "ok"
    assert report.to_dict()["event_count"] == report.event_count
    # Determinism
    assert analyze_run(path).to_dict() == report.to_dict()
    direct = compute_metrics(result.events, path=None)
    assert direct.by_name()["event_frequency_by_type"].value == (
        report.by_name()["event_frequency_by_type"].value
    )


def test_analyze_run_missing_file(tmp_path: Path) -> None:
    """Missing files raise ReplayError through the analytics entrypoint."""
    with pytest.raises(ReplayError):
        analyze_run(tmp_path / "missing.jsonl")


def test_lifecycle_events_do_not_break_metrics() -> None:
    """Minimal lifecycle-only streams still yield structured metrics."""
    events = (
        SimulationStarted(
            sequence=0,
            tick=Tick(value=0),
            seed=1,
            ticks=1,
            agent_count=1,
            run_name="x",
        ),
        SimulationCompleted(
            sequence=1,
            tick=Tick(value=1),
            ticks_executed=1,
        ),
    )
    report = compute_metrics(events)
    assert report.event_count == 2
    assert report.by_name()["trade_activity_rate"].value == 0.0
    assert report.by_name()["agent_activity_distribution"].status == "empty"
