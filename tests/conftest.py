"""Shared fixtures for the test harness.

The fixtures here keep the suite hermetic: no real Anthropic calls, no shared
filesystem state, no leakage from `~/.config/measure-twice` into the tests.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from workflow_analyzer.schemas import PromptRunResult


# ---------------------------------------------------------------------------
# Filesystem isolation
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_config_dir(tmp_path, monkeypatch):
    """Redirect the user config path so tests never touch the real ~/.config.

    The four config helpers (`load_config`, `save_config`, `resolve_api_key`,
    `has_api_key`) all have `path: Path = CONFIG_PATH` as a default argument.
    Python evaluates default args once at function-definition time, so
    monkey-patching `cfg.CONFIG_PATH` alone is not enough — the functions
    keep their original-CONFIG_PATH bindings and would happily read/write
    the developer's real `~/.config/measure-twice/config.toml`. We wrap the
    four entrypoints so any caller (including `cli.py`'s
    `user_config.save_config(...)`) lands in `tmp_path` instead.
    """
    from workflow_analyzer import config as cfg
    fake_dir = tmp_path / "measure-twice"
    fake_path = fake_dir / "config.toml"
    monkeypatch.setattr(cfg, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg, "CONFIG_PATH", fake_path)

    real_load = cfg.load_config
    real_save = cfg.save_config
    real_resolve = cfg.resolve_api_key
    real_has = cfg.has_api_key

    monkeypatch.setattr(
        cfg, "load_config", lambda path=fake_path: real_load(path)
    )
    monkeypatch.setattr(
        cfg, "save_config",
        lambda updates, path=fake_path: real_save(updates, path),
    )
    monkeypatch.setattr(
        cfg, "resolve_api_key",
        lambda explicit=None, path=fake_path: real_resolve(explicit, path),
    )
    monkeypatch.setattr(
        cfg, "has_api_key", lambda path=fake_path: real_has(path)
    )
    return fake_path


@pytest.fixture
def tmp_db(tmp_path):
    """A fresh sqlite db path for storage tests."""
    return tmp_path / "test.db"


@pytest.fixture
def no_env_api_key(monkeypatch):
    """Ensure ANTHROPIC_API_KEY isn't inherited from the developer's shell."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    yield


# ---------------------------------------------------------------------------
# PromptRunResult factories
# ---------------------------------------------------------------------------

def _make_result(
    prompt_id: str = "cycle_time",
    prompt_title: str = "1. Cycle Time Extraction",
    run_number: int = 1,
    extracted_metrics: dict | None = None,
    extraction_success: bool = True,
    error_message: str | None = None,
    input_tokens: int = 1200,
    output_tokens: int = 400,
    latency_ms: int = 800,
    raw_response: str = "{}",
    model: str = "claude-haiku-4-5",
    confidence: str = "high",
) -> PromptRunResult:
    return PromptRunResult(
        prompt_id=prompt_id,
        prompt_title=prompt_title,
        run_number=run_number,
        raw_response=raw_response,
        extracted_metrics=extracted_metrics,
        extraction_success=extraction_success,
        error_message=error_message,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        confidence=confidence,
    )


@pytest.fixture
def make_result():
    """Factory for building `PromptRunResult` instances in tests."""
    return _make_result


@pytest.fixture
def successful_results(make_result):
    """A small bundle of 5 successful cycle_time runs with realistic metrics."""
    base = {
        "active_work_days": 8.5,
        "active_work_percent": 60.0,
        "handoff_count": 15,
        "wait_time_days": 5.0,
        "total_cycle_time_days": 14.0,
    }
    out = []
    for i, jitter in enumerate([0.0, 0.5, -0.3, 0.2, -0.1]):
        metrics = {k: v + (v * jitter * 0.1) for k, v in base.items()}
        out.append(make_result(
            run_number=i + 1,
            extracted_metrics=metrics,
            extraction_success=True,
        ))
    return out


@pytest.fixture
def failed_results(make_result):
    """3 failed runs (e.g. all 401 from a bad key)."""
    return [
        make_result(
            run_number=i + 1,
            extracted_metrics=None,
            extraction_success=False,
            error_message="API call failed: Error code: 401 - invalid x-api-key",
            input_tokens=0,
            output_tokens=0,
        )
        for i in range(3)
    ]


@pytest.fixture
def workflow_sample_path():
    """Path to the bundled sample workflow that ships with the repo."""
    here = Path(__file__).parent.parent
    return here / "examples" / "feature-deploy" / "workflow.txt"
