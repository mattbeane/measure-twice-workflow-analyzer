"""Regression: never report a cheerful "Done" over a pile of failed calls.

Pre-hardening, a key with zero balance / a typo / an empty workflow would
produce 140 failed API calls and the CLI would still print "Done. Session 1 ·
0/140 runs · actual cost $0.00" with exit 0. Newbie conclusion: "I broke it."

The fix surfaces the actual error count and adds a remediation hint when more
than half the calls failed.
"""
from typer.testing import CliRunner

from workflow_analyzer.cli import app


runner = CliRunner()


def _short_circuit_with(results_factory, monkeypatch):
    """Replace `WorkflowAnalyzer` with one that returns whatever the factory
    builds, so we exercise the CLI summary path without any real API call."""
    from workflow_analyzer import cli as cli_mod

    class _FakeAnalyzer:
        async def analyze(self, config, on_progress=None):
            return results_factory()

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", lambda: _FakeAnalyzer())


def test_zero_results_exits_non_zero_and_surfaces_actionable_error(
    tmp_path, monkeypatch, isolated_config_dir
):
    """No results at all (e.g. bad key, all failed before list was populated)
    must exit non-zero and tell the user where to check."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and slack and calendar stuff.\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    _short_circuit_with(lambda: [], monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db)]
    )
    assert result.exit_code != 0
    # Actionable: the message points the user at a thing to check.
    assert "API key" in result.output or "balance" in result.output


def test_partial_failure_summary_appears_when_some_calls_fail(
    tmp_path, monkeypatch, isolated_config_dir, successful_results, failed_results
):
    """Mixed run (e.g. rate-limit on a new account): the count of failures
    must surface so the user knows the results are thin."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and slack and calendar stuff.\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    mixed = successful_results + failed_results
    _short_circuit_with(lambda: mixed, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db)]
    )
    # We don't assert exit code (mixed runs still produce a session); we
    # assert the user sees the failure count.
    assert "3" in result.output
    assert "failed" in result.output.lower()


def test_over_half_failed_triggers_extra_remediation_hint(
    tmp_path, monkeypatch, isolated_config_dir, make_result
):
    """When >= 50% of calls failed, the CLI prints a louder hint about likely
    causes (rate limits, no balance)."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and slack and calendar stuff.\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")

    # 2 succeeded, 8 failed → 80% failure
    results = [make_result(run_number=i, extraction_success=True,
                           extracted_metrics={"x": 1.0}) for i in range(2)]
    results += [make_result(run_number=i, extraction_success=False,
                            extracted_metrics=None,
                            error_message="rate limit") for i in range(8)]
    _short_circuit_with(lambda: results, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db)]
    )
    # The fix in cli.py mentions "rate limits" or "API balance" specifically
    # for the high-failure case. We look for either keyword.
    low = result.output.lower()
    assert ("rate limit" in low) or ("balance" in low) or ("thin" in low)


def test_quiet_mode_suppresses_the_human_summary(
    tmp_path, monkeypatch, isolated_config_dir, successful_results, failed_results
):
    """`--quiet` is for scripts. The yellow human-readable failure note is
    gated on `not quiet`, so we confirm it's silent in quiet mode."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and slack and calendar stuff.\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    mixed = successful_results + failed_results
    _short_circuit_with(lambda: mixed, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db), "--quiet"]
    )
    # In --quiet mode the human-friendly "N of M calls failed" line is
    # suppressed. We assert the loud phrasing is absent.
    assert "calls failed" not in result.output
