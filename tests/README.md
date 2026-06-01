# Regression test suite

```bash
uv sync --group dev
uv run pytest                                 # 158 tests in ~1s
uv run pytest --cov=workflow_analyzer         # with coverage
uv run pytest --cov=workflow_analyzer --cov-report=term-missing
```

Hermetic — no Anthropic calls, no shared filesystem state. The Anthropic SDK
is mocked everywhere it matters.

## Coverage

**92% line coverage** (1205 statements, 96 missed).

| Module | Coverage |
|---|---|
| `cost.py` | **100%** |
| `corpus.py` | **100%** |
| `prompts.py` | **100%** |
| `schemas.py` | **100%** |
| `config.py` | **100%** |
| `storage.py` | **100%** |
| `stats.py` | **99%** |
| `runner.py` | **95%** |
| `cli.py` | **88%** |
| `report.py` | **83%** |
| `dashboard.py` | **70%** |

The remaining gaps are mostly Rich rendering branches in `dashboard.py` and
a few cli.py paths that need full stdin/stdout streaming to drive
(`mtso configure` re-prompt on bad numeric input, the rare-path log lines).

## What's covered, by file

| File | What it pins |
|---|---|
| `test_cost.py` | Haiku 4.5 pricing, per-run heuristic, `BudgetTracker` |
| `test_corpus.py` | csv ↔ json schema parity, reliability buckets, csv columns |
| `test_stats.py` | mean/median/CV math, high-variance threshold, summary totals |
| `test_stats_edges.py` | unknown prompt id, skill category, confidence-weighted aggregation |
| `test_prompts.py` | 14 prompts (8 process + 6 skill), `{workflow_data}` placeholder |
| `test_storage.py` | round-trip, list-sessions, no-key-at-rest privacy invariant |
| `test_storage_edges.py` | `get_prompt_results` filtering |
| `test_config.py` | defaults, mode-600 file permissions, API key resolution order |
| `test_config_edges.py` | `_coerce` / `_format` round-trip, silent chmod fallback |
| `test_cli_smoke.py` | --help, prompts, list-sessions, show/corpus, configure --show |
| `test_cli_extended.py` | configure interactive flow, show --full/--dashboard, corpus re-export, analyze flag combos |
| `test_runner.py` | Two-call pipeline, markdown-fenced JSON, confidence flag, API/extraction failure paths, budget enforcement, adaptive stopping, per-prompt isolation |
| `test_report.py` | Section headings, high-variance markers, executive summary |
| `test_dashboard.py` | Bar/color helpers, render_dashboard smoke on real and failed results |
| **Regression: encoding fallback** (`test_encoding_fallback.py`) | cp1252 / Latin-1 paste doesn't crash |
| **Regression: loud failure summary** (`test_failure_summary.py`) | never report cheerful "Done" over failed calls |
| **Regression: partial save on Ctrl-C** (`test_partial_save_on_interrupt.py`) | mid-run interrupt persists completed runs |

The bottom three pin the hardening commit `09c66ee` — those tests will fail
if any of those behaviors regress.

## Notes on the conftest fixtures

`isolated_config_dir` wraps `config.load_config`, `save_config`,
`resolve_api_key`, and `has_api_key`. The config helpers each carry
`path: Path = CONFIG_PATH` as a default arg, evaluated once at module
import. Monkey-patching `cfg.CONFIG_PATH` alone is **not** enough — the
functions keep their original bindings and would silently read/write the
real `~/.config/measure-twice/config.toml`. The wrappers redirect every
call site to the test's `tmp_path`.
