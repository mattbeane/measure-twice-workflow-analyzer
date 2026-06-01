"""stats.py — coverage fills for the branches missed by test_stats.py.

Targets:
* `analyze_prompt_results` with no results (the early-return path).
* `analyze_prompt_results` for a skill-category prompt id.
* `extract_numeric_metrics` against a list of numbers.
* `calculate_confidence_weighted_stats` with empty / mismatched inputs.
"""
from workflow_analyzer.stats import (
    analyze_prompt_results,
    calculate_confidence_weighted_stats,
    extract_numeric_metrics,
)


def test_analyze_prompt_results_unknown_prompt_returns_zero_state(successful_results):
    """A prompt id that doesn't appear in `results` returns a PromptStats
    populated with zeros so downstream code doesn't have to special-case it."""
    out = analyze_prompt_results(successful_results, "totally_unknown_prompt_id")
    assert out.prompt_id == "totally_unknown_prompt_id"
    assert out.n_runs == 0
    assert out.n_successful == 0
    assert out.metrics == {}


def test_analyze_prompt_results_skill_category(make_result):
    """`category` is derived from a fixed set of process prompt ids. Anything
    else is classified as skill."""
    metrics = {"score": 80.0}
    skill_runs = [
        make_result(prompt_id="challenge_calibration",
                    prompt_title="C1. Challenge Calibration",
                    run_number=i + 1,
                    extracted_metrics=metrics)
        for i in range(3)
    ]
    out = analyze_prompt_results(skill_runs, "challenge_calibration")
    assert out.category == "skill"
    assert out.n_successful == 3
    assert "score" in out.metrics


def test_extract_numeric_metrics_top_level_list_of_numbers():
    """Lists of numbers get extracted with indexed keys."""
    out = extract_numeric_metrics({"vals": [1.0, 2.5, 4.0]})
    # `_extract_metrics`'s list branch indexes by position when items are numeric.
    assert out["vals[0]"] == 1.0
    assert out["vals[1]"] == 2.5
    assert out["vals[2]"] == 4.0


def test_extract_numeric_metrics_ignores_lists_of_non_numbers():
    out = extract_numeric_metrics({"items": [{"x": 1}, {"x": 2}]})
    # Non-numeric list items are not recursed — by design.
    assert "items[0]" not in out


def test_confidence_weighted_stats_empty_inputs():
    mean, median = calculate_confidence_weighted_stats([], [])
    assert mean == 0.0
    assert median == 0.0


def test_confidence_weighted_stats_mismatched_lengths_returns_zero():
    mean, median = calculate_confidence_weighted_stats([1.0, 2.0], ["high"])
    assert mean == 0.0
    assert median == 0.0


def test_confidence_weighted_stats_high_weights_pull_toward_high_values():
    """Two values: 10 (low weight) and 100 (high weight). The weighted mean
    should sit much closer to 100 than the plain average (55)."""
    mean, _ = calculate_confidence_weighted_stats(
        [10.0, 100.0], ["low", "high"]
    )
    assert mean > 55  # plain average is 55, weighted should be higher
