"""Researcher-facing Typer CLI for Civitas Lab.

The CLI is a thin adapter: it validates operator input into domain
``SimulationConfig`` values, runs the simulation engine, persists
event streams, and replays existing JSONL logs. It contains no
simulation policy logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from civitas import __version__
from civitas.domain import CANONICAL_SEED, SimulationConfig
from civitas.engine import SimulationEngine, SimulationResult
from civitas.storage import ReplayError, ReplayResult, replay_run, write_events
from civitas.storage.replay import event_to_brief

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


def default_events_path(config: SimulationConfig) -> Path:
    """Return the default JSONL output path for ``config``."""
    return Path("runs") / f"{config.run_name}_seed{config.seed}.jsonl"


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


def render_run_summary(
    result: SimulationResult,
    output_path: Path,
) -> None:
    """Print a Rich summary of a completed simulation run."""
    table = Table(title="Simulation Run", show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("fingerprint", result.config.fingerprint())
    table.add_row("ticks_executed", str(result.ticks_executed))
    table.add_row("agents", str(len(result.world.agents)))
    table.add_row("alive", str(len(result.world.alive_agents())))
    table.add_row("events", str(len(result.events)))
    table.add_row("output", str(output_path))
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


@app.command("run")
def run_command(
    seed: SeedOpt = CANONICAL_SEED,
    ticks: TicksOpt = 100,
    agent_count: AgentsOpt = 10,
    run_name: NameOpt = "default",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="JSONL path for the event stream "
            "(default: runs/<name>_seed<seed>.jsonl).",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
) -> None:
    """Run a deterministic simulation and write events to JSONL."""
    config = build_config(seed, ticks, agent_count, run_name)
    output_path = output if output is not None else default_events_path(config)
    result = SimulationEngine().run(config)
    write_events(output_path, result.events)
    render_run_summary(result, output_path)


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


def _render_replay_metadata(result: ReplayResult) -> None:
    """Print metadata and verification notes for a replay result."""
    meta = result.metadata
    table = Table(title="Replay", show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("path", str(result.path))
    table.add_row("run_name", str(meta.run_name))
    table.add_row("seed", str(meta.seed))
    table.add_row("ticks_configured", str(meta.ticks_configured))
    table.add_row("ticks_executed", str(meta.ticks_executed))
    table.add_row("agent_count", str(meta.agent_count))
    table.add_row("events_in_file", str(meta.event_count))
    table.add_row("events_matched", str(len(result.events)))
    table.add_row("has_started", str(meta.has_started))
    table.add_row("has_completed", str(meta.has_completed))
    console.print(table)
    if result.verification_notes:
        console.print("[yellow]Verification notes:[/yellow]")
        for note in result.verification_notes:
            console.print(f"  - {note}")


def _render_type_counts(type_counts: dict[str, int]) -> None:
    """Print event-type histogram for matched events."""
    if not type_counts:
        console.print("No events matched the current filters.")
        return
    table = Table(title="Event types", show_header=True, header_style="bold")
    table.add_column("event_type", style="cyan")
    table.add_column("count", justify="right")
    for event_type, count in type_counts.items():
        table.add_row(event_type, str(count))
    console.print(table)


def _render_final_state(result: ReplayResult) -> None:
    """Print partial final-state summary derived from events."""
    final = result.final_state
    if final is None:
        return
    table = Table(
        title="Final state (event-derived, partial)",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("agents_spawned", str(final.agents_spawned))
    table.add_row("agents_born", str(final.agents_born))
    table.add_row("agents_died", str(final.agents_died))
    table.add_row("estimated_living", str(final.estimated_living))
    table.add_row("last_population_alive", str(final.last_population_alive))
    table.add_row("last_wealth_total_money", str(final.last_wealth_total_money))
    table.add_row("actions", str(final.actions))
    table.add_row(
        "technologies_discovered",
        str(list(final.technologies_discovered)),
    )
    table.add_row("institutions_created", str(list(final.institutions_created)))
    table.add_row("cities_created", str(list(final.cities_created)))
    console.print(table)
    console.print(
        "[dim]Note: this is not a full World reconstruction; "
        "only quantities present in the event log are shown.[/dim]"
    )


@app.command("replay")
def replay_command(
    path: Annotated[
        Path,
        typer.Argument(
            exists=False,
            dir_okay=False,
            readable=True,
            help="Path to a JSONL event log produced by civitas run.",
        ),
    ],
    summary: Annotated[
        bool,
        typer.Option(
            "--summary/--no-summary",
            help="Show run metadata and event-type counts (default: on).",
        ),
    ] = True,
    list_events: Annotated[
        bool,
        typer.Option(
            "--list/--no-list",
            help="List matched events after the summary.",
        ),
    ] = False,
    from_tick: Annotated[
        int | None,
        typer.Option("--from-tick", min=0, help="Inclusive minimum tick."),
    ] = None,
    to_tick: Annotated[
        int | None,
        typer.Option("--to-tick", min=0, help="Inclusive maximum tick."),
    ] = None,
    agent: Annotated[
        list[int] | None,
        typer.Option(
            "--agent",
            help="Only events referencing this agent id (repeatable).",
        ),
    ] = None,
    event_type: Annotated[
        list[str] | None,
        typer.Option(
            "--event-type",
            help="Only events of this type name (repeatable).",
        ),
    ] = None,
    verify: Annotated[
        bool,
        typer.Option(
            "--verify/--no-verify",
            help="Check SimulationStarted/Completed metadata continuity.",
        ),
    ] = True,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Exit with code 1 when verification notes are present.",
        ),
    ] = False,
    final_state: Annotated[
        bool,
        typer.Option(
            "--final-state",
            help="Show partial final-state summary derived from events.",
        ),
    ] = False,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            min=1,
            help="Maximum number of listed events (requires --list).",
        ),
    ] = None,
) -> None:
    """Replay and filter an existing JSONL simulation event log."""
    agent_ids = frozenset(agent) if agent else None
    event_types = frozenset(event_type) if event_type else None
    try:
        result = replay_run(
            path,
            from_tick=from_tick,
            to_tick=to_tick,
            agent_ids=agent_ids,
            event_types=event_types,
            include_final_state=final_state,
            verify=verify,
        )
    except ReplayError as exc:
        console.print(f"[red]Replay failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc

    if summary:
        _render_replay_metadata(result)
        _render_type_counts(result.type_counts)
    if final_state:
        _render_final_state(result)
    if list_events:
        listed = result.events if limit is None else result.events[:limit]
        for event in listed:
            brief = event_to_brief(event)
            console.print(
                f"{brief['sequence']:>6}  tick={brief['tick']:<4}  "
                f"{brief['event_type']}"
                + (f"  agent={brief['agent_id']}" if "agent_id" in brief else "")
                + (f"  action={brief['action']}" if "action" in brief else "")
            )
        if limit is not None and len(result.events) > limit:
            remaining = len(result.events) - limit
            console.print(f"[dim]… {remaining} more event(s) omitted[/dim]")
    if strict and result.verification_notes:
        raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point for the ``civitas`` command."""
    app()


if __name__ == "__main__":
    main()
