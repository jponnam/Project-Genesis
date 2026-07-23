# Architecture

Civitas Lab is a **deterministic, tick-based society simulation** with a layered design: domain models and event bus at the core, systems that mutate world state, JSONL persistence for research runs, and an offline observatory (CLI + API + UI) that reads those runs without replaying the full simulation engine.

## Layer overview

```text
┌─────────────────────────────────────────────────────────────┐
│  CLI (`civitas`)  ·  FastAPI API  ·  Observatory UI (Jinja) │
├─────────────────────────────────────────────────────────────┤
│  Analytics · Emergence · Compare · Replay · Inspect         │
│  (offline over JSONL — no World rebuild required)           │
├─────────────────────────────────────────────────────────────┤
│  SimulationEngine  →  ActionExecutor  →  Systems            │
│  UtilityPolicy · Needs · Economy · Governance · Knowledge … │
├─────────────────────────────────────────────────────────────┤
│  World · Agents · DomainEvent bus · Clock · SeededRNG       │
├─────────────────────────────────────────────────────────────┤
│  JsonlEventStore · Config (TOML) · Catalogs (tech/law/…)    │
└─────────────────────────────────────────────────────────────┘
```

## Core runtime

| Component | Role |
|-----------|------|
| `SimulationClock` | Discrete ticks; each tick advances world time |
| `SeededRNG` | All stochastic draws; same seed ⇒ same trajectory |
| `World` / `Agent` | Mutable state: needs, inventory, relationships, knowledge, … |
| `EventBus` | Publishes typed `DomainEvent` instances during a tick |
| `UtilityPolicy` | Scores candidate actions from agent needs and context |
| `ActionExecutor` | Applies chosen actions; emits domain events |
| Systems | Food, water, energy, economy, government, tech, memory, … |

Bootstrap of a seed world emits foundational events (fire, hearth, tax schedule, council, well, settlement) so governance and infrastructure exist from tick zero.

## Persistence

- Default store: append-only **JSONL** (`JsonlEventStore`).
- Each line is one event record (`schema_version`, `event_id`, `tick`, `event_type`, `payload`, …).
- Runs are identified by path (CLI) or basename under `CIVITAS_RUNS_DIR` (API/UI).
- **Holdings** (final inventories) are not reconstructed from the event log; analytics report flows and census snapshots that *are* in the log.

## Observatory stack

| Surface | Package | Purpose |
|---------|---------|---------|
| Replay / inspect | `civitas.storage` | Stream and summarize JSONL |
| Metrics / emergence / compare | `civitas.analytics` | Offline research metrics |
| HTTP API | `civitas.api` | Read-only FastAPI app |
| UI | `civitas.observatory` | Server-rendered Jinja2 + light JS |

Install extras: `pip install -e ".[observatory]"` (included in `.[dev]`).

## Design constraints (Phase 21)

- Metrics and emergence rules must be **derivable from persisted events**.
- No full `World` rebuild from JSONL for analytics.
- UI is intentionally not a React SPA.
- LLM providers remain **mock-only** in this repository; do not claim live model integration.
