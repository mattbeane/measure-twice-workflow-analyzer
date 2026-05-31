"""Async API runner for parallel workflow analysis."""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Callable

import anthropic

from .prompts import ALL_PROMPTS, PROMPT_BY_ID, SYSTEM_MESSAGE, PromptDefinition
from .schemas import PromptRunResult
from .cost import BudgetTracker
from . import config as user_config


@dataclass
class RunConfig:
    """Configuration for an analysis run."""
    workflow_data: str
    runs_per_prompt: int = 1000  # Statistically defensible by default; adaptive stopping trims it
    model: str = "claude-haiku-4-5"  # Fast and cheap for bulk runs
    extraction_model: str = "claude-haiku-4-5"
    max_concurrent: int = 20  # How many API calls to run in parallel
    max_concurrent_prompts: int = 5  # How many prompts to analyze in parallel
    prompt_ids: Optional[list[str]] = None  # None = all prompts
    temperature: float = 0.7  # Some variance for Monte Carlo effect
    budget_usd: Optional[float] = None  # Hard spend ceiling; None = no cap

    # Adaptive stopping settings (RASC-inspired)
    adaptive_stopping: bool = True
    min_runs_before_stop: int = 3  # Must have at least this many before considering stop
    early_stop_confidence: str = "high"  # Minimum confidence to consider for early stop
    early_stop_metric_agreement: float = 0.15  # Max coefficient of variation to stop early


