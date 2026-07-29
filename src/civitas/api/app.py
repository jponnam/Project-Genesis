"""FastAPI application for inspecting and launching local Civitas runs.

Existing JSONL files are never mutated. Scenario/campaign POST routes only
create new artifacts under ``CIVITAS_RUNS_DIR`` (default: ``runs/``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

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
from civitas.api.executions import (
    ExecutionNotFoundError,
    InvalidExecutionIdError,
    execute_campaign,
    execute_scenario,
    list_campaign_executions,
    load_campaign_results,
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
from civitas.campaigns import (
    CampaignNotFoundError,
    list_campaigns,
    load_campaign,
)
from civitas.observatory.routes import (
    router as observatory_router,
)
from civitas.observatory.routes import (
    templates as observatory_templates,
)
from civitas.scenarios import ScenarioNotFoundError, list_scenarios, load_scenario
from civitas.storage.summary import build_inspection

app = FastAPI(
    title="Civitas Lab Research API",
    description=(
        "Research API over local JSONL simulation runs. Existing logs are immutable; "
        "scoped POST routes create new scenario/campaign artifacts under the runs dir. "
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


@app.get("/favicon.ico", include_in_schema=False)
def favicon_redirect() -> RedirectResponse:
    """Avoid browser favicon 404s while serving the packaged SVG asset."""
    return RedirectResponse(url="/ui/static/favicon.svg", status_code=307)


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


@app.exception_handler(CampaignNotFoundError)
@app.exception_handler(ScenarioNotFoundError)
@app.exception_handler(ExecutionNotFoundError)
async def _manifest_not_found_handler(
    _request: Request,
    exc: CampaignNotFoundError | ScenarioNotFoundError | ExecutionNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidExecutionIdError)
async def _invalid_execution_handler(
    _request: Request,
    exc: InvalidExecutionIdError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> HTMLResponse | JSONResponse:
    """Render branded UI errors while preserving API JSON error contracts."""
    if request.url.path.startswith("/ui/"):
        return observatory_templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": f"Error {exc.status_code}",
                "status_code": exc.status_code,
                "detail": str(exc.detail),
            },
            status_code=exc.status_code,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


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


@app.get("/scenarios", response_model=list[dict[str, Any]], tags=["executions"])
def get_scenarios() -> list[dict[str, Any]]:
    """List scenario manifests available to the local server."""
    return [scenario.to_dict() for scenario in list_scenarios()]


@app.get("/scenarios/{scenario_id}", response_model=dict[str, Any], tags=["executions"])
def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Return one scenario manifest."""
    return load_scenario(scenario_id).to_dict()


@app.post(
    "/scenarios/{scenario_id}/run",
    response_model=dict[str, Any],
    tags=["executions"],
    status_code=201,
)
def post_scenario_run(scenario_id: str) -> dict[str, Any]:
    """Create one new scenario JSONL under ``CIVITAS_RUNS_DIR``."""
    return execute_scenario(scenario_id)


@app.get("/campaigns", response_model=list[dict[str, Any]], tags=["executions"])
def get_campaigns() -> list[dict[str, Any]]:
    """List campaign manifests available to the local server."""
    return [campaign.to_dict() for campaign in list_campaigns()]


@app.get("/campaigns/{campaign_id}", response_model=dict[str, Any], tags=["executions"])
def get_campaign(campaign_id: str) -> dict[str, Any]:
    """Return one campaign manifest."""
    return load_campaign(campaign_id).to_dict()


@app.post(
    "/campaigns/{campaign_id}/run",
    response_model=dict[str, Any],
    tags=["executions"],
    status_code=201,
)
def post_campaign_run(campaign_id: str, compare: bool = True) -> dict[str, Any]:
    """Create a fresh campaign execution and persisted aggregate report."""
    return execute_campaign(campaign_id, compare=compare)


@app.get(
    "/campaigns/{campaign_id}/executions",
    response_model=list[str],
    tags=["executions"],
)
def get_campaign_executions(campaign_id: str) -> list[str]:
    """List persisted execution ids for one campaign."""
    _ = load_campaign(campaign_id)
    return list_campaign_executions(campaign_id)


@app.get(
    "/campaigns/{campaign_id}/results",
    response_model=dict[str, Any],
    tags=["executions"],
)
def get_campaign_results(
    campaign_id: str,
    execution_id: str | None = None,
) -> dict[str, Any]:
    """Load latest or selected persisted campaign results."""
    _ = load_campaign(campaign_id)
    return load_campaign_results(campaign_id, execution_id)


def create_app() -> FastAPI:
    """Factory used by tests and ASGI servers."""
    # Ensure default runs dir concept is documented at import/create time.
    _ = default_runs_dir()
    return app
