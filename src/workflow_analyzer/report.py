"""Report generation for analysis results."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table

from .schemas import PromptRunResult
from .stats import (
    analyze_all_results,
    calculate_summary,
    SummaryStats,
    PromptStats,
    MetricStats
)


def generate_summary_table(summary: SummaryStats) -> Table:
    """Generate a rich table with summary statistics."""
    table = Table(title="Analysis Summary", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Total Runs", str(summary.total_runs))
    table.add_row("Successful", f"{summary.total_successful} ({summary.overall_success_rate:.0f}%)")
    table.add_row("Failed", str(summary.total_failed))
    table.add_row("", "")
    table.add_row("Process Prompts", str(summary.process_prompts_run))
    table.add_row("Skill Prompts", str(summary.skill_prompts_run))
    table.add_row("", "")
    table.add_row("Input Tokens", f"{summary.total_input_tokens:,}")
    table.add_row("Output Tokens", f"{summary.total_output_tokens:,}")
    table.add_row("Est. Cost", f"${summary.total_cost_estimate:.3f}")
    table.add_row("Avg Latency", f"{summary.avg_latency_ms:.0f}ms")

    if summary.high_variance_metrics:
        table.add_row("", "")
        table.add_row("[yellow]High Variance[/]", f"{len(summary.high_variance_metrics)} metrics")

    return table


def format_metric_line(metric: MetricStats) -> str:
    """Format a single metric line for text report."""
    ci_low, ci_high = metric.confidence_95
    variance_flag = " ⚠️ HIGH VARIANCE" if metric.is_high_variance else ""

    return (
        f"  {metric.metric_name}:\n"
        f"    Mean: {metric.mean:.2f} ± {metric.std_dev:.2f}\n"
        f"    Range: {metric.min_val:.2f} - {metric.max_val:.2f}\n"
        f"    95% CI: [{ci_low:.2f}, {ci_high:.2f}]\n"
        f"    CV: {metric.coefficient_of_variation:.1f}%{variance_flag}\n"
    )


def generate_report(results: list[PromptRunResult]) -> str:
    """Generate a full text report."""
    summary = calculate_summary(results)
    all_stats = analyze_all_results(results)

    lines = [
        "=" * 80,
        "WORKFLOW ANALYSIS REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
        "",
        "SUMMARY",
        "-" * 40,
        f"Total API Calls: {summary.total_runs}",
        f"Successful: {summary.total_successful} ({summary.overall_success_rate:.0f}%)",
        f"Failed: {summary.total_failed}",
        f"Process Prompts: {summary.process_prompts_run}",
        f"Skill Prompts: {summary.skill_prompts_run}",
        f"Estimated Cost: ${summary.total_cost_estimate:.3f}",
        "",
    ]

    if summary.high_variance_metrics:
        lines.extend([
            "⚠️  HIGH VARIANCE METRICS (CV > 20%):",
            *[f"  - {m}" for m in summary.high_variance_metrics[:10]],
            "",
        ])

    # Process prompts
    lines.extend([
        "=" * 80,
        "PROCESS ANALYSIS RESULTS",
        "=" * 80,
        "",
    ])

    process_ids = ["cycle_time", "bottleneck", "handoff", "decision",
                   "value_waste", "information_flow", "exception", "approval"]

    for pid in process_ids:
        if pid in all_stats:
            stats = all_stats[pid]
            lines.extend(format_prompt_section(stats))

    # Skill prompts
    lines.extend([
        "=" * 80,
        "SKILL DEVELOPMENT ANALYSIS RESULTS",
        "=" * 80,
        "",
    ])

    # 3 Cs Framework: Challenge, Complexity, Connection
    skill_ids = ["challenge_calibration", "challenge_continuity",
                 "complexity_exposure", "expert_guidance_quality",
                 "relationship_health", "developmental_trajectory"]

    for pid in skill_ids:
        if pid in all_stats:
            stats = all_stats[pid]
            lines.extend(format_prompt_section(stats))

    return "\n".join(lines)


def format_prompt_section(stats: PromptStats) -> list[str]:
    """Format a section for a single prompt."""
    lines = [
        f"### {stats.prompt_title}",
        f"Runs: {stats.n_successful}/{stats.n_runs} successful ({stats.success_rate:.0f}%)",
        "",
    ]

    if not stats.metrics:
        lines.append("  No metrics extracted.\n")
        return lines

    # Group metrics by type for cleaner display
    for metric_name, metric_stats in sorted(stats.metrics.items()):
        lines.append(format_metric_line(metric_stats))

    lines.append("")
    return lines


def generate_executive_summary(results: list[PromptRunResult]) -> str:
    """Generate a brief executive summary of key findings."""
    summary = calculate_summary(results)
    all_stats = analyze_all_results(results)

    lines = [
        "EXECUTIVE SUMMARY",
        "=" * 40,
        "",
    ]

    # Key process metrics
    if "cycle_time" in all_stats and all_stats["cycle_time"].metrics:
        ct = all_stats["cycle_time"]
        if "total_cycle_time_days" in ct.metrics:
            m = ct.metrics["total_cycle_time_days"]
            lines.append(f"📊 Cycle Time: {m.mean:.1f} ± {m.std_dev:.1f} days")

        if "wait_time_percent" in ct.metrics:
            m = ct.metrics["wait_time_percent"]
            lines.append(f"⏳ Wait Time: {m.mean:.0f}% ± {m.std_dev:.0f}%")

        if "handoff_count" in ct.metrics:
            m = ct.metrics["handoff_count"]
            lines.append(f"🔄 Handoffs: {m.mean:.0f} ± {m.std_dev:.0f}")

    # Key skill metrics
    if "collaboration" in all_stats and all_stats["collaboration"].metrics:
        collab = all_stats["collaboration"]
        if "cross_level_mentoring_count" in collab.metrics:
            m = collab.metrics["cross_level_mentoring_count"]
            lines.append(f"👥 Mentoring Instances: {m.mean:.0f} ± {m.std_dev:.0f}")

        if "high_skill_yield_percent" in collab.metrics:
            m = collab.metrics["high_skill_yield_percent"]
            lines.append(f"🎯 High Skill Yield: {m.mean:.0f}% ± {m.std_dev:.0f}%")

    lines.extend([
        "",
        f"Analysis based on {summary.total_successful} successful runs across {summary.process_prompts_run + summary.skill_prompts_run} prompts.",
        f"Estimated cost: ${summary.total_cost_estimate:.3f}",
    ])

    if summary.high_variance_metrics:
        lines.extend([
            "",
            f"⚠️  {len(summary.high_variance_metrics)} metrics showed high variance (>20% CV) - results for these should be interpreted with caution.",
        ])

    return "\n".join(lines)
