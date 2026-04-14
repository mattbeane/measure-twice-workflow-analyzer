"""Terminal dashboard for workflow analysis results."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .stats import analyze_all_results, calculate_summary, SummaryStats, PromptStats


def make_bar(value: float, max_val: float = 100, width: int = 10,
             fill_char: str = "█", empty_char: str = "░") -> str:
    """Create a simple bar visualization."""
    if max_val == 0:
        return empty_char * width
    filled = int((value / max_val) * width)
    filled = min(filled, width)
    return fill_char * filled + empty_char * (width - filled)


def score_color(score: float) -> str:
    """Get color based on score (0-100)."""
    if score >= 75:
        return "green"
    elif score >= 50:
        return "yellow"
    else:
        return "red"


def confidence_label(std: float, mean: float) -> str:
    """Get confidence label based on coefficient of variation."""
    if mean == 0:
        return "[dim](no data)[/]"
    cv = (std / mean) * 100
    if cv <= 10:
        return "[green]±low[/]"
    elif cv <= 25:
        return "[yellow]±med[/]"
    else:
        return "[red]±high[/]"


def calculate_3c_scores(all_stats: dict[str, PromptStats]) -> dict[str, tuple[float, float]]:
    """Calculate the 3 C scores from individual prompt results. Returns (mean, std)."""
    scores = {
        "challenge": (None, None),
        "complexity": (None, None),
        "connection": (None, None),
        "overall": (None, None)
    }

    # Challenge = average of C1, C2
    c_means, c_stds = [], []
    if "challenge_calibration" in all_stats:
        metrics = all_stats["challenge_calibration"].metrics
        if "challenge_calibration_score" in metrics:
            c_means.append(metrics["challenge_calibration_score"].mean)
            c_stds.append(metrics["challenge_calibration_score"].std_dev)
    if "challenge_continuity" in all_stats:
        metrics = all_stats["challenge_continuity"].metrics
        if "challenge_continuity_score" in metrics:
            c_means.append(metrics["challenge_continuity_score"].mean)
            c_stds.append(metrics["challenge_continuity_score"].std_dev)
    if c_means:
        scores["challenge"] = (sum(c_means) / len(c_means), sum(c_stds) / len(c_stds))

    # Complexity = average of C3, C4
    cx_means, cx_stds = [], []
    if "complexity_exposure" in all_stats:
        metrics = all_stats["complexity_exposure"].metrics
        if "complexity_exposure_score" in metrics:
            cx_means.append(metrics["complexity_exposure_score"].mean)
            cx_stds.append(metrics["complexity_exposure_score"].std_dev)
    if "expert_guidance_quality" in all_stats:
        metrics = all_stats["expert_guidance_quality"].metrics
        if "expert_guidance_score" in metrics:
            cx_means.append(metrics["expert_guidance_score"].mean)
            cx_stds.append(metrics["expert_guidance_score"].std_dev)
    if cx_means:
        scores["complexity"] = (sum(cx_means) / len(cx_means), sum(cx_stds) / len(cx_stds))

    # Connection = average of C5, C6
    cn_means, cn_stds = [], []
    if "relationship_health" in all_stats:
        metrics = all_stats["relationship_health"].metrics
        if "relationship_health_score" in metrics:
            cn_means.append(metrics["relationship_health_score"].mean)
            cn_stds.append(metrics["relationship_health_score"].std_dev)
    if "developmental_trajectory" in all_stats:
        metrics = all_stats["developmental_trajectory"].metrics
        if "developmental_trajectory_score" in metrics:
            cn_means.append(metrics["developmental_trajectory_score"].mean)
            cn_stds.append(metrics["developmental_trajectory_score"].std_dev)
    if cn_means:
        scores["connection"] = (sum(cn_means) / len(cn_means), sum(cn_stds) / len(cn_stds))

    # Overall = geometric mean of 3 Cs
    valid_scores = [(m, s) for m, s in [scores["challenge"], scores["complexity"], scores["connection"]] if m is not None]
    if valid_scores:
        product = 1
        for m, _ in valid_scores:
            product *= max(m, 1)
        overall_mean = product ** (1/len(valid_scores))
        overall_std = sum(s for _, s in valid_scores) / len(valid_scores)
        scores["overall"] = (overall_mean, overall_std)

    return scores


def get_metric(all_stats: dict, prompt_id: str, metric_name: str, default: float = 0) -> tuple[float, float]:
    """Get a metric's mean and std, with defaults."""
    if prompt_id in all_stats and metric_name in all_stats[prompt_id].metrics:
        m = all_stats[prompt_id].metrics[metric_name]
        return (m.mean, m.std_dev)
    return (default, 0)


