# Sample run output

A completed run of the analyzer against `../sample_workflow.txt` at 5 runs per prompt (66 API calls, ~$0.24 on Claude Haiku 4.5).

Generated via `python ../run_demo.py` from the repo root with a valid `ANTHROPIC_API_KEY`.

## Files

- **`sample_run_report.md`** — full text report: per-prompt means, std devs, ranges, 95% CIs, high-variance flags
- **`sample_run_dashboard.html`** — the terminal dashboard rendered to HTML (same panels you'd see running `wfa analyze ... -d`)
- **`sample_run_dashboard.svg`** — same dashboard as SVG (useful for slides)

## What to look at first

Scan `sample_run_report.md` for the `⚠️ HIGH VARIANCE` flags near the top. Those are the metrics where the LLM disagreed with itself across runs — the places you should be most skeptical of any single-shot analysis. That's the whole point of the Monte Carlo framing: see the model's confidence, not just its answer.

## Regenerate

```bash
uv run python run_demo.py
```

Overwrites these files and drops a fresh `demo.db` (gitignored) for `wfa show 1` replay.
