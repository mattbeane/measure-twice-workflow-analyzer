"""Regression: KeyboardInterrupt mid-run must save whatever already completed.

Pre-hardening, Ctrl-C discarded all results — but Anthropic had already billed
for the runs that finished before the interrupt. The participant lost any
record of what they paid for.

Matt's fix (commit 09c66ee) exposes `analyzer._last_progress_results` so the
CLI can catch the KeyboardInterrupt and persist whatever completed.
"""
from typer.testing import CliRunner

from workflow_analyzer.cli import app


runner = CliRunner()


def test_keyboard_interrupt_persists_completed_runs(
    tmp_path, monkeypatch, isolated_config_dir, successful_results
):
    """Mid-run Ctrl-C → CLI catches it and writes a session with the
    runs that already finished."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and slack and calendar stuff.\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")

    from workflow_analyzer import cli as cli_mod

    class _InterruptingAnalyzer:
        """Pretends 5 runs completed, then raises KeyboardInterrupt to
        simulate Ctrl-C during the in-progress batch."""

        def __init__(self):
            # The CLI reads this attribute after catching KeyboardInterrupt.
            self._last_progress_results = list(successful_results)

        async def analyze(self, config, on_progress=None):
            raise KeyboardInterrupt()

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", _InterruptingAnalyzer)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db)]
    )

    # 1. The user is told it was interrupted, not that it succeeded silently.
    assert "Interrupted" in result.output or "interrupted" in result.output

    # 2. The session was persisted with the completed runs (so the user has a
    # record of what Anthropic billed them for).
    from workflow_analyzer.storage import AnalysisStorage
    sessions = AnalysisStorage(str(db)).list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["total_runs"] == len(successful_results)


def test_interrupt_with_zero_completed_runs_exits_cleanly(
    tmp_path, monkeypatch, isolated_config_dir
):
    """If the user Ctrl-Cs before any run completes, we still don't crash;
    we exit non-zero with a clean message."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and slack and calendar stuff.\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")

    from workflow_analyzer import cli as cli_mod

    class _InstantInterruptAnalyzer:
        def __init__(self):
            self._last_progress_results = []  # nothing finished

        async def analyze(self, config, on_progress=None):
            raise KeyboardInterrupt()

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", _InstantInterruptAnalyzer)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db)]
    )

    assert result.exit_code != 0
    # No raw "KeyboardInterrupt" traceback to the user.
    assert "Traceback" not in result.output