def render_dashboard(results: list, workflow_name: str = "Workflow Analysis",
                     outcome: str = None, console: Console = None) -> None:
    """Render the full dashboard to the terminal."""
    if console is None:
        console = Console()

    # Calculate all stats
    summary = calculate_summary(results)
    all_stats = analyze_all_results(results)
    c_scores = calculate_3c_scores(all_stats)

    # Get key metrics
    cycle_days, cycle_std = get_metric(all_stats, "cycle_time", "total_cycle_time_days")
    wait_pct, wait_std = get_metric(all_stats, "cycle_time", "wait_time_percent")
    active_pct = 100 - wait_pct
    handoffs, _ = get_metric(all_stats, "handoff", "total_handoffs")
    handoff_delay, _ = get_metric(all_stats, "handoff", "average_delay_hours")
    handoffs_rework, _ = get_metric(all_stats, "handoff", "handoffs_causing_rework")
    handoffs_info_loss, _ = get_metric(all_stats, "handoff", "handoffs_with_info_loss")

    # Bottleneck
    top_bn_days, top_bn_std = get_metric(all_stats, "bottleneck", "top_bottleneck_days")

    # Skill metrics
    edge_hours, _ = get_metric(all_stats, "challenge_calibration", "appropriate_challenge_hours")
    too_easy, _ = get_metric(all_stats, "challenge_calibration", "too_easy_hours")
    too_hard, _ = get_metric(all_stats, "challenge_calibration", "too_hard_hours")
    total_skill_hours = edge_hours + too_easy + too_hard if (edge_hours + too_easy + too_hard) > 0 else 1
    stretch_pct = (edge_hours / total_skill_hours) * 100
    cruise_pct = (too_easy / total_skill_hours) * 100

    # Learning metrics
    learn_by_doing, _ = get_metric(all_stats, "complexity_exposure", "learning_by_doing_instances")
    warmth, _ = get_metric(all_stats, "relationship_health", "warmth_signals")
    graduation, _ = get_metric(all_stats, "developmental_trajectory", "graduation_signals")
    novice_auth, _ = get_metric(all_stats, "developmental_trajectory", "novice_authorship")

    # High variance metrics
    high_var_short = []
    if summary.high_variance_metrics:
        for m in summary.high_variance_metrics[:3]:
            short = m.split(".")[-1][:20]
            high_var_short.append(short)

    # Clear screen
    console.clear()

    # === HEADER ===
    outcome_line = outcome if outcome else f"{cycle_days:.0f} days → analysis complete"
    header = Table(show_header=False, box=box.DOUBLE_EDGE, expand=True, border_style="cyan")
    header.add_column()
    header.add_row(f"[bold white]WORKFLOW ANALYSIS: {workflow_name}[/]")
    header.add_row(f"[bold cyan]{outcome_line}[/]")
    console.print(header)

    # === ROW 1: Process Metrics ===
    row1 = Table(show_header=True, box=box.SQUARE, expand=True)
    row1.add_column("⏱ CYCLE TIME", justify="center", width=26)
    row1.add_column("🎯 EFFICIENCY", justify="center", width=26)
    row1.add_column("📈 SKILL YIELD", justify="center", width=26)

    cycle_bar = make_bar(min(cycle_days, 15), 15, 10)
    cycle_conf = confidence_label(cycle_std, cycle_days)

    row1.add_row(
        f"[cyan]{cycle_bar}[/] {cycle_days:.0f} days\n{cycle_conf}",
        f"Active [green]{make_bar(active_pct, 100, 8)}[/] {active_pct:.0f}%\nWait   [red]{make_bar(wait_pct, 100, 8)}[/] {wait_pct:.0f}%",
        f"Stretch [green]{make_bar(stretch_pct, 100, 8)}[/] {stretch_pct:.0f}%\nCruise  [yellow]{make_bar(cruise_pct, 100, 8)}[/] {cruise_pct:.0f}%"
    )
    console.print(row1)

    # === ROW 2: Bottlenecks & Handoffs ===
    row2 = Table(show_header=True, box=box.SQUARE, expand=True)
    row2.add_column("🚧 BOTTLENECKS", justify="left", width=40)
    row2.add_column("🔄 HANDOFFS", justify="left", width=38)

    bn_bar = make_bar(min(top_bn_days, 5), 5, 6)
    row2.add_row(
        f"Top delay: [red]{bn_bar}[/] {top_bn_days:.1f} days\n[dim](requirements/decisions)[/]",
        f"{handoffs:.0f} total, {handoff_delay:.1f}hr avg delay\n{handoffs_rework:.0f} rework, {handoffs_info_loss:.0f} info loss"
    )
    console.print(row2)

    # === ROW 3: The 3 Cs & Learning ===
    row3 = Table(show_header=True, box=box.SQUARE, expand=True)
    row3.add_column("🎓 THE 3 Cs", justify="left", width=40)
    row3.add_column("🧠 LEARNING CAPTURED", justify="left", width=38)

    def fmt_c(name: str, val: tuple) -> str:
        if val[0] is None:
            return f"{name}: [dim]no data[/]"
        color = score_color(val[0])
        bar = make_bar(val[0], 100, 8)
        return f"{name} [{color}]{bar}[/] {val[0]:.0f}"

    ov_mean, ov_std = c_scores["overall"]
    if ov_mean:
        ov_color = score_color(ov_mean)
        ov_bar = make_bar(ov_mean, 100, 8)
        overall_line = f"[bold]OVERALL  [{ov_color}]{ov_bar}[/] {ov_mean:.0f}[/]"
    else:
        overall_line = "[dim]OVERALL: no data[/]"

    row3.add_row(
        f"{fmt_c('Challenge ', c_scores['challenge'])}\n{fmt_c('Complexity', c_scores['complexity'])}\n{fmt_c('Connection', c_scores['connection'])}\n{overall_line}",
        f"Edge work: [green]{edge_hours:.0f}h[/] (growth zone)\nLearn-by-doing: {learn_by_doing:.0f} instances\nWarmth signals: {warmth:.0f} (trust/care)\nGraduation: {graduation:.0f} (→independence)"
    )
    console.print(row3)

    # === ROW 4: Trajectory & Warnings ===
    row4 = Table(show_header=True, box=box.SQUARE, expand=True)
    row4.add_column("📊 TRAJECTORY", justify="left", width=40)
    row4.add_column("⚠️  VARIANCE", justify="left", width=38)

    trajectory_text = f"Novice authorship: {novice_auth:.0f} instances\nNext challenges: {graduation:.0f} set up\nDirection: [green]→ Positive[/]"

    if high_var_short:
        var_lines = [f"{summary.total_failed} extraction failures"]
        for hv in high_var_short:
            var_lines.append(f"• {hv}")
        if len(summary.high_variance_metrics) > 3:
            var_lines.append(f"[dim]+{len(summary.high_variance_metrics)-3} more[/]")
        variance_text = "\n".join(var_lines)
    else:
        variance_text = "[green]✓ All metrics stable[/]"

    row4.add_row(trajectory_text, variance_text)
    console.print(row4)

    # === FOOTER ===
    footer = f"[dim]{summary.total_successful}/{summary.total_runs} runs  │  ${summary.total_cost_estimate:.3f}  │  {summary.avg_latency_ms/1000:.1f}s avg[/]"
    console.print(f"\n{footer}", justify="center")
