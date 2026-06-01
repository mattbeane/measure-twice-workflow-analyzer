"""Extended CLI coverage: configure interactive flow, show/corpus on a real
session, flag combinations, and the analyze flags not exercised elsewhere.
"""
from typer.testing import CliRunner

from workflow_analyzer.cli import app
from workflow_analyzer.storage import AnalysisStorage


runner = CliRunner()


# ---------------------------------------------------------------------------
# configure — interactive flow
# ---------------------------------------------------------------------------

def test_configure_saves_api_key_and_defaults_from_stdin(
    isolated_config_dir, no_env_api_key
):
    """Pipe through the three Typer prompts: api_key, default_runs,
    default_budget_usd. Verify all three land in the config file."""
    result = runner.invoke(
        app, ["configure"],
        input="sk-ant-test-key-not-real\n777\n25.0\n",
    )
    assert result.exit_code == 0
    assert "Saved" in result.output

    from workflow_analyzer import config
    cfg = config.load_config(isolated_config_dir)
    assert cfg["default_runs"] == 777
    assert cfg["default_budget_usd"] == 25.0
    assert cfg["api_key"] == "sk-ant-test-key-not-real"


def test_configure_blank_key_keeps_existing_value(isolated_config_dir, no_env_api_key):
    """Pressing Enter at the key prompt keeps the previously-saved key."""
    from workflow_analyzer import config
    config.save_config({"api_key": "previously-saved-key"}, isolated_config_dir)
    # Press Enter at the api_key prompt (blank), then accept defaults.
    result = runner.invoke(
        app, ["configure"],
        input="\n\n\n",
    )
    assert result.exit_code == 0
    cfg = config.load_config(isolated_config_dir)
    assert cfg["api_key"] == "previously-saved-key"


def test_configure_warns_when_no_key_is_present(isolated_config_dir, no_env_api_key):
    """If after the interactive flow there's still no key, the user gets
    a yellow callout pointing at how to fix it."""
    result = runner.invoke(
        app, ["configure"],
        input="\n\n\n",
    )
    assert result.exit_code == 0
    assert "No API key set" in result.output


# ---------------------------------------------------------------------------
# show — with a real session in the db
# ---------------------------------------------------------------------------

def _seed_session(db_path, results, name="seed"):
    return AnalysisStorage(str(db_path)).create_session(
        workflow_data="emails and stuff",
        runs_per_prompt=5,
        results=results,
        workflow_name=name,
    )


def test_show_summary_mode_renders(tmp_path, successful_results):
    db = tmp_path / "show.db"
    sid = _seed_session(db, successful_results)
    result = runner.invoke(app, ["show", str(sid), "--db", str(db)])
    assert result.exit_code == 0
    assert "Total Runs" in result.output


def test_show_full_mode_includes_per_prompt_section(tmp_path, successful_results):
    db = tmp_path / "show.db"
    sid = _seed_session(db, successful_results)
    result = runner.invoke(app, ["show", str(sid), "--db", str(db), "--full"])
    assert result.exit_code == 0
    # The full report includes the SUMMARY header that the bare summary
    # mode does not.
    assert "WORKFLOW ANALYSIS REPORT" in result.output


def test_show_dashboard_mode_renders(tmp_path, successful_results):
    db = tmp_path / "show.db"
    sid = _seed_session(db, successful_results)
    result = runner.invoke(
        app, ["show", str(sid), "--db", str(db), "--dashboard"]
    )
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# corpus re-export
# ---------------------------------------------------------------------------

def test_corpus_re_export_writes_both_files(tmp_path, successful_results):
    db = tmp_path / "corpus.db"
    sid = _seed_session(db, successful_results, name="reexport")
    out_dir = tmp_path / "redo"
    result = runner.invoke(
        app, ["corpus", str(sid), "--db", str(db), "--out-dir", str(out_dir)]
    )
    assert result.exit_code == 0
    assert (out_dir / "corpus.csv").exists()
    assert (out_dir / "corpus.json").exists()


# ---------------------------------------------------------------------------
# analyze: --no-corpus, --process-only, --skill-only, --prompts
# ---------------------------------------------------------------------------

def _short_circuit_with(results_factory, monkeypatch):
    from workflow_analyzer import cli as cli_mod

    class _FakeAnalyzer:
        async def analyze(self, config, on_progress=None):
            return results_factory()

    monkeypatch.setattr(cli_mod, "WorkflowAnalyzer", lambda: _FakeAnalyzer())


def test_analyze_no_corpus_skips_csv_export(
    tmp_path, monkeypatch, isolated_config_dir, successful_results
):
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and stuff\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    _short_circuit_with(lambda: successful_results, monkeypatch)

    db = tmp_path / "wf.db"
    out_dir = tmp_path / "wf-analysis"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db),
              "--out-dir", str(out_dir), "--no-corpus"]
    )
    assert result.exit_code == 0
    # Report is still produced; corpus files are not.
    assert (out_dir / "report.md").exists()
    assert not (out_dir / "corpus.csv").exists()
    assert not (out_dir / "corpus.json").exists()


def test_analyze_process_only_uses_only_process_prompts(
    tmp_path, monkeypatch, isolated_config_dir, successful_results
):
    """Verify the cost banner reflects process-only prompt count (8)."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and stuff\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    _short_circuit_with(lambda: successful_results, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db),
              "--process-only"]
    )
    assert result.exit_code == 0
    # 8 prompts × 10 runs = 80 max runs.
    assert "8 prompts" in result.output


def test_analyze_skill_only_uses_only_skill_prompts(
    tmp_path, monkeypatch, isolated_config_dir, successful_results
):
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and stuff\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    _short_circuit_with(lambda: successful_results, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db),
              "--skill-only"]
    )
    assert result.exit_code == 0
    assert "6 prompts" in result.output


def test_analyze_explicit_prompt_ids_via_comma_list(
    tmp_path, monkeypatch, isolated_config_dir, successful_results
):
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and stuff\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    _short_circuit_with(lambda: successful_results, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db),
              "-p", "cycle_time,bottleneck"]
    )
    assert result.exit_code == 0
    assert "2 prompts" in result.output


def test_analyze_with_dashboard_flag_renders(
    tmp_path, monkeypatch, isolated_config_dir, successful_results
):
    """`--dashboard` after the run should render Rich output without crashing."""
    wf = tmp_path / "wf.txt"
    wf.write_text("emails and stuff\n" * 20)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    _short_circuit_with(lambda: successful_results, monkeypatch)

    db = tmp_path / "wf.db"
    result = runner.invoke(
        app, ["analyze", str(wf), "--quick", "--yes", "--db", str(db),
              "--dashboard"]
    )
    assert result.exit_code == 0
