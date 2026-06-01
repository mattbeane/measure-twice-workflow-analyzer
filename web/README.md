# Measure Twice, Spend Once — Browser Tool

A single self-contained `index.html`. No build step, no dependencies, no server. It runs the workflow Monte Carlo entirely in the browser, calling Anthropic directly with the user's own key. **Nothing touches our infrastructure** — same privacy posture as the CLI, zero install for the user.

This is the path for non-technical users: they open a URL, paste a key, paste data, click Run.

---

## Ship it (Replit, ~2 minutes)

**Option A — standalone static site (simplest):**
1. New Replit → "HTML, CSS, JS" (static) template.
2. Replace `index.html` with this file.
3. Run → publish. Done. That URL is the tool.

**Option B — add to the existing measuretwicespendonce.com site:**
1. Drop this file into the site project as `tool.html` (or `analyze.html`).
2. Link it from the homepage with a prominent "Get the tool / Analyze your workflow" button.
3. Redeploy.

Either way it's a static file — any host works (Replit, Netlify, GitHub Pages, S3).

---

## Before the alpha — 2 quick checks

1. **Model id.** Top of the `<script>`: `const MODEL = "claude-haiku-4-5";`. If a tester sees an error mentioning the model (404 / "model not found"), their account needs a dated id — swap it there (e.g. a `claude-haiku-4-5-YYYYMMDD` string) and redeploy. Test once with your own key first.
2. **One real run.** Paste your key, click "Load example: support ticket", leave depth on Standard, Run. You should see the progress bar fill, a live spend counter (a few cents), and a results table where the **reliability** column has a mix of green/amber/red. That red is the point — it's the model telling you which numbers not to trust.

---

## What the tester experiences

1. **Connect** — paste Anthropic key (optionally save to browser). Clear privacy statement.
2. **Paste data** — their own workflow, or one of three loaded examples (fetched from the public repo; falls back to an inline sample if offline).
3. **Measure** — pick depth (5/10/25 runs), lenses (process / skill / both), and a budget cap. Live cost estimate updates as they type.
4. **Run** — bounded-concurrency Monte Carlo with progress + live spend; stops cleanly at the budget cap; survives individual call failures.
5. **Results** — calibrated dashboard: per-metric mean, 95% CI, CV%, and a color-coded reliability flag. Summary strip counts high/moderate/low.
6. **Export** — `corpus.csv` and `corpus.json` download locally. Next-step pointer to the brief playbook.

---

## Cost & limits

- Cost scales with data size × runs × number of analyses. The example at Standard depth (10 runs) is roughly **$1–2** on Haiku 4.5. A budget cap (default $10) hard-stops the run.
- Each tester uses their own key, so rate limits are per-tester. Concurrency is capped at 5 to stay gentle.
- This browser tool is tuned for **modest N** (≤25). The full statistically-defensible N≈1000 run lives in the CLI (`mtso`) — link in the footer.

---

## Known edges (fine for alpha, note for later)

- **API key friction** is the one real hurdle for non-technical users — they must create and paste a key. A screenshotted "how to get your key" walkthrough is the highest-value next addition.
- The three "Load example" buttons fetch from the public GitHub repo; if GitHub is unreachable, the support example falls back to an inline copy. The other two need the network.
- No persistence of results across reloads (by design — nothing stored server-side). Download the corpus before closing.

---

## Don't forget the survey

The workflow-selection scan used in the workshop is a **separate** Google Form + Sheet (it needs Sheets for live multi-person aggregation). Its scoring criteria should match the website's "Choose Your Workflow" page. Tracked in the workshop materials, not in this repo.
