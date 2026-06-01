"""Cost math: pricing, per-run heuristic, estimate(), BudgetTracker.

The README claims real numbers ("~$50 for a defensible run"). The estimator is
the only thing standing between a workshop participant and a surprise bill, so
the math here gets pinned down.
"""
from workflow_analyzer import cost


def test_haiku_pricing_constants_match_anthropic_published():
    # Haiku 4.5: $1.00 / Mtok input, $5.00 / Mtok output.
    # Changing these is a real product decision — failing this test means the
    # author intentionally moved the source of truth.
    assert cost.PRICE_INPUT_PER_MTOK == 1.00
    assert cost.PRICE_OUTPUT_PER_MTOK == 5.00


def test_cost_of_tokens_matches_hand_math():
    # 1M input + 1M output = $1 + $5 = $6 exactly.
    assert cost.cost_of_tokens(1_000_000, 1_000_000) == 6.0
    # 500k input @ $0.5, 200k output @ $1.0 = $1.5
    assert abs(cost.cost_of_tokens(500_000, 200_000) - 1.5) < 1e-9


def test_cost_of_tokens_zero_tokens_is_zero():
    assert cost.cost_of_tokens(0, 0) == 0


def test_tokens_per_run_scales_with_workflow_size():
    in_small, out_small = cost.tokens_per_run(0)
    in_big, out_big = cost.tokens_per_run(40_000)
    # Output overhead is constant; input grows with workflow size.
    assert out_small == out_big
    assert in_big > in_small
    # ~4 chars/token → 40k chars adds ~10k tokens.
    assert in_big - in_small >= 9_000


def test_estimate_returns_sensible_max_and_typical():
    est = cost.estimate(n_prompts=14, runs_per_prompt=1000, workflow_chars=15_000)
    assert est.n_prompts == 14
    assert est.max_runs == 14_000
    # max_cost is the unbounded ceiling; typical is the adaptive-stopping
    # expectation. typical < max by construction.
    assert est.typical_cost < est.max_cost
    # On a 15K-char workflow, a 1000-run analysis is in the tens of dollars,
    # not pennies and not thousands.
    assert 10 < est.max_cost < 500


def test_estimate_summary_line_mentions_haiku_4_5_and_dollar_signs():
    est = cost.estimate(n_prompts=14, runs_per_prompt=10, workflow_chars=15_000)
    line = est.summary_line()
    assert "Haiku 4.5" in line
    assert "$" in line
    assert "140" in line  # max_runs


# ---------------------------------------------------------------------------
# BudgetTracker
# ---------------------------------------------------------------------------

def test_budget_tracker_none_means_no_cap():
    bt = cost.BudgetTracker(budget_usd=None)
    bt.add(input_tokens=1_000_000, output_tokens=1_000_000)
    assert bt.exceeded is False


def test_budget_tracker_under_cap_not_exceeded():
    bt = cost.BudgetTracker(budget_usd=10.0)
    bt.add(input_tokens=100, output_tokens=100)
    assert bt.spent < 10.0
    assert bt.exceeded is False


def test_budget_tracker_at_or_above_cap_is_exceeded():
    bt = cost.BudgetTracker(budget_usd=0.01)
    # 1M input @ $1 = $1.00 — well above $0.01
    bt.add(input_tokens=1_000_000, output_tokens=0)
    assert bt.spent >= 0.01
    assert bt.exceeded is True


def test_budget_tracker_accumulates_across_calls():
    bt = cost.BudgetTracker(budget_usd=None)
    bt.add(input_tokens=100, output_tokens=200)
    first = bt.spent
    bt.add(input_tokens=100, output_tokens=200)
    assert bt.spent == first * 2
