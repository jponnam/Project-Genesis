# Phase 22 — Open Simulation Depth and Research Campaigns

**Status:** Design approved for sequential milestone delivery  
**Constraint:** No new domain catalogs (`TechnologyKind` / `LawKind` / `InstitutionKind` / `InfrastructureKind` / `CityKind`)  
**Base revision:** `main` @ Phase 21 Milestone 10 (`ca57fd9`)  
**Primary objective:** Make existing Phases 9–20 civilization content exerciseable in open deterministic runs, close event-ledger gaps that block honest stock analytics, and turn scenarios/observatory into an executable research campaign loop.

---

## 1. Problem statement

Phase 21 made Civitas Lab observable: replay, inspect, metrics, emergence, compare, scenarios recipes, FastAPI, and the Observatory UI. The bottleneck is no longer “can a researcher see a run?” — it is “do default runs exercise the civilization depth the catalogs claim?”

Confirmed gaps on tip of `main`:

| Gap | Evidence |
|---|---|
| Default world stays camp-minimal | `WorldFactory` + `default_*` seed **fire** (discovered), **fire_hearth** (active), **tax_schedule**, **council**, **well**, **settlement** only |
| Config has no depth knobs | `SimulationConfig` fields: `seed`, `ticks`, `agent_count`, `run_name` |
| Scenarios are recipes only | CLI: `civitas scenarios list\|show` — no `run` |
| Holdings unavailable | `final_resource_holdings_available=False` hardcoded in `storage/summary.py` |
| No world projector | Replay/docs explicitly avoid full `World` rebuild from JSONL |
| Observatory cannot launch runs | Read-only API/UI over `CIVITAS_RUNS_DIR` |
| Emergence metrics reserved | `detect_emergence(..., metrics=)` currently discarded |
| Docs drift | `EVENT_MODEL.md` mentions `schema_version`; `DomainEvent.to_record()` does not emit one |
| Scenario honesty | e.g. `technological_diffusion.toml`: “Most Phase 10–20 catalog techs remain undiscovered…” |

Phase 22 opens **depth and campaigns** without adding another ceramics/glass-style catalog phase.

---

## 2. Confirmed architecture inventory (pre-design)

### Runtime bootstrap (unchanged contract)

1. `SimulationConfig` → `WorldFactory.create` → systems tick → `DomainEvent` bus → JSONL.
2. Layer rules from Phase 21 still bind: domain isolation; systems no cross-imports; analytics/api/observatory outside the tick loop.

### Default seed set (camp minimal)

| Entity class | Seeded kinds (active/discovered) |
|---|---|
| Technology | `FIRE` discovered |
| Innovation | `FIRE_HEARTH` active |
| Law | `TAX_SCHEDULE` active |
| Institution | `COUNCIL` |
| Infrastructure | `WELL` |
| City | `SETTLEMENT` capital |

Late craft / civic / medical / navigation trees exist as enums + effect math but are not auto-unlocked in short default runs.

### Observatory surface (Phase 21 complete)

- CLI: `run`, `replay`, `inspect`, `metrics`, `emergence`, `compare`, `scenarios`, `serve`, `config`
- Packages: `storage`, `analytics`, `api`, `observatory`, `scenarios`
- UI/API: read-only over existing JSONL files

---

## 3. Target architecture

```text
Scenario / Campaign TOML
        │
        ▼
World preset / bootstrap overlay  ──►  SimulationConfig (+ fingerprint)
        │
        ▼
Engine (existing catalogs + systems) ──► JSONL run artifacts
        │
        ├─► Analytics / Emergence / Compare
        ├─► Deterministic world projector (partial, labeled)
        └─► Observatory (read + scoped “create new run” only)
```

**Presets over new kinds:** named overlays (e.g. `camp_minimal`, `early_craft`, `civic_dense`) deterministically enable *existing* entities/discoveries. They must not invent new enum values.

**Census before metrics:** stock holdings metrics ship only after periodic inventory/money census events exist in the log.

**Campaign writes:** new JSONL under `CIVITAS_RUNS_DIR` only — never rewrite historical logs.

---

## 4. Architecture decisions

| ID | Decision | Rationale |
|---|---|---|
| AD-1 | No new catalog kinds | Phase 21 thesis stands: breadth already exceeds default-run depth |
| AD-2 | Named world presets / overlays | Opens mid-tree content without hardcoding glass/crystal into every demo |
| AD-3 | Fingerprint includes preset | Reproducibility: seed alone is insufficient once overlays exist |
| AD-4 | Scenario `run` + campaign manifests | Recipes become executable research loops |
| AD-5 | Resource stock census events before stock metrics | Honesty: no fabricated holdings |
| AD-6 | Pure deterministic projector | Optional summary/state from events; partial fields labeled |
| AD-7 | Observatory may create runs, not edit logs | Scoped mutation for campaigns; keep audit trail append-only |
| AD-8 | One PR per milestone | Same delivery discipline as Phase 21 |

