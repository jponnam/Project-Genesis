"""Jinja2 UI routes for the Civitas observatory."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from civitas.analytics import analyze_emergence, analyze_run, compare_runs
from civitas.api.catalog import (
    ReplayError,
    RunNotFoundError,
    build_agent_summaries,
    describe_run,
    detail_run,
    list_run_paths,
    load_run_events,
    paginate_events,
    resolve_run_path,
)
from civitas.api.executions import (
    ExecutionNotFoundError,
    execute_campaign,
    execute_scenario,
    list_campaign_executions,
    load_campaign_results,
)
from civitas.api.models import RunListItem
from civitas.campaigns import CampaignNotFoundError, list_campaigns, load_campaign
from civitas.scenarios import ScenarioNotFoundError, list_scenarios, load_scenario
from civitas.storage.summary import build_inspection

if TYPE_CHECKING:
    from collections.abc import Sequence

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
router = APIRouter(tags=["observatory"])


def _run_catalog() -> tuple[list[RunListItem], list[dict[str, Any]]]:
    """Return run models and presentation metadata from real files."""
    runs: list[RunListItem] = []
    rows: list[dict[str, Any]] = []
    for path in list_run_paths():
        readable = True
        try:
            run = describe_run(path)
        except ReplayError:
            readable = False
            run = RunListItem(
                run_id=path.stem,
                path=str(path),
                size_bytes=path.stat().st_size,
            )
        runs.append(run)
        rows.append(
            {
                "run": run,
                "readable": readable,
                "modified_at": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    tz=UTC,
                ),
            }
        )
    rows.sort(key=lambda item: item["modified_at"], reverse=True)
    return runs, rows


def _sparkline_points(
    series: Sequence[tuple[int, int | float]],
    *,
    width: int = 600,
    height: int = 120,
) -> str:
    """Normalize a real numeric series into accessible inline-SVG points."""
    if not series:
        return ""
    values = [float(value) for _tick, value in series]
    low, high = min(values), max(values)
    spread = high - low or 1.0
    denominator = max(len(values) - 1, 1)
    points: list[str] = []
    for index, value in enumerate(values):
        x = index * width / denominator
        y = height - ((value - low) / spread) * (height - 12) - 6
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


@router.get("/", response_class=HTMLResponse)
def observatory_home(request: Request) -> HTMLResponse:
    """Real-data overview landing page."""
    runs, rows = _run_catalog()
    scenarios = list_scenarios()
    campaigns = list_campaigns()
    readable = [row for row in rows if row["readable"]]
    total_events = sum(int(row["run"].event_count or 0) for row in readable)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "Overview",
            "runs": runs,
            "run_rows": rows,
            "runs_available": bool(runs),
            "scenario_count": len(scenarios),
            "campaign_count": len(campaigns),
            "readable_count": len(readable),
            "total_events": total_events,
            "latest": rows[0] if rows else None,
        },
    )


@router.get("/runs", response_class=HTMLResponse)
def observatory_runs(request: Request) -> HTMLResponse:
    """Searchable, sortable run catalog."""
    runs, rows = _run_catalog()
    return templates.TemplateResponse(
        request,
        "runs.html",
        {
            "title": "Runs",
            "runs": runs,
            "run_rows": rows,
            "runs_available": bool(runs),
        },
    )


@router.get("/scenarios", response_class=HTMLResponse)
def observatory_scenarios(request: Request) -> HTMLResponse:
    """List executable scenario manifests."""
    return templates.TemplateResponse(
        request,
        "scenarios.html",
        {"title": "Scenarios", "scenarios": list_scenarios()},
    )


@router.get("/scenarios/{scenario_id}", response_class=HTMLResponse)
def observatory_scenario(request: Request, scenario_id: str) -> HTMLResponse:
    """Show one scenario and its run action."""
    try:
        scenario = load_scenario(scenario_id)
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "scenario_detail.html",
        {"title": scenario.title, "scenario": scenario},
    )


@router.post("/scenarios/{scenario_id}/run")
def observatory_scenario_run(scenario_id: str) -> RedirectResponse:
    """Create a scenario artifact and redirect to its dashboard."""
    try:
        result = execute_scenario(scenario_id)
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(
        url=f"/ui/runs/{result['run_id']}?launched=1",
        status_code=303,
    )


@router.get("/campaigns", response_class=HTMLResponse)
def observatory_campaigns(request: Request) -> HTMLResponse:
    """List campaign manifests and persisted execution counts."""
    campaigns = list_campaigns()
    counts = {
        campaign.id: len(list_campaign_executions(campaign.id))
        for campaign in campaigns
    }
    return templates.TemplateResponse(
        request,
        "campaigns.html",
        {"title": "Campaigns", "campaigns": campaigns, "counts": counts},
    )


@router.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
def observatory_campaign(request: Request, campaign_id: str) -> HTMLResponse:
    """Show one campaign and latest aggregate results when present."""
    try:
        campaign = load_campaign(campaign_id)
        executions = list_campaign_executions(campaign_id)
        latest = (
            load_campaign_results(campaign_id, executions[0]) if executions else None
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "campaign_detail.html",
        {
            "title": campaign.title,
            "campaign": campaign,
            "executions": executions,
            "report": latest,
        },
    )


@router.post("/campaigns/{campaign_id}/run")
def observatory_campaign_run(campaign_id: str) -> RedirectResponse:
    """Create a campaign execution and redirect to its aggregate view."""
    try:
        execute_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(
        url=f"/ui/campaigns/{campaign_id}?launched=1",
        status_code=303,
    )


@router.get("/campaigns/{campaign_id}/results", response_class=HTMLResponse)
def observatory_campaign_results(
    request: Request,
    campaign_id: str,
    execution_id: str | None = None,
) -> HTMLResponse:
    """Render persisted campaign results without re-running simulations."""
    try:
        campaign = load_campaign(campaign_id)
        report = load_campaign_results(campaign_id, execution_id)
    except (CampaignNotFoundError, ExecutionNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "campaign_detail.html",
        {
            "title": campaign.title,
            "campaign": campaign,
            "executions": list_campaign_executions(campaign_id),
            "report": report,
        },
    )


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def observatory_run(
    request: Request,
    run_id: str,
    from_tick: Annotated[int | None, Query(ge=0)] = None,
    to_tick: Annotated[int | None, Query(ge=0)] = None,
    agent_id: Annotated[int | None, Query(ge=0)] = None,
    event_type: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=10, le=200)] = 40,
) -> HTMLResponse:
    """Overview dashboard for one run."""
    try:
        path, events = load_run_events(run_id)
        detail = detail_run(path)
        summary = build_inspection(path)
        metrics = analyze_run(path)
        emergence = analyze_emergence(path)
        agents = build_agent_summaries(events)
        _total, event_page = paginate_events(
            events,
            offset=offset,
            limit=limit,
            from_tick=from_tick,
            to_tick=to_tick,
            agent_id=agent_id,
            event_type=event_type,
        )
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReplayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    metrics_by_name = metrics.by_name()
    event_freq = metrics_by_name.get("event_frequency_by_type")
    activity = metrics_by_name.get("agent_activity_distribution")
    resource_inequality = metrics_by_name.get("resource_inequality")
    event_by_tick = metrics_by_name.get("event_frequency_by_tick")
    wealth_gini = metrics_by_name.get("wealth_gini_bps")
    money_series = metrics_by_name.get("money_alive_series")
    wealth = summary.wealth
    event_series = (
        [(int(tick), int(value)) for tick, value in event_by_tick.value.items()]
        if event_by_tick and event_by_tick.status == "ok"
        else []
    )
    gini_series = (
        [(int(tick), int(value)) for tick, value in wealth_gini.details["series"]]
        if wealth_gini and wealth_gini.status == "ok"
        else []
    )
    money_alive_series = (
        [(int(tick), int(value)) for tick, value in money_series.details["series"]]
        if money_series and money_series.status == "ok"
        else []
    )
    laws = tuple(
        f"{data.get('kind')}:{data.get('name')}"
        for event in events
        if event.event_type == "LawCreated"
        for data in (event.model_dump(mode="json"),)
    )
    infrastructure = tuple(
        f"{data.get('kind')}:{data.get('name')}"
        for event in events
        if event.event_type == "InfrastructureCreated"
        for data in (event.model_dump(mode="json"),)
    )
    governments = tuple(
        str(data.get("name"))
        for event in events
        if event.event_type == "GovernmentCreated"
        for data in (event.model_dump(mode="json"),)
    )

    return templates.TemplateResponse(
        request,
        "run.html",
        {
            "title": f"Run {run_id}",
            "run": detail,
            "summary": summary,
            "metrics": metrics,
            "emergence": emergence,
            "agents": agents,
            "event_page": event_page,
            "event_total": _total,
            "filters": {
                "from_tick": from_tick,
                "to_tick": to_tick,
                "agent_id": agent_id,
                "event_type": event_type,
                "offset": offset,
                "limit": limit,
            },
            "event_frequency": (
                dict(list(event_freq.value.items())[:16])
                if event_freq and event_freq.status == "ok"
                else {}
            ),
            "activity": (
                dict(list(activity.value.items())[:16])
                if activity and activity.status == "ok"
                else {}
            ),
            "wealth": wealth,
            "resource_holdings_available": summary.final_resource_holdings_available,
            "resource_holdings": summary.resource_holdings,
            "resource_inequality": (
                resource_inequality
                if resource_inequality and resource_inequality.status == "ok"
                else None
            ),
            "event_series": event_series,
            "event_series_points": _sparkline_points(event_series),
            "gini_series": gini_series,
            "gini_series_points": _sparkline_points(gini_series),
            "money_series": money_alive_series,
            "money_series_points": _sparkline_points(money_alive_series),
            "event_types": tuple(summary.event_types),
            "laws": laws,
            "infrastructure": infrastructure,
            "governments": governments,
        },
    )


@router.get("/runs/{run_id}/agents/{agent_id}", response_class=HTMLResponse)
def observatory_agent(
    request: Request,
    run_id: str,
    agent_id: int,
) -> HTMLResponse:
    """Agent detail view."""
    try:
        _path, events = load_run_events(run_id)
        agents = {item.agent_id: item for item in build_agent_summaries(events)}
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail=f"agent not found: {agent_id}")
        _total, event_page = paginate_events(
            events,
            offset=0,
            limit=100,
            agent_id=agent_id,
        )
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReplayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request,
        "agent.html",
        {
            "title": f"Agent {agent_id}",
            "run_id": run_id,
            "agent": agents[agent_id],
            "events": event_page,
            "event_total": _total,
        },
    )


@router.get("/compare", response_class=HTMLResponse)
def observatory_compare(
    request: Request,
    left: Annotated[str | None, Query()] = None,
    right: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    """Side-by-side seed/run comparison using inspection summaries."""
    runs = []
    for path in list_run_paths():
        try:
            runs.append(describe_run(path))
        except ReplayError:
            continue

    comparison = None
    error = None
    if left and right:
        if left == right:
            error = "Select two different runs to produce a meaningful comparison."
        else:
            try:
                left_path = resolve_run_path(left)
                right_path = resolve_run_path(right)
                comparison = compare_runs(left_path, right_path)
            except (RunNotFoundError, ReplayError) as exc:
                error = str(exc)

    return templates.TemplateResponse(
        request,
        "compare.html",
        {
            "title": "Compare runs",
            "runs": runs,
            "left": left,
            "right": right,
            "comparison": comparison,
            "error": error,
        },
    )


@router.get("/open/{run_id}")
def open_run(run_id: str) -> RedirectResponse:
    """Convenience redirect used by the run selector form."""
    return RedirectResponse(url=f"/ui/runs/{run_id}", status_code=303)


@router.get("/open")
def open_selected_run(
    run_id: Annotated[str, Query(min_length=1)],
) -> RedirectResponse:
    """No-JavaScript redirect helper for the overview selector."""
    return RedirectResponse(url=f"/ui/runs/{run_id}", status_code=303)
