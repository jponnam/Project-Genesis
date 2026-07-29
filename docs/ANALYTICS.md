# Analytics

Offline metrics are computed by streaming JSONL runs — no live `World` rebuild.

## Entry points

| Surface | How |
|---------|-----|
| Python | `civitas.analytics.engine.compute_run_metrics(path)` |
| CLI | `civitas metrics PATH [--format json\|text]` |
| API | `GET /runs/{run_id}/metrics` |
| UI | Run detail page panels |

## Metric families

Metrics are event-derivable aggregates, including:

- **Population** — births, deaths, alive counts from census / lifecycle events
- **Economy** — trades, production/consumption flows, wealth census fields (`gini_bps`, share bps)
- **Social** — relationship / trust / reputation activity present in the log
- **Governance** — law, vote, institution, tax/treasury signals
- **Knowledge** — research, innovation, diffusion, teaching events
- **Built form** — infrastructure and city-related events when present

Exact field names live in `civitas.analytics.types` and are stable for JSON consumers.

## Design rules

1. Every metric must be justified by events in the log.
2. Prefer census snapshots already emitted by the engine (e.g. wealth Gini, `ResourcesObserved`) over inventing stock levels.
3. Label unavailable reconstructions rather than guessing.
4. Keep computation streaming / single-pass friendly where possible.

Stock inequality / per-resource holding series are Phase 22 Milestone 5 candidates now that `ResourcesObserved` exists.

## Related

- Seed comparison: [OBSERVATORY.md](OBSERVATORY.md) and `civitas compare`
- Emergence overlays: [EMERGENCE_DETECTION.md](EMERGENCE_DETECTION.md)
