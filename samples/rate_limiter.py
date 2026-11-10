"""
samples/rate_limiter.py - Industrial Token Bucket & Sliding Window Rate Limiter.

Implements token bucket capacity, refill rate calculations, burst defense,
and temporal sliding window request limiting in pure Python standard library.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional


class RateLimitExceeded(Exception):
    """Raised when an operation exceeds allowed request frequency."""
    pass


class TokenBucket:
    """
    Standard Token Bucket Rate Limiter with continuous temporal refilling.
    """
    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        initial_tokens: Optional[float] = None,
        now: Optional[float] = None,
    ):
        if capacity <= 0:
            raise ValueError(f"Capacity must be strictly positive, got {capacity}")
        if refill_rate <= 0:
            raise ValueError(f"Refill rate must be strictly positive, got {refill_rate}")

        self.capacity: float = float(capacity)
        self.refill_rate: float = float(refill_rate)
        if initial_tokens is not None:
            if initial_tokens < 0:
                raise ValueError("Initial tokens cannot be negative.")
            self.tokens: float = min(float(initial_tokens), self.capacity)
        else:
            self.tokens: float = self.capacity

        self.last_refill: float = now if now is not None else time.time()

    def _refill(self, now: Optional[float] = None) -> float:
        """Refills accumulated tokens proportional to elapsed wall-clock seconds."""
        current_time = now if now is not None else time.time()
        elapsed = current_time - self.last_refill
        if elapsed > 0:
            added = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + added)
            self.last_refill = current_time
        return self.tokens

    def consume(self, tokens: float = 1.0, now: Optional[float] = None) -> bool:
        """
        Attempts to consume the specified number of tokens.
        Returns True if tokens were consumed; False if insufficient tokens exist.
        """
        if tokens <= 0:
            return True
        if tokens > self.capacity:
            return False

        self._refill(now)
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_until_available(self, tokens: float = 1.0, now: Optional[float] = None) -> float:
        """
        Calculates wall-clock seconds remaining until tokens become available.
        """
        if tokens <= 0:
            return 0.0
        if tokens > self.capacity:
            return float("inf")

        self._refill(now)
        if self.tokens >= tokens:
            return 0.0

        deficit = tokens - self.tokens
        return round(deficit / self.refill_rate, 4)

    def reset(self, now: Optional[float] = None) -> None:
        """Resets the bucket to full capacity."""
        self.tokens = self.capacity
        self.last_refill = now if now is not None else time.time()


class SlidingWindowRateLimiter:
    """
    Sliding Window Log Rate Limiter per client key.
    """
    def __init__(self, max_requests: int, window_seconds: float):
        if max_requests <= 0:
            raise ValueError(f"max_requests must be positive, got {max_requests}")
        if window_seconds <= 0:
            raise ValueError(f"window_seconds must be positive, got {window_seconds}")

        self.max_requests: int = int(max_requests)
        self.window_seconds: float = float(window_seconds)
        self._history: Dict[str, List[float]] = {}

    def allow_request(self, key: str, now: Optional[float] = None) -> bool:
        """
        Checks whether client key is permitted another request within sliding window.
        """
        if not key:
            return False

        current_time = now if now is not None else time.time()
        cutoff = current_time - self.window_seconds

        timestamps = self._history.get(key, [])
        # Prune expired entries
        valid_timestamps = [t for t in timestamps if t >= cutoff]

        if len(valid_timestamps) < self.max_requests:
            valid_timestamps.append(current_time)
            self._history[key] = valid_timestamps
            return True

        self._history[key] = valid_timestamps
        return False

    def get_remaining_calls(self, key: str, now: Optional[float] = None) -> int:
        """Returns the number of remaining requests allowed in the current window."""
        if not key:
            return 0

        current_time = now if now is not None else time.time()
        cutoff = current_time - self.window_seconds

        timestamps = [t for t in self._history.get(key, []) if t >= cutoff]
        remaining = self.max_requests - len(timestamps)
        return max(0, remaining)

    def clear(self, key: Optional[str] = None) -> None:
        """Clears client history for a key or all keys."""
        if key is not None:
            self._history.pop(key, None)
        else:
            self._history.clear()


def evaluate_rate_limit(
    tokens_available: float,
    bucket_capacity: float,
    refill_rate_per_sec: float,
    elapsed_seconds: float,
    requested_tokens: int,
) -> tuple[bool, float]:
    """
    Evaluates a rate limit request using the token bucket algorithm.
    Returns: (is_allowed: bool, remaining_tokens: float)
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
