from functools import lru_cache

@lru_cache(maxsize=128)
def compute_fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError('n must be non-negative')
    if n in (0, 1):
        return n
    return compute_fibonacci(n - 1) + compute_fibonacci(n - 2)