@dataclass
class RunProgress:
    """Progress tracking for the run."""
    total_calls: int = 0
    completed_calls: int = 0
    failed_calls: int = 0
    results: list[PromptRunResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    spent_usd: float = 0.0
    budget_stopped: bool = False  # True if the run halted because the budget was hit

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def calls_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0
        return self.completed_calls / self.elapsed_seconds


class WorkflowAnalyzer:
    """Runs Monte Carlo style workflow analysis using parallel LLM calls."""

    def __init__(self, api_key: Optional[str] = None):
        # Resolve key: explicit > ANTHROPIC_API_KEY env > config file.
        resolved = user_config.resolve_api_key(api_key)
        self.client = anthropic.AsyncAnthropic(api_key=resolved)

    async def analyze(
        self,
        config: RunConfig,
        progress_callback: Optional[Callable[[RunProgress], None]] = None
    ) -> list[PromptRunResult]:
        """
        Run analysis with specified configuration in parallel.

        With adaptive stopping enabled, will stop analyzing a prompt early
        if sufficient agreement and confidence is reached.

        Args:
            config: Run configuration
            progress_callback: Optional callback for progress updates

        Returns:
            List of all run results
        """
        # Determine which prompts to run
        if config.prompt_ids:
            prompts = [PROMPT_BY_ID[pid] for pid in config.prompt_ids]
        else:
            prompts = ALL_PROMPTS

        # Calculate max possible calls for progress tracking
        max_calls = len(prompts) * config.runs_per_prompt

        # Initialize progress
        progress = RunProgress(total_calls=max_calls)

        # Budget enforcement (shared across all prompts)
        budget = BudgetTracker(config.budget_usd)

        # Semaphore for concurrency control (API calls)
        semaphore = asyncio.Semaphore(config.max_concurrent)

        # Semaphore for concurrent prompts
        prompt_semaphore = asyncio.Semaphore(config.max_concurrent_prompts)

        async def run_one_prompt(prompt: PromptDefinition) -> list[PromptRunResult]:
            async with prompt_semaphore:
                return await self._run_prompt_adaptive(
                    prompt, config, semaphore, progress, budget, progress_callback
                )

        # Run all prompts in parallel (bounded by semaphore)
        tasks = [run_one_prompt(prompt) for prompt in prompts]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results, handling any exceptions
        all_results = []
        for item in results_nested:
            if isinstance(item, Exception):
                print(f"Prompt analysis failed: {item}")
                continue
            all_results.extend(item)

        return all_results

    async def _run_prompt_adaptive(
        self,
        prompt: PromptDefinition,
        config: RunConfig,
        semaphore: asyncio.Semaphore,
        progress: RunProgress,
        budget: BudgetTracker,
        progress_callback: Optional[Callable[[RunProgress], None]] = None
    ) -> list[PromptRunResult]:
        """
        Run a prompt with adaptive stopping.

        Runs up to runs_per_prompt times, but may stop early if:
        1. We have at least min_runs_before_stop results
        2. All runs have high confidence
        3. Key metrics have low variance (coefficient of variation < threshold)

        Also halts immediately if the shared budget ceiling is reached.
        """
        results = []

        for run_num in range(1, config.runs_per_prompt + 1):
            # Hard budget ceiling — stop before spending more.
            if budget.exceeded:
                progress.budget_stopped = True
                skipped = config.runs_per_prompt - len(results)
                progress.total_calls -= skipped
                break

            async with semaphore:
                result = await self._run_prompt(prompt, run_num, config)
                results.append(result)

                progress.completed_calls += 1
                if not result.extraction_success:
                    progress.failed_calls += 1
                progress.results.append(result)
                budget.add(result.input_tokens, result.output_tokens)
                progress.spent_usd = budget.spent

                if progress_callback:
                    progress_callback(progress)

            # Check for early stopping
            if config.adaptive_stopping and len(results) >= config.min_runs_before_stop:
                if self._should_stop_early(results, config):
                    # Adjust progress total to reflect early stop
                    skipped = config.runs_per_prompt - len(results)
                    progress.total_calls -= skipped
                    break

        return results

    def _should_stop_early(
        self,
        results: list[PromptRunResult],
        config: RunConfig
    ) -> bool:
        """
        Determine if we should stop sampling early based on RASC criteria.

        For workflow analysis, we check:
        1. All runs have confidence >= required level
        2. Key numeric metrics have low variance (coefficient of variation)
        """
        valid_results = [r for r in results if r.extraction_success and r.extracted_metrics]

        if len(valid_results) < config.min_runs_before_stop:
            return False

        # Check confidence levels
        confidence_order = {"high": 3, "medium": 2, "low": 1}
        required_confidence = confidence_order.get(config.early_stop_confidence, 3)

        for r in valid_results:
            result_confidence = confidence_order.get(r.confidence, 1)
            if result_confidence < required_confidence:
                return False

        # Check metric variance - extract key numeric values and compute CV
        import statistics
        all_metrics: dict[str, list[float]] = {}

        for r in valid_results:
            self._extract_metrics(r.extracted_metrics, all_metrics)

        # Check if any key metric has high variance
        for name, values in all_metrics.items():
            if len(values) >= config.min_runs_before_stop:
                mean = statistics.mean(values)
                if mean != 0:
                    std_dev = statistics.stdev(values) if len(values) > 1 else 0
                    cv = std_dev / abs(mean)
                    if cv > config.early_stop_metric_agreement:
                        return False  # High variance, keep sampling

        return True

    def _extract_metrics(self, obj: dict, result: dict[str, list[float]], prefix: str = ""):
        """Recursively extract numeric metrics from a dict."""
        if not isinstance(obj, dict):
            return
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if key not in result:
                    result[key] = []
                result[key].append(float(v))
            elif isinstance(v, dict):
                self._extract_metrics(v, result, key)

    async def _run_prompt(
        self,
        prompt: PromptDefinition,
        run_num: int,
        config: RunConfig
    ) -> PromptRunResult:
        """Run a single prompt and extract metrics."""

        start_time = time.time()

        # Step 1: Run the analysis prompt
        try:
            formatted_prompt = prompt.prompt_template.format(
                workflow_data=config.workflow_data
            )

            response = await self.client.messages.create(
                model=config.model,
                max_tokens=4096,
                temperature=config.temperature,
                system=SYSTEM_MESSAGE,
                messages=[{"role": "user", "content": formatted_prompt}]
            )

            raw_response = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

        except Exception as e:
            return PromptRunResult(
                prompt_id=prompt.id,
                prompt_title=prompt.title,
                run_number=run_num,
                raw_response="",
                extracted_metrics=None,
                extraction_success=False,
                error_message=f"API call failed: {str(e)}",
                model=config.model,
                input_tokens=0,
                output_tokens=0,
                latency_ms=int((time.time() - start_time) * 1000)
            )

        # Step 2: Extract structured metrics with confidence
        confidence = "medium"  # Default
        try:
            # Add confidence request to extraction prompt
            extraction_with_confidence = f"""{prompt.extraction_prompt}

IMPORTANT: Also include a "_confidence" field at the top level with value "high", "medium", or "low" based on:
- high: The workflow data clearly supports all extracted metrics
- medium: Most metrics are well-supported but some required inference
- low: Significant inference or assumptions were needed"""

            extraction_response = await self.client.messages.create(
                model=config.extraction_model,
                max_tokens=2048,
                temperature=0,  # Deterministic for extraction
                messages=[
                    {
                        "role": "user",
                        "content": f"""Here is a workflow analysis output:

{raw_response}

{extraction_with_confidence}"""
                    }
                ]
            )

            extraction_text = extraction_response.content[0].text.strip()

            # Try to parse JSON (handle markdown code blocks)
            if extraction_text.startswith("```"):
                # Remove markdown code block
                lines = extraction_text.split("\n")
                extraction_text = "\n".join(lines[1:-1])

            extracted_metrics = json.loads(extraction_text)

            # Extract confidence from metrics if present
            if "_confidence" in extracted_metrics:
                confidence = extracted_metrics.pop("_confidence")

            extraction_success = True
            error_message = None

            # Update token counts
            input_tokens += extraction_response.usage.input_tokens
            output_tokens += extraction_response.usage.output_tokens

        except json.JSONDecodeError as e:
            extracted_metrics = None
            extraction_success = False
            error_message = f"JSON parse failed: {str(e)}"
            confidence = "low"
        except Exception as e:
            extracted_metrics = None
            extraction_success = False
            error_message = f"Extraction failed: {str(e)}"
            confidence = "low"

        latency_ms = int((time.time() - start_time) * 1000)

        return PromptRunResult(
            prompt_id=prompt.id,
            prompt_title=prompt.title,
            run_number=run_num,
            raw_response=raw_response,
            extracted_metrics=extracted_metrics,
            extraction_success=extraction_success,
            error_message=error_message,
            model=config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            confidence=confidence
        )


async def run_analysis(
    workflow_data: str,
    runs_per_prompt: int = 5,
    prompt_ids: Optional[list[str]] = None,
    progress_callback: Optional[Callable[[RunProgress], None]] = None,
    api_key: Optional[str] = None
) -> list[PromptRunResult]:
    """
    Convenience function to run analysis.

    Args:
        workflow_data: The workflow data to analyze
        runs_per_prompt: Number of runs per prompt (default 5)
        prompt_ids: Optional list of prompt IDs to run (default all)
        progress_callback: Optional progress callback
        api_key: Optional API key (uses ANTHROPIC_API_KEY env var if not provided)

    Returns:
        List of all run results
    """
    analyzer = WorkflowAnalyzer(api_key=api_key)
    config = RunConfig(
        workflow_data=workflow_data,
        runs_per_prompt=runs_per_prompt,
        prompt_ids=prompt_ids
    )
    return await analyzer.analyze(config, progress_callback)
