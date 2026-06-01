# Process-selection criteria (canonical)

The 5 criteria for the "Score a Workflow" scan — *which process deserves attention to measure first.* Each scored 1–5. **This file is the single source of truth.** The website's scan page, the workshop survey spec, and the facilitator aggregation prompt must all match it. Change it here, propagate everywhere.

Synthesized from Dynamic Work Design (Repenning & Kieffer, *There's Got to Be a Better Way*) + classic Lean/Six-Sigma project selection. The logic chains: **does it matter × is it broken × does fixing it compound × can we see it × can we act on it.**

Score key (used in the copy-to-chat block): **S P F V I**.

---

### 1. Stakes (S)
*If this ran beautifully, would it move something that matters — customers, revenue, risk, strategy?*
- **5** — High: directly affects revenue, key customers, or strategic goals
- **3** — Medium: important but not mission-critical
- **1** — Low: nice to have, not business-critical

### 2. Pain / Firefighting (P)
*How much does this run on workarounds, rework, and heroics today?*
- **5** — Constant firefighting; heroics needed to get it done
- **3** — Recurring friction we route around
- **1** — Mostly runs fine

### 3. Frequency (F)
*How often does this process run?*
- **5** — Many times a day / continuously
- **3** — Weekly-ish
- **1** — Rarely / one-off

### 4. Visibility (V)
*How much of this work leaves a trail you could actually look at — emails, tickets, chats, docs?*
- **5** — Rich written trail (emails, Slack, tickets, docs)
- **3** — Some in writing, some verbal
- **1** — Mostly in people's heads / hallway conversations

### 5. Improvability (I)
*Could this team actually change how this works, or is it locked by forces outside the room?*
- **5** — Largely within our control to redesign
- **3** — Partly; needs some external buy-in
- **1** — Locked by regulation / other orgs / leadership

---

**Total** = sum of the five (max 25). Higher = stronger candidate to *measure first* (measure, not fix).

**Copy-to-chat format:** `process name | S# P# F# V# I#` — e.g. `sales pipeline | S5 P4 F4 V3 I2`.

**Practicality note:** Visibility doubles as a gate — a high-Stakes, low-Visibility process may need its data trail created before the tool can read it. Worth measuring, but expect a setup step first.
