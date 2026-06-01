# Facilitator prompt: turn the workflow scan into a ranked report

**When to use:** Segment 4 of the workshop. Participants have brainstormed candidate processes and scored them on the 5 criteria (on the site, or freehand), then dumped everything into the meeting chat. You paste that chat dump into any LLM (Claude, ChatGPT, Gemini — whatever you have open), under the prompt below, and screen-share what comes back.

**Why this and not a tool:** the chat dump is messy — different formats, partial scores, freehand notes, duplicate process names. An LLM handles that gracefully; a parser doesn't. Nothing is stored anywhere; this runs in your own AI session and disappears.

---

## How to run it (30 seconds)

1. Copy everything from the meeting chat (all the pasted scores + any brainstormed process names).
2. Open any AI chat. Paste the prompt below.
3. Under it, paste the chat dump where it says `[PASTE THE CHAT DUMP HERE]`.
4. Send. Screen-share the result.

The scores use the format `process | S# P# F# V# I#` — Stakes, Pain, Frequency, Visibility, Improvability, each 1–5 — but the prompt is built to tolerate any reasonable variation (missing scores, prose, different orders, duplicate names).

---

## THE PROMPT (copy everything in this block)

```
You are helping a facilitator run a workshop on choosing which work process a team
should MEASURE first (not fix — measure). Below is a raw dump from a meeting chat:
people brainstormed candidate processes and scored them on five 1–5 criteria. The
dump is messy — varied formats, partial entries, freehand notes, duplicate or
near-duplicate process names. Parse it as best you can; don't ask me to clean it up.

The five criteria (each 1–5, higher = stronger candidate to measure):
- S = STAKES: does it move customers, revenue, risk, or strategy?
- P = PAIN / FIREFIGHTING: does it run on workarounds, rework, and heroics?
- F = FREQUENCY: how often does it run?
- V = VISIBILITY: how much trail does the work leave (emails, tickets, chats, docs)?
- I = IMPROVABILITY: can this team actually change how it works?

Common score format is "process name | S4 P5 F3 V4 I2" but accept anything reasonable.
Merge obvious duplicate process names (e.g. "deal pipeline" and "sales pipeline").
If a score is missing, note it; don't invent it.

Produce, in this order:

1. RANKED TABLE — one row per process, columns: Process | #raters | avg S | avg P |
   avg F | avg V | avg I | TOTAL (sum of the five avgs, max 25) | Divergence
   (Low/Med/High — how much raters disagreed on that process's total). Sort by TOTAL desc.

2. TOP 3 TO MEASURE — the three highest-total processes, each with one sentence on why
   it's a strong candidate and the single biggest caveat (e.g. "high stakes but low
   visibility — you may need to create the data trail first").

3. MOST DIVIDED — the 1–2 processes where raters most disagreed, with a one-line prompt
   the facilitator can ask the room ("Some of you scored X a 5 on pain and some a 2 —
   what are you each seeing?"). Divergence is discussion gold, not noise.

4. READ OF THE ROOM — first tell me whether this looks like ONE INTACT TEAM scoring
   shared processes, or a MASHUP of individuals from different teams/orgs scoring their
   own separate processes. Decide from whether processes are shared across raters.
   Then:
   - If INTACT TEAM: recommend the single process the team should converge on, and why.
   - If MASHUP: do NOT force convergence. Instead surface 2–3 cross-cutting PATTERNS
     ("nearly everyone's top pick chokes on an approval handoff"), and frame the close
     as each person leaving with their own top-scored process to measure.
   - If UNCLEAR/MIXED: say so, give both the shared candidate and the individual-pick
     framing, and let the facilitator decide live.

Keep it tight and screen-readable. No preamble. Lead with the ranked table.

[PASTE THE CHAT DUMP HERE]
```

---

## Notes

- **Group composition is handled inside the prompt** (step 4). You don't need a different prompt for an intact team vs. a random mashup — it detects which and adapts the close. For an open-enrollment room of isolates, expect the "mashup → patterns + individual picks" path; for a booked intact team, expect "converge on one."
- **Divergence is the teaching moment.** When the report flags a split, run it — "what are you each seeing?" surfaces the different mental models people hold about their own work. That conversation is often worth more than the ranking.
- **Re-run freely.** If the room adds processes or re-scores, paste the new dump and run again. Stateless, costs cents, no setup.
- **Criteria are canonical.** S/P/F/V/I here must match the survey spec (`WORKSHOP_LIKERT_SURVEY_SPEC.md`) and the site's "Choose a Workflow" page. Change all three together if they ever change.
