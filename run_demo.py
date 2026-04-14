"""One-shot demo runner: analyze sample, save text report + HTML/SVG dashboard."""
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from workflow_analyzer.runner import WorkflowAnalyzer, RunConfig
from workflow_analyzer.report import generate_report
from workflow_analyzer.dashboard import render_dashboard
from workflow_analyzer.storage import AnalysisStorage

load_dotenv(override=True)

OUT = Path("demo-output")
OUT.mkdir(exist_ok=True)

workflow_path = Path("sample_workflow.txt")
workflow_data = workflow_path.read_text()

print(f"Running analysis on {workflow_path} (5 runs per prompt)...")

config = RunConfig(
    workflow_data=workflow_data,
    runs_per_prompt=5,
    prompt_ids=None,
)

analyzer = WorkflowAnalyzer()

def on_progress(p):
    pct = p.completed_calls / p.total_calls * 100 if p.total_calls else 0
    print(f"  {p.completed_calls}/{p.total_calls} ({pct:.0f}%) - {p.calls_per_second:.1f}/s", end="\r")

results = asyncio.run(analyzer.analyze(config, on_progress))
print()

# 1. Text report
report_path = OUT / "sample_run_report.md"
report_path.write_text(generate_report(results))
print(f"✓ Text report: {report_path}")

# 2. HTML dashboard via rich recording
rec_console = Console(record=True, width=140)
render_dashboard(results, workflow_name="Sample: CSV Export Feature Request", console=rec_console)

html_path = OUT / "sample_run_dashboard.html"
rec_console.save_html(str(html_path), inline_styles=True)
print(f"✓ HTML dashboard: {html_path}")

svg_path = OUT / "sample_run_dashboard.svg"
rec_console.save_svg(str(svg_path), title="Workflow Analyzer — Sample Run")
print(f"✓ SVG dashboard: {svg_path}")

# 3. Also persist to DB so it can be re-shown
storage = AnalysisStorage("demo-output/demo.db")
session_id = storage.create_session(
    workflow_data=workflow_data,
    runs_per_prompt=5,
    results=results,
    workflow_name="sample_demo_run",
)
print(f"✓ DB session: demo-output/demo.db (session {session_id})")
