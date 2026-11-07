"""
lru_cache.py - Least Recently Used (LRU) Cache data structure with state mutations.
Sample Target 2 for TestForge Benchmark Suite (Data Structures & State Mutation).
"""

from __future__ import annotations
from typing import Any, Optional, Dict, List


class Node:
    """Doubly-linked list node for LRU entry tracking."""
    def __init__(self, key: str, value: Any):
        self.key: str = key
        self.value: Any = value
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None


class LRUCache:
    """
    Fixed-capacity Least Recently Used (LRU) Cache with O(1) lookups,
    insertions, and evictions. Tracks cache hit/miss ratios.
    """
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer greater than zero.")
        self.capacity: int = capacity
        self.lookup: Dict[str, Node] = {}
        self.hits: int = 0
        self.misses: int = 0

        # Sentinel head and tail nodes
        self.head: Node = Node("__HEAD__", None)
        self.tail: Node = Node("__TAIL__", None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: Node) -> None:
        """Detaches an existing node from the doubly-linked list."""
        prev_node = node.prev
        next_node = node.next
        if prev_node and next_node:
            prev_node.next = next_node
            next_node.prev = prev_node

    def _add_to_front(self, node: Node) -> None:
        """Inserts node immediately after head sentinel (most recently used)."""
        node.next = self.head.next
        node.prev = self.head
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node

    def get(self, key: str) -> Optional[Any]:
        """Retrieves item by key and marks it as most recently used."""
        if key in self.lookup:
            node = self.lookup[key]
            self._remove(node)
            self._add_to_front(node)
            self.hits += 1
            return node.value
        self.misses += 1
        return None

    def put(self, key: str, value: Any) -> Optional[str]:
        """
        Inserts or updates key-value pair.
        Returns the evicted key if capacity was exceeded, else None.
        """
        evicted_key: Optional[str] = None
        if key in self.lookup:
            node = self.lookup[key]
            node.value = value
            self._remove(node)
            self._add_to_front(node)
            return None

        if len(self.lookup) >= self.capacity:
            # Evict least recently used (node before tail sentinel)
            lru_node = self.tail.prev
            if lru_node and lru_node != self.head:
                self._remove(lru_node)
                del self.lookup[lru_node.key]
                evicted_key = lru_node.key

        new_node = Node(key, value)
        self.lookup[key] = new_node
        self._add_to_front(new_node)
        return evicted_key

    def size(self) -> int:
        """Returns the current number of cached items."""
        return len(self.lookup)

    def clear(self) -> None:
        """Resets the cache, freeing all nodes and counters."""
        self.lookup.clear()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.hits = 0
        self.misses = 0

    def get_hit_ratio(self) -> float:
        """Computes current hit ratio between 0.0 and 1.0."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round(self.hits / total, 4)

