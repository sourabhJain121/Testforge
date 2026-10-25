"""
samples/rate_limiter.py - Token bucket algorithm with time-decay and burst boundaries.
"""

def evaluate_rate_limit(
    tokens_available: float,
    bucket_capacity: float,
    refill_rate_per_sec: float,
    elapsed_seconds: float,
    requested_tokens: int
) -> tuple[bool, float]:
    """
    Evaluates a rate limit request using the token bucket algorithm.

    Returns:
      (is_allowed: bool, remaining_tokens: float)

    Rules:
      - capacity must be >= 1.0.
      - requested_tokens must be >= 1.
      - tokens cannot exceed bucket_capacity after refill.
      - request is granted only if replenished tokens >= requested_tokens.
    """
    if bucket_capacity < 1.0 or requested_tokens < 1:
        return (False, max(0.0, tokens_available))

    if elapsed_seconds < 0.0 or refill_rate_per_sec < 0.0:
        return (False, tokens_available)

    # Refill tokens
    refilled = tokens_available + (refill_rate_per_sec * elapsed_seconds)
    current_tokens = min(bucket_capacity, refilled)

    if current_tokens >= float(requested_tokens):
        new_balance = current_tokens - float(requested_tokens)
        return (True, round(new_balance, 3))

    return (False, round(current_tokens, 3))
