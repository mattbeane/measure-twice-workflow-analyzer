# Troubleshooting

Fastest path when stuck: point your AI coding assistant (Claude Code, Cursor, Codex) at this repo and paste the error. It'll resolve most setup issues faster than this page.

---

**`mtso: command not found`**
The install didn't put `mtso` on your PATH. If you used pipx: run `pipx ensurepath`, then close and reopen your terminal. If you cloned the repo: use `./setup.sh`, or run via `uv run mtso ...` from the repo directory.

**`No API key found`**
Run `mtso configure` and paste your key, or set it for one session: `export ANTHROPIC_API_KEY=sk-ant-...`. Check what's configured with `mtso configure --show`.

**`authentication_error` / 401 from the API**
Your key is wrong, revoked, or has no credit. Make a fresh key at [console.anthropic.com](https://console.anthropic.com) and re-run `mtso configure`. Confirm the account has billing set up.

**`rate_limit_error` / 429**
You're sending calls faster than your account tier allows. The tool retries, but on a low tier a 1000-run job may crawl. Options: use `--quick` while testing; lower concurrency isn't exposed as a flag yet (ask your assistant to adjust `max_concurrent` in `runner.py` if needed); or request a higher rate limit from Anthropic.

**The run is taking forever**
A full 1000-run job across 14 prompts is thousands of API calls — minutes, not seconds. Adaptive stopping shortens it when metrics are stable. Use `--quick` to validate your setup first. Watch the live cost counter in the progress bar.

**It cost more / less than expected**
Cost scales with how much workflow text you feed it (it's included in every call) and how uncertain the metrics are (uncertain metrics run more). The pre-run estimate is a guide; the budget prompt is the hard cap. Set `--budget` to enforce a ceiling.

**Lots of `low` reliability rows in my corpus**
That's information, not a bug. It means the model genuinely disagrees with itself on those metrics given your data — usually because the data is ambiguous about them. Treat low-reliability metrics as questions to investigate, not answers to cite. (The sample data deliberately produces several, to make this visible.)

**`JSON parse failed` in some runs**
Occasional extraction failures are normal across thousands of calls; they're dropped and the metric is computed from the successful runs. If *most* runs for a prompt fail, the workflow text may be too short or off-format — make sure it actually contains the kind of events that prompt looks for (timestamps, handoffs, etc.).

**Python version errors on install**
Needs Python 3.9+. Check with `python3 --version`. If you're below 3.9, install a newer Python (`brew install python` on Mac) and reinstall.
