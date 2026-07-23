# Demonstration scenarios

These TOML files configure **research observation recipes** for the existing
Civitas engine. They do **not** hard-code simulation outcomes.

Each scenario declares:

- deterministic `seed` / `ticks` / `agents` / `run_name`
- a research question
- the exact `civitas run ...` command
- observable signals to look for with `inspect` / `metrics` / `emergence`
- honest limitations

## List scenarios

```bash
civitas scenarios list
civitas scenarios show technological_diffusion
```

## Suggested workflow

```bash
civitas scenarios show wealth_concentration
# copy the printed command, or:
civitas run --seed 42 --ticks 40 --agents 8 --name wealth_conc
civitas inspect runs/wealth_conc_seed42.jsonl
civitas metrics runs/wealth_conc_seed42.jsonl
civitas emergence runs/wealth_conc_seed42.jsonl
```
