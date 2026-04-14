"""CLI for workflow analysis tool."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import typer
from rich.console import Console

# Load .env file - override=True ensures it overwrites empty env vars
_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env", override=True)
load_dotenv(override=True)  # Also check current working directory
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text

from .prompts import ALL_PROMPTS, PROCESS_PROMPTS, SKILL_PROMPTS
from .runner import WorkflowAnalyzer, RunConfig, RunProgress
from .storage import AnalysisStorage
from .stats import analyze_all_results, calculate_summary
from .report import generate_report, generate_summary_table
from .dashboard import render_dashboard

app = typer.Typer(
    name="workflow-analyzer",
    help="Monte Carlo style workflow analysis using LLMs"
)
console = Console()


def create_progress_display(progress: RunProgress) -> Panel:
    """Create a rich panel showing current progress."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="bold")
    table.add_column("Value")

    pct = progress.completed_calls / progress.total_calls * 100 if progress.total_calls > 0 else 0

    table.add_row("Progress", f"{progress.completed_calls}/{progress.total_calls} ({pct:.0f}%)")
    table.add_row("Successful", f"{progress.completed_calls - progress.failed_calls}")
    table.add_row("Failed", f"{progress.failed_calls}")
    table.add_row("Speed", f"{progress.calls_per_second:.1f} calls/sec")
    table.add_row("Elapsed", f"{progress.elapsed_seconds:.1f}s")

    # Estimate remaining time
    if progress.calls_per_second > 0:
        remaining = (progress.total_calls - progress.completed_calls) / progress.calls_per_second
        table.add_row("ETA", f"{remaining:.0f}s")

    return Panel(table, title="[bold blue]Analysis Progress[/]", border_style="blue")


@app.command()
def analyze(
    workflow_file: Path = typer.Argument(
        ...,
        help="Path to workflow data file (text/markdown)",
        exists=True
    ),
    runs: int = typer.Option(
        5,
        "--runs", "-r",
        help="Number of runs per prompt (default 5)"
    ),
    prompts: Optional[str] = typer.Option(
        None,
        "--prompts", "-p",
        help="Comma-separated prompt IDs to run (default: all)"
    ),
    process_only: bool = typer.Option(
        False,
        "--process-only",
        help="Only run process analysis prompts"
    ),
    skill_only: bool = typer.Option(
        False,
        "--skill-only",
        help="Only run skill development prompts"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file for report (default: stdout)"
    ),
    db: Path = typer.Option(
        "workflow_analysis.db",
        "--db",
        help="Database file path"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Name for this analysis session"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet", "-q",
        help="Minimal output"
    ),
    dashboard: bool = typer.Option(
        False,
        "--dashboard", "-d",
        help="Show visual dashboard after analysis"
    )
):
    """
    Analyze a workflow data file using Monte Carlo LLM analysis.

    Runs each analysis prompt multiple times and aggregates results
    with statistics showing variance and confidence intervals.
    """
    # Read workflow data
    workflow_data = workflow_file.read_text()

    if not quiet:
        console.print(f"\n[bold]Workflow Analyzer[/] - Monte Carlo Analysis")
        console.print(f"Input: {workflow_file}")
        console.print(f"Runs per prompt: {runs}")

    # Determine which prompts to run
    prompt_ids = None
    if prompts:
        prompt_ids = [p.strip() for p in prompts.split(",")]
    elif process_only:
        prompt_ids = [p.id for p in PROCESS_PROMPTS]
    elif skill_only:
        prompt_ids = [p.id for p in SKILL_PROMPTS]

    if prompt_ids:
        n_prompts = len(prompt_ids)
    else:
        n_prompts = len(ALL_PROMPTS)
        prompt_ids = None  # None means all

    total_calls = n_prompts * runs

    if not quiet:
        console.print(f"Total API calls: {total_calls}")
        console.print()

    # Run analysis with progress display
    config = RunConfig(
        workflow_data=workflow_data,
        runs_per_prompt=runs,
        prompt_ids=prompt_ids
    )

    analyzer = WorkflowAnalyzer()

    # Progress tracking with live display
    last_progress = [None]  # Use list to allow mutation in closure

    def on_progress(progress: RunProgress):
        last_progress[0] = progress

    async def run_with_progress():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=quiet
        ) as progress_bar:
            task = progress_bar.add_task("Analyzing...", total=total_calls)

            def update_progress(p: RunProgress):
                on_progress(p)
                progress_bar.update(task, completed=p.completed_calls)

            return await analyzer.analyze(config, update_progress)

    results = asyncio.run(run_with_progress())

    # Store results
    storage = AnalysisStorage(str(db))
    session_id = storage.create_session(
        workflow_data=workflow_data,
        runs_per_prompt=runs,
        results=results,
        workflow_name=name or workflow_file.stem
    )

    if not quiet:
        console.print(f"\n[green]Analysis complete![/] Session ID: {session_id}")

    # Generate and display report
    report = generate_report(results)
    summary = calculate_summary(results)

    if output:
        output.write_text(report)
        if not quiet:
            console.print(f"Report saved to: {output}")
    elif dashboard:
        # Show visual dashboard
        workflow_title = name or workflow_file.stem
        render_dashboard(results, workflow_name=workflow_title, console=console)
    else:
        console.print()
        console.print(generate_summary_table(summary))
        console.print()

        # Show key metrics
        all_stats = analyze_all_results(results)

        for prompt_id, stats in all_stats.items():
            if stats.n_successful > 0:
                console.print(f"\n[bold]{stats.prompt_title}[/] ({stats.n_successful}/{stats.n_runs} successful)")

                # Show top metrics
                for metric_name, metric_stats in list(stats.metrics.items())[:5]:
                    variance_flag = " [yellow]⚠ HIGH VAR[/]" if metric_stats.is_high_variance else ""
                    console.print(
                        f"  {metric_name}: "
                        f"[cyan]{metric_stats.mean:.2f}[/] "
                        f"± {metric_stats.std_dev:.2f} "
                        f"(range: {metric_stats.min_val:.2f}-{metric_stats.max_val:.2f})"
                        f"{variance_flag}"
                    )


