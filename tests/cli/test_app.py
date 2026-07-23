"""Unit tests for the Civitas Lab Typer CLI."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from civitas import __version__
from civitas.cli.app import app, build_config, default_events_path, main
from civitas.domain import CANONICAL_SEED, SimulationConfig
from civitas.storage import JsonlEventStore, write_events

runner = CliRunner()


def test_help_lists_core_commands() -> None:
    """Root help must advertise the researcher-facing commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("version", "config", "run", "replay", "inspect", "metrics"):
        assert command in result.stdout


def test_version_command_prints_package_version() -> None:
    """``civitas version`` must print the package version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_version_flag_prints_package_version() -> None:
    """``civitas --version`` must print the package version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_config_show_defaults_to_research_config() -> None:
    """``config show`` with no options must reflect research defaults."""
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert str(CANONICAL_SEED) in result.stdout
    assert "seed=42|ticks=100|agents=10|name=default" in result.stdout
    assert "SimulationConfig" in result.stdout


def test_config_show_accepts_overrides() -> None:
    """``config show`` must validate and display overridden fields."""
    result = runner.invoke(
        app,
        [
            "config",
            "show",
            "--seed",
            "7",
            "--ticks",
            "25",
            "--agents",
            "3",
            "--name",
            "trial",
        ],
    )
    assert result.exit_code == 0
    assert "seed=7|ticks=25|agents=3|name=trial" in result.stdout
    assert "trial" in result.stdout


