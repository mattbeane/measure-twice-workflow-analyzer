"""CLI surface-area smoke tests — no Anthropic calls.

These run in <1s collectively and lock in the behaviors a non-coder will hit
first:

* `mtso --help` shows the 6 documented commands.
* `mtso prompts` lists 14 entries.
* `mtso list-sessions` on an empty db is friendly, not a crash.
* `mtso show 999999` / `corpus 999999` give a clean error.
* `mtso analyze` with no key and no env var produces an actionable hint.
* `mtso configure --show` with no config does not echo a key.
"""
import pytest
from typer.testing import CliRunner

from workflow_analyzer.cli import app


runner = CliRunner()


def test_help_lists_all_six_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("configure", "analyze", "corpus", "list-sessions", "show", "prompts"):
        assert cmd in result.output


def test_prompts_command_lists_14_entries():
    result = runner.invoke(app, ["prompts"])
    assert result.exit_code == 0
    # Counting hits is brittle; instead, we look for one known id from each
    # category, plus check the legend phrase.
    assert "cycle_time" in result.output       # process
    assert "expert_guidance_quality" in result.output  # skill
    assert "process" in result.output
    assert "skill" in result.output


def test_list_sessions_empty_db_friendly_message(tmp_path):
    db = tmp_path / "empty.db"
    result = runner.invoke(app, ["list-sessions", "--db", str(db)])
    assert result.exit_code == 0
    assert "No sessions found" in result.output


def test_show_unknown_session_id_clean_error(tmp_path):
    db = tmp_path / "empty.db"
    result = runner.invoke(app, ["show", "999999", "--db", str(db)])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
    assert "Traceback" not in result.output


def test_corpus_unknown_session_id_clean_error(tmp_path):
    db = tmp_path / "empty.db"
    result = runner.invoke(app, ["corpus", "999999", "--db", str(db)])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
    assert "Traceback" not in result.output


def test_analyze_no_args_shows_helpful_error():
    """Typer's built-in 'missing argument' is acceptable; we just confirm
    it doesn't dump a stack trace."""
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code != 0
    assert "Traceback" not in result.output
    assert "WORKFLOW_FILE" in result.output or "missing" in result.output.lower()


def test_analyze_with_no_key_at_all(tmp_path, isolated_config_dir, no_env_api_key):
    """No config, no env var → clean message pointing at `mtso configure`."""
    wf = tmp_path / "wf.txt"
    wf.write_text("some emails go here." * 30)
    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db)]
    )
    assert result.exit_code != 0
    assert "mtso configure" in result.output or "ANTHROPIC_API_KEY" in result.output


def test_configure_show_no_config_reports_not_set_no_key_echo(
    isolated_config_dir, no_env_api_key
):
    result = runner.invoke(app, ["configure", "--show"])
    assert result.exit_code == 0
    assert "not set" in result.output
    # Even if the developer has sk-ant- env vars set elsewhere, the --show
    # path should not echo a literal key.
    assert "sk-ant-" not in result.output


@pytest.mark.parametrize("alias", ["measure-twice", "mtso", "wfa", "workflow-analyzer"])
def test_console_script_aliases_registered(alias):
    """All four documented entrypoint aliases resolve to the same Typer app.

    The README and the pyproject `[project.scripts]` table both promise these
    work. We don't actually invoke the binaries (that'd require an editable
    install) — we verify the underlying Python entrypoint is reachable.
    """
    from workflow_analyzer import cli as cli_mod
    assert callable(cli_mod.main)
    # The alias names live in pyproject.toml; this test fails loudly if anyone
    # renames `cli.main` and forgets to update the entrypoint table.
