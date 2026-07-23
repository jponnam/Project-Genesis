"""Jinja2 UI routes for the Civitas observatory."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

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
from civitas.api.models import RunListItem
from civitas.storage.summary import build_inspection

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
router = APIRouter(tags=["observatory"])


@router.get("/", response_class=HTMLResponse)
def observatory_home(request: Request) -> HTMLResponse:
    """Run selector landing page."""
    runs: list[RunListItem] = []
    for path in list_run_paths():
        try:
            runs.append(describe_run(path))
        except ReplayError:
            runs.append(
                RunListItem(
                    run_id=path.stem,
                    path=str(path),
                    size_bytes=path.stat().st_size,
                )
            )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "Civitas Observatory",
            "runs": runs,
            "runs_available": bool(runs),
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
            offset=0,
            limit=40,
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
    wealth = summary.wealth

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
            },
            "event_frequency": (
                event_freq.value if event_freq and event_freq.status == "ok" else {}
            ),
            "activity": activity.value if activity and activity.status == "ok" else {},
            "wealth": wealth,
            "resource_holdings_available": summary.final_resource_holdings_available,
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
