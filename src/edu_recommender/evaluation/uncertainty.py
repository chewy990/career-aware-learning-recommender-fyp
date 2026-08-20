"""Own evaluation uncertainty responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import hashlib
import math
import random
from statistics import mean, median, stdev

from .contracts import DEFAULT_BOOTSTRAP_REPLICATES, METRIC_NAMES
from .reporting import _models_from_rows


def build_uncertainty_rows(
    profile_rows: list[dict[str, object]],
    random_seed: int,
    bootstrap_replicates: int,
) -> list[dict[str, object]]:
    """Build uncertainty rows deterministically from the supplied evidence."""

    if bootstrap_replicates <= 0:
        raise ValueError("bootstrap_replicates must be positive")
    rows: list[dict[str, object]] = []
    for model in _models_from_rows(profile_rows):
        for k in sorted({int(row["k"]) for row in profile_rows}):
            group = [
                row
                for row in profile_rows
                if row["model"] == model and int(row["k"]) == k
            ]
            for metric in METRIC_NAMES:
                values = [float(row[metric]) for row in group]
                derived_seed = _derived_seed(random_seed, model, k, metric)
                lower, upper = bootstrap_mean_confidence_interval(
                    values,
                    seed=derived_seed,
                    replicates=bootstrap_replicates,
                )
                rows.append(
                    {
                        "model": model,
                        "k": k,
                        "metric": metric,
                        "profile_count": len(values),
                        "mean": round(mean(values), 4) if values else 0.0,
                        "median": round(median(values), 4) if values else 0.0,
                        "sample_stddev": round(stdev(values), 4)
                        if len(values) > 1
                        else 0.0,
                        "ci_95_lower": round(lower, 4),
                        "ci_95_upper": round(upper, 4),
                        "bootstrap_replicates": bootstrap_replicates,
                        "random_seed": random_seed,
                    }
                )
    return rows

def bootstrap_mean_confidence_interval(
    values: list[float],
    seed: int,
    replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
) -> tuple[float, float]:
    """Estimate a seeded percentile interval for the mean by resampling profiles."""

    if not values:
        return 0.0, 0.0
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    generator = random.Random(seed)
    sample_size = len(values)
    bootstrap_means = sorted(
        sum(generator.choice(values) for _ in range(sample_size)) / sample_size
        for _ in range(replicates)
    )
    return (
        _percentile(bootstrap_means, 0.025),
        _percentile(bootstrap_means, 0.975),
    )

def _derived_seed(base_seed: int, model: str, k: int, metric: str) -> int:
    payload = f"{base_seed}:{model}:{k}:{metric}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

def _percentile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        return 0.0
    position = (len(sorted_values) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    fraction = position - lower_index
    return (
        sorted_values[lower_index] * (1 - fraction)
        + sorted_values[upper_index] * fraction
    )
