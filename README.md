# Civitas Lab

**Open-source AI research platform for studying emergent intelligence,
autonomous agents, and civilization formation.**

Civitas Lab is not a game and not a simulation toy. It is a deterministic,
reproducible research substrate for investigating emergence, long-term
planning, memory, relationships, economies, institutions, governments,
markets, misinformation, conflict, alliances, innovation, culture, and
technological progress in populations of autonomous AI agents.

## Design Principles

| Principle | Meaning |
|---|---|
| Determinism | Same seed → identical simulation, always |
| Event sourcing | Every meaningful state change is a `DomainEvent` |
| Clean architecture | Domain has no outward dependencies |
| Decoupled systems | Systems communicate only through domain events |
| Research-grade quality | Typed, tested, linted, reproducible |

## Architecture

```
src/civitas/
├── domain/       # Core models, value objects, domain events
├── engine/       # Clock, seeded RNG, world lifecycle, tick loop
├── systems/      # Needs, policy, economy, governance, … (decoupled)
├── storage/      # Append-only JSONL event persistence & replay
├── analytics/    # Offline metrics over event streams
└── cli/          # Researcher-facing Typer interface
```

### Layer rules

1. **domain** depends on nothing inside Civitas Lab.
2. **engine** and **systems** depend on **domain** only (plus stdlib / approved libs).
3. **systems** must not import each other.
4. **storage** and **analytics** read/write event streams; they never own policy.
5. **cli** is a thin adapter over engine and storage.

```text
                 ┌─────────────┐
                 │     cli     │
                 └──────┬──────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     ┌────────┐   ┌─────────┐   ┌──────────┐
     │ engine │──▶│ systems │──▶│ storage  │
     └───┬────┘   └────┬────┘   └────┬─────┘
         │             │             │
         └──────┬──────┴──────┬──────┘
                ▼             ▼
           ┌────────┐   ┌───────────┐
           │ domain │   │ analytics │
           └────────┘   └───────────┘
```

## Tech Stack (Phase 1)

- Python 3.14+
- Pydantic v2
- Typer
- Rich
- pytest / mypy / ruff

Later phases may introduce FastAPI, React, PostgreSQL, Redis, OpenTelemetry,
LLM SDKs, DuckDB/Polars, Temporal, and Ray — **only when explicitly requested**.

## Development Setup

```bash
# Requires uv (https://docs.astral.sh/uv/)
uv python install 3.14
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Quality gates

```bash
pytest
ruff check src tests
ruff format --check src tests
mypy
```

All four must pass before a milestone is considered complete.

### CLI

```bash
civitas --help
civitas version
civitas config show
civitas config show --seed 42 --ticks 100 --agents 10 --name default
civitas config fingerprint --seed 7 --ticks 50
```

The CLI validates options into an immutable `SimulationConfig`. Simulation
execution (`civitas run`) arrives in a later Phase 1 milestone.

## Roadmap

| Phase | Focus |
|---|---|
| **1** | Project structure, config, CLI, clock, domain models, events, RNG, world factory, needs, utility policy, action executor, engine, JSONL storage |
| **2** | Locations, movement, resources, food/water/energy, population, birth/death |
| **3** | Economy, trading, markets, prices, production, taxes, wealth |
| **4** | Relationships, trust, reputation, families, social networks |
| **5** | Governments, laws, institutions, voting, cities, infrastructure |
| **6** | Technology, research, innovation, knowledge diffusion |
| **7** | LLM integration, agent cognition, reflection, planning, memory retrieval |

## Current Milestone

**Phase 1 — Milestone 8: World Factory**

Immutable `World` aggregate and deterministic `WorldFactory`. Seed `42`
always produces identical initial worlds; per-agent RNG streams make each
agent's traits depend only on `(seed, agent_id)`.

### Completed

- Milestone 1: Project structure, packaging, quality gates
- Milestone 2: Simulation configuration models
- Milestone 3: CLI skeleton (`civitas` entry point)
- Milestone 4: Simulation clock (`Tick` + `SimulationClock`)
- Milestone 5: Domain models (`Agent` + attributes)
- Milestone 6: Domain events + event bus
- Milestone 7: Seeded RNG
- Milestone 8: World factory
- Testing / linting / formatting gates (established in Milestone 1)

## License

MIT
