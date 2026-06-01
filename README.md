# Measure Twice, Spend Once

**Measure your workflows before you change them.**

This tool takes the messy exhaust of real work — emails, Slack threads, meeting notes — and uses AI to produce a *calibrated* quantitative picture of how that work actually happens: cycle time, bottlenecks, handoffs, decision delays, skill-development signals. Each metric is run many times (Monte Carlo style) so you see not just a number, but **how much to trust it.**

It's the companion tool to the *Measure Twice, Spend Once* workshop. You run it on your own data, on your own machine, with your own API key. **Your data never leaves your laptop except to go directly to Anthropic's API.** Nobody else — including the authors — ever sees it. ([Details](docs/privacy.md).)

---

## Why it exists

The biggest way to waste money on AI is to redesign a process before you understand it. Surveys tell you what people *think* is happening. This tool measures what's *actually* happening — and, crucially, tells you where the AI itself is uncertain, so you don't build a business case on a number the model was guessing at.

Run it. Get a `corpus.csv` of calibrated metrics. Take that to your AI tool to build the one-page brief that gets your next decision funded. (That second step is the [playbook](playbook/PLAYBOOK.md).)

> *On the roadmap:* a companion tool for rolling up and comparing many teams' briefs, so decision-makers can prioritize across a portfolio. This measurement tool stays free and open.

---

## Two ways to run it

- **In the browser — no install.** Open the page, paste your Anthropic key, paste your workflow data, click Run. Best for non-technical users. Self-contained, bring-your-own-key, runs entirely client-side. See [`web/`](web/).
- **Command line (`mtso`)** — the full-power version with statistically-defensible runs (N≈1000) and adaptive stopping. Setup below.

---

## Quick start

```bash
# 1. Install (see docs/quickstart.md if you don't have pipx)
pipx install measure-twice

# 2. Set up your Anthropic API key (stored locally, mode 600)
mtso configure

# 3. Try it on the sample data
mtso analyze examples/feature-deploy/workflow.txt --quick

# 4. When ready, run it for real on your own workflow
mtso analyze path/to/your-workflow.txt
```

New to this? Start with **[docs/quickstart.md](docs/quickstart.md)** — a 5-minute setup written for non-developers.

---

## What you get

Every run writes an analysis folder next to your input:

```
your-workflow-analysis/
├── corpus.csv      ← the canonical output: every metric, with confidence
├── corpus.json     ← same data, structured for programmatic use
└── report.md       ← human-readable summary
```

**`corpus.csv` is the important one.** One row per metric, with:

| column | meaning |
|--------|---------|
| `mean`, `median` | the metric's central value across runs |
| `cv_percent` | coefficient of variation — how much the model disagreed with itself |
| `ci_low`, `ci_high` | 95% confidence interval |
| `n_runs` | how many runs informed this metric |
| `reliability` | plain-language flag: **high** (trust it) / **moderate** (note the spread) / **low** (the model is guessing — treat as a question) |

The `reliability` column is the whole point. **Low-variance metrics you can take to a CFO. High-variance metrics are questions, not answers.**

---

## Commands

```bash
mtso configure                 # set up API key + defaults (run once)
mtso analyze <file>            # full run (default 1000 runs/prompt, ~$50 — you set a budget)
mtso analyze <file> --quick    # fast demo (10 runs/prompt, ~$2 on the sample)
mtso analyze <file> --budget 25    # hard spend ceiling
mtso analyze <file> --process-only # just the process prompts
mtso corpus <session-id>       # re-export corpus.csv from a past run
mtso list-sessions             # browse past runs
mtso show <session-id> -d      # re-inspect a run with the dashboard
mtso prompts                   # list the analysis prompts
```

`measure-twice` works as a longer alias for `mtso`. (`wfa` / `workflow-analyzer` still work too, for old muscle memory.)

---

## Cost & the budget prompt

A full, statistically defensible run (1000 runs/prompt with adaptive stopping) lands around **$50** on Claude Haiku 4.5 — less for simple workflows, since the tool stops sampling a metric early once it's confident.

Before any real run, the tool shows an estimate and **asks you to set a budget ceiling.** It tracks spend live and stops cleanly if you hit the cap. Use `--quick` (≈ $2 on the sample, a few minutes) to smoke-test your setup first.

---

## How it works

1. Your workflow text is sent to Claude with each of 14 analysis prompts (8 process + 6 skill).
2. Each prompt runs many times. Because the model varies run to run, you get a *distribution* per metric, not a single guess.
3. The tool computes mean, spread, confidence interval, and a reliability flag per metric.
4. **Adaptive stopping:** metrics that stabilize quickly stop early; uncertain ones run longer. Compute goes where the uncertainty is.

This is the "measure twice" half. The "spend once" half — turning these metrics into a decision — is the [playbook](playbook/PLAYBOOK.md).

---

## Privacy

- Runs entirely on your machine.
- Your data goes only to Anthropic's API, via your own key.
- The authors never see your data, your key, or your results.
- For enterprise use, see [docs/privacy.md](docs/privacy.md) on disabling training-data retention via your Anthropic Workspace.

---

## Stuck?

See [docs/troubleshooting.md](docs/troubleshooting.md), or point your coding assistant (Claude Code, Cursor, Codex) at this repo and describe what's happening — it'll sort you out faster than any README.

## License

MIT. Go nuts.
