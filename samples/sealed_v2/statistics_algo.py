"""Pure Python Statistics algorithms from CPython statistics.py"""
import math

def calculate_mean(data: list[float]) -> float:
    """Return the sample arithmetic mean of data."""
    if not data:
        raise ValueError('mean requires at least one data point')
    return sum(data) / len(data)

def calculate_median(data: list[float]) -> float:
    """Return the median (middle value) of numeric data."""
    if not data:
        raise ValueError('median requires at least one data point')
    s = sorted(data)
    n = len(s)
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0

def calculate_variance(data: list[float]) -> float:
    """Return the sample variance of data (with N-1 degrees of freedom)."""
    if len(data) < 2:
        raise ValueError('variance requires at least two data points')
    m = calculate_mean(data)
    ss = sum((x - m) ** 2 for x in data)
    return ss / (len(data) - 1)

def calculate_stdev(data: list[float]) -> float:
    """Return the square root of the sample variance."""
    var = calculate_variance(data)
    return math.sqrt(var)
