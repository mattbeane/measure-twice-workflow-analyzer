# The Brief Playbook — *Show Your Work, Make the Ask*

You ran `mtso analyze` and you have a `corpus.csv`. This playbook turns it into the one-page brief that gets your next decision funded.

**The move:** you are not asking AI to *write* for you. You are using AI as an *analyst* over a dataset too big to hold in your head — thousands of runs across 14 analyses — to find the argument the data actually supports, then state it honestly (including what you don't know).

**What you need:**
- Your `corpus.csv` (from `mtso analyze`)
- An AI tool with file upload + code execution: Claude (Pro) analysis tool, or ChatGPT (Plus) Data Analysis
- ~30 focused minutes

Upload `corpus.csv` to your AI tool, then run these seven prompts in order. Each one's output feeds the next.

---

## The brief you're building (7 sections, one page)

1. **The Ask** — what you want approved, up front
2. **What's Broken** — the problem, with one headline number
3. **What We Measured** — 3–5 metrics, each *with its confidence*
4. **What We'd Do** — the intervention, scoped
5. **What We Expect** — predicted impact + the counterfactual
6. **What We Don't Know** — honest unknowns *(this is the section that makes a CFO trust the rest)*
7. **What We'll Measure** — how you'll know it worked

---

## The seven prompts

### 1 — Pattern detection  *(code)*
> I've uploaded `corpus.csv` — metrics from a Monte Carlo workflow analysis. Each row has a mean, a coefficient of variation (`cv_percent`), a confidence interval, and a `reliability` flag. Write and run Python that returns the 5 most reliable findings (high reliability, large effect) and the 5 most uncertain (low reliability, large effect range). Show the numbers.

### 2 — Competing causal stories  *(chat)*
> Based on those patterns, give me 3 distinct causal stories this data could support for *why* this workflow underperforms. For each: a 2-sentence summary, the 3 strongest supporting metrics (with values), and the 2 metrics that most undercut it. Don't pick a winner yet.

### 3 — Triage  *(run 3 times, compare)*
> Of all the metrics in `corpus.csv`, which 3 belong in an executive brief and why? Which should be left out, and why? 
>
> **Run this prompt 3 times in 3 fresh chats.** Where the answers agree = solid, use those. Where they diverge = the choice itself is uncertain; that's a sign to either drop the metric or flag it.

### 4 — Evidence marshaling  *(code)*
> I'm going to argue for [your chosen story/intervention]. Using `corpus.csv`, write Python that pulls the strongest *supporting* data points and the strongest *undermining* data points for that argument — exact values and their reliability flags. No paraphrasing.

### 5 — Gap identification  *(chat)*
> Given this corpus, what's missing that would resolve the biggest remaining uncertainty about my decision? Name 3 specific things I'd need to measure next, and what each would tell me. These become my "What We Don't Know" section.

### 6 — Adversarial probe  *(code)*
> Here's my draft brief: [paste]. Using `corpus.csv`, write Python to find the single data point that most undermines it. Quote it with its value and reliability. Then tell me honestly: should this change my brief, or can I defensibly stand on it?

### 7 — Compose  *(chat)*
> Using everything above — chosen story, the 3 triaged metrics, supporting/undermining evidence, the gaps, and the adversarial point — write the one-page brief in these 7 sections: Ask, What's Broken, What We Measured, What We'd Do, What We Expect, What We Don't Know, What We'll Measure. Keep every claim matched to its confidence. One page.

---

## The discipline

The `reliability` column is your conscience. A metric flagged **low** does not belong in "What We Measured" as a fact — it belongs in "What We Don't Know" as a question. A brief that only shows the strong numbers and hides the weak ones is a pitch. A brief that shows both is an analysis. **Decision-makers fund analyses.**

---

## Reuse it

These seven prompts are a pipeline. Save this file. Next time you have a `corpus.csv` from any workflow, run the same seven and you'll have a brief in half an hour. That's the skill you're building — not "using AI," but *running a calibrated analytical pipeline over your own work data.*
