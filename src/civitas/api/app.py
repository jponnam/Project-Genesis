"""Read-only FastAPI application for inspecting local Civitas runs.

The API never mutates JSONL files. It only discovers and analyzes existing
run artifacts under ``CIVITAS_RUNS_DIR`` (default: ``runs/``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from civitas import __version__
from civitas.analytics import analyze_emergence, analyze_run, compare_runs
from civitas.api.catalog import (
    ReplayError,
    RunNotFoundError,
    build_agent_summaries,
    default_runs_dir,
    describe_run,
    detail_run,
    list_run_paths,
    load_run_events,
    paginate_events,
    resolve_run_path,
    summary_dict,
)
from civitas.api.models import (
    AgentListResponse,
    ErrorResponse,
    EventPage,
    HealthResponse,
    RunDetail,
    RunListItem,
    TimelineResponse,
)
from civitas.observatory.routes import router as observatory_router
from civitas.storage.summary import build_inspection

app = FastAPI(
    title="Civitas Lab Research API",
    description=(
        "Read-only HTTP API over local JSONL simulation runs. "
        "Does not execute or modify simulations. "
        "Observatory UI is served under /ui/."
    ),
    version=__version__,
)

_OBSERVATORY_STATIC = Path(__file__).resolve().parent.parent / "observatory" / "static"
app.mount(
    "/ui/static",
    StaticFiles(directory=str(_OBSERVATORY_STATIC)),
    name="observatory-static",
)
app.include_router(observatory_router, prefix="/ui")


@app.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    """Send browsers to the observatory home page."""
    return RedirectResponse(url="/ui/", status_code=307)


def _http_error(status_code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


@app.exception_handler(RunNotFoundError)
async def _run_not_found_handler(
    _request: Request,
    exc: RunNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


@app.exception_handler(ReplayError)
async def _replay_error_handler(
    _request: Request,
    exc: ReplayError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Return API liveness information."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/runs", response_model=list[RunListItem], tags=["runs"])
def list_runs() -> list[RunListItem]:
    """List discovered JSONL runs in the configured runs directory."""
    items: list[RunListItem] = []
    for path in list_run_paths():
        try:
            items.append(describe_run(path))
        except ReplayError:
            # Skip unreadable files but keep the catalog resilient.
            items.append(
                RunListItem(
                    run_id=path.stem,
                    path=str(path),
                    size_bytes=path.stat().st_size,
                )
            )
    return items


@app.get(
    "/runs/{run_id}",
    response_model=RunDetail,
    tags=["runs"],
    responses={404: {"model": ErrorResponse}},
)
def get_run(run_id: str) -> RunDetail:
    """Return metadata for one run."""
    _path, _events = load_run_events(run_id)
    return detail_run(_path)


@app.get(
    "/runs/{run_id}/events",
    response_model=EventPage,
    tags=["runs"],
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def get_events(
    run_id: str,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    from_tick: Annotated[int | None, Query(ge=0)] = None,
    to_tick: Annotated[int | None, Query(ge=0)] = None,
    agent_id: Annotated[int | None, Query(ge=0)] = None,
    event_type: Annotated[str | None, Query(min_length=1)] = None,
) -> EventPage:
    """Return a paginated, optionally filtered event page."""
    _path, events = load_run_events(run_id)
    try:
        total, page = paginate_events(
            events,
            offset=offset,
            limit=limit,
            from_tick=from_tick,
            to_tick=to_tick,
            agent_id=agent_id,
            event_type=event_type,
        )
    except ReplayError as exc:
        raise _http_error(400, str(exc)) from exc
    return EventPage(
        run_id=run_id,
        total=total,
        offset=offset,
        limit=limit,
        events=page,
    )


@app.get(
    "/runs/{run_id}/summary",
    response_model=dict[str, Any],
    tags=["runs"],
)
def get_summary(run_id: str) -> dict[str, Any]:
    """Return the event-derived inspection summary."""
    path, _events = load_run_events(run_id)
    return summary_dict(path)


@app.get(
    "/runs/{run_id}/metrics",
    response_model=dict[str, Any],
    tags=["runs"],
)
def get_metrics(run_id: str) -> dict[str, Any]:
    """Return offline analytics metrics for the run."""
    path, _events = load_run_events(run_id)
    return analyze_run(path).to_dict()


@app.get(
    "/runs/{run_id}/emergence",
    response_model=dict[str, Any],
    tags=["runs"],
)
def get_emergence(run_id: str) -> dict[str, Any]:
    """Return rule-based emergence findings for the run."""
    path, _events = load_run_events(run_id)
    return analyze_emergence(path).to_dict()


@app.get(
    "/runs/{run_id}/agents",
    response_model=AgentListResponse,
    tags=["runs"],
)
def get_agents(run_id: str) -> AgentListResponse:
    """Return agent summaries reconstructed from events."""
    _path, events = load_run_events(run_id)
    return AgentListResponse(run_id=run_id, agents=build_agent_summaries(events))


@app.get(
    "/runs/{run_id}/timeline",
    response_model=TimelineResponse,
    tags=["runs"],
)
def get_timeline(run_id: str) -> TimelineResponse:
    """Return notable timeline entries from the inspection summary."""
    path, _events = load_run_events(run_id)
    report = build_inspection(path)
    return TimelineResponse(run_id=run_id, entries=list(report.notable_events))


@app.get(
    "/compare",
    response_model=dict[str, Any],
    tags=["compare"],
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def compare_run_ids(
    left: Annotated[str, Query(min_length=1, description="Left run_id")],
    right: Annotated[str, Query(min_length=1, description="Right run_id")],
) -> dict[str, Any]:
    """Compare two runs from the configured runs directory."""
    left_path = resolve_run_path(left)
    right_path = resolve_run_path(right)
    return compare_runs(left_path, right_path).to_dict()


def create_app() -> FastAPI:
    """Factory used by tests and ASGI servers."""
    # Ensure default runs dir concept is documented at import/create time.
    _ = default_runs_dir()
    return app
