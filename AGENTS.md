# AGENTS.md

## Cursor Cloud specific instructions

Civitas Lab is a pure Python research library (no web/GUI, no external services).
The "application" is the importable `civitas` package plus its quality gates.
There is currently no runnable CLI command (the `cli` layer is a stub in early phases).

### Environment

- Requires Python 3.14+. It is managed by `uv`, which the update script installs
  Python for and syncs dependencies into `.venv/`. Activate with
  `source .venv/bin/activate`.
- `uv` lives at `~/.local/bin` and is on PATH for interactive shells (sourced via
  `~/.bashrc`). If a non-interactive shell can't find it, call it as
  `~/.local/bin/uv`.

### Quality gates (all must pass; see README "Quality gates")

- `pytest`
- `ruff check src tests`
- `ruff format --check src tests`
- `mypy`

Note: `mypy` is configured via `pyproject.toml` (`packages = ["civitas"]`,
`mypy_path = "src"`), so run bare `mypy` with no path arguments. `pytest` uses
`filterwarnings = ["error"]`, so any warning fails the test run.
