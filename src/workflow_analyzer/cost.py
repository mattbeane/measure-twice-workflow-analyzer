"""Cost estimation and budget enforcement.

A "solid" statistically-defensible run (N≈1000 with adaptive stopping) lands around
$50 on Haiku 4.5. We never silently cap — the CLI prompts the user to confirm or set a
budget before a real run, and the runner enforces it as a hard ceiling mid-flight.
"""

from dataclasses import dataclass
from typing import Optional

# Claude Haiku 4.5 pricing, USD per 1M tokens. Single source of truth — keep
# stats.py / cli.py referencing these rather than hardcoding.
PRICE_INPUT_PER_MTOK = 1.00
PRICE_OUTPUT_PER_MTOK = 5.00

CHARS_PER_TOKEN = 4  # rough English heuristic

# Per-run token assumptions (each "run" = one analysis call + one extraction call).
_ANALYSIS_OVERHEAD_TOKENS = 600    # system + prompt template scaffolding
_ANALYSIS_OUTPUT_TOKENS = 650
_EXTRACTION_INPUT_TOKENS = 1300    # analysis output echoed back + extraction prompt
_EXTRACTION_OUTPUT_TOKENS = 320

# With adaptive stopping, low-variance prompts stop near the floor while high-variance
# ones run to N. Empirically effective runs land well under the max; use this to show a
# "typical" figure alongside the worst-case ceiling.
TYPICAL_FRACTION_OF_MAX = 0.45


def tokens_per_run(workflow_chars: int) -> tuple[int, int]:
    """Estimated (input_tokens, output_tokens) for a single run."""
    workflow_tokens = workflow_chars / CHARS_PER_TOKEN
    input_tokens = int(workflow_tokens + _ANALYSIS_OVERHEAD_TOKENS + _EXTRACTION_INPUT_TOKENS)
    output_tokens = _ANALYSIS_OUTPUT_TOKENS + _EXTRACTION_OUTPUT_TOKENS
    return input_tokens, output_tokens


def cost_of_tokens(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * PRICE_INPUT_PER_MTOK
            + output_tokens * PRICE_OUTPUT_PER_MTOK) / 1_000_000


@dataclass
class CostEstimate:
    n_prompts: int
    runs_per_prompt: int
    workflow_chars: int
    max_runs: int
    max_cost: float       # if every prompt runs to N (no early stopping)
    typical_cost: float   # expected with adaptive stopping

    def summary_line(self) -> str:
        return (f"{self.n_prompts} prompts × up to {self.runs_per_prompt} runs "
                f"= up to {self.max_runs:,} runs. "
                f"Est. ${self.typical_cost:.0f} typical, ${self.max_cost:.0f} max "
                f"(Haiku 4.5).")


def estimate(n_prompts: int, runs_per_prompt: int, workflow_chars: int) -> CostEstimate:
    in_tok, out_tok = tokens_per_run(workflow_chars)
    per_run = cost_of_tokens(in_tok, out_tok)
    max_runs = n_prompts * runs_per_prompt
    max_cost = per_run * max_runs
    return CostEstimate(
        n_prompts=n_prompts,
        runs_per_prompt=runs_per_prompt,
        workflow_chars=workflow_chars,
        max_runs=max_runs,
        max_cost=max_cost,
        typical_cost=max_cost * TYPICAL_FRACTION_OF_MAX,
    )


class BudgetTracker:
    """Tracks cumulative spend during a run and signals when a cap is exceeded."""

    def __init__(self, budget_usd: Optional[float]):
        self.budget_usd = budget_usd
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    @property
    def spent(self) -> float:
        return cost_of_tokens(self.input_tokens, self.output_tokens)

    @property
    def exceeded(self) -> bool:
        return self.budget_usd is not None and self.spent >= self.budget_usd
