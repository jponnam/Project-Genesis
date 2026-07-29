# Emergence detection

Emergence in Civitas Lab is **explicit and rule-based**, not a black-box classifier. Detectors read the same offline metrics / event streams as analytics and emit structured findings with evidence.

## Entry points

| Surface | How |
|---------|-----|
| Python | `civitas.analytics.emergence.detect_emergence(path)` (and related helpers) |
| CLI | `civitas emergence PATH [--format json\|text]` |
| API | `GET /runs/{run_id}/emergence` |
| UI | Run detail emergence panel |

## What “emergence” means here

A finding is a named rule that fired because thresholds or patterns in the event-derived metrics were met — for example sustained inequality movement, knowledge diffusion spikes, or governance activity clusters. Rules cite the signals they used so researchers can audit them.

Phase 22 adds depth-oriented rules:

- `mid_tree_activation` — at least two non-fire technologies active/discovered
- `civic_densification` — at least three active institutions and two cities
- `craft_stock_specialization` — repeated production plus metric-derived
  resource-stock inequality (uses `resource_inequality` and
  `final_resource_holdings`)

## Honesty constraints

- No claim of open-ended “AI discovered civilization patterns” without a listed rule.
- No LLM adjudication in the default pipeline (mock LLM only elsewhere in the repo).
- Absence of a finding means rules did not fire — not that nothing interesting happened.

## Extending

Add rules in `civitas.analytics.emergence` with:

1. A stable finding id / title
2. Clear predicates over metrics or event counts
3. Evidence payload suitable for JSON and UI
4. Tests that use small fixture JSONL runs
