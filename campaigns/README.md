# Research campaigns

Campaign TOML files declare **seed × preset sweeps** over the existing engine.
They do not hard-code outcomes.

Each campaign declares:

- `seeds` — one or more RNG seeds
- `ticks` / `agents` / optional `preset`
- `run_name_prefix` — output files are `<prefix>_seed<seed>.jsonl`
- research question + limitations

## Commands

```bash
civitas campaign list
civitas campaign show seed_sweep_demo
civitas campaign run seed_sweep_demo -o runs/campaigns/seed_sweep_demo
civitas campaign run seed_sweep_demo -o runs/campaigns/seed_sweep_demo --no-compare
```

`campaign run` executes every seed, writes JSONL under the output directory,
and (by default) builds consecutive-pair comparison reports via `compare_many`.
