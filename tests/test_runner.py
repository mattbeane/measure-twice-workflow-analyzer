"""Runner: the async LLM-calling loop, with the Anthropic SDK mocked.

The runner has the highest blast radius if it regresses — it's the layer that
charges the user's Anthropic account. These tests pin:

* Happy-path two-call pipeline (analysis → extraction → metrics).
* Markdown code-fence handling for JSON extraction.
* `_confidence` field hoisting from extracted metrics.
* API failure → recorded as a failed run, not a crash.
* JSON parse failure → recorded as failed extraction.
* Budget enforcement halts a run early.
* Adaptive stopping fires when metrics agree.
* Per-prompt isolation — a failure in one prompt doesn't kill the batch.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import pytest

from workflow_analyzer.runner import (
    RunConfig,
    RunProgress,
    WorkflowAnalyzer,
    run_analysis,
)


# ---------------------------------------------------------------------------
# Anthropic SDK mock
# ---------------------------------------------------------------------------

@dataclass
class _Usage:
    input_tokens: int
    output_tokens: int


@dataclass
class _ContentBlock:
    text: str


@dataclass
class _Message:
    content: list
    usage: _Usage


def _msg(text: str, in_tok: int = 100, out_tok: int = 60) -> _Message:
    return _Message(content=[_ContentBlock(text=text)], usage=_Usage(in_tok, out_tok))


class _ScriptedMessages:
    """An async `client.messages.create(...)` stand-in that returns scripted
    responses in order. Each prompt produces two calls (analysis + extraction)
    so the script length must be 2 × n_runs × n_prompts."""

    def __init__(self, responses: list[_Message]):
        self._responses = list(responses)
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        if not self._responses:
            raise AssertionError("scripted messages exhausted")
        return self._responses.pop(0)


class _ScriptedClient:
    def __init__(self, responses: list[_Message]):
        self.messages = _ScriptedMessages(responses)


class _RaisingClient:
    """A client whose first call raises — for the API-failure path."""
    def __init__(self, exc: Exception):
        async def create(**kwargs):
            raise exc
        self.messages = type("M", (), {"create": create})()


def _build_analyzer(monkeypatch, client) -> WorkflowAnalyzer:
    """Build a WorkflowAnalyzer without going through `anthropic.AsyncAnthropic`."""
    # Bypass __init__ which constructs a real client.
    analyzer = WorkflowAnalyzer.__new__(WorkflowAnalyzer)
    analyzer.client = client
    return analyzer


def _config(workflow_data: str = "real workflow text " * 30, **kw) -> RunConfig:
    defaults = dict(
        workflow_data=workflow_data,
        runs_per_prompt=2,
        max_concurrent=4,
        max_concurrent_prompts=2,
        prompt_ids=["cycle_time"],
        adaptive_stopping=False,
    )
    defaults.update(kw)
    return RunConfig(**defaults)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_happy_path_two_call_pipeline(monkeypatch):
    metrics = {"total_cycle_time_days": 14.0, "handoff_count": 5, "_confidence": "high"}
    responses = [
        # Analysis (run 1), Extraction (run 1), Analysis (run 2), Extraction (run 2)
        _msg("(analysis run 1)"), _msg(json.dumps(metrics)),
        _msg("(analysis run 2)"), _msg(json.dumps(metrics)),
    ]
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))

    results = asyncio.run(analyzer.analyze(_config()))

    assert len(results) == 2
    assert all(r.extraction_success for r in results)
    # _confidence was hoisted off the metrics dict.
    assert all("_confidence" not in r.extracted_metrics for r in results)
    assert all(r.confidence == "high" for r in results)


def test_markdown_fenced_json_in_extraction_response_is_parsed(monkeypatch):
    metrics = {"x": 1.0}
    fenced = f"```json\n{json.dumps(metrics)}\n```"
    responses = [_msg("(analysis)"), _msg(fenced)]
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))

    cfg = _config(runs_per_prompt=1)
    results = asyncio.run(analyzer.analyze(cfg))
    assert results[0].extraction_success is True
    assert results[0].extracted_metrics == {"x": 1.0}


def test_confidence_defaults_to_medium_when_field_absent(monkeypatch):
    responses = [_msg("(analysis)"), _msg(json.dumps({"x": 1.0}))]
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    results = asyncio.run(analyzer.analyze(_config(runs_per_prompt=1)))
    assert results[0].confidence == "medium"


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

def test_api_error_recorded_as_failed_run_not_raised(monkeypatch):
    """If the analysis-call raises, the run goes into the list as a failure
    with an error_message — the batch must not crash."""
    analyzer = _build_analyzer(monkeypatch, _RaisingClient(RuntimeError("kaboom")))
    results = asyncio.run(analyzer.analyze(_config(runs_per_prompt=1)))
    assert len(results) == 1
    r = results[0]
    assert r.extraction_success is False
    assert "API call failed" in r.error_message
    assert r.input_tokens == 0
    assert r.output_tokens == 0


def test_json_parse_failure_recorded_with_low_confidence(monkeypatch):
    """Extraction returns garbage that isn't JSON → JSONDecodeError → run is
    marked failed, confidence drops to 'low'."""
    responses = [_msg("(analysis)"), _msg("this is not json at all")]
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    results = asyncio.run(analyzer.analyze(_config(runs_per_prompt=1)))
    r = results[0]
    assert r.extraction_success is False
    assert "JSON parse failed" in r.error_message
    assert r.confidence == "low"


def test_extraction_call_raises_recorded_as_extraction_failure(monkeypatch):
    """If the extraction-call itself raises (but analysis succeeded), we
    record the failure under "Extraction failed" not "API call failed"."""

    class _AnalysisOkExtractionRaises:
        def __init__(self):
            self.calls = 0

        async def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return _msg("(analysis ok)")
            raise RuntimeError("extraction blew up")

    client = type("C", (), {"messages": _AnalysisOkExtractionRaises()})()
    analyzer = _build_analyzer(monkeypatch, client)
    results = asyncio.run(analyzer.analyze(_config(runs_per_prompt=1)))
    r = results[0]
    assert r.extraction_success is False
    assert "Extraction failed" in r.error_message
    assert r.confidence == "low"
    # Analysis raw response is still preserved.
    assert "analysis ok" in r.raw_response


# ---------------------------------------------------------------------------
# Budget enforcement
# ---------------------------------------------------------------------------

def test_budget_exceeded_halts_remaining_runs(monkeypatch):
    """With a tight budget and runs that report meaningful token counts, the
    runner stops scheduling further runs once the cap is hit."""
    expensive = _Message(content=[_ContentBlock(text=json.dumps({"x": 1.0}))],
                          usage=_Usage(input_tokens=1_000_000, output_tokens=0))
    # Schedule 10 runs but only the first round (~2 calls) should fit.
    responses = [_msg("(analysis)"), expensive] * 10
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    cfg = _config(runs_per_prompt=10, budget_usd=0.5)  # $0.50 cap; 1M in-tok = $1
    results = asyncio.run(analyzer.analyze(cfg))
    # Far fewer than 10 runs should have completed.
    assert len(results) < 10


# ---------------------------------------------------------------------------
# Adaptive stopping
# ---------------------------------------------------------------------------

def test_adaptive_stop_when_metrics_agree_after_min_runs(monkeypatch):
    """With adaptive stopping enabled and tightly-agreeing metrics, the
    runner should stop before runs_per_prompt."""
    stable = json.dumps({"x": 10.0, "_confidence": "high"})
    responses = [_msg("(analysis)"), _msg(stable)] * 20  # plenty of headroom
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    cfg = _config(
        runs_per_prompt=20,
        adaptive_stopping=True,
        min_runs_before_stop=3,
        early_stop_confidence="high",
        early_stop_metric_agreement=0.15,
    )
    results = asyncio.run(analyzer.analyze(cfg))
    # All confident, zero variance → must stop at the floor (3).
    assert len(results) == 3


def test_adaptive_stop_does_not_fire_with_high_variance(monkeypatch):
    """If the metric values disagree, sampling keeps going to the configured
    runs_per_prompt."""
    values = [10.0, 100.0, 10.0, 100.0, 10.0, 100.0, 10.0, 100.0]
    responses = []
    for v in values:
        responses.append(_msg("(analysis)"))
        responses.append(_msg(json.dumps({"x": v, "_confidence": "high"})))
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    cfg = _config(
        runs_per_prompt=len(values),
        adaptive_stopping=True,
        min_runs_before_stop=3,
        early_stop_metric_agreement=0.05,  # very tight; 10/100 won't satisfy
    )
    results = asyncio.run(analyzer.analyze(cfg))
    assert len(results) == len(values)


def test_adaptive_stop_does_not_fire_below_min_runs(monkeypatch):
    """Even with perfectly stable metrics, we never stop before the floor."""
    stable = json.dumps({"x": 1.0, "_confidence": "high"})
    responses = [_msg("(analysis)"), _msg(stable)] * 10
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    cfg = _config(
        runs_per_prompt=10,
        adaptive_stopping=True,
        min_runs_before_stop=5,
        early_stop_confidence="high",
        early_stop_metric_agreement=0.50,
    )
    results = asyncio.run(analyzer.analyze(cfg))
    # Stops at the floor (5), not earlier.
    assert len(results) == 5


def test_adaptive_stop_blocked_when_any_run_is_low_confidence(monkeypatch):
    """All `early_stop_confidence` runs must clear the bar; one low-confidence
    extraction is enough to keep sampling."""
    low = json.dumps({"x": 1.0, "_confidence": "low"})
    high = json.dumps({"x": 1.0, "_confidence": "high"})
    responses = [
        _msg("a"), _msg(low),
        _msg("a"), _msg(high),
        _msg("a"), _msg(high),
        _msg("a"), _msg(high),
        _msg("a"), _msg(high),
    ]
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    cfg = _config(
        runs_per_prompt=5,
        adaptive_stopping=True,
        min_runs_before_stop=3,
        early_stop_confidence="high",
    )
    results = asyncio.run(analyzer.analyze(cfg))
    # One "low" in the first three → must run all 5.
    assert len(results) == 5


# ---------------------------------------------------------------------------
# Progress + per-prompt isolation
# ---------------------------------------------------------------------------

def test_progress_callback_invoked_after_each_run(monkeypatch):
    metrics = json.dumps({"x": 1.0})
    responses = [_msg("a"), _msg(metrics)] * 3
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))

    seen: list[int] = []

    def cb(p: RunProgress):
        seen.append(p.completed_calls)

    asyncio.run(analyzer.analyze(_config(runs_per_prompt=3), progress_callback=cb))
    # Monotonically non-decreasing, and the last seen value covers the final run.
    assert seen == sorted(seen)
    assert seen[-1] >= 3


def test_last_progress_results_exposed_for_interrupt_handler(monkeypatch):
    """The CLI relies on `analyzer._last_progress_results` to recover partial
    state on Ctrl-C. Pin that contract."""
    metrics = json.dumps({"x": 1.0})
    responses = [_msg("a"), _msg(metrics), _msg("a"), _msg(metrics)]
    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))
    asyncio.run(analyzer.analyze(_config(runs_per_prompt=2)))
    assert hasattr(analyzer, "_last_progress_results")
    assert len(analyzer._last_progress_results) == 2


def test_per_prompt_exception_does_not_kill_batch(monkeypatch):
    """If `_run_prompt_adaptive` raises (not a per-call failure but a
    per-prompt failure), the batch still returns whatever else completed."""
    metrics = json.dumps({"x": 1.0})
    responses = [_msg("a"), _msg(metrics)] * 4

    analyzer = _build_analyzer(monkeypatch, _ScriptedClient(responses))

    # Have the first prompt blow up via a monkey-patched method.
    real_run = analyzer._run_prompt_adaptive
    calls = {"n": 0}

    async def maybe_explode(prompt, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("prompt 1 died")
        return await real_run(prompt, *args, **kwargs)

    analyzer._run_prompt_adaptive = maybe_explode
    cfg = _config(prompt_ids=["cycle_time", "bottleneck"], runs_per_prompt=2)
    results = asyncio.run(analyzer.analyze(cfg))
    # Prompt 1 lost; prompt 2 should still produce 2 results.
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Metric extraction helper
# ---------------------------------------------------------------------------

def test_extract_metrics_recursive_flattening():
    analyzer = WorkflowAnalyzer.__new__(WorkflowAnalyzer)
    out: dict = {}
    analyzer._extract_metrics({"a": 1, "b": {"c": 2.5, "d": {"e": 3}}}, out)
    assert out == {"a": [1.0], "b.c": [2.5], "b.d.e": [3.0]}


def test_extract_metrics_skips_bool_and_strings():
    analyzer = WorkflowAnalyzer.__new__(WorkflowAnalyzer)
    out: dict = {}
    analyzer._extract_metrics({"flag": True, "name": "abc", "n": 1}, out)
    assert "flag" not in out
    assert "name" not in out
    assert out == {"n": [1.0]}


def test_extract_metrics_handles_non_dict_input():
    analyzer = WorkflowAnalyzer.__new__(WorkflowAnalyzer)
    out: dict = {}
    # Non-dict input is a no-op (the engineering judge's "non-dict JSON"
    # silent-corruption concern).
    analyzer._extract_metrics([1, 2, 3], out)  # type: ignore[arg-type]
    analyzer._extract_metrics("a string", out)  # type: ignore[arg-type]
    assert out == {}


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def test_run_analysis_convenience_wraps_analyzer(monkeypatch):
    """`run_analysis` is the module-level helper that constructs an analyzer
    and calls .analyze(). Verify it threads through correctly."""
    metrics = json.dumps({"x": 1.0})
    responses = [_msg("a"), _msg(metrics)]

    # Patch the analyzer factory used inside run_analysis to return our
    # pre-mocked instance.
    import workflow_analyzer.runner as runner_mod

    real_init = WorkflowAnalyzer.__init__

    def fake_init(self, api_key=None):
        # Skip the real AsyncAnthropic construction.
        self.client = _ScriptedClient(list(responses))

    monkeypatch.setattr(WorkflowAnalyzer, "__init__", fake_init)
    try:
        results = asyncio.run(
            runner_mod.run_analysis(workflow_data="x" * 200,
                                     runs_per_prompt=1,
                                     prompt_ids=["cycle_time"])
        )
        assert len(results) == 1
        assert results[0].extraction_success is True
    finally:
        monkeypatch.setattr(WorkflowAnalyzer, "__init__", real_init)
