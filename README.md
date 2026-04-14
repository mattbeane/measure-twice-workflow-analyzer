# Workflow Analyzer

A CLI that takes a messy trace of real work (emails, Slack, meeting notes) and runs a battery of LLM-powered analyses over it — Monte Carlo style, so you can see where the model is confident and where it isn't.

Built as the working prototype behind the **Measure Twice, Spend Once** workshop. Feed it the kind of communication dump you'd have to reconstruct a workflow from, and it gives you quantified cycle time, handoff count, skill-development signals, and more — each metric run N times so variance is visible.

## What it does

- Ingests a text file of mixed-format work traces (see `sample_workflow.txt` for the shape)
- Runs ~12 analysis prompts across two categories: **process** (cycle time, wait time, handoffs, rework) and **skill** (who learned what, coaching moments, missed opportunities)
- Each prompt runs N times (default 5) against Claude
- Aggregates results with mean, std dev, and high-variance flags
- Persists every session to SQLite so you can go back and compare
- Optional rich terminal dashboard

## Quick start

```bash
# 1. Clone
git clone https://github.com/mattbeane/measure-twice-workflow-analyzer
cd measure-twice-workflow-analyzer

# 2. Install (uses uv — https://docs.astral.sh/uv/)
uv sync

# 3. Add your Anthropic API key
cp .env.example .env
# then edit .env

# 4. Run the sample
uv run wfa analyze sample_workflow.txt --runs 5 --dashboard
```

## Commands

```bash
wfa analyze <file>          # Run full analysis
wfa analyze <file> -r 10    # More runs = tighter confidence intervals (and higher cost)
wfa analyze <file> --process-only
wfa analyze <file> --skill-only
wfa list-sessions           # Browse past runs
wfa show <session-id>       # Re-inspect a past session
wfa show <session-id> -d    # ...with dashboard
wfa prompts                 # List all analysis prompts
```

## Stuck on setup?

This is a prototype, not a product. If `uv sync` or your API key or anything else trips you up, **ask your local coding assistant** (Claude Code, Cursor, Codex, whatever you use). Point it at this repo and describe what's happening — it will sort you out faster than any README I could write.

## Cost

Each `analyze` run of the sample with `--runs 5` is roughly 60 API calls. Expect a few cents per run on the current Claude Haiku/Sonnet pricing. `wfa list-sessions` shows a cost estimate per session.

## Extending

The interesting surface area for modification:

- **`src/workflow_analyzer/prompts.py`** — add or edit analysis prompts. Each prompt has a `prompt_template` (what to ask) and an `extraction_prompt` (how to get structured numbers back out). Copy an existing one as a template.
- **`src/workflow_analyzer/schemas.py`** — the metric schemas each prompt extracts into
- **`src/workflow_analyzer/runner.py`** — concurrency, retries, progress
- **`src/workflow_analyzer/dashboard.py`** — terminal visualization

Adding a new prompt is the highest-leverage change — it lets you ask a new quantitative question of every workflow you feed in.

## Input format

There's no strict format. Dump whatever communication trace you have: emails with headers, Slack transcripts with timestamps, meeting notes, calendar entries. The denser the timestamps and actor names, the better the cycle-time and handoff numbers will be. `sample_workflow.txt` is a representative shape.

## Caveats

- LLMs hallucinate numbers. The Monte Carlo framing exists *specifically* so you can see when the model is confabulating — watch for the `⚠ HIGH VAR` flag.
- Prompts are calibrated to Claude. Swap providers and you'll need to re-tune.
- SQLite storage is single-user. Don't share the `.db` file expecting multi-user semantics.

## License

MIT. Go nuts.
