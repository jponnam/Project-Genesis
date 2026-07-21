"""Researcher-facing Typer CLI for Civitas Lab.

The CLI is a thin adapter: it validates operator input into domain
``SimulationConfig`` values and renders results. It contains no
simulation policy or engine logic.
"""

from __future__ import annotations

from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from civitas import __version__
from civitas.domain import CANONICAL_SEED, SimulationConfig

console = Console(highlight=False)

app = typer.Typer(
    name="civitas",
    help="Civitas Lab — deterministic multi-agent civilization research platform.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

config_app = typer.Typer(
    name="config",
    help="Inspect and validate simulation configuration.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")

SeedOpt = Annotated[
    int,
    typer.Option(
        "--seed",
        help="RNG seed (non-negative). Canonical research seed is 42.",
    ),
]
TicksOpt = Annotated[
    int,
    typer.Option("--ticks", help="Number of simulation ticks."),
]
AgentsOpt = Annotated[
    int,
    typer.Option("--agents", help="Initial agent population."),
]
NameOpt = Annotated[
    str,
    typer.Option(
        "--name",
        help="Human-readable run label (does not affect RNG).",
    ),
]


def build_config(
    seed: int,
    ticks: int,
    agent_count: int,
    run_name: str,
) -> SimulationConfig:
    """Validate CLI options into an immutable ``SimulationConfig``.

    Raises:
        typer.Exit: If validation fails (exit code 1).
    """
    try:
        return SimulationConfig(
            seed=seed,
            ticks=ticks,
            agent_count=agent_count,
            run_name=run_name,
        )
    except ValidationError as exc:
        console.print(f"[red]Invalid configuration:[/red]\n{exc}")
        raise typer.Exit(code=1) from exc


def render_config_table(config: SimulationConfig) -> None:
    """Print a Rich table describing ``config``."""
    table = Table(title="SimulationConfig", show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("seed", str(config.seed))
    table.add_row("ticks", str(config.ticks))
    table.add_row("agent_count", str(config.agent_count))
    table.add_row("run_name", config.run_name)
    table.add_row("fingerprint", config.fingerprint())
    console.print(table)


def _version_callback(value: bool) -> None:
    """Eager ``--version`` handler for the root callback."""
    if value:
        console.print(__version__)
        raise typer.Exit(code=0)


@app.callback()
def root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print the package version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Civitas Lab command-line interface."""
    # Typer requires the annotated option to appear in the signature.
    del version


@app.command("version")
def version_command() -> None:
    """Print the installed Civitas Lab package version."""
    console.print(__version__)


@config_app.command("show")
def config_show(
    seed: SeedOpt = CANONICAL_SEED,
    ticks: TicksOpt = 100,
    agent_count: AgentsOpt = 10,
    run_name: NameOpt = "default",
) -> None:
    """Validate options and display the resulting configuration."""
    config = build_config(seed, ticks, agent_count, run_name)
    render_config_table(config)


@config_app.command("fingerprint")
def config_fingerprint(
    seed: SeedOpt = CANONICAL_SEED,
    ticks: TicksOpt = 100,
    agent_count: AgentsOpt = 10,
    run_name: NameOpt = "default",
) -> None:
    """Print only the configuration fingerprint (script-friendly)."""
    config = build_config(seed, ticks, agent_count, run_name)
    console.print(config.fingerprint())


def main() -> None:
    """Console-script entry point for the ``civitas`` command."""
    app()


if __name__ == "__main__":
    main()