def test_config_fingerprint_is_script_friendly() -> None:
    """``config fingerprint`` must print only the fingerprint line."""
    result = runner.invoke(
        app,
        ["config", "fingerprint", "--seed", "42", "--ticks", "100"],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == "seed=42|ticks=100|agents=10|name=default"


def test_config_show_rejects_invalid_seed() -> None:
    """Invalid configuration must exit with code 1 and an error message."""
    result = runner.invoke(app, ["config", "show", "--seed", "-1"])
    assert result.exit_code == 1
    assert "Invalid configuration" in result.stdout


def test_config_show_rejects_zero_ticks() -> None:
    """Zero ticks must fail validation through the CLI."""
    result = runner.invoke(app, ["config", "show", "--ticks", "0"])
    assert result.exit_code == 1
    assert "Invalid configuration" in result.stdout


def test_config_fingerprint_rejects_blank_name() -> None:
    """Blank run names must fail validation through the CLI."""
    result = runner.invoke(app, ["config", "fingerprint", "--name", "   "])
    assert result.exit_code == 1
    assert "Invalid configuration" in result.stdout


def test_build_config_returns_domain_model() -> None:
    """build_config must return a validated SimulationConfig instance."""
    config = build_config(seed=1, ticks=2, agent_count=3, run_name="x")
    assert isinstance(config, SimulationConfig)
    assert config == SimulationConfig(seed=1, ticks=2, agent_count=3, run_name="x")


def test_main_is_callable() -> None:
    """Console-script entry point must be a zero-arg callable."""
    assert callable(main)
    assert main.__name__ == "main"


def test_config_help_lists_show_and_fingerprint() -> None:
    """Config subgroup help must list show and fingerprint commands."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "show" in result.stdout
    assert "fingerprint" in result.stdout


def test_default_events_path_uses_name_and_seed() -> None:
    """Default JSONL path is runs/<name>_seed<seed>.jsonl."""
    config = SimulationConfig(seed=42, run_name="trial")
    assert default_events_path(config) == Path("runs") / "trial_seed42.jsonl"


def test_run_writes_jsonl_and_summary(tmp_path: Path) -> None:
    """``civitas run`` executes a simulation and persists events."""
    output = tmp_path / "out.jsonl"
    result = runner.invoke(
        app,
        [
            "run",
            "--seed",
            "42",
            "--ticks",
            "2",
            "--agents",
            "3",
            "--name",
            "cli",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert output.is_file()
    assert "Simulation Run" in result.stdout
    assert "seed=42|ticks=2|agents=3|name=cli" in result.stdout
    assert "ticks_executed" in result.stdout
    events = JsonlEventStore(output).read_all()
    assert len(events) > 0
    assert events[0].event_type == "SimulationStarted"
    assert events[-1].event_type == "SimulationCompleted"


def test_run_is_reproducible_for_seed_forty_two(tmp_path: Path) -> None:
    """Two CLI runs with seed 42 write identical JSONL bytes."""
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    args = [
        "run",
        "--seed",
        "42",
        "--ticks",
        "2",
        "--agents",
        "3",
        "--output",
    ]
    assert runner.invoke(app, [*args, str(first)]).exit_code == 0
    assert runner.invoke(app, [*args, str(second)]).exit_code == 0
    assert first.read_bytes() == second.read_bytes()


def test_run_rejects_invalid_config(tmp_path: Path) -> None:
    """Invalid run options exit with code 1 before writing output."""
    output = tmp_path / "nope.jsonl"
    result = runner.invoke(
        app,
        ["run", "--seed", "-1", "--output", str(output)],
    )
    assert result.exit_code == 1
    assert "Invalid configuration" in result.stdout
    assert not output.exists()


def _cli_mini_run(tmp_path: Path) -> Path:
    """Write a small deterministic JSONL run for replay CLI tests."""
    output = tmp_path / "cli_replay.jsonl"
    result = runner.invoke(
        app,
        [
            "run",
            "--seed",
            "42",
            "--ticks",
            "2",
            "--agents",
            "2",
            "--name",
            "cli_replay",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout
    return output


def test_replay_summary_reads_existing_run(tmp_path: Path) -> None:
    """``civitas replay`` prints metadata for a valid JSONL run."""
    output = _cli_mini_run(tmp_path)
    result = runner.invoke(app, ["replay", str(output)])
    assert result.exit_code == 0, result.stdout
    assert "Replay" in result.stdout
    assert "cli_replay" in result.stdout
    assert "Event types" in result.stdout
    assert "SimulationStarted" in result.stdout


def test_replay_filters_by_event_type_and_lists(tmp_path: Path) -> None:
    """Replay supports event-type filters and event listing."""
    output = _cli_mini_run(tmp_path)
    result = runner.invoke(
        app,
        [
            "replay",
            str(output),
            "--event-type",
            "ActionSelected",
            "--list",
            "--limit",
            "3",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "ActionSelected" in result.stdout
    assert "action=" in result.stdout


def test_replay_final_state_flag(tmp_path: Path) -> None:
    """``--final-state`` shows the partial event-derived summary."""
    output = _cli_mini_run(tmp_path)
    result = runner.invoke(app, ["replay", str(output), "--final-state"])
    assert result.exit_code == 0, result.stdout
    assert "Final state" in result.stdout
    assert "estimated_living" in result.stdout
    assert "not a full World reconstruction" in result.stdout


def test_replay_missing_file_errors(tmp_path: Path) -> None:
    """Missing replay paths exit with a clear error."""
    result = runner.invoke(app, ["replay", str(tmp_path / "missing.jsonl")])
    assert result.exit_code == 1
    assert "Replay failed" in result.stdout
    assert "not found" in result.stdout


def test_replay_strict_fails_on_incomplete_log(tmp_path: Path) -> None:
    """``--strict`` exits non-zero when verification notes exist."""
    output = _cli_mini_run(tmp_path)
    events = list(JsonlEventStore(output).read_all())
    truncated = [e for e in events if e.event_type != "SimulationCompleted"]
    bad = tmp_path / "incomplete.jsonl"
    write_events(bad, truncated)
    result = runner.invoke(app, ["replay", str(bad), "--strict"])
    assert result.exit_code == 1
    assert "Verification notes" in result.stdout


def test_inspect_text_summary(tmp_path: Path) -> None:
    """``civitas inspect`` prints a Rich summary for a valid run."""
    output = _cli_mini_run(tmp_path)
    result = runner.invoke(app, ["inspect", str(output)])
    assert result.exit_code == 0, result.stdout
    assert "Run inspection" in result.stdout
    assert "cli_replay" in result.stdout
    assert "Event types" in result.stdout
    assert "Final wealth census" in result.stdout
    assert "final holdings" in result.stdout.lower() or (
        "Final per-agent resource inventories" in result.stdout
    )


def test_inspect_json_format(tmp_path: Path) -> None:
    """``civitas inspect --format json`` emits machine-readable JSON."""
    output = _cli_mini_run(tmp_path)
    result = runner.invoke(app, ["inspect", str(output), "--format", "json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["seed"] == 42
    assert payload["run_name"] == "cli_replay"
    assert payload["event_count"] > 0
    assert payload["final_resource_holdings_available"] is False


def test_inspect_missing_file(tmp_path: Path) -> None:
    """Missing inspect paths exit with a clear error."""
    result = runner.invoke(app, ["inspect", str(tmp_path / "missing.jsonl")])
    assert result.exit_code == 1
    assert "Inspect failed" in result.stdout


def test_metrics_text_and_json(tmp_path: Path) -> None:
    """``civitas metrics`` supports Rich and JSON output."""
    output = _cli_mini_run(tmp_path)
    text = runner.invoke(app, ["metrics", str(output)])
    assert text.exit_code == 0, text.stdout
    assert "Analytics metrics" in text.stdout
    assert "wealth_gini_bps" in text.stdout
    raw = runner.invoke(app, ["metrics", str(output), "--format", "json"])
    assert raw.exit_code == 0, raw.stdout
    payload = json.loads(raw.stdout)
    assert payload["event_count"] > 0
    names = {metric["name"] for metric in payload["metrics"]}
    assert "action_diversity_entropy" in names
