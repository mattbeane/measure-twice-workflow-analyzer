"""dashboard.py — Rich-rendered terminal dashboard.

We don't test the visual output, just that:
* Helpers (`make_bar`, `score_color`, `confidence_label`) behave at boundaries.
* `render_dashboard` doesn't raise on representative input.
"""
from rich.console import Console

from workflow_analyzer.dashboard import (
    confidence_label,
    make_bar,
    render_dashboard,
    score_color,
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def test_make_bar_full_when_at_max():
    assert make_bar(100, max_val=100, width=10) == "█" * 10


def test_make_bar_empty_when_zero():
    assert make_bar(0, max_val=100, width=10) == "░" * 10


def test_make_bar_clamps_when_value_exceeds_max():
    # No errors, no overflow beyond width.
    out = make_bar(200, max_val=100, width=8)
    assert len(out) == 8
    assert out == "█" * 8


def test_make_bar_zero_max_returns_all_empty():
    # Guard against ZeroDivisionError.
    assert make_bar(50, max_val=0, width=5) == "░" * 5


def test_score_color_thresholds():
    assert score_color(80) == "green"
    assert score_color(75) == "green"   # boundary
    assert score_color(60) == "yellow"
    assert score_color(50) == "yellow"  # boundary
    assert score_color(20) == "red"


def test_confidence_label_zero_mean_returns_no_data():
    # Otherwise we'd hit a ZeroDivisionError in CV calculation.
    assert "no data" in confidence_label(std=1.0, mean=0).lower()


def test_confidence_label_low_cv_is_green_low():
    # CV = 5/100 = 5% → "low" variance (green).
    out = confidence_label(std=5.0, mean=100.0)
    assert "low" in out.lower()
    assert "green" in out.lower()


def test_confidence_label_high_cv_is_red_high():
    out = confidence_label(std=50.0, mean=100.0)
    assert "high" in out.lower()
    assert "red" in out.lower()


# ---------------------------------------------------------------------------
# render_dashboard end-to-end (smoke)
# ---------------------------------------------------------------------------

def test_render_dashboard_does_not_raise_on_successful_results(successful_results):
    console = Console(record=True, width=140)
    render_dashboard(successful_results, workflow_name="t", console=console)
    out = console.export_text()
    assert out  # produced some output


def test_render_dashboard_handles_only_failures(failed_results):
    """Even when nothing extracted, the dashboard must render without
    raising — that's what a workshop participant will sometimes see."""
    console = Console(record=True, width=140)
    render_dashboard(failed_results, workflow_name="all-failed", console=console)
    out = console.export_text()
    assert out


def test_render_dashboard_mixed_results(successful_results, failed_results):
    console = Console(record=True, width=140)
    render_dashboard(successful_results + failed_results,
                     workflow_name="mixed", console=console)
    out = console.export_text()
    assert out
