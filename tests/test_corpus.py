"""Corpus export — the canonical hand-off artifact.

These tests pin the column schema, the reliability legend, and the csv ↔ json
parity. Any participant who opens corpus.csv in Excel needs the columns to be
exactly what the README promises.
"""
import csv
import json

from workflow_analyzer import corpus
from workflow_analyzer.corpus import reliability_flag


# ---------------------------------------------------------------------------
# reliability_flag — the buckets a non-statistician reads
# ---------------------------------------------------------------------------

def test_reliability_high_when_cv_ten_or_less():
    assert reliability_flag(cv_percent=5.0, n=10) == "high"
    assert reliability_flag(cv_percent=10.0, n=10) == "high"


def test_reliability_moderate_in_the_ten_to_twenty_band():
    assert reliability_flag(cv_percent=15.0, n=10) == "moderate"
    assert reliability_flag(cv_percent=20.0, n=10) == "moderate"


def test_reliability_low_when_cv_above_twenty():
    assert reliability_flag(cv_percent=25.0, n=10) == "low"
    assert reliability_flag(cv_percent=200.0, n=10) == "low"


def test_reliability_insufficient_runs_below_two_samples():
    # This label was undocumented before Matt's hardening commit. The README
    # now lists it, so a participant opening Excel can interpret the row.
    assert reliability_flag(cv_percent=0.0, n=0) == "insufficient_runs"
    assert reliability_flag(cv_percent=0.0, n=1) == "insufficient_runs"


# ---------------------------------------------------------------------------
# build_rows + export
# ---------------------------------------------------------------------------

def test_build_rows_returns_one_row_per_metric(successful_results):
    rows = corpus.build_rows(successful_results)
    # successful_results carries five metrics on cycle_time
    assert len(rows) == 5
    metrics = {r.metric for r in rows}
    assert "active_work_days" in metrics
    assert "handoff_count" in metrics


def test_build_rows_every_row_has_a_reliability_flag(successful_results):
    rows = corpus.build_rows(successful_results)
    valid = {"high", "moderate", "low", "insufficient_runs"}
    for r in rows:
        assert r.reliability in valid, f"unexpected reliability: {r.reliability!r}"


def test_build_rows_sorted_by_category_then_prompt_then_metric(successful_results):
    rows = corpus.build_rows(successful_results)
    keys = [(r.category, r.prompt_id, r.metric) for r in rows]
    assert keys == sorted(keys)


def test_export_writes_both_files(successful_results, tmp_path):
    csv_path, json_path = corpus.export(
        successful_results, tmp_path, workflow_name="sample"
    )
    assert csv_path.exists()
    assert json_path.exists()
    assert csv_path.name == "corpus.csv"
    assert json_path.name == "corpus.json"


def test_csv_columns_match_documented_schema(successful_results, tmp_path):
    csv_path, _ = corpus.export(successful_results, tmp_path, workflow_name="sample")
    with csv_path.open() as f:
        header = next(csv.reader(f))
    # README promises these — locking in the order matters for downstream tooling.
    expected = [
        "prompt_id", "prompt_title", "category", "metric",
        "mean", "median", "std_dev", "cv_percent",
        "ci_low", "ci_high", "min_val", "max_val",
        "n_runs", "reliability",
    ]
    assert header == expected


def test_csv_and_json_have_same_row_count(successful_results, tmp_path):
    csv_path, json_path = corpus.export(
        successful_results, tmp_path, workflow_name="sample"
    )
    with csv_path.open() as f:
        csv_rows = list(csv.DictReader(f))
    payload = json.loads(json_path.read_text())
    assert len(csv_rows) == len(payload["rows"])
    assert len(csv_rows) == payload["metric_count"]


def test_json_payload_contains_reliability_legend(successful_results, tmp_path):
    _, json_path = corpus.export(successful_results, tmp_path, workflow_name="sample")
    payload = json.loads(json_path.read_text())
    legend = payload["reliability_legend"]
    # Every label that can appear in `reliability` must be defined in the legend
    # so a non-coder can interpret it.
    for label in ("high", "moderate", "low", "insufficient_runs"):
        assert label in legend
        assert legend[label]  # non-empty explanation


def test_export_skips_failed_runs(make_result, tmp_path):
    """Failed extractions shouldn't pollute metric rows — they have no metrics."""
    only_failures = [
        make_result(extraction_success=False, extracted_metrics=None) for _ in range(3)
    ]
    csv_path, _ = corpus.export(only_failures, tmp_path, workflow_name="empty")
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows == []
