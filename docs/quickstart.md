# Quickstart — 5 minutes, no dev experience needed

This gets you from zero to a real analysis. If anything trips you up, see [troubleshooting.md](troubleshooting.md) or ask your AI coding assistant.

---

## 1. Get an Anthropic API key (2 min)

1. Go to [console.anthropic.com](https://console.anthropic.com).
2. Sign in (or sign up).
3. Left menu → **API Keys** → **Create Key**.
4. Copy it. It starts with `sk-ant-`. Keep it somewhere safe — you'll paste it once in step 3.

> An API key is like a credit card for AI usage. This tool uses Haiku, the cheapest model. **Real costs (on the bundled ~15 KB sample):** a `--quick` smoke test (10 runs/prompt) runs about **$2** and takes **a few minutes** — longer on a brand-new account, which starts with low rate limits. A full default run (1,000 runs/prompt, with adaptive stopping) is roughly **$40–50**. Bigger inputs cost more, because your workflow text is sent on every call. **You set a spending cap before every run, and the tool stops when it's hit.**

---

## 2. Install the tool (2 min)

**The easy way — `pipx`:**

```bash
pipx install measure-twice
```

Don't have `pipx`?

- **Mac:** `brew install pipx && pipx ensurepath`
- **Anything else:** `python3 -m pip install --user pipx && python3 -m pipx ensurepath`

Then close and reopen your terminal, and run the `pipx install` line above.

**Or, from this repo (if you cloned it):**

```bash
cd measure-twice
./setup.sh          # sets up everything for you
```

---

## 3. Add your key (30 sec)

```bash
mtso configure
```

Paste your key when asked. It's saved to `~/.config/measure-twice/config.toml` on your machine only (file permissions locked to you). Press Enter to accept the defaults for everything else.

---

## 4. Smoke-test on sample data (1 min)

```bash
mtso analyze examples/feature-deploy/workflow.txt --quick
```

`--quick` does a shallow 10-run pass — about **$2** and a few minutes on the sample (longer on a brand-new account). You'll get an analysis folder with `corpus.csv`, `corpus.json`, and `report.md`. Open `corpus.csv` in Excel or Google Sheets and look at the `reliability` column.

> The `reliability` column has four values: **high** (trust it), **moderate** (note the spread), **low** (the model disagreed with itself — treat as a question, not an answer), and **insufficient_runs** (too few successful runs to judge — usually means that metric failed extraction on most runs; ignore or re-run deeper).

---

## 5. Run it for real, on your own work

1. **Gather one workflow's exhaust into a text file.** Copy real emails, Slack threads, and meeting notes for one instance of a process you care about — start to finish. Paste them into a `.txt` file. Don't clean it up; messy is fine. Timestamps and names make the analysis better.

2. **Run it:**
   ```bash
   mtso analyze my-workflow.txt
   ```
   It'll show a cost estimate and ask you to set a budget (default $50). A full run is roughly **$40–50** on a sample-sized input and takes several minutes; larger inputs cost proportionally more. The budget cap is a hard stop.

3. **Open `my-workflow-analysis/corpus.csv`.** That's your calibrated picture. The high-reliability rows are trustworthy. The low-reliability rows are questions to dig into.

4. **Build your case.** Take `corpus.csv` to Claude or ChatGPT and follow the [playbook](../playbook/PLAYBOOK.md) to turn it into a one-page brief.

---

## What "measure twice" means

You just measured a workflow *before* deciding how to change it. That's the discipline. Don't redesign a process — or buy an AI tool to "fix" it — until you know, with calibrated confidence, what's actually happening. Measure twice. Spend once.
