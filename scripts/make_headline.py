"""Generate an executive 'headline' view from a corpus.csv.

The full corpus (80+ metrics with CV/CI) is analyst-facing. This distills it to a
handful of plain-language findings, each with a traffic-light trust badge — what a
decision-maker actually reads. Keep the HEADLINE map in sync with the JS version in
web/index.html.

Usage:  python scripts/make_headline.py <corpus.csv> [out.md]
"""
import csv, sys
from pathlib import Path

# metric key -> (plain label, unit suffix). Curated, decision-relevant, exec-legible.
# Keep in sync with HEADLINE in web/index.html.
HEADLINE = [
    # Where the time goes
    ("cycle_time.total_cycle_time_days",     "End-to-end cycle time",                 " days"),
    ("cycle_time.wait_time_percent",         "Time spent waiting, not working",       "%"),
    ("bottleneck.top_bottleneck_days",       "Biggest single bottleneck",             " days"),
    ("approval.total_approval_wait_days",    "Days lost waiting on approvals",        " days"),
    ("value_waste.rework_percent",           "Time lost to rework",                   "%"),
    ("handoff.total_handoffs",               "Handoffs between people/teams",         ""),
    ("information_flow.repeated_questions",  "Times the same question got re-asked",  "×"),
    # What's happening to skill
    ("challenge_calibration.challenge_calibration_score", "Were people stretched at the right level? (0–100)", ""),
    ("relationship_health.relationship_health_score",     "Relationship climate for skill-building (0–100)",   ""),
    ("developmental_trajectory.developmental_trajectory_score", "Are people growing toward independence? (0–100)", ""),
]
LIGHT = {"high": "🟢", "moderate": "🟡", "low": "🔴", "insufficient_runs": "⚪"}
TRUST = {"high": "trust it", "moderate": "note the spread", "low": "the model is guessing",
         "insufficient_runs": "too few runs"}


def make(corpus_csv: Path, out_md: Path):
    by = {}
    for r in csv.DictReader(open(corpus_csv)):
        by[f"{r['prompt_id']}.{r['metric']}"] = r

    lines = ["# Headline\n",
             "What the analysis found, distilled — with a trust flag on each number. "
             "🟢 trust it · 🟡 note the spread · 🔴 the model is guessing (a question, not an answer).\n"]
    process_rows, skill_rows = [], []
    for key, label, unit in HEADLINE:
        r = by.get(key)
        if not r:
            continue
        mean = float(r["mean"])
        val = f"{mean:.0f}{unit}"
        rel = r["reliability"]
        line = f"- {LIGHT.get(rel,'⚪')} **{label}:** {val}  _( {TRUST.get(rel,rel)} )_"
        (skill_rows if key.startswith(("challenge","relationship","developmental","expert","complexity")) else process_rows).append(line)

    if process_rows:
        lines.append("\n**Where the time goes**\n")
        lines += process_rows
    if skill_rows:
        lines.append("\n**What's happening to skill** *(thin data here — read as signal, not fact)*\n")
        lines += skill_rows

    lines.append("\n---\n*The full analysis (every metric, with confidence intervals) is in `corpus.csv`. "
                 "This headline is the decision-maker's view.*")
    out_md.write_text("\n".join(lines) + "\n")
    return len(process_rows) + len(skill_rows)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent / "headline.md"
    n = make(src, out)
    print(f"wrote {out} — {n} headline findings")
