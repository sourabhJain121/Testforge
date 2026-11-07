"""
samples/interval_set.py - Disjoint Interval Union and Query Utility.
License: MIT
Author: TestForge Benchmark Suite
LOC: ~115 lines
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple


@dataclass(frozen=True)
class Interval:
    """Half-open continuous interval [start, end)."""
    start: float
    end: float

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError(f"Invalid interval: start ({self.start}) cannot exceed end ({self.end})")

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def is_empty(self) -> bool:
        return self.start == self.end

    def contains(self, point: float) -> bool:
        return self.start <= point < self.end

    def overlaps(self, other: "Interval") -> bool:
        """True if the two intervals share any common points."""
        return max(self.start, other.start) < min(self.end, other.end)

    def touches(self, other: "Interval") -> bool:
        """True if the intervals overlap or are immediately adjacent."""
        return max(self.start, other.start) <= min(self.end, other.end)

    def merge(self, other: "Interval") -> "Interval":
        if not self.touches(other):
            raise ValueError(f"Cannot merge disjoint intervals: {self} and {other}")
        return Interval(min(self.start, other.start), max(self.end, other.end))

    def intersection(self, other: "Interval") -> Optional["Interval"]:
        s = max(self.start, other.start)
        e = min(self.end, other.end)
        return Interval(s, e) if s < e else None


class IntervalSet:
    """
    Maintains a canonical, sorted set of disjoint non-empty intervals.
    Automatically merges adjacent or overlapping spans on insertion.
    """

    def __init__(self, intervals: Optional[List[Interval]] = None):
        self._intervals: List[Interval] = []
        if intervals:
            for iv in intervals:
                self.add(iv)

    def __len__(self) -> int:
        return len(self._intervals)

    def __iter__(self) -> Iterator[Interval]:
        return iter(self._intervals)

    @property
    def total_length(self) -> float:
        return sum(iv.length for iv in self._intervals)

    def add(self, new_iv: Interval) -> None:
        if new_iv.is_empty:
            return

        merged_start = new_iv.start
        merged_end = new_iv.end
        new_list: List[Interval] = []
        inserted = False

        for iv in self._intervals:
            if iv.end < merged_start:
                new_list.append(iv)
            elif iv.start > merged_end:
                if not inserted:
                    new_list.append(Interval(merged_start, merged_end))
                    inserted = True
                new_list.append(iv)
            else:
                # Overlap or touch: expand merge boundary
                merged_start = min(merged_start, iv.start)
                merged_end = max(merged_end, iv.end)

        if not inserted:
            new_list.append(Interval(merged_start, merged_end))

        self._intervals = new_list

    def contains_point(self, point: float) -> bool:
        for iv in self._intervals:
            if iv.contains(point):
                return True
            if iv.start > point:
                break
        return False

    def intersect(self, other: "IntervalSet") -> "IntervalSet":
        result = IntervalSet()
        for a in self._intervals:
            for b in other._intervals:
                if b.start >= a.end:
                    break
                common = a.intersection(b)
                if common:
                    result.add(common)
        return result

    def to_tuples(self) -> List[Tuple[float, float]]:
        return [(iv.start, iv.end) for iv in self._intervals]
