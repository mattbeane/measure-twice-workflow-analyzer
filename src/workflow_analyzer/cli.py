"""Measure Twice, Spend Once — CLI.

Commands:
    mtso configure              Set up your API key and defaults (run this first)
    mtso analyze <file>         Run the Monte Carlo analysis on a workflow file
    mtso corpus <session-id>    Re-export corpus.csv / corpus.json from a saved run
    mtso list-sessions          Browse past runs
    mtso show <session-id>      Re-inspect a past run
    mtso prompts                List the analysis prompts
"""

import asyncio
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table

# Backward-compat: still load a local .env if present (older setups).
_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env", override=False)
load_dotenv(override=False)

from .prompts import ALL_PROMPTS, PROCESS_PROMPTS, SKILL_PROMPTS
from .runner import WorkflowAnalyzer, RunConfig, RunProgress
from .storage import AnalysisStorage
from .stats import analyze_all_results, calculate_summary
from .report import generate_report, generate_summary_table
from .dashboard import render_dashboard
from . import config as user_config
from . import cost as cost_mod
from . import corpus as corpus_mod

app = typer.Typer(
    name="mtso",
    help="Measure Twice, Spend Once — Monte Carlo workflow analysis using AI.",
    no_args_is_help=True,
)
console = Console()

QUICK_RUNS = 10  # facilitator demo / smoke-test depth


