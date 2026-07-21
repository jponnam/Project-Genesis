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
civitas run --seed 42 --ticks 100 --agents 10 --name default
civitas run --seed 42 --ticks 20 --agents 5 -o runs/demo.jsonl
```

`civitas run` executes a deterministic simulation and writes the event
stream to JSONL (default: `runs/<name>_seed<seed>.jsonl`).

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

**Phase 2 — Milestone 6: Energy**

`REST` restores energy via domain `apply_rest` / `EnergySystem`.
`spend_energy` powers MOVE costs. The utility policy skips `REST` when
energy is already full.

### Completed

**Phase 1:** structure → config → CLI → clock → domain → events → RNG →
world factory → needs → utility policy → action executor → engine →
JSONL storage → `civitas run`

**Phase 2:**
- Milestone 1: Locations
- Milestone 2: Movement
- Milestone 3: Resource gathering
- Milestone 4: Food
- Milestone 5: Water
- Milestone 6: Energy

## License

MIT
