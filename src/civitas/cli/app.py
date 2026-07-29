"""Researcher-facing Typer CLI for Civitas Lab.

The CLI is a thin adapter: it validates operator input into domain
``SimulationConfig`` values, runs the simulation engine, persists
event streams, and replays existing JSONL logs. It contains no
simulation policy logic.
"""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Annotated, Literal

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from civitas import __version__
from civitas.analytics import (
    ComparisonReport,
    EmergenceReport,
    MetricsReport,
    analyze_emergence,
    analyze_run,
    compare_runs,
)
from civitas.campaigns import (
    CampaignNotFoundError,
    CampaignReport,
    list_campaigns,
    load_campaign,
    run_campaign,
)
from civitas.domain import CANONICAL_SEED, SimulationConfig, WorldPreset
from civitas.engine import SimulationEngine, SimulationResult
from civitas.scenarios import ScenarioNotFoundError, list_scenarios, load_scenario
from civitas.storage import (
    ProjectedState,
    ReplayError,
    ReplayResult,
    RunInspection,
    build_inspection,
    project_run,
    replay_run,
    write_events,
)
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

scenarios_app = typer.Typer(
    name="scenarios",
    help="List, inspect, and execute data-driven demonstration scenarios.",
    no_args_is_help=True,
)
app.add_typer(scenarios_app, name="scenarios")

campaign_app = typer.Typer(
    name="campaign",
    help="List, inspect, and execute research campaign seed sweeps.",
    no_args_is_help=True,
)
app.add_typer(campaign_app, name="campaign")

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
PresetOpt = Annotated[
    str,
    typer.Option(
        "--preset",
        help=(
            "World bootstrap preset: camp_minimal (default), early_craft, "
            "or civic_dense. Affects initial catalogs; included in fingerprint."
        ),
    ),
]


def build_config(
    seed: int,
    ticks: int,
    agent_count: int,
    run_name: str,
    preset: str = WorldPreset.CAMP_MINIMAL.value,
) -> SimulationConfig:
    """Validate CLI options into an immutable ``SimulationConfig``.

    Raises:
        typer.Exit: If validation fails (exit code 1).
    """
    try:
        resolved_preset = WorldPreset(preset)
        return SimulationConfig(
            seed=seed,
            ticks=ticks,
            agent_count=agent_count,
            run_name=run_name,
            preset=resolved_preset,
        )
    except (ValidationError, ValueError) as exc:
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
    table.add_row("preset", config.preset.value)
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
    preset: PresetOpt = WorldPreset.CAMP_MINIMAL.value,
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
    config = build_config(seed, ticks, agent_count, run_name, preset=preset)
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
    preset: PresetOpt = WorldPreset.CAMP_MINIMAL.value,
) -> None:
    """Validate options and display the resulting configuration."""
    config = build_config(seed, ticks, agent_count, run_name, preset=preset)
    render_config_table(config)


@config_app.command("fingerprint")
def config_fingerprint(
    seed: SeedOpt = CANONICAL_SEED,
    ticks: TicksOpt = 100,
    agent_count: AgentsOpt = 10,
    run_name: NameOpt = "default",
    preset: PresetOpt = WorldPreset.CAMP_MINIMAL.value,
) -> None:
    """Print only the configuration fingerprint (script-friendly)."""
    config = build_config(seed, ticks, agent_count, run_name, preset=preset)
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


