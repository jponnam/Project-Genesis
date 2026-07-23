# Reproducibility

Civitas Lab aims for **seed-deterministic** trajectories: the same configuration and RNG seed should produce the same event log on the same software version.

## Guarantees

| Knob | Effect |
|------|--------|
| `seed` in config / CLI | Initializes `SeededRNG`; all draws go through it |
| Config TOML | Catalog unlocks, tick count, agent setup, economy knobs |
| Package version | Event schemas and system order must match to compare logs bit-for-bit |

Re-run:

```bash
civitas run --config path/to/config.toml --seed 42 --ticks 20 --output runs/demo.jsonl
```

Byte-identical JSONL is expected when version, config, seed, and tick count match. Cross-version comparisons should use analytics/`civitas compare`, not raw file hashes alone.

## Verifying a run

```bash
civitas replay runs/demo.jsonl --verify
civitas inspect runs/demo.jsonl
civitas metrics runs/demo.jsonl --format json
```

`--strict` on replay fails on unknown or malformed event types.

## Comparing seeds

```bash
civitas compare runs/a.jsonl runs/b.jsonl
```

Or Observatory `GET /compare` / `/ui/compare` with two run ids under `CIVITAS_RUNS_DIR`.

## What can break determinism

- Non-seeded randomness outside `SeededRNG` (treat as a bug)
- Floating iteration order over unsorted sets/dicts in new code
- Parallel execution that reorders event emission
- Different dependency versions that change numeric edge cases

## Research hygiene

1. Record package version, config path, seed, and ticks with every published run.
2. Prefer scenario TOMLs under `scenarios/` for shared demos.
3. Do not claim LLM-driven decisions unless a real provider is wired (this repo ships mock-only).
