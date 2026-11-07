import time

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.fill_rate = fill_rate
        self.last_update = time.monotonic()

    def consume(self, amount: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
        self.last_update = now
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False
