"""Unit tests for the Civitas Lab Typer CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from civitas import __version__
from civitas.cli.app import app, build_config, default_events_path, main
from civitas.domain import CANONICAL_SEED, SimulationConfig
from civitas.storage import JsonlEventStore

runner = CliRunner()


def test_help_lists_version_config_and_run() -> None:
    """Root help must advertise version, config, and run commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "version" in result.stdout
    assert "config" in result.stdout
    assert "run" in result.stdout


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
