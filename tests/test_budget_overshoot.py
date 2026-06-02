"""Budget enforcement: overshoot is bounded by one concurrency-wave.

The user-facing claim Matt left in the loud failure summary path
('approximate ceiling') depends on a specific bound: in the worst case,
when the cap is hit mid-batch, the runs that are already in flight at
that moment complete before each prompt's next-iteration check halts
the loop. The maximum number of in-flight runs at any moment is
`max_concurrent_prompts` (because each prompt's loop is sequential —
only one call per prompt is in flight at a time).

So the bound is: final_spend <= cap + max_concurrent_prompts * per_call_cost.

These tests pin that bound. Future refactors that change the order of
operations in `_run_prompt_adaptive` — e.g. moving the budget check
after the call instead of before, or making the per-prompt loop
concurrent — would either tighten or break the bound. The tests should
fail loudly in either direction.
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
)


# ---------------------------------------------------------------------------
# Minimal scripted Anthropic client — same pattern as test_runner.py but
# parametrized by a fixed per-call token cost so spend per call is predictable.
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


def _fixed_msg(in_tok: int, out_tok: int, text: str = "(content)") -> _Message:
    return _Message(content=[_ContentBlock(text=text)], usage=_Usage(in_tok, out_tok))


class _FixedCostClient:
    """Mock client whose messages.create returns the same scripted response
    every time, so each call costs the same number of input/output tokens.

    Costs are predictable, so we can compute the exact in-flight overshoot
    bound and assert against it.
    """

    def __init__(self, in_tok: int = 1_000, out_tok: int = 200,
                 extraction_in: int = 1_000, extraction_out: int = 200):
        self._cycle = [
            _fixed_msg(in_tok, out_tok, "(analysis)"),
            _fixed_msg(extraction_in, extraction_out, json.dumps({"x": 1.0})),
        ]
        self._idx = 0
        self.calls = 0
        self.messages = self

    async def create(self, **kwargs):
        msg = self._cycle[self._idx % 2]
        self._idx += 1
        self.calls += 1
        return msg


def _build_analyzer(client) -> WorkflowAnalyzer:
    """Construct a WorkflowAnalyzer without going through `__init__` (which
    would build a real `AsyncAnthropic`)."""
    a = WorkflowAnalyzer.__new__(WorkflowAnalyzer)
    a.client = client
    return a


def _per_call_cost(in_tok: int, out_tok: int) -> float:
    """Cost per analysis call given fixed input/output tokens. Uses the
    same pricing constants the runner does."""
    from workflow_analyzer import cost
    return (in_tok * cost.PRICE_INPUT_PER_MTOK
            + out_tok * cost.PRICE_OUTPUT_PER_MTOK) / 1_000_000


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_overshoot_bounded_by_max_concurrent_prompts():
    """Worst-case bound: final_spend <= cap + max_concurrent_prompts * per_call.

    With max_concurrent_prompts=5 and a tight cap, up to 5 calls may be
    in flight at the moment the cap is exceeded. They all settle before
    each prompt halts.
    """
    # Per-call: cheap enough that many runs fit, expensive enough to walk
    # past the cap clearly in one wave.
    IN_TOK, OUT_TOK = 1_000, 200
    per_call = _per_call_cost(IN_TOK, OUT_TOK)
    # Note: in cost accounting, _both_ the analysis and extraction calls
    # contribute to the BudgetTracker. The runner calls both in
    # `_run_prompt` and adds their token totals once via budget.add.
    per_run = per_call * 2  # analysis + extraction

    MAX_CONCURRENT_PROMPTS = 5
    cap = per_run * 10            # roughly 10 runs' worth of budget
    expected_max_spend = cap + MAX_CONCURRENT_PROMPTS * per_run

    client = _FixedCostClient(IN_TOK, OUT_TOK)
    analyzer = _build_analyzer(client)
    cfg = RunConfig(
        workflow_data="x" * 4_000,
        runs_per_prompt=200,                       # way more than the cap allows
        prompt_ids=["cycle_time", "bottleneck", "handoff",
                    "decision", "value_waste", "information_flow",
                    "exception", "approval"],     # all 8 process prompts
        max_concurrent=MAX_CONCURRENT_PROMPTS,
        max_concurrent_prompts=MAX_CONCURRENT_PROMPTS,
        adaptive_stopping=False,
        budget_usd=cap,
    )

    results = asyncio.run(analyzer.analyze(cfg))

    # Total spend across all runs.
    actual_spend = sum(
        _per_call_cost(r.input_tokens, r.output_tokens) for r in results
    )

    assert actual_spend >= cap, (
        f"Expected to reach the cap; actual_spend={actual_spend:.4f} cap={cap:.4f}"
    )
    assert actual_spend <= expected_max_spend, (
        f"Overshoot exceeded the in-flight wave bound: "
        f"actual_spend={actual_spend:.4f}, cap={cap:.4f}, "
        f"expected_max={expected_max_spend:.4f}, "
        f"overshoot={actual_spend - cap:.4f}, "
        f"bound={MAX_CONCURRENT_PROMPTS * per_run:.4f}"
    )


def test_overshoot_serial_prompts_bounded_by_one_call():
    """With max_concurrent_prompts=1, only one prompt's loop runs at a
    time, so the overshoot is at most one full per-run cost (the single
    call that pushed budget over the cap)."""
    IN_TOK, OUT_TOK = 1_500, 300
    per_call = _per_call_cost(IN_TOK, OUT_TOK)
    per_run = per_call * 2

    cap = per_run * 5
    expected_max_spend = cap + per_run

    client = _FixedCostClient(IN_TOK, OUT_TOK)
    analyzer = _build_analyzer(client)
    cfg = RunConfig(
        workflow_data="x" * 6_000,
        runs_per_prompt=50,
        prompt_ids=["cycle_time"],            # one prompt, sequential by design
        max_concurrent=1,
        max_concurrent_prompts=1,
        adaptive_stopping=False,
        budget_usd=cap,
    )

    results = asyncio.run(analyzer.analyze(cfg))
    actual_spend = sum(
        _per_call_cost(r.input_tokens, r.output_tokens) for r in results
    )

    assert actual_spend >= cap, (
        f"Expected to reach the cap; actual_spend={actual_spend:.4f} cap={cap:.4f}"
    )
    assert actual_spend <= expected_max_spend, (
        f"Serial-prompt overshoot exceeded one per-run bound: "
        f"actual_spend={actual_spend:.4f}, cap={cap:.4f}, "
        f"expected_max={expected_max_spend:.4f}"
    )


def test_progress_budget_stopped_flag_is_true_when_cap_hits():
    """The CLI's loud-failure messaging reads `progress.budget_stopped`
    to render the 'budget reached' note. Pin that the runner sets it
    when the cap fires."""
    IN_TOK, OUT_TOK = 2_000, 400
    per_call = _per_call_cost(IN_TOK, OUT_TOK)
    per_run = per_call * 2
    cap = per_run * 3

    client = _FixedCostClient(IN_TOK, OUT_TOK)
    analyzer = _build_analyzer(client)
    cfg = RunConfig(
        workflow_data="x" * 8_000,
        runs_per_prompt=20,
        prompt_ids=["cycle_time"],
        max_concurrent_prompts=1,
        max_concurrent=1,
        adaptive_stopping=False,
        budget_usd=cap,
    )

    captured: list[RunProgress] = []
    asyncio.run(analyzer.analyze(cfg, progress_callback=captured.append))

    final_progress = captured[-1]
    assert final_progress.budget_stopped is True, (
        f"Expected RunProgress.budget_stopped=True after cap fired, "
        f"got {final_progress.budget_stopped}"
    )


def test_no_budget_cap_does_not_set_stopped_flag():
    """The flag must only flip when the runner halts due to a cap.
    A normal completion (no cap configured) leaves it False."""
    IN_TOK, OUT_TOK = 800, 100

    client = _FixedCostClient(IN_TOK, OUT_TOK)
    analyzer = _build_analyzer(client)
    cfg = RunConfig(
        workflow_data="x" * 2_000,
        runs_per_prompt=3,
        prompt_ids=["cycle_time"],
        max_concurrent_prompts=1,
        max_concurrent=1,
        adaptive_stopping=False,
        budget_usd=None,                       # no cap
    )

    asyncio.run(analyzer.analyze(cfg))
    # We re-read the analyzer's last-progress-results trail; budget_stopped
    # is on RunProgress, not on the result list. Access via the same hook
    # the CLI uses for KeyboardInterrupt recovery.
    # The analyzer doesn't expose progress directly, but if a callback was
    # set we'd see it. Use one:
    captured: list[RunProgress] = []
    asyncio.run(analyzer.analyze(cfg, progress_callback=captured.append))
    assert captured, "Expected at least one progress callback invocation"
    assert captured[-1].budget_stopped is False, (
        "RunProgress.budget_stopped flipped True without a cap being hit"
    )
