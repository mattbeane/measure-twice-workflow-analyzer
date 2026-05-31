"""Statistical analysis of Monte Carlo results with confidence weighting."""

import statistics
from dataclasses import dataclass
from typing import Any, Optional

from .schemas import PromptRunResult


# Confidence weights for CISC-style weighted aggregation
CONFIDENCE_WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}


@dataclass
class MetricStats:
    """Statistics for a single metric across runs."""
    metric_name: str
    values: list[float]
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    range_val: float
    coefficient_of_variation: float  # std_dev / mean * 100
    n_samples: int
    # Confidence-weighted values (CISC-style)
    weighted_mean: float = 0.0
    weighted_median: float = 0.0

    @property
    def confidence_95(self) -> tuple[float, float]:
        """95% confidence interval (assuming normal distribution)."""
        if self.n_samples < 2:
            return (self.mean, self.mean)
        margin = 1.96 * self.std_dev / (self.n_samples ** 0.5)
        return (self.mean - margin, self.mean + margin)

    @property
    def is_high_variance(self) -> bool:
        """Flag if variance is concerning (>20% coefficient of variation)."""
        return self.coefficient_of_variation > 20

    @property
    def best_estimate(self) -> float:
        """
        Return the best estimate of the metric value.
        Uses confidence-weighted median if available, otherwise regular median.
        """
        return self.weighted_median if self.weighted_median != 0 else self.median


@dataclass
class PromptStats:
    """Aggregated statistics for a single prompt across runs."""
    prompt_id: str
    prompt_title: str
    category: str
    n_runs: int
    n_successful: int
    n_failed: int
    success_rate: float
    metrics: dict[str, MetricStats]

    def get_key_metrics(self) -> list[MetricStats]:
        """Get the most important metrics for display."""
        return list(self.metrics.values())


def calculate_metric_stats(name: str, values: list[float]) -> MetricStats:
    """Calculate statistics for a list of numeric values."""
    if not values:
        return MetricStats(
            metric_name=name,
            values=[],
            mean=0,
            median=0,
            std_dev=0,
            min_val=0,
            max_val=0,
            range_val=0,
            coefficient_of_variation=0,
            n_samples=0
        )

    n = len(values)
    mean = statistics.mean(values)
    median = statistics.median(values)
    std_dev = statistics.stdev(values) if n > 1 else 0
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    cv = (std_dev / mean * 100) if mean != 0 else 0

    return MetricStats(
        metric_name=name,
        values=values,
        mean=mean,
        median=median,
        std_dev=std_dev,
        min_val=min_val,
        max_val=max_val,
        range_val=range_val,
        coefficient_of_variation=cv,
        n_samples=n
    )


def extract_numeric_metrics(extracted: dict) -> dict[str, float]:
    """
    Recursively extract all numeric values from a metrics dict.
    Returns flat dict with dot-notation keys for nested values.
    """
    result = {}

    def _extract(obj: Any, prefix: str = ""):
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            result[prefix] = float(obj)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else k
                _extract(v, key)
        elif isinstance(obj, list):
            # For lists, only extract numeric values at top level
            # or count/aggregate list items
            if obj and isinstance(obj[0], (int, float)):
                for i, v in enumerate(obj):
                    result[f"{prefix}[{i}]"] = float(v)

    _extract(extracted)
    return result


def calculate_confidence_weighted_stats(
    values: list[float],
    confidences: list[str]
) -> tuple[float, float]:
    """
    Calculate confidence-weighted mean and median.

    Args:
        values: List of metric values
        confidences: Corresponding confidence levels

    Returns:
        Tuple of (weighted_mean, weighted_median)
    """
    if not values or len(values) != len(confidences):
        return 0.0, 0.0

    # Weighted mean
    total_weight = 0.0
    weighted_sum = 0.0
    for val, conf in zip(values, confidences):
        weight = CONFIDENCE_WEIGHTS.get(conf, 0.3)
        weighted_sum += val * weight
        total_weight += weight

    weighted_mean = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Weighted median - add copies based on weight
    weighted_samples = []
    for val, conf in zip(values, confidences):
        weight = CONFIDENCE_WEIGHTS.get(conf, 0.3)
        copies = max(1, int(weight * 10))
        weighted_samples.extend([val] * copies)

    weighted_median = statistics.median(weighted_samples) if weighted_samples else 0.0

    return weighted_mean, weighted_median


