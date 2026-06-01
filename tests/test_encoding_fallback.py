"""Regression: cp1252 / Latin-1 input must not crash with UnicodeDecodeError.

Hardened in commit 09c66ee — Outlook/Word exports are commonly cp1252, and
the prior `workflow_file.read_text()` default of UTF-8 strict raised a raw
Python traceback that looked like the tool crashed.

The fix in `cli.py` falls back to `errors="replace"` and prints a yellow
note. These tests pin both halves of that contract.
"""
from typer.testing import CliRunner

from workflow_analyzer.cli import app


runner = CliRunner()


def _write_cp1252(path, text: str = "Hi José, the café meeting with D'Souza is at 2pm.") -> None:
    """Write text in cp1252 so the bytes are NOT valid UTF-8 for accented chars."""
    path.write_bytes(text.encode("cp1252"))


def test_cp1252_workflow_file_does_not_raise_unicode_decode_error(
    tmp_path, isolated_config_dir, no_env_api_key, monkeypatch
):
    """Even with no API key set, the file read must happen first and succeed.

    The boundary we're testing is `read_text()` inside `analyze`. The exit
    here will be a clean "No API key found" message, not a UnicodeDecodeError.
    """
    wf = tmp_path / "outlook-export.txt"
    _write_cp1252(wf)

    # We do NOT need a key for this test — we only care that the read succeeds
    # before the key check. The current cli.py checks the key first, so we
    # need to provide one to reach the read path.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")

    # Mock analyzer.analyze to short-circuit before any API call.
    from workflow_analyzer import cli as cli_mod

    class _FakeAnalyzer:
        async def analyze(self, config, on_progress=None):
            return []  # empty results triggers a clean "No results" exit

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", lambda: _FakeAnalyzer())

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app,
        ["analyze", str(wf), "--quick", "--yes", "--db", str(db), "--quiet"],
    )

    # The critical assertion: no UnicodeDecodeError in stderr/stdout, and no
    # raw Python traceback. Either an empty-results clean exit or a successful
    # short-circuit is acceptable.
    assert "UnicodeDecodeError" not in result.output
    assert "Traceback" not in result.output


def test_cp1252_fallback_emits_a_note(tmp_path, isolated_config_dir, monkeypatch):
    """When the file isn't clean UTF-8, the user gets a one-liner heads-up
    so they know the analysis is still useful."""
    wf = tmp_path / "outlook-export.txt"
    _write_cp1252(wf, "Hi José — café meeting with D'Souza at 2pm. " * 10)

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")

    from workflow_analyzer import cli as cli_mod

    class _FakeAnalyzer:
        async def analyze(self, config, on_progress=None):
            return []  # short-circuit

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", lambda: _FakeAnalyzer())

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app,
        ["analyze", str(wf), "--quick", "--yes", "--db", str(db)],
    )

    # The fallback path prints a "wasn't clean UTF-8" note. We assert the
    # substring (not the exact formatting) so we don't couple to Rich styling.
    assert "UTF-8" in result.output or "Outlook" in result.output


def test_utf8_workflow_file_does_not_emit_the_fallback_note(
    tmp_path, isolated_config_dir, monkeypatch
):
    """A clean UTF-8 file goes through the happy path with no scary message."""
    wf = tmp_path / "clean.txt"
    wf.write_text("Hi team. Standup at 10am.\n" * 20, encoding="utf-8")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")

    from workflow_analyzer import cli as cli_mod

    class _FakeAnalyzer:
        async def analyze(self, config, on_progress=None):
            return []

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", lambda: _FakeAnalyzer())

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app,
        ["analyze", str(wf), "--quick", "--yes", "--db", str(db)],
    )
    assert "wasn't clean UTF-8" not in result.output