def _render_inspection(report: RunInspection) -> None:
    """Print a Rich human-readable inspection summary."""
    overview = Table(title="Run inspection", show_header=True, header_style="bold")
    overview.add_column("Field", style="cyan")
    overview.add_column("Value")
    overview.add_row("path", report.path)
    overview.add_row("run_name", str(report.run_name))
    overview.add_row("seed", str(report.seed))
    overview.add_row("ticks_configured", str(report.ticks_configured))
    overview.add_row("ticks_executed", str(report.ticks_executed))
    overview.add_row("agent_count_configured", str(report.agent_count_configured))
    overview.add_row("event_count", str(report.event_count))
    overview.add_row("agents_spawned", str(report.agents_spawned))
    overview.add_row("births", str(report.births))
    overview.add_row("deaths", str(report.deaths))
    overview.add_row("estimated_living", str(report.estimated_living))
    overview.add_row("trades", str(report.trades))
    overview.add_row("actions", str(report.actions))
    overview.add_row("institutions", str(list(report.institutions)))
    overview.add_row("cities", str(list(report.cities)))
    overview.add_row(
        "technologies_discovered",
        str(list(report.technologies_discovered)),
    )
    console.print(overview)

    if report.verification_notes:
        console.print("[yellow]Verification notes:[/yellow]")
        for note in report.verification_notes:
            console.print(f"  - {note}")

    types = Table(title="Event types", show_header=True, header_style="bold")
    types.add_column("event_type", style="cyan")
    types.add_column("count", justify="right")
    for event_type, count in report.event_types.items():
        types.add_row(event_type, str(count))
    console.print(types)

    resources = Table(
        title="Resource flows",
        show_header=True,
        header_style="bold",
    )
    resources.add_column("flow", style="cyan")
    resources.add_column("totals")
    resources.add_row("gathered", str(report.resources_gathered))
    resources.add_row("consumed", str(report.resources_consumed))
    resources.add_row("produced", str(report.resources_produced))
    resources.add_row("traded", str(report.resources_traded))
    resources.add_row(
        "final_holdings_available",
        str(report.final_resource_holdings_available),
    )
    console.print(resources)
    if report.resource_holdings is not None:
        holdings = Table(
            title="Final resource holdings census",
            show_header=True,
            header_style="bold",
        )
        holdings.add_column("Field", style="cyan")
        holdings.add_column("Value")
        holdings.add_row(
            "alive_totals", str(list(report.resource_holdings.alive_totals))
        )
        holdings.add_row(
            "escrow_totals", str(list(report.resource_holdings.escrow_totals))
        )
        holdings.add_row("dead_totals", str(list(report.resource_holdings.dead_totals)))
        holdings.add_row("stack_count", str(report.resource_holdings.stack_count))
        holdings.add_row(
            "distinct_resources",
            str(report.resource_holdings.distinct_resources),
        )
        holdings.add_row(
            "agent_holdings",
            str(list(report.resource_holdings.agent_holdings)),
        )
        console.print(holdings)
    else:
        console.print(
            "[dim]Final per-agent resource inventories unavailable in this "
            "log (no ResourcesObserved census).[/dim]"
        )

    if report.wealth is not None:
        wealth = Table(
            title="Final wealth census",
            show_header=True,
            header_style="bold",
        )
        wealth.add_column("Field", style="cyan")
        wealth.add_column("Value")
        for field_info in fields(report.wealth):
            wealth.add_row(
                field_info.name,
                str(getattr(report.wealth, field_info.name)),
            )
        console.print(wealth)
    else:
        console.print("[dim]Wealth census: unavailable in this log.[/dim]")

    if report.population is not None:
        population = Table(
            title="Final population census",
            show_header=True,
            header_style="bold",
        )
        population.add_column("Field", style="cyan")
        population.add_column("Value")
        population.add_row("total", str(report.population.total))
        population.add_row("alive", str(report.population.alive))
        population.add_row("dead", str(report.population.dead))
        population.add_row(
            "location_counts",
            str(list(report.population.location_counts)),
        )
        console.print(population)

    social = Table(title="Social changes", show_header=True, header_style="bold")
    social.add_column("Field", style="cyan")
    social.add_column("Value")
    for field_info in fields(report.social):
        social.add_row(
            field_info.name,
            str(getattr(report.social, field_info.name)),
        )
    console.print(social)

    if report.notable_events:
        console.print("[bold]Notable events[/bold]")
        for notable in report.notable_events:
            console.print(f"  - {notable}")
    else:
        console.print("[dim]Notable events: none beyond routine observations.[/dim]")


