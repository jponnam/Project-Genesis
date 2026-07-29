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
- **Economy** — trades, production/consumption flows, wealth census fields (`gini_bps`, share bps), `money_alive_series`
- **Resource stocks** — `final_resource_holdings`, `resource_holdings_series`, `resource_inequality` from `ResourcesObserved`
- **Social** — relationship / trust / reputation activity present in the log
- **Governance** — law, vote, institution, tax/treasury signals
- **Knowledge** — research, innovation, diffusion, teaching events
- **Built form** — infrastructure and city-related events when present

Exact field names live in `civitas.analytics.types` / metric `name` keys and are stable for JSON consumers.

## Design rules

1. Every metric must be justified by events in the log.
2. Prefer census snapshots already emitted by the engine (e.g. wealth Gini, `ResourcesObserved`) over inventing stock levels.
3. Label unavailable reconstructions rather than guessing.
4. Keep computation streaming / single-pass friendly where possible.

Stock metrics (`final_resource_holdings`, `resource_holdings_series`,
`resource_inequality`, `money_alive_series`) are available once the corresponding
censuses appear in the log; otherwise they report `status=empty`.

## Related

- Seed comparison: [OBSERVATORY.md](OBSERVATORY.md) and `civitas compare`
- Emergence overlays: [EMERGENCE_DETECTION.md](EMERGENCE_DETECTION.md)
