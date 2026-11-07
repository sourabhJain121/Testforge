"""
stats_calculator.py - Numerical and Statistical Calculation Engine.
Sample Target 4 for TestForge Benchmark Suite (Numerical Precision, Bessel's Correction & Edge Cases).
"""

from __future__ import annotations
import math
from typing import List, Dict, Optional


def calculate_mean(values: List[float]) -> float:
    """Computes arithmetic mean of a non-empty numeric sequence."""
    if not values:
        raise ValueError("Cannot compute mean of empty sequence.")
    return sum(values) / len(values)


def calculate_variance(values: List[float], ddof: int = 1) -> float:
    """
    Computes sample variance (ddof=1, Bessel's correction) or
    population variance (ddof=0).
    """
    n = len(values)
    if n == 0:
        raise ValueError("Cannot compute variance of empty sequence.")
    if n <= ddof:
        raise ValueError(f"Degrees of freedom ({n - ddof}) must be strictly positive.")

    mean_val = calculate_mean(values)
    squared_diffs = sum((x - mean_val) ** 2 for x in values)
    return squared_diffs / (n - ddof)


def calculate_stddev(values: List[float], ddof: int = 1) -> float:
    """Computes standard deviation with specified degrees of freedom."""
    var = calculate_variance(values, ddof=ddof)
    return math.sqrt(var)


def calculate_median(values: List[float]) -> float:
    """Computes sample median for odd or even length sequence."""
    if not values:
        raise ValueError("Cannot compute median of empty sequence.")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_vals[mid])
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0


def calculate_z_scores(values: List[float]) -> List[float]:
    """
    Computes normalized standard scores (z-scores).
    Returns all zeros if standard deviation is zero (constant population).
    """
    if len(values) < 2:
        raise ValueError("At least 2 values required to compute z-scores.")
    mean_val = calculate_mean(values)
    std_val = calculate_stddev(values, ddof=1)
    if math.isclose(std_val, 0.0, abs_tol=1e-12):
        return [0.0 for _ in values]
    return [round((x - mean_val) / std_val, 4) for x in values]


def calculate_summary_stats(values: List[float]) -> Dict[str, float]:
    """Aggregates descriptive statistics into a single structured report."""
    if not values:
        raise ValueError("Cannot compute summary statistics for empty sequence.")
    mean_val = calculate_mean(values)
    std_val = calculate_stddev(values, ddof=1) if len(values) > 1 else 0.0
    return {
        "count": float(len(values)),
        "mean": round(mean_val, 4),
        "median": round(calculate_median(values), 4),
        "min": float(min(values)),
        "max": float(max(values)),
        "stddev": round(std_val, 4),
    }

