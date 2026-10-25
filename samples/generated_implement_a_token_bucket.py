from collections import defaultdict
from time import time

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = defaultdict(float)
        self.last_refill_time = defaultdict(float)

    def refill(self, client_ip: str) -> None:
        current_time = time()
        if self.last_refill_time[client_ip] < current_time:
            time_elapsed = current_time - self.last_refill_time[client_ip]
            self.tokens[client_ip] += time_elapsed * self.refill_rate
            self.tokens[client_ip] = min(self.tokens[client_ip], self.capacity)
            self.last_refill_time[client_ip] = current_time

    def consume(self, client_ip: str, tokens_needed: int) -> bool:
        self.refill(client_ip)
        if self.tokens[client_ip] >= tokens_needed:
            self.tokens[client_ip] -= tokens_needed
            return True
        return False

class BurstTokenBucket:
    def __init__(self, capacity: int, refill_rate: float, burst_capacity: int):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.burst_capacity = burst_capacity
        self.tokens = defaultdict(float)
        self.last_refill_time = defaultdict(float)

    def refill(self, client_ip: str) -> None:
        current_time = time()
        if self.last_refill_time[client_ip] < current_time:
            time_elapsed = current_time - self.last_refill_time[client_ip]
            self.tokens[client_ip] += time_elapsed * self.refill_rate
            self.tokens[client_ip] = min(self.tokens[client_ip], self.capacity)
            self.last_refill_time[client_ip] = current_time

    def consume(self, client_ip: str, tokens_needed: int) -> bool:
        self.refill(client_ip)
        if self.tokens[client_ip] >= tokens_needed:
            self.tokens[client_ip] -= tokens_needed
            return True
        if self.tokens[client_ip] + tokens_needed <= self.burst_capacity:
            self.tokens[client_ip] += tokens_needed
            return True
        return False