---

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Presets smuggle “new content” as hardcoded factories | Data-driven overlays; tests assert only existing kinds |
| Default demos silently become Phase-20 glass towns | Keep `camp_minimal` as default; document richer presets |
| Projector overclaims World identity | Expose only proven fields; label unavailable |
| Campaign UI becomes a game launcher | Local-only; writes JSONL; no multiplayer/SaaS |
| Metric vanity from sparse unlocks | Emergence rules fire only when signals exist |

---

## 6. Milestone plan and acceptance criteria

### M1 — Design + gap inventory (this PR)

**Deliverables**

- `docs/PHASE_22_DESIGN.md` (this document)
- README roadmap / current milestone points at Phase 22 M1
- No simulation behavior changes

**Acceptance**

- [ ] `pytest` passes
- [ ] `ruff check src tests` passes
- [ ] `ruff format --check .` passes
- [ ] `mypy` passes
- [ ] Design lists M2–M10 with hard constraints

### M2 — World presets / bootstrap overlays

**Deliverables:** Named presets (at least `camp_minimal`, `early_craft`, plus one civic/craft-dense option) that deterministically activate existing entities/discoveries; config or scenario TOML wiring; fingerprint includes preset; identical seed+preset ⇒ identical world tests.

### M3 — `civitas scenarios run`

**Deliverables:** Execute a scenario TOML end-to-end (run → JSONL → optional inspect/metrics/emergence summary). Preserve `list`/`show`.

### M4 — Resource stock census events

**Deliverables:** Periodic inventory/money stock observations (or equivalent ledger fields) so holdings are event-derivable; flip `final_resource_holdings_available` when reconstruction is sound; align `EVENT_MODEL.md` with actual record shape (`schema_version` only if implemented).

### M5 — Stock metrics

**Deliverables:** Analytics for per-resource holdings, resource inequality (Phase 21 candidate omitted for honesty), money series from censuses; CLI/API/UI wiring; unavailable only when events absent.

### M6 — Deterministic world projector

**Deliverables:** Pure `events → projected summary/state` API in storage/analytics; deterministic tests; partial OK if labeled; no invented inventories.

### M7 — Research campaigns / seed sweeps

**Deliverables:** Campaign manifest (TOML): seeds × preset × ticks; `civitas campaign run`; aggregate compare report built on existing compare.

### M8 — Observatory campaign surface

**Deliverables:** UI/API to run a local scenario/campaign (write new JSONL under `CIVITAS_RUNS_DIR` only), list campaigns, view aggregates. Do not edit past logs.

### M9 — Depth-oriented emergence + metric composition

**Deliverables:** Use reserved `metrics` arg in `detect_emergence`; add rules for mid-tree unlock, craft specialization, civic densification — only when presets/open runs produce signals.

### M10 — Depth demos + portfolio docs

**Deliverables:** Scenarios that reliably show pottery→irrigation (and optionally one later craft path) under documented presets; update ANALYTICS/EVENT_MODEL/OBSERVATORY/DEMO_GUIDE/README; screenshots of depth + campaigns.

Optional stretch (not required for phase complete): event `schema_version` + migration notes; tagged `v0.2.0` release notes.

---

## 7. Verification commands (every milestone)

```bash
source .venv/bin/activate
pytest
ruff check src tests
ruff format --check .
mypy
```

---

## 8. Out of scope (Phase 22)

- New `TechnologyKind` / `LawKind` / `InstitutionKind` / `InfrastructureKind` / `CityKind` values
- Hardcoding Phase 20 glass/crystal into the default `WorldFactory` camp seed
- PostgreSQL, Redis, Celery, Ray, Temporal, DuckDB/Polars platform rewrite
- Real LLM provider integration (mock/null only)
- React/SPA rewrite (keep Jinja + light JS)
- First-class `culture` subsystem
- Fabricating holdings or claiming full live-`World` identity without a proven projector
- Merging directly to `main`
- Implementing M2–M10 inside the M1 design PR

---

## 9. Execution status

| Milestone | Status |
|---|---|
| Design document | Complete (this file) |
| M1 Design + gap inventory | Merged |
| M2 World presets | Merged |
| M3 Scenarios run | Merged |
| M4 Stock census events | In progress |
| M5 Stock metrics | Pending |
| M6 World projector | Pending |
| M7 Research campaigns | Pending |
| M8 Observatory campaigns | Pending |
| M9 Depth emergence | Pending |
| M10 Depth demos + docs | Pending |