def _render_metrics(report: MetricsReport) -> None:
    """Print a Rich table of analytics metric results."""
    table = Table(title="Analytics metrics", show_header=True, header_style="bold")
    table.add_column("name", style="cyan")
    table.add_column("status")
    table.add_column("value")
    for metric in report.metrics:
        table.add_row(metric.name, metric.status, str(metric.value))
    console.print(table)
    console.print(f"[dim]events={report.event_count} path={report.path}[/dim]")


def _render_emergence(report: EmergenceReport) -> None:
    """Print emergence findings as a Rich table."""
    table = Table(title="Emergence findings", show_header=True, header_style="bold")
    table.add_column("pattern", style="cyan")
    table.add_column("strength", justify="right")
    table.add_column("confidence", justify="right")
    table.add_column("ticks")
    table.add_column("explanation")
    if not report.findings:
        console.print(
            "[dim]No emergence patterns matched the explicit rule thresholds "
            "for this run.[/dim]"
        )
    for finding in report.findings:
        table.add_row(
            finding.pattern,
            f"{finding.strength:.2f}",
            f"{finding.confidence:.2f}",
            f"{finding.tick_start}-{finding.tick_end}",
            finding.explanation,
        )
    if report.findings:
        console.print(table)
    console.print(
        f"[dim]rules_evaluated={len(report.rules_evaluated)} path={report.path}[/dim]"
    )


def _render_comparison(report: ComparisonReport) -> None:
    """Print a Rich comparison table."""
    overview = Table(title="Run comparison", show_header=True, header_style="bold")
    overview.add_column("Field", style="cyan")
    overview.add_column("Left")
    overview.add_column("Right")
    overview.add_row("path", report.left.path, report.right.path)
    overview.add_row("seed", str(report.left.seed), str(report.right.seed))
    overview.add_row("run_name", str(report.left.run_name), str(report.right.run_name))
    overview.add_row(
        "event_count",
        str(report.left.event_count),
        str(report.right.event_count),
    )
    overview.add_row(
        "estimated_living",
        str(report.left.estimated_living),
        str(report.right.estimated_living),
    )
    overview.add_row(
        "wealth_gini_bps",
        str(report.left.wealth_gini_bps),
        str(report.right.wealth_gini_bps),
    )
    overview.add_row(
        "actions",
        str(report.left.actions),
        str(report.right.actions),
    )
    console.print(overview)

    if report.deltas:
        deltas = Table(title="Deltas", show_header=True, header_style="bold")
        deltas.add_column("field", style="cyan")
        deltas.add_column("left")
        deltas.add_column("right")
        for delta in report.deltas:
            deltas.add_row(delta.field, str(delta.left), str(delta.right))
        console.print(deltas)
    else:
        console.print("[dim]No field deltas.[/dim]")

    console.print(f"shared_emergence={list(report.shared_emergence)}")
    console.print(f"unique_left_emergence={list(report.unique_left_emergence)}")
    console.print(f"unique_right_emergence={list(report.unique_right_emergence)}")
    for note in report.notes:
        console.print(f"[yellow]note:[/yellow] {note}")


@scenarios_app.command("list")
def scenarios_list_command() -> None:
    """List available demonstration scenarios."""
    scenarios = list_scenarios()
    if not scenarios:
        console.print("[yellow]No scenarios found.[/yellow]")
        raise typer.Exit(code=1)
    table = Table(title="Scenarios", show_header=True, header_style="bold")
    table.add_column("id", style="cyan")
    table.add_column("title")
    table.add_column("seed", justify="right")
    table.add_column("ticks", justify="right")
    table.add_column("agents", justify="right")
    for scenario in scenarios:
        table.add_row(
            scenario.id,
            scenario.title,
            str(scenario.seed),
            str(scenario.ticks),
            str(scenario.agents),
        )
    console.print(table)