def analyze_prompt_results(
    results: list[PromptRunResult],
    prompt_id: str,
    use_confidence_weighting: bool = True
) -> PromptStats:
    """
    Analyze results for a single prompt across multiple runs.

    Uses confidence-weighted aggregation (CISC-inspired) to give higher
    weight to confident assessments.

    Args:
        results: All results (will filter to prompt_id)
        prompt_id: The prompt to analyze
        use_confidence_weighting: Whether to compute confidence-weighted stats

    Returns:
        Aggregated statistics
    """
    prompt_results = [r for r in results if r.prompt_id == prompt_id]

    if not prompt_results:
        return PromptStats(
            prompt_id=prompt_id,
            prompt_title="Unknown",
            category="unknown",
            n_runs=0,
            n_successful=0,
            n_failed=0,
            success_rate=0,
            metrics={}
        )

    # Determine category from prompt ID
    process_ids = ["cycle_time", "bottleneck", "handoff", "decision",
                   "value_waste", "information_flow", "exception", "approval"]
    category = "process" if prompt_id in process_ids else "skill"

    n_runs = len(prompt_results)
    successful = [r for r in prompt_results if r.extraction_success and r.extracted_metrics]
    n_successful = len(successful)
    n_failed = n_runs - n_successful
    success_rate = n_successful / n_runs * 100 if n_runs > 0 else 0

    # Collect all numeric metrics across successful runs with their confidences
    all_metrics: dict[str, list[float]] = {}
    all_confidences: dict[str, list[str]] = {}

    for result in successful:
        numeric_vals = extract_numeric_metrics(result.extracted_metrics)
        confidence = getattr(result, 'confidence', 'medium')
        for key, val in numeric_vals.items():
            if key not in all_metrics:
                all_metrics[key] = []
                all_confidences[key] = []
            all_metrics[key].append(val)
            all_confidences[key].append(confidence)

    # Calculate stats for each metric
    metric_stats = {}
    for name, values in all_metrics.items():
        if values:  # Only include metrics that appeared in at least one run
            base_stats = calculate_metric_stats(name, values)

            # Add confidence-weighted stats
            if use_confidence_weighting and name in all_confidences:
                w_mean, w_median = calculate_confidence_weighted_stats(
                    values, all_confidences[name]
                )
                base_stats.weighted_mean = w_mean
                base_stats.weighted_median = w_median

            metric_stats[name] = base_stats

    return PromptStats(
        prompt_id=prompt_id,
        prompt_title=prompt_results[0].prompt_title,
        category=category,
        n_runs=n_runs,
        n_successful=n_successful,
        n_failed=n_failed,
        success_rate=success_rate,
        metrics=metric_stats
    )


def analyze_all_results(results: list[PromptRunResult]) -> dict[str, PromptStats]:
    """
    Analyze all results grouped by prompt.

    Returns:
        Dict mapping prompt_id to PromptStats
    """
    # Get unique prompt IDs
    prompt_ids = set(r.prompt_id for r in results)

    return {
        pid: analyze_prompt_results(results, pid)
        for pid in sorted(prompt_ids)
    }


@dataclass
class SummaryStats:
    """High-level summary statistics across all prompts."""
    total_runs: int
    total_successful: int
    total_failed: int
    overall_success_rate: float
    total_input_tokens: int
    total_output_tokens: int
    total_cost_estimate: float  # USD estimate
    avg_latency_ms: float
    process_prompts_run: int
    skill_prompts_run: int
    high_variance_metrics: list[str]  # Metrics with CV > 20%


def calculate_summary(results: list[PromptRunResult]) -> SummaryStats:
    """Calculate high-level summary statistics."""
    total_runs = len(results)
    successful = [r for r in results if r.extraction_success]
    total_successful = len(successful)
    total_failed = total_runs - total_successful
    success_rate = total_successful / total_runs * 100 if total_runs > 0 else 0

    total_input = sum(r.input_tokens for r in results)
    total_output = sum(r.output_tokens for r in results)

    # Pricing lives in cost.py (Haiku 4.5: $1/1M in, $5/1M out) — single source of truth.
    from .cost import cost_of_tokens
    cost = cost_of_tokens(total_input, total_output)

    avg_latency = statistics.mean(r.latency_ms for r in results) if results else 0

    # Count prompts by category
    process_ids = {"cycle_time", "bottleneck", "handoff", "decision",
                   "value_waste", "information_flow", "exception", "approval"}
    prompt_ids = set(r.prompt_id for r in results)
    process_count = len(prompt_ids & process_ids)
    skill_count = len(prompt_ids - process_ids)

    # Find high-variance metrics
    all_stats = analyze_all_results(results)
    high_variance = []
    for prompt_stats in all_stats.values():
        for metric_name, metric_stats in prompt_stats.metrics.items():
            if metric_stats.is_high_variance:
                high_variance.append(f"{prompt_stats.prompt_id}.{metric_name}")

    return SummaryStats(
        total_runs=total_runs,
        total_successful=total_successful,
        total_failed=total_failed,
        overall_success_rate=success_rate,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_cost_estimate=cost,
        avg_latency_ms=avg_latency,
        process_prompts_run=process_count,
        skill_prompts_run=skill_count,
        high_variance_metrics=high_variance
    )
