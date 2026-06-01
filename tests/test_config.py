"""User config: defaults, file persistence, API key resolution order, mode 600.

`docs/privacy.md` line 12 promises: "Stored locally at
`~/.config/measure-twice/config.toml`, file permissions locked to your user
(mode 600)." That promise is tested here.
"""
import os
import stat

import pytest

from workflow_analyzer import config


# ---------------------------------------------------------------------------
# load_config defaults
# ---------------------------------------------------------------------------

def test_load_config_missing_file_returns_defaults(isolated_config_dir):
    cfg = config.load_config(isolated_config_dir)
    assert cfg["default_runs"] == 1000
    assert cfg["default_budget_usd"] == 50.0
    assert cfg["model"] == "claude-haiku-4-5"


def test_load_config_user_overrides_take_precedence(isolated_config_dir):
    isolated_config_dir.parent.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.write_text(
        'default_runs = 30\n'
        'default_budget_usd = 5.0\n'
        'model = "claude-opus-4-1"\n'
    )
    cfg = config.load_config(isolated_config_dir)
    assert cfg["default_runs"] == 30
    assert cfg["default_budget_usd"] == 5.0
    assert cfg["model"] == "claude-opus-4-1"


def test_load_config_ignores_comments_and_blank_lines(isolated_config_dir):
    isolated_config_dir.parent.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.write_text(
        '# preamble\n'
        '\n'
        'default_runs = 7\n'
        '\n'
        '# trailing comment\n'
    )
    cfg = config.load_config(isolated_config_dir)
    assert cfg["default_runs"] == 7


# ---------------------------------------------------------------------------
# save_config
# ---------------------------------------------------------------------------

def test_save_config_writes_file_and_returns_path(isolated_config_dir):
    out = config.save_config({"default_runs": 12}, isolated_config_dir)
    assert out == isolated_config_dir
    assert isolated_config_dir.exists()


def test_saved_config_round_trips(isolated_config_dir):
    config.save_config(
        {"default_runs": 33, "default_budget_usd": 2.5}, isolated_config_dir
    )
    cfg = config.load_config(isolated_config_dir)
    assert cfg["default_runs"] == 33
    assert cfg["default_budget_usd"] == 2.5


@pytest.mark.skipif(
    os.name != "posix",
    reason="mode 600 promise is POSIX-specific; Windows has its own ACL model",
)
def test_saved_config_is_mode_600(isolated_config_dir):
    # docs/privacy.md line 12: "file permissions locked to your user (mode 600)"
    config.save_config({"default_runs": 1, "api_key": "test-value-not-real"},
                       isolated_config_dir)
    mode = isolated_config_dir.stat().st_mode & 0o777
    assert mode == 0o600, f"expected 0o600, got 0o{mode:o}"


def test_save_config_merges_existing_keys(isolated_config_dir):
    config.save_config({"default_runs": 1}, isolated_config_dir)
    config.save_config({"default_budget_usd": 99.0}, isolated_config_dir)
    cfg = config.load_config(isolated_config_dir)
    assert cfg["default_runs"] == 1
    assert cfg["default_budget_usd"] == 99.0


# ---------------------------------------------------------------------------
# resolve_api_key precedence: explicit > env > file
# ---------------------------------------------------------------------------

def test_resolve_explicit_argument_wins(isolated_config_dir, monkeypatch, no_env_api_key):
    config.save_config({"api_key": "from-file"}, isolated_config_dir)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    assert config.resolve_api_key(
        explicit="from-explicit", path=isolated_config_dir
    ) == "from-explicit"


def test_resolve_env_beats_file(isolated_config_dir, monkeypatch, no_env_api_key):
    config.save_config({"api_key": "from-file"}, isolated_config_dir)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    assert config.resolve_api_key(path=isolated_config_dir) == "from-env"


def test_resolve_file_when_no_env(isolated_config_dir, no_env_api_key):
    config.save_config({"api_key": "from-file"}, isolated_config_dir)
    assert config.resolve_api_key(path=isolated_config_dir) == "from-file"


def test_resolve_none_when_nothing_set(isolated_config_dir, no_env_api_key):
    assert config.resolve_api_key(path=isolated_config_dir) is None


def test_has_api_key_reflects_state(isolated_config_dir, no_env_api_key):
    assert config.has_api_key(isolated_config_dir) is False
    config.save_config({"api_key": "x"}, isolated_config_dir)
    assert config.has_api_key(isolated_config_dir) is True