# ---------------------------------------------------------------------------
# configure
# ---------------------------------------------------------------------------
@app.command()
def configure(
    show: bool = typer.Option(False, "--show", help="Show current config and exit"),
):
    """Set up your Anthropic API key and defaults. Run this once before analyzing."""
    cfg = user_config.load_config()

    if show:
        console.print(Panel.fit(
            f"[bold]Config:[/] {user_config.CONFIG_PATH}\n"
            f"API key: {'set' if user_config.has_api_key() else '[red]not set[/]'}\n"
            f"Default runs: {cfg['default_runs']}\n"
            f"Default budget: ${cfg['default_budget_usd']}\n"
            f"Model: {cfg['model']}",
            title="Measure Twice, Spend Once",
        ))
        return

    console.print("\n[bold]Measure Twice, Spend Once — setup[/]\n")
    console.print("Your API key is stored locally at "
                  f"[cyan]{user_config.CONFIG_PATH}[/] (mode 600).")
    console.print("It is used to call Anthropic directly from your machine. "
                  "[bold]Nothing is sent to the tool authors.[/]\n")

    existing = "set" if user_config.has_api_key() else "not set"
    api_key = typer.prompt(
        f"Anthropic API key (currently {existing}; press Enter to keep)",
        default="", show_default=False, hide_input=True,
    )

    runs = typer.prompt("Default runs per prompt", default=cfg["default_runs"], type=int)
    budget = typer.prompt("Default budget per run (USD)", default=cfg["default_budget_usd"], type=float)

    updates = {"default_runs": runs, "default_budget_usd": budget}
    if api_key.strip():
        updates["api_key"] = api_key.strip()

    path = user_config.save_config(updates)
    console.print(f"\n[green]Saved[/] → {path}")
    if not user_config.has_api_key():
        console.print("[yellow]No API key set.[/] Set one with `mtso configure`, or export "
                      "ANTHROPIC_API_KEY before running `mtso analyze`.")


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------
@app.command()
def analyze(
    workflow_file: Path = typer.Argument(..., help="Path to workflow data file", exists=True),
    runs: Optional[int] = typer.Option(None, "--runs", "-r", help="Runs per prompt (default: from config, 1000)"),
    quick: bool = typer.Option(False, "--quick", help=f"Fast demo run ({QUICK_RUNS} runs/prompt)"),
    budget: Optional[float] = typer.Option(None, "--budget", help="Hard spend ceiling in USD"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the cost confirmation prompt"),
    prompts: Optional[str] = typer.Option(None, "--prompts", "-p", help="Comma-separated prompt IDs (default: all)"),
    process_only: bool = typer.Option(False, "--process-only", help="Only process-analysis prompts"),
    skill_only: bool = typer.Option(False, "--skill-only", help="Only skill-development prompts"),
    out_dir: Optional[Path] = typer.Option(None, "--out-dir", "-o", help="Output directory for corpus + report (default: <file>-analysis/)"),
    no_corpus: bool = typer.Option(False, "--no-corpus", help="Skip corpus.csv / corpus.json export"),
    db: Path = typer.Option("workflow_analysis.db", "--db", help="Session database path"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name for this run"),
    dashboard: bool = typer.Option(False, "--dashboard", "-d", help="Show the terminal dashboard after"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
):
    """Analyze a workflow file with Monte Carlo LLM analysis and export a corpus."""
    cfg = user_config.load_config()

    if not user_config.has_api_key():
        console.print("[red]No API key found.[/] Run [bold]mtso configure[/] first "
                      "(or export ANTHROPIC_API_KEY).")
        raise typer.Exit(1)

    workflow_data = workflow_file.read_text()

    # Resolve N: --quick > --runs > config default
    if quick:
        n_runs = QUICK_RUNS
    elif runs is not None:
        n_runs = runs
    else:
        n_runs = int(cfg["default_runs"])

    # Which prompts
    prompt_ids = None
    if prompts:
        prompt_ids = [p.strip() for p in prompts.split(",")]
    elif process_only:
        prompt_ids = [p.id for p in PROCESS_PROMPTS]
    elif skill_only:
        prompt_ids = [p.id for p in SKILL_PROMPTS]
    n_prompts = len(prompt_ids) if prompt_ids else len(ALL_PROMPTS)

    # Cost estimate + budget confirmation
    est = cost_mod.estimate(n_prompts, n_runs, len(workflow_data))
    if not quiet:
        console.print(Panel.fit(
            f"[bold]Measure Twice, Spend Once[/]\n"
            f"Input: {workflow_file}  ({len(workflow_data):,} chars)\n"
            f"{est.summary_line()}",
            border_style="blue",
        ))

    resolved_budget = budget
    if resolved_budget is None and not yes:
        # Prompt the user to set/confirm a budget. Default = config ($50).
        default_budget = float(cfg["default_budget_usd"])
        resolved_budget = typer.prompt(
            "Set a budget ceiling for this run in USD (0 = no cap)",
            default=default_budget, type=float,
        )
    elif resolved_budget is None and yes:
        resolved_budget = float(cfg["default_budget_usd"])

    if resolved_budget == 0:
        resolved_budget = None  # explicit no-cap

    if not yes and not quiet:
        cap = f"${resolved_budget:.0f}" if resolved_budget else "no cap"
        if not typer.confirm(f"Proceed? (budget: {cap})", default=True):
            raise typer.Exit(0)

    # Run
    config = RunConfig(
        workflow_data=workflow_data,
        runs_per_prompt=n_runs,
        prompt_ids=prompt_ids,
        budget_usd=resolved_budget,
    )
    analyzer = WorkflowAnalyzer()

    async def run_with_progress():
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TaskProgressColumn(), TimeElapsedColumn(),
            console=console, disable=quiet,
        ) as bar:
            task = bar.add_task("Analyzing...", total=est.max_runs)

            def update(p: RunProgress):
                bar.update(task, completed=p.completed_calls,
                           description=f"Analyzing... (${p.spent_usd:.2f})")
            return await analyzer.analyze(config, update)

    results = asyncio.run(run_with_progress())

    if not results:
        console.print("[red]No results produced.[/] Check your API key and connection.")
        raise typer.Exit(1)

    summary = calculate_summary(results)

    # Persist session
    storage = AnalysisStorage(str(db))
    session_id = storage.create_session(
        workflow_data=workflow_data, runs_per_prompt=n_runs,
        results=results, workflow_name=name or workflow_file.stem,
    )

    # Output directory
    target_dir = out_dir or workflow_file.parent / f"{workflow_file.stem}-analysis"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Report
    (target_dir / "report.md").write_text(generate_report(results))

    # Corpus — the canonical hand-off artifact
    corpus_paths = None
    if not no_corpus:
        corpus_paths = corpus_mod.export(results, target_dir, name or workflow_file.stem)

    if not quiet:
        console.print(f"\n[green]Done.[/] Session {session_id} · "
                      f"{summary.total_successful}/{summary.total_runs} runs · "
                      f"actual cost ${summary.total_cost_estimate:.2f}")
        if resolved_budget and summary.total_cost_estimate >= resolved_budget * 0.99:
            console.print(f"[yellow]Budget ceiling (${resolved_budget:.0f}) reached — "
                          f"run stopped early. Results reflect partial sampling.[/]")
        console.print(f"  report:  {target_dir / 'report.md'}")
        if corpus_paths:
            console.print(f"  corpus:  {corpus_paths[0]}")
            console.print(f"           {corpus_paths[1]}")
            console.print("\n[dim]Upload corpus.csv to your AI tool to build your brief.[/]")

    if dashboard:
        render_dashboard(results, workflow_name=name or workflow_file.stem, console=console)


# ---------------------------------------------------------------------------
# corpus (export from a saved session)
# ---------------------------------------------------------------------------
@app.command()
def corpus(
    session_id: int = typer.Argument(..., help="Session ID to export"),
    out_dir: Path = typer.Option(Path("."), "--out-dir", "-o", help="Output directory"),
    db: Path = typer.Option("workflow_analysis.db", "--db", help="Session database path"),
):
    """Re-export corpus.csv / corpus.json from a previously stored run."""
    storage = AnalysisStorage(str(db))
    session = storage.get_session(session_id)
    if not session:
        console.print(f"[red]Session {session_id} not found in {db}.[/]")
        raise typer.Exit(1)
    results = storage.get_session_results(session_id)
    name = session.get("workflow_name", f"session-{session_id}")
    csv_path, json_path = corpus_mod.export(results, out_dir, name)
    console.print(f"[green]Exported[/] {len(corpus_mod.build_rows(results))} metrics:")
    console.print(f"  {csv_path}")
    console.print(f"  {json_path}")


# ---------------------------------------------------------------------------
# list-sessions
# ---------------------------------------------------------------------------
@app.command(name="list-sessions")
def list_sessions(
    db: Path = typer.Option("workflow_analysis.db", "--db", help="Session database path"),
    limit: int = typer.Option(10, "--limit", "-n", help="How many to show"),
):
    """List recent analysis sessions."""
    storage = AnalysisStorage(str(db))
    sessions = storage.list_sessions(limit)
    if not sessions:
        console.print("[yellow]No sessions found.[/]")
        return

    table = Table(title="Recent Analysis Sessions")
    for col in ("ID", "Name", "Date", "Runs", "Success", "Cost"):
        table.add_column(col, style="cyan" if col == "ID" else None)
    for s in sessions:
        rate = s["successful_runs"] / s["total_runs"] * 100 if s["total_runs"] else 0
        c = cost_mod.cost_of_tokens(s["total_input_tokens"], s["total_output_tokens"])
        table.add_row(str(s["id"]), s["workflow_name"] or "-", s["created_at"][:19],
                      str(s["total_runs"]), f"{rate:.0f}%", f"${c:.2f}")
    console.print(table)


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------
@app.command()
def show(
    session_id: int = typer.Argument(..., help="Session ID to show"),
    db: Path = typer.Option("workflow_analysis.db", "--db", help="Session database path"),
    full: bool = typer.Option(False, "--full", "-f", help="Show full report"),
    dash: bool = typer.Option(False, "--dashboard", "-d", help="Show the dashboard"),
):
    """Show results for a specific session."""
    storage = AnalysisStorage(str(db))
    session = storage.get_session(session_id)
    if not session:
        console.print(f"[red]Session {session_id} not found.[/]")
        raise typer.Exit(1)

    results = storage.get_session_results(session_id)
    if full:
        console.print(generate_report(results))
    elif dash:
        render_dashboard(results, workflow_name=session.get("workflow_name", f"Session {session_id}"), console=console)
    else:
        console.print(generate_summary_table(calculate_summary(results)))
        for prompt_id, stats in analyze_all_results(results).items():
            if stats.n_successful > 0:
                console.print(f"\n[bold]{stats.prompt_title}[/]")
                for metric_name, ms in list(stats.metrics.items())[:3]:
                    console.print(f"  {metric_name}: {ms.mean:.2f} ± {ms.std_dev:.2f}")


# ---------------------------------------------------------------------------
# prompts
# ---------------------------------------------------------------------------
@app.command()
def prompts():
    """List available analysis prompts."""
    table = Table(title="Analysis Prompts")
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
