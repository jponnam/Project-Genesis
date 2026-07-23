# Civitas Lab

**Deterministic society simulation for research on agents, institutions, and
event-sourced civilization dynamics.**

Civitas Lab is a reproducible, tick-based research substrate — not a game.
Populations of autonomous agents act under explicit utility policies; optional
cognition uses a **seeded mock LLM adapter only** (no live model provider).
Every meaningful change is a typed domain event persisted to JSONL for offline
replay, analytics, and the Simulation Observatory.

## Design principles

| Principle | Meaning |
|---|---|
| Determinism | Same seed + config + version → same trajectory |
| Event sourcing | Meaningful state changes are `DomainEvent` records |
| Clean architecture | Domain has no outward Civitas dependencies |
| Decoupled systems | Systems communicate through domain events |
| Research honesty | Metrics and emergence rules must be event-derivable |

## Architecture

```text
CLI / Observatory UI / FastAPI
        │
        ▼
Replay · Inspect · Analytics · Emergence · Compare
        │
        ▼
SimulationEngine → ActionExecutor → Systems
        │
        ▼
World · Agents · EventBus · Clock · SeededRNG
        │
        ▼
JSONL event store · TOML config · catalogs
```

Package layout:

```text
src/civitas/
├── domain/        # models, value objects, domain events
├── engine/        # clock, RNG, world lifecycle, tick loop
├── systems/       # needs, policy, economy, governance, …
├── llm/           # Protocol + mock adapters (no live provider)
├── storage/       # JSONL persistence, replay, inspect summaries
├── analytics/     # offline metrics, emergence, seed compare
├── api/           # read-only FastAPI research API
├── observatory/   # Jinja2 UI + static assets
├── scenarios/     # demonstration recipe loader
└── cli/           # Typer entrypoint (`civitas`)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for layer rules and
observatory boundaries.

## Quick start

```bash
# Requires uv (https://docs.astral.sh/uv/)
uv python install 3.14
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

civitas version
civitas run --seed 42 --ticks 20 --agents 6 --name demo
civitas inspect runs/demo_seed42.jsonl
civitas metrics runs/demo_seed42.jsonl
```

### Observatory

```bash
export CIVITAS_RUNS_DIR=$PWD/runs
civitas serve --host 127.0.0.1 --port 8000
# UI:      http://127.0.0.1:8000/ui/
# OpenAPI: http://127.0.0.1:8000/docs
```

![Observatory home](docs/images/observatory_home.png)

![Run dashboard](docs/images/observatory_run.png)

![Seed comparison](docs/images/observatory_compare.png)

## Sample session

```bash
civitas run --seed 42 --ticks 20 --agents 6 --name portfolio_demo
civitas inspect runs/portfolio_demo_seed42.jsonl
```

Example inspect summary (abridged):

```text
path                    runs/portfolio_demo_seed42.jsonl
run_name                portfolio_demo
seed                    42
ticks_executed          20
event_count             3096
agents_spawned          6
births                  11
deaths                  0
estimated_living        17
institutions            ['council:Camp Council']
cities                  ['settlement:Camp City']
technologies_discovered ['pottery:Camp Pottery', 'irrigation:Camp Irrigation']
```

```bash
civitas emergence runs/portfolio_demo_seed42.jsonl
civitas compare runs/portfolio_demo_seed42.jsonl runs/portfolio_alt_seed7.jsonl
civitas scenarios list
civitas scenarios show wealth_concentration
```

## Documentation

| Doc | Topic |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layers and runtime |
| [`docs/EVENT_MODEL.md`](docs/EVENT_MODEL.md) | Domain events & JSONL |
| [`docs/ANALYTICS.md`](docs/ANALYTICS.md) | Offline metrics |
| [`docs/EMERGENCE_DETECTION.md`](docs/EMERGENCE_DETECTION.md) | Rule-based findings |
| [`docs/OBSERVATORY.md`](docs/OBSERVATORY.md) | API + UI |
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | Seeds and verification |
| [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md) | Portfolio demo path |
| [`docs/PHASE_21_DESIGN.md`](docs/PHASE_21_DESIGN.md) | Phase 21 plan |
| [`scenarios/README.md`](scenarios/README.md) | Demonstration recipes |

## Capabilities

- Deterministic multi-agent simulation through Phases 1–20 civilization catalogs
- Append-only JSONL event logs with typed round-trip persistence
- CLI: `run`, `replay`, `inspect`, `metrics`, `emergence`, `compare`, `scenarios`, `serve`, `config`
- Offline analytics and explicit emergence rules over persisted events
- Read-only FastAPI research API and Jinja2 Observatory UI
- Seed / run comparison for counterfactual research
- Data-driven demonstration scenarios (TOML)

## Limitations

- No live LLM provider — mock adapter only
- Final per-agent resource **holdings** are not reconstructed from JSONL (flows and census snapshots are)
- Observatory is local/read-only; it does not launch or mutate simulations
- Analytics omit metrics that cannot be honestly derived from events
- Not a multiplayer game client or production SaaS stack

## Quality status

```bash
pytest
ruff check src tests
ruff format --check .
mypy
```

Phase 21 Milestone 10 baseline on this branch: **1307** tests passing;
coverage typically ~**89%** under `pytest --cov` (see CI / local run).

## Tech stack

Python 3.14+, Pydantic v2, Typer, Rich, pytest / mypy / ruff; optional
FastAPI + Jinja2 + uvicorn via `.[observatory]` (included in `.[dev]`).

## Roadmap

| Phase | Focus |
|---|---|
| **1–20** | Engine through glass/crystal civilization catalogs (complete on `main`) |
| **21** | Simulation observatory and emergence analytics (**complete** — no new catalogs) |
| Next | Portfolio polish, deeper research tooling, or catalog work only if requested |

## Current milestone

**Phase 21 Milestone 10: Portfolio documentation** — README, architecture /
event / analytics / emergence / observatory / reproducibility / demo guides,
and real Observatory screenshots. See `docs/PHASE_21_DESIGN.md`.

### Completed (summary)

Phases **1–20** delivered the deterministic engine, economy, social systems,
governance, knowledge, cognition ports (mock), and civilization catalog
progression through glasscraft. Phase **21** M1–M10 delivered quality repair,
replay/inspect, analytics, emergence, research API, Observatory UI, seed
comparison, demonstration scenarios, and portfolio documentation.

Detailed milestone lists for Phases 1–20 remain in git history and prior
release notes; the living design for Phase 21 is
[`docs/PHASE_21_DESIGN.md`](docs/PHASE_21_DESIGN.md).

## License

MIT
