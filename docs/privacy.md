# Privacy & data handling

Short version: **this tool runs on your machine. Your data goes only to the AI provider you choose, using your own API key. The authors of this tool never see your data, your key, or your results.**

---

## Where everything lives

| Thing | Where it goes |
|-------|---------------|
| Your workflow data | Read from your local file or pasted into the browser. Sent only to the AI provider you select (Anthropic, OpenAI, Google, or xAI) for analysis. |
| Your API key | **CLI**: stored locally at `~/.config/measure-twice/config.toml`, file permissions locked to your user (mode 600). **Browser tool**: stored only in your browser's `localStorage`, keyed by provider so you can save one key per provider and switch between them. Never transmitted anywhere except as the auth header on your own API calls to the provider you selected. |
| Your results | Written to a local folder next to your input file. Stored in a local SQLite database (`workflow_analysis.db`). Never uploaded. |
| Telemetry / analytics | None. The tool phones home to nobody. |

There is no server. There is no hosted version. There is no account with us. The tool is an open-source program you run yourself.

---

## What your AI provider sees

When the tool analyzes your workflow, it sends that text to the API of the provider you selected — exactly as if you'd pasted it into that provider's chat product yourself. Their data-handling terms govern that exchange.

**For enterprise / sensitive data:**

- Use an API key issued under your organization's commercial agreement with the provider (e.g. an Anthropic Workspace, an OpenAI organization with the no-training default, a Google Workspace Vertex/AI Studio account, an xAI team). Most providers do not train on inputs under their commercial agreement; verify per provider before running on sensitive material.
- Confirm the provider's data-retention settings in their console before running on sensitive material.
- If your organization prohibits sending certain data to third-party APIs, treat this tool the same as any other use of an external LLM and clear it through the same review.

---

## What this means for distributing the tool to teams

Because nothing touches our infrastructure, distributing this tool inside your organization carries the same data-governance profile as letting your teams use any of the four big-lab chat products directly — no additional vendor, no additional data-processing agreement with us, no SOC 2 dependency on us. The external party in the loop is whichever provider the user picks, under their own API key and the provider's own terms.

If your security team asks "where does the data go," the answer is: **from the employee's laptop, directly to the AI provider they selected, under that provider's own API agreement. The tool authors are not in the data path.**

---

## Browser tool: experimental disclaimer for non-Anthropic providers

The browser tool's reliability flag (high / moderate / low) is empirically calibrated against Claude Haiku 4.5's variance profile. When a participant selects OpenAI, Google, or xAI, the page surfaces an **"Experimental"** notice — those providers' reliability flags may be more or less conservative than expected until per-provider recalibration ships. xAI gets an additional note: their credit-gate paywall is strict (no free-tier credits at signup; any API call returns 403 until credits are purchased in the console).

The CLI (`mtso analyze`) stays Anthropic-only for now — the multi-provider work lives in the browser tool first. When the browser path proves out, the CLI will follow.

---

## Reading the code

This is open source. The network surface is:

1. **Provider API calls.**
   - **CLI** (`src/workflow_analyzer/runner.py`): only to Anthropic.
   - **Browser tool** (`web/index.html`): to whichever of the four provider endpoints you selected (`api.anthropic.com`, `api.openai.com`, `generativelanguage.googleapis.com`, or `api.x.ai`). The page never calls a provider you didn't pick.
2. **Fetching the bundled example workflows from this public GitHub repo** — only when you click a "Load example" button in the browser tool, and only public sample data (never your data).

There are no other outbound connections, no telemetry, no analytics. Read the code, or have your security team read it.