@app.command()
def list_sessions(
    db: Path = typer.Option(
        "workflow_analysis.db",
        "--db",
        help="Database file path"
    ),
    limit: int = typer.Option(
        10,
        "--limit", "-n",
        help="Number of sessions to show"
    )
):
    """List recent analysis sessions."""
    storage = AnalysisStorage(str(db))
    sessions = storage.list_sessions(limit)

    if not sessions:
        console.print("[yellow]No sessions found.[/]")
        return

    table = Table(title="Recent Analysis Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Date")
    table.add_column("Runs")
    table.add_column("Success Rate")
    table.add_column("Cost Est.")

    for s in sessions:
        success_rate = s["successful_runs"] / s["total_runs"] * 100 if s["total_runs"] > 0 else 0
        cost = (s["total_input_tokens"] * 0.25 + s["total_output_tokens"] * 1.25) / 1_000_000

        table.add_row(
            str(s["id"]),
            s["workflow_name"] or "-",
            s["created_at"][:19],
            str(s["total_runs"]),
            f"{success_rate:.0f}%",
            f"${cost:.3f}"
        )

    console.print(table)


@app.command()
def show(
    session_id: int = typer.Argument(..., help="Session ID to show"),
    db: Path = typer.Option(
        "workflow_analysis.db",
        "--db",
        help="Database file path"
    ),
    full: bool = typer.Option(
        False,
        "--full", "-f",
        help="Show full report"
    ),
    dash: bool = typer.Option(
        False,
        "--dashboard", "-d",
        help="Show visual dashboard"
    )
):
    """Show results for a specific session."""
    storage = AnalysisStorage(str(db))
    session = storage.get_session(session_id)

    if not session:
        console.print(f"[red]Session {session_id} not found.[/]")
        raise typer.Exit(1)

    results = storage.get_session_results(session_id)

    if full:
        report = generate_report(results)
        console.print(report)
    elif dash:
        workflow_name = session.get("workflow_name", f"Session {session_id}")
        render_dashboard(results, workflow_name=workflow_name, console=console)
    else:
        summary = calculate_summary(results)
        console.print(generate_summary_table(summary))

        all_stats = analyze_all_results(results)
        for prompt_id, stats in all_stats.items():
            if stats.n_successful > 0:
                console.print(f"\n[bold]{stats.prompt_title}[/]")
                for metric_name, metric_stats in list(stats.metrics.items())[:3]:
                    console.print(
                        f"  {metric_name}: {metric_stats.mean:.2f} ± {metric_stats.std_dev:.2f}"
                    )


@app.command()
def prompts():
    """List available analysis prompts."""
    table = Table(title="Available Analysis Prompts")
    table.add_column("ID", style="cyan")
    table.add_column("Category")
    table.add_column("Title")

    for p in PROCESS_PROMPTS:
        table.add_row(p.id, "[blue]process[/]", p.title)

    for p in SKILL_PROMPTS:
        table.add_row(p.id, "[green]skill[/]", p.title)

    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