@scenarios_app.command("show")
def scenarios_show_command(
    scenario_id: Annotated[str, typer.Argument(help="Scenario id.")],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option("--format", help="Rich text or JSON."),
    ] = "text",
) -> None:
    """Show one demonstration scenario recipe."""
    try:
        scenario = load_scenario(scenario_id)
    except ScenarioNotFoundError as exc:
        console.print(f"[red]Scenario failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    if output_format == "json":
        console.print_json(json.dumps(scenario.to_dict()))
        return
    table = Table(title=scenario.title, show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("id", scenario.id)
    table.add_row("research_question", scenario.research_question)
    table.add_row("seed", str(scenario.seed))
    table.add_row("ticks", str(scenario.ticks))
    table.add_row("agents", str(scenario.agents))
    table.add_row("run_name", scenario.run_name)
    table.add_row("preset", scenario.preset)
    table.add_row("command", scenario.command)
    console.print(table)
    console.print("[bold]Observable signals[/bold]")
    for item in scenario.observable_signals:
        console.print(f"  - {item}")
    console.print("[bold]Limitations[/bold]")
    for item in scenario.limitations:
        console.print(f"  - {item}")


@scenarios_app.command("run")
def scenarios_run_command(
    scenario_id: Annotated[str, typer.Argument(help="Scenario id to execute.")],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="JSONL path for the event stream "
            "(default: runs/<run_name>_seed<seed>.jsonl).",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
    analyze: Annotated[
        bool,
        typer.Option(
            "--analyze/--no-analyze",
            help="After the run, print inspect, metrics, and emergence summaries.",
        ),
    ] = False,
) -> None:
    """Execute a demonstration scenario end-to-end into a JSONL run."""
    try:
        scenario = load_scenario(scenario_id)
        config = scenario.to_config()
    except ScenarioNotFoundError as exc:
        console.print(f"[red]Scenario failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except (ValidationError, ValueError) as exc:
        console.print(f"[red]Invalid scenario configuration:[/red]\n{exc}")
        raise typer.Exit(code=1) from exc

    output_path = output if output is not None else default_events_path(config)
    console.print(
        f"[bold]Running scenario[/bold] {scenario.id} "
        f"(preset={config.preset.value}, seed={config.seed}, "
        f"ticks={config.ticks}, agents={config.agent_count})"
    )
    result = SimulationEngine().run(config)
    write_events(output_path, result.events)
    render_run_summary(result, output_path)

    if not analyze:
        return
    try:
        inspection = build_inspection(output_path)
        metrics = analyze_run(output_path)
        emergence = analyze_emergence(output_path)
    except ReplayError as exc:
        console.print(f"[red]Scenario analysis failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc
    _render_inspection(inspection)
    _render_metrics(metrics)
    _render_emergence(emergence)


@campaign_app.command("list")
def campaign_list_command() -> None:
    """List available research campaigns."""
    campaigns = list_campaigns()
    if not campaigns:
        console.print("[yellow]No campaigns found.[/yellow]")
        raise typer.Exit(code=1)
    table = Table(title="Campaigns", show_header=True, header_style="bold")
    table.add_column("id", style="cyan")
    table.add_column("title")
    table.add_column("seeds", justify="right")
    table.add_column("ticks", justify="right")
    table.add_column("preset")
    for campaign in campaigns:
        table.add_row(
            campaign.id,
            campaign.title,
            str(len(campaign.seeds)),
            str(campaign.ticks),
            campaign.preset,
        )
    console.print(table)


@campaign_app.command("show")
def campaign_show_command(
    campaign_id: Annotated[str, typer.Argument(help="Campaign id.")],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option("--format", help="Rich text or JSON."),
    ] = "text",
) -> None:
    """Show one research campaign manifest."""
    try:
        campaign = load_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        console.print(f"[red]Campaign failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    if output_format == "json":
        console.print_json(json.dumps(campaign.to_dict()))
        return
    table = Table(title=campaign.title, show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("id", campaign.id)
    table.add_row("research_question", campaign.research_question)
    table.add_row("seeds", str(list(campaign.seeds)))
    table.add_row("ticks", str(campaign.ticks))
    table.add_row("agents", str(campaign.agents))
    table.add_row("preset", campaign.preset)
    table.add_row("run_name_prefix", campaign.run_name_prefix)
    console.print(table)
    console.print("[bold]Limitations[/bold]")
    for item in campaign.limitations:
        console.print(f"  - {item}")


def _render_campaign_report(report: CampaignReport) -> None:
    """Print campaign execution and pairwise compare summaries."""
    table = Table(title=f"Campaign {report.campaign_id}", show_header=True)
    table.add_column("seed", justify="right", style="cyan")
    table.add_column("events", justify="right")
    table.add_column("living", justify="right")
    table.add_column("gini_bps", justify="right")
    table.add_column("path")
    for item in report.runs:
        snap = item.snapshot
        table.add_row(
            str(item.seed),
            str(item.event_count),
            str(snap.estimated_living),
            str(snap.wealth_gini_bps),
            item.path,
        )
    console.print(table)
    for note in report.notes:
        console.print(f"[dim]{note}[/dim]")
    if report.comparisons:
        console.print(
            f"[bold]Pair comparisons[/bold]: {len(report.comparisons)} "
            "(consecutive seeds)"
        )
        for comparison in report.comparisons:
            console.print(
                f"  - seed {comparison.left.seed} vs {comparison.right.seed}: "
                f"deltas={len(comparison.deltas)} "
                f"shared_emergence={list(comparison.shared_emergence)}"
            )


@campaign_app.command("run")
def campaign_run_command(
    campaign_id: Annotated[str, typer.Argument(help="Campaign id to execute.")],
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Directory for campaign JSONL outputs (default: runs/campaigns/<id>).",
            file_okay=False,
            writable=True,
        ),
    ] = None,
    compare: Annotated[
        bool,
        typer.Option(
            "--compare/--no-compare",
            help="Build consecutive-pair comparison reports after the sweep.",
        ),
    ] = True,
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option("--format", help="Rich text or JSON report."),
    ] = "text",
) -> None:
    """Execute a research campaign seed sweep into JSONL runs."""
    try:
        campaign = load_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        console.print(f"[red]Campaign failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except (ValidationError, ValueError) as exc:
        console.print(f"[red]Invalid campaign configuration:[/red]\n{exc}")
        raise typer.Exit(code=1) from exc

    destination = (
        output_dir
        if output_dir is not None
        else Path("runs") / "campaigns" / campaign.id
    )
    if output_format != "json":
        console.print(
            f"[bold]Running campaign[/bold] {campaign.id} "
            f"({len(campaign.seeds)} seeds, preset={campaign.preset})"
        )
    report = run_campaign(campaign, output_dir=destination, compare=compare)
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict()))
        return
    _render_campaign_report(report)


@app.command("compare")
def compare_command(
    left: Annotated[
        Path,
        typer.Argument(exists=False, dir_okay=False, help="First JSONL run path."),
    ],
    right: Annotated[
        Path,
        typer.Argument(exists=False, dir_okay=False, help="Second JSONL run path."),
    ],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option("--format", help="Rich text or JSON output."),
    ] = "text",
) -> None:
    """Compare two deterministic simulation runs."""
    try:
        report = compare_runs(left, right)
    except ReplayError as exc:
        console.print(f"[red]Compare failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict()))
        return
    _render_comparison(report)


@app.command("serve")
def serve_command(
    host: Annotated[
        str,
        typer.Option("--host", help="Bind address for the research API."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", min=1, max=65535, help="Bind port."),
    ] = 8000,
    runs_dir: Annotated[
        Path | None,
        typer.Option(
            "--runs-dir",
            help="Directory of JSONL runs (sets CIVITAS_RUNS_DIR).",
            file_okay=False,
        ),
    ] = None,
) -> None:
    """Serve the read-only research API (requires the observatory extra)."""
    import os

    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "[red]API dependencies missing.[/red] Install with: "
            'uv pip install -e ".[observatory]"'
        )
        raise typer.Exit(code=1) from exc

    if runs_dir is not None:
        os.environ["CIVITAS_RUNS_DIR"] = str(runs_dir.resolve())
    console.print(
        f"Serving Civitas research API on http://{host}:{port} "
        f"(runs_dir={os.environ.get('CIVITAS_RUNS_DIR', 'runs')})"
    )
    uvicorn.run("civitas.api.app:app", host=host, port=port, log_level="info")


@app.command("emergence")
def emergence_command(
    path: Annotated[
        Path,
        typer.Argument(
            exists=False,
            dir_okay=False,
            readable=True,
            help="Path to a JSONL event log produced by civitas run.",
        ),
    ],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option(
            "--format",
            help="Output format: Rich text table or machine-readable JSON.",
        ),
    ] = "text",
) -> None:
    """Detect rule-based emergence patterns in a JSONL run."""
    try:
        report = analyze_emergence(path)
    except ReplayError as exc:
        console.print(f"[red]Emergence failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict()))
        return
    _render_emergence(report)


@app.command("metrics")
def metrics_command(
    path: Annotated[
        Path,
        typer.Argument(
            exists=False,
            dir_okay=False,
            readable=True,
            help="Path to a JSONL event log produced by civitas run.",
        ),
    ],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option(
            "--format",
            help="Output format: Rich text table or machine-readable JSON.",
        ),
    ] = "text",
) -> None:
    """Compute offline analytics metrics for a JSONL run."""
    try:
        report = analyze_run(path)
    except ReplayError as exc:
        console.print(f"[red]Metrics failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict()))
        return
    _render_metrics(report)


@app.command("inspect")
def inspect_command(
    path: Annotated[
        Path,
        typer.Argument(
            exists=False,
            dir_okay=False,
            readable=True,
            help="Path to a JSONL event log produced by civitas run.",
        ),
    ],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option(
            "--format",
            help="Output format: Rich text summary or machine-readable JSON.",
        ),
    ] = "text",
) -> None:
    """Inspect a JSONL run and print an event-derived summary."""
    try:
        report = build_inspection(path)
    except ReplayError as exc:
        console.print(f"[red]Inspect failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc

    if output_format == "json":
        console.print_json(json.dumps(report.to_dict()))
        return
    _render_inspection(report)


def _render_projection(state: ProjectedState) -> None:
    """Print a Rich table for a projected partial world state."""
    table = Table(title="Projected state", show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("path", str(state.path))
    table.add_row("seed", str(state.seed))
    table.add_row("run_name", str(state.run_name))
    table.add_row("ticks_configured", str(state.ticks_configured))
    table.add_row("ticks_executed", str(state.ticks_executed))
    table.add_row("event_count", str(state.event_count))
    table.add_row("estimated_living_ids", str(list(state.estimated_living_ids)))
    table.add_row("institutions", str(list(state.institutions)))
    table.add_row("cities", str(list(state.cities)))
    table.add_row(
        "technologies_discovered",
        str(list(state.technologies_discovered)),
    )
    table.add_row("last_wealth_alive_total", str(state.last_wealth_alive_total))
    table.add_row("last_wealth_gini_bps", str(state.last_wealth_gini_bps))
    table.add_row("last_population_alive", str(state.last_population_alive))
    table.add_row(
        "resource_holdings_available",
        str(state.resource_holdings_available),
    )
    table.add_row("resource_alive_totals", str(list(state.resource_alive_totals)))
    table.add_row(
        "resource_agent_holdings",
        str(list(state.resource_agent_holdings)),
    )
    table.add_row("unavailable", str(list(state.unavailable)))
    console.print(table)
    console.print("[dim]Partial projection only — not a full World rebuild.[/dim]")


@app.command("project")
def project_command(
    path: Annotated[
        Path,
        typer.Argument(
            exists=False,
            dir_okay=False,
            readable=True,
            help="Path to a JSONL event log produced by civitas run.",
        ),
    ],
    output_format: Annotated[
        Literal["text", "json"],
        typer.Option(
            "--format",
            help="Output format: Rich text table or machine-readable JSON.",
        ),
    ] = "text",
) -> None:
    """Project a partial world state from a JSONL event log."""
    try:
        state = project_run(path)
    except ReplayError as exc:
        console.print(f"[red]Project failed:[/red] {exc}")
        raise typer.Exit(code=exc.exit_code) from exc
    if output_format == "json":
        console.print_json(json.dumps(state.to_dict()))
        return
    _render_projection(state)


def main() -> None:
    """Console-script entry point for the ``civitas`` command."""
    app()


if __name__ == "__main__":
    main()
