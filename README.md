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
├── llm/          # Optional language-model adapters (Protocol + mocks)
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
| **8** | Effect wiring from innovations into action outcomes |
| **9** | Technology prerequisite trees and deeper tech progression |
| **10** | Writing, record-keeping, and institutional memory |

## Current Milestone

**Phase 10 — Milestone 12: Forum cities**

``CityKind.FORUM`` is a non-capital specialized seat (not seeded). Living
agents at an active forum receive ``+1`` teachings per knower via
``location_has_active_forum`` and ``FORUM_TEACHINGS_PER_KNOWER_BONUS``,
stacking with academy, scriptorium, curriculum, and scribe through
``effective_teachings_per_knower``. Census and ``CitiesObserved`` report
``active_forum_count``.

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
- Milestone 7: Population
- Milestone 8: Birth
- Milestone 9: Death

**Phase 3:**
- Milestone 1: Economy
- Milestone 2: Trading
- Milestone 3: Markets
- Milestone 4: Prices
- Milestone 5: Production
- Milestone 6: Taxes
- Milestone 7: Wealth

**Phase 4:**
- Milestone 1: Relationships
- Milestone 2: Trust
- Milestone 3: Reputation
- Milestone 4: Families
- Milestone 5: Social networks

**Phase 5:**
- Milestone 1: Governments
- Milestone 2: Laws
- Milestone 3: Voting
- Milestone 4: Institutions
- Milestone 5: Cities
- Milestone 6: Infrastructure

**Phase 6:**
- Milestone 1: Technology
- Milestone 2: Research
- Milestone 3: Innovation
- Milestone 4: Knowledge diffusion

**Phase 7:**
- Milestone 1: Episodic memory encoding
- Milestone 2: Reflection
- Milestone 3: Planning
- Milestone 4: Memory retrieval

**Phase 8:**
- Milestone 1: Effect wiring
- Milestone 2: Infrastructure effects
- Milestone 3: Birth knowledge inheritance
- Milestone 4: Trust-gated teaching

**Phase 9:**
- Milestone 1: Technology prerequisite trees
- Milestone 2: Irrigation technology
- Milestone 3: Tax redirection to government treasuries
- Milestone 4: Institution budgets
- Milestone 5: Treasury-funded infrastructure construction
- Milestone 6: Storehouse infrastructure
- Milestone 7: Road infrastructure
- Milestone 8: Institution-funded infrastructure construction
- Milestone 9: Guild institutions
- Milestone 10: Market fee laws
- Milestone 11: Outpost cities
- Milestone 12: Metallurgy technology

**Phase 10:**
- Milestone 1: Writing technology
- Milestone 2: Archive institutions
- Milestone 3: Scriptorium infrastructure
- Milestone 4: Curriculum laws
- Milestone 5: Library cities
- Milestone 6: Bureaucracy institutions
- Milestone 7: Mathematics technology
- Milestone 8: Academy institutions
- Milestone 9: Observatory infrastructure
- Milestone 10: Astronomy technology
- Milestone 11: Calendar laws
- Milestone 12: Forum cities

## License

MIT
