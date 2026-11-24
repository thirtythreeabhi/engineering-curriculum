"""Statistical utilities: Bootstrap confidence intervals for continuous evaluation."""

import math
import random
from typing import Dict, List, Tuple


def compute_bootstrap_confidence_interval(
    scores: List[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Computes the sample mean and non-parametric bootstrap confidence interval.
    """
    if not scores:
        return {"mean": 0.0, "std_err": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

    n = len(scores)
    sample_mean = sum(scores) / n

    if n == 1:
        return {
            "mean": round(sample_mean, 4),
            "std_err": 0.0,
            "ci_lower": round(sample_mean, 4),
            "ci_upper": round(sample_mean, 4),
        }

    random.seed(seed)
    bootstrap_means: List[float] = []

    for _ in range(n_bootstrap):
        sample = [scores[random.randint(0, n - 1)] for _ in range(n)]
        bootstrap_means.append(sum(sample) / n)

    bootstrap_means.sort()

    alpha = 1.0 - confidence_level
    lower_idx = int(math.floor(alpha / 2.0 * n_bootstrap))
    upper_idx = int(math.ceil((1.0 - alpha / 2.0) * n_bootstrap)) - 1

    ci_lower = max(0.0, bootstrap_means[lower_idx])
    ci_upper = min(1.0, bootstrap_means[upper_idx])

    variance = sum((m - sample_mean) ** 2 for m in bootstrap_means) / n_bootstrap
    std_err = math.sqrt(variance)

    return {
        "mean": round(sample_mean, 4),
        "std_err": round(std_err, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
    }
