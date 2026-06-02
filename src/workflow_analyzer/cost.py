"""Cost estimation and budget enforcement.

Token assumptions are CALIBRATED against 4,319 real Haiku-4.5 calls (the N=300
demo run on the 15.5 KB feature-deploy sample): mean 5,546 input / 1,824 output
tokens per run. The prior estimate assumed 970 output and under-quoted cost ~1.4×
across the board (worse for the displayed banner). Re-measure if the prompts or
the two-call pipeline change materially.

A real run is NOT cheap: on the bundled sample, ~$2 for --quick (N=10) and ~$200
for a full N=1000 pass. That is why the CLI/web both make you set a budget cap
before a run and enforce it mid-flight.
"""

from dataclasses import dataclass
from typing import Optional

# Claude Haiku 4.5 pricing, USD per 1M tokens. Single source of truth — keep
# stats.py / cli.py / the web tool referencing these rather than hardcoding.
PRICE_INPUT_PER_MTOK = 1.00
PRICE_OUTPUT_PER_MTOK = 5.00

CHARS_PER_TOKEN = 4  # rough English heuristic

# Per-run token assumptions (each "run" = one analysis call + one extraction call).
# Measured from 4,319 real calls. Input = workflow text (sent every analysis call)
# + this overhead (system, prompt scaffolding, the analysis output echoed into the
# extraction call). Output is the combined analysis + extraction output.
_INPUT_OVERHEAD_TOKENS = 1700      # non-workflow input per run (measured ~1656)
_OUTPUT_TOKENS_PER_RUN = 1850      # analysis + extraction output (measured ~1824)


def tokens_per_run(workflow_chars: int) -> tuple[int, int]:
    """Estimated (input_tokens, output_tokens) for a single run."""
    workflow_tokens = workflow_chars / CHARS_PER_TOKEN
    input_tokens = int(workflow_tokens + _INPUT_OVERHEAD_TOKENS)
    output_tokens = _OUTPUT_TOKENS_PER_RUN
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
    max_cost: float       # every prompt runs to N (no early stopping)

    def summary_line(self) -> str:
        return (f"{self.n_prompts} prompts × up to {self.runs_per_prompt} runs "
                f"= up to {self.max_runs:,} runs. "
                f"Est. ~${self.max_cost:.0f} (Haiku 4.5); adaptive stopping may lower it. "
                f"Set a budget cap.")


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
