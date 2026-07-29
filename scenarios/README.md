# Demonstration scenarios

These TOML files configure **research observation recipes** for the existing
Civitas engine. They do **not** hard-code simulation outcomes.

Each scenario declares:

- deterministic `seed` / `ticks` / `agents` / `run_name`
- a research question
- the exact `civitas run ...` command
- observable signals to look for with `inspect` / `metrics` / `emergence`
- honest limitations

## List / show / run

```bash
civitas scenarios list
civitas scenarios show technological_diffusion
civitas scenarios run wealth_concentration
civitas scenarios run wealth_concentration --analyze
civitas scenarios run institutional_formation -o runs/inst.jsonl
```

`scenarios run` builds a ``SimulationConfig`` from the recipe (including
optional ``preset``) and writes JSONL. ``--analyze`` then prints inspect,
metrics, and emergence summaries for that run.

## Suggested workflow

```bash
civitas scenarios show wealth_concentration
civitas scenarios run wealth_concentration --analyze
# or copy the printed command:
civitas run --seed 42 --ticks 40 --agents 8 --name wealth_conc
civitas inspect runs/wealth_conc_seed42.jsonl
civitas metrics runs/wealth_conc_seed42.jsonl
civitas emergence runs/wealth_conc_seed42.jsonl
```
