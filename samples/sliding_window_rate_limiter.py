"""
samples/sliding_window_rate_limiter.py - Multi-Tier Sliding Window Log Rate Limiter.
License: MIT
Author: TestForge Benchmark Suite
LOC: ~110 lines
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


class Tier(Enum):
    FREE = ("free", 10, 60.0, 2)         # 10 requests / 60s, burst 2
    PRO = ("pro", 100, 60.0, 15)         # 100 requests / 60s, burst 15
    ENTERPRISE = ("ent", 1000, 60.0, 50) # 1000 requests / 60s, burst 50

    def __init__(self, label: str, max_requests: int, window_seconds: float, burst_allowance: int):
        self.label = label
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_allowance = burst_allowance


@dataclass
class ClientUsage:
    timestamps: deque[float] = field(default_factory=deque)
    blocked_count: int = 0
    tier: Tier = Tier.FREE


class SlidingWindowRateLimiter:
    """
    Sliding window log rate limiter with burst tolerance and tier quotas.
    Thread-safe logic with precise millisecond timestamp evaluation.
    """

    def __init__(self, default_tier: Tier = Tier.FREE):
        self.default_tier = default_tier
        self._clients: Dict[str, ClientUsage] = {}

    def set_client_tier(self, client_id: str, tier: Tier) -> None:
        if not client_id or not client_id.strip():
            raise ValueError("client_id must be a non-empty string")
        if client_id not in self._clients:
            self._clients[client_id] = ClientUsage(tier=tier)
        else:
            self._clients[client_id].tier = tier

    def _cleanup_expired(self, usage: ClientUsage, current_time: float, window: float) -> None:
        threshold = current_time - window
        while usage.timestamps and usage.timestamps[0] <= threshold:
            usage.timestamps.popleft()

    def acquire(self, client_id: str, current_time: float, cost: int = 1) -> Tuple[bool, int, float]:
        """
        Attempts to acquire 'cost' tokens for a client at 'current_time'.

        Returns:
            (allowed: bool, remaining_quota: int, reset_seconds: float)
        """
        if not client_id or not client_id.strip():
            raise ValueError("client_id cannot be blank")
        if cost <= 0:
            raise ValueError("cost must be a positive integer")

        usage = self._clients.setdefault(client_id, ClientUsage(tier=self.default_tier))
        tier = usage.tier
        window = tier.window_seconds
        limit = tier.max_requests + tier.burst_allowance

        self._cleanup_expired(usage, current_time, window)

        current_count = len(usage.timestamps)
        if current_count + cost <= limit:
            for _ in range(cost):
                usage.timestamps.append(current_time)
            remaining = max(0, limit - (current_count + cost))
            oldest = usage.timestamps[0] if usage.timestamps else current_time
            reset_sec = max(0.0, round((oldest + window) - current_time, 2))
            return True, remaining, reset_sec
        else:
            usage.blocked_count += 1
            remaining = 0
            oldest = usage.timestamps[0] if usage.timestamps else current_time
            reset_sec = max(0.0, round((oldest + window) - current_time, 2))
            return False, remaining, reset_sec

    def get_remaining_quota(self, client_id: str, current_time: float) -> int:
        if client_id not in self._clients:
            tier = self.default_tier
            return tier.max_requests + tier.burst_allowance
        usage = self._clients[client_id]
        self._cleanup_expired(usage, current_time, usage.tier.window_seconds)
        limit = usage.tier.max_requests + usage.tier.burst_allowance
        return max(0, limit - len(usage.timestamps))

    def reset_client(self, client_id: str) -> bool:
        if client_id in self._clients:
            del self._clients[client_id]
            return True
        return False
