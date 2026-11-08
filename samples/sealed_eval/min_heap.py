"""
samples/sealed_eval/min_heap.py

Domain: Data Structures & Algorithms
Implements an array-backed binary min-heap priority queue.
"""

from typing import List, Optional, Any


class MinHeap:
    """Array-backed binary min-heap where parent <= children."""

    def __init__(self, items: Optional[List[float]] = None):
        self._heap: List[float] = []
        if items:
            for it in items:
                self.push(float(it))

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def peek(self) -> Optional[float]:
        """Returns the smallest element without removing it."""
        if not self._heap:
            return None
        return self._heap[0]

    def push(self, value: float) -> None:
        """Inserts a new value and sifts it up to maintain heap property."""
        self._heap.append(value)
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> Optional[float]:
        """Removes and returns the minimum element."""
        if not self._heap:
            return None
        if len(self._heap) == 1:
            return self._heap.pop()

        min_val = self._heap[0]
        self._heap[0] = self._heap.pop()
        self._sift_down(0)
        return min_val

    def _sift_up(self, index: int) -> None:
        parent = (index - 1) // 2
        while index > 0 and self._heap[index] < self._heap[parent]:
            self._heap[index], self._heap[parent] = self._heap[parent], self._heap[index]
            index = parent
            parent = (index - 1) // 2

    def _sift_down(self, index: int) -> None:
        size = len(self._heap)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index

            if left < size and self._heap[left] < self._heap[smallest]:
                smallest = left
            if right < size and self._heap[right] < self._heap[smallest]:
                smallest = right

            if smallest != index:
                self._heap[index], self._heap[smallest] = self._heap[smallest], self._heap[index]
                index = smallest
            else:
                break

    def to_sorted_list(self) -> List[float]:
        """Drains a copy of the heap into a sorted ascending list."""
        copy_heap = MinHeap(self._heap)
        res: List[float] = []
        while not copy_heap.is_empty():
            val = copy_heap.pop()
            if val is not None:
                res.append(val)
        return res
