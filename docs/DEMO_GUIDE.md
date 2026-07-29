# Demo guide

Short path from clone to a portfolio-ready observatory session.

## 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 2. Pick a scenario

```bash
civitas scenarios list
civitas scenarios show wealth_concentration
civitas scenarios run institutional_formation --analyze
civitas scenarios run early_craft_depth --analyze
civitas scenarios run civic_density --analyze
```

Scenarios are TOML under `scenarios/` (research questions, exact run commands, signals, limitations). Prefer `civitas scenarios run <id>` to execute a recipe end-to-end.

## 3. Run two seeds

```bash
mkdir -p runs
civitas run --seed 42 --ticks 20 --agents 6 --name portfolio_demo
civitas run --seed 7 --ticks 20 --agents 6 --name portfolio_alt
```

Or use `civitas scenarios run <id> -o runs/...jsonl` / copy the printed command from `civitas scenarios show <id>`.

## 4. CLI research loop

```bash
civitas inspect runs/portfolio_demo_seed42.jsonl
civitas metrics runs/portfolio_demo_seed42.jsonl
civitas emergence runs/portfolio_demo_seed42.jsonl
civitas compare runs/portfolio_demo_seed42.jsonl runs/portfolio_alt_seed7.jsonl
```

## 5. Observatory

```bash
export CIVITAS_RUNS_DIR=$PWD/runs
civitas serve --host 127.0.0.1 --port 8765
```

Browse:

- Home: `http://127.0.0.1:8765/ui/`
- Run: `http://127.0.0.1:8765/ui/runs/portfolio_demo_seed42`
- Compare: `http://127.0.0.1:8765/ui/compare`

API docs: `http://127.0.0.1:8765/docs`

## Phase 22 depth + campaign demo

```bash
civitas scenarios run early_craft_depth --analyze
civitas scenarios run civic_density --analyze
civitas campaign run seed_sweep_demo -o runs/campaigns/seed_sweep_demo
```

In the Observatory:

- `/ui/runs/civic_density_seed7` shows resource stock census metrics.
- `/ui/campaigns/seed_sweep_demo` launches a fresh seed sweep and displays
  event/living/Gini comparisons.
- Existing logs remain immutable; each web launch creates a fresh artifact.

## 6. Quality gate (contributors)

```bash
pytest
ruff check src tests
ruff format --check .
mypy
```

## Sample inspect-style output

Text inspect summarizes ticks, event counts, population signals, and notes when final holdings are unavailable. JSON (`--format json`) is the stable machine interface for notebooks.

## Portfolio screenshots

See [OBSERVATORY.md](OBSERVATORY.md) for captured UI images from this flow,
including the campaign and civic-depth dashboards.
