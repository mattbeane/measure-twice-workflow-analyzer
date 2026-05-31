"""Corpus export — the canonical hand-off artifact.

`corpus.csv` / `corpus.json` is what a workshop participant uploads to their own AI
tool (Claude Pro analysis / ChatGPT Plus Data Analysis) to drive the brief-writing
playbook. One row per (prompt, metric): the calibrated picture with confidence and a
plain-language reliability flag.
"""

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from .schemas import PromptRunResult
from .stats import analyze_all_results, MetricStats


# Reliability buckets keyed off coefficient of variation. These are the words that let
# a non-statistician read the corpus: "trust this number" vs "the model is guessing."
def reliability_flag(cv_percent: float, n: int) -> str:
    if n < 2:
        return "insufficient_runs"
    if cv_percent <= 10:
        return "high"          # tight agreement across runs — trust it
    if cv_percent <= 20:
        return "moderate"      # usable, note the spread
    return "low"               # the model disagrees with itself — treat as a question


@dataclass
class CorpusRow:
    prompt_id: str
    prompt_title: str
    category: str
    metric: str
    mean: float
    median: float
    std_dev: float
    cv_percent: float
    ci_low: float
    ci_high: float
    min_val: float
    max_val: float
    n_runs: int
    reliability: str


def build_rows(results: list[PromptRunResult]) -> list[CorpusRow]:
    rows: list[CorpusRow] = []
    all_stats = analyze_all_results(results)
    for prompt_id, pstats in all_stats.items():
        for metric_name, m in pstats.metrics.items():
            m: MetricStats
            ci_low, ci_high = m.confidence_95
            rows.append(CorpusRow(
                prompt_id=prompt_id,
                prompt_title=pstats.prompt_title,
                category=pstats.category,
                metric=metric_name,
                mean=round(m.mean, 3),
                median=round(m.median, 3),
                std_dev=round(m.std_dev, 3),
                cv_percent=round(m.coefficient_of_variation, 1),
                ci_low=round(ci_low, 3),
                ci_high=round(ci_high, 3),
                min_val=round(m.min_val, 3),
                max_val=round(m.max_val, 3),
                n_runs=m.n_samples,
                reliability=reliability_flag(m.coefficient_of_variation, m.n_samples),
            ))
    # Stable, human-friendly ordering: category, then prompt, then metric.
    rows.sort(key=lambda r: (r.category, r.prompt_id, r.metric))
    return rows


_FIELDS = [
    "prompt_id", "prompt_title", "category", "metric",
    "mean", "median", "std_dev", "cv_percent",
    "ci_low", "ci_high", "min_val", "max_val",
    "n_runs", "reliability",
]


def write_csv(rows: list[CorpusRow], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))
    return path


def write_json(rows: list[CorpusRow], path: Path,
               workflow_name: Optional[str] = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "workflow_name": workflow_name,
        "metric_count": len(rows),
        "schema": _FIELDS,
        "reliability_legend": {
            "high": "CV <= 10% — tight agreement across runs; trust it",
            "moderate": "CV 10-20% — usable, note the spread",
            "low": "CV > 20% — the model disagrees with itself; treat as a question",
            "insufficient_runs": "fewer than 2 successful runs",
        },
        "rows": [asdict(r) for r in rows],
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def export(results: list[PromptRunResult], out_dir: Path,
           workflow_name: Optional[str] = None) -> tuple[Path, Path]:
    """Write both corpus.csv and corpus.json into out_dir. Returns (csv_path, json_path)."""
    rows = build_rows(results)
    csv_path = write_csv(rows, out_dir / "corpus.csv")
    json_path = write_json(rows, out_dir / "corpus.json", workflow_name)
    return csv_path, json_path
