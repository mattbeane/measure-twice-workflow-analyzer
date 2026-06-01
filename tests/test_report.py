"""report.py — text and table generators consumed by the CLI `--full` view.

These tests pin the output structure (headings, row counts, currency format).
"""
from rich.console import Console

from workflow_analyzer import report
from workflow_analyzer.report import (
    format_metric_line,
    format_prompt_section,
    generate_executive_summary,
    generate_report,
    generate_summary_table,
)
from workflow_analyzer.stats import (
    analyze_all_results,
    calculate_metric_stats,
    calculate_summary,
)


def test_generate_report_has_required_section_headings(successful_results):
    text = generate_report(successful_results)
    assert "WORKFLOW ANALYSIS REPORT" in text
    assert "SUMMARY" in text
    assert "PROCESS ANALYSIS RESULTS" in text
    assert "SKILL DEVELOPMENT ANALYSIS RESULTS" in text


def test_generate_report_shows_run_totals(successful_results, failed_results):
    text = generate_report(successful_results + failed_results)
    assert "Total API Calls: 8" in text
    assert "Successful: 5" in text
    assert "Failed: 3" in text


def test_generate_report_currency_format(successful_results):
    text = generate_report(successful_results)
    # cost.cost_of_tokens with three decimal places.
    assert "$" in text
    assert "Estimated Cost:" in text


def test_generate_report_high_variance_section_only_when_present(make_result):
    """High variance section is conditional — empty when all metrics are tight."""
    # 5 tight runs around the same value → no high-variance metrics.
    tight = [
        make_result(run_number=i + 1, extraction_success=True,
                    extracted_metrics={"x": 10.0 + i * 0.0001})
        for i in range(5)
    ]
    text = generate_report(tight)
    assert "HIGH VARIANCE METRICS" not in text


def test_generate_report_lists_high_variance_metrics_when_present(make_result):
    spread = [10.0, 50.0, 100.0, 5.0, 90.0]
    runs = [
        make_result(run_number=i + 1, extraction_success=True,
                    extracted_metrics={"jumpy": v})
        for i, v in enumerate(spread)
    ]
    text = generate_report(runs)
    assert "HIGH VARIANCE METRICS" in text
    assert "jumpy" in text


def test_format_prompt_section_handles_empty_metrics(failed_results):
    """When every run failed, the per-prompt section reports 'No metrics
    extracted.' rather than crashing on empty stats."""
    all_stats = analyze_all_results(failed_results)
    pstats = all_stats["cycle_time"]
    lines = format_prompt_section(pstats)
    joined = "\n".join(lines)
    assert "No metrics extracted." in joined


def test_format_metric_line_high_variance_marker():
    """The yellow CV warning marker shows up on > 20% CV."""
    m = calculate_metric_stats("noisy", [10.0, 50.0, 100.0, 5.0, 90.0])
    assert m.is_high_variance
    line = format_metric_line(m)
    assert "HIGH VARIANCE" in line


def test_format_metric_line_no_high_variance_marker_when_tight():
    m = calculate_metric_stats("steady", [10.0, 10.05, 10.0, 10.02, 10.01])
    assert not m.is_high_variance
    line = format_metric_line(m)
    assert "HIGH VARIANCE" not in line


def test_generate_summary_table_returns_rich_table(successful_results):
    table = generate_summary_table(calculate_summary(successful_results))
    # Render to a string to confirm Rich didn't choke on the data.
    console = Console(record=True, width=120)
    console.print(table)
    out = console.export_text()
    assert "Analysis Summary" in out
    assert "Total Runs" in out
    assert "Successful" in out


def test_generate_executive_summary_includes_cycle_time_if_present(successful_results):
    text = generate_executive_summary(successful_results)
    # The cycle_time prompt is the most user-facing.
    assert "Cycle Time" in text
    # Cost line at the bottom.
    assert "Estimated cost" in text


def test_generate_executive_summary_handles_empty_results():
    text = generate_executive_summary([])
    assert "EXECUTIVE SUMMARY" in text
    assert "Analysis based on 0 successful runs" in text
