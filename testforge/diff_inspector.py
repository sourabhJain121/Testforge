"""
diff_inspector.py - Deterministic Blackboard Checkpoint Diff & Comparison Engine.

Provides deep, semantic, and deterministic comparisons between two TestForge
Blackboard checkpoints or arbitrary snapshot payloads.

Guarantees:
  1. Determinism: Exact identical inputs yield exact identical diff outputs
     regardless of dictionary insertion order.
  2. Partition-Aware: Semantic grouping by Blackboard partition (metadata,
     target, suite, mutant, metrics, critic).
  3. Edge-Case Discrimination: Explicitly distinguishes between missing fields,
     explicit nulls (None), empty collections ({}, []), and zero/false values.
  4. Specialized Mutant Deltas: Tracks mutants transitioned across killed,
     survived, or newly synthesized across stages.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from pydantic import BaseModel, Field


class DiffChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"
    MISSING_VS_NULL = "MISSING_VS_NULL"
    UNCHANGED = "UNCHANGED"


class DiffItem(BaseModel):
    """Represents a discrete difference at a specific object path."""
    path: str
    partition: str
    change_type: DiffChangeType
    base_value: Any = None
    target_value: Any = None
    description: str = ""
    is_missing_in_base: bool = False
    is_missing_in_target: bool = False
    is_null_in_base: bool = False
    is_null_in_target: bool = False


class DiffSummary(BaseModel):
    """Aggregate statistics for a checkpoint comparison."""
    total_differences: int = 0
    added_count: int = 0
    removed_count: int = 0
    changed_count: int = 0
    missing_vs_null_count: int = 0
    unchanged_count: int = 0


class MutantTransition(BaseModel):
    """Tracks a single mutant's lifecycle change between checkpoints."""
    mutant_id: str
    operator: str = ""
    line_number: int = 0
    base_status: Optional[str] = None
    target_status: Optional[str] = None
    diff_patch: Optional[str] = None


class CheckpointDiffResult(BaseModel):
    """Complete structured diff between two checkpoints."""
    base_checkpoint_id: Optional[str] = None
    target_checkpoint_id: Optional[str] = None
    base_stage: Optional[str] = None
    target_stage: Optional[str] = None
    base_created_at: Optional[float] = None
    target_created_at: Optional[float] = None
    summary: DiffSummary = Field(default_factory=DiffSummary)
    partition_summaries: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    differences: List[DiffItem] = Field(default_factory=list)
    mutant_delta: Dict[str, List[Any]] = Field(default_factory=dict)


_SENTINEL_MISSING = object()


def _classify_partition(path: str) -> str:
    """Extracts top-level Blackboard partition from dotted path."""
    parts = path.split(".")
    root = parts[0] if parts else "general"
    known = {"metadata", "target", "suite", "mutant", "metrics", "critic"}
    return root if root in known else "other"


def _deterministic_sort_key(item: Any) -> str:
    """Helper to deterministically sort arbitrary items."""
    if isinstance(item, (int, float, str, bool)):
        return str(item)
    if isinstance(item, dict):
        return str(sorted(item.items(), key=lambda kv: str(kv[0])))
    return str(item)


class DeterministicDiffInspector:
    """
    Engine for computing deterministic, semantic diffs across Blackboard snapshots.
    """

    def __init__(self, include_unchanged: bool = False):
        self.include_unchanged = include_unchanged

    def compare(
        self,
        base_data: Any,
        target_data: Any,
        base_checkpoint_id: Optional[str] = None,
        target_checkpoint_id: Optional[str] = None,
        base_stage: Optional[str] = None,
        target_stage: Optional[str] = None,
        base_created_at: Optional[float] = None,
        target_created_at: Optional[float] = None,
    ) -> CheckpointDiffResult:
        """
        Executes a deterministic diff between two snapshot dictionaries or structures.
        """
        differences: List[DiffItem] = []
        
        # Traverse recursively
        self._diff_recursive(base_data, target_data, path="", differences=differences)
        
        # Sort differences deterministically by path
        differences.sort(key=lambda d: d.path)

        # Compute summary counts
        summary = DiffSummary()
        partition_summaries: Dict[str, Dict[str, int]] = {}

        for diff in differences:
            part = diff.partition
            if part not in partition_summaries:
                partition_summaries[part] = {
                    "total": 0, "added": 0, "removed": 0,
                    "changed": 0, "missing_vs_null": 0, "unchanged": 0
                }

            if diff.change_type == DiffChangeType.ADDED:
                summary.added_count += 1
                summary.total_differences += 1
                partition_summaries[part]["added"] += 1
                partition_summaries[part]["total"] += 1
            elif diff.change_type == DiffChangeType.REMOVED:
                summary.removed_count += 1
                summary.total_differences += 1
                partition_summaries[part]["removed"] += 1
                partition_summaries[part]["total"] += 1
            elif diff.change_type == DiffChangeType.CHANGED:
                summary.changed_count += 1
                summary.total_differences += 1
                partition_summaries[part]["changed"] += 1
                partition_summaries[part]["total"] += 1
            elif diff.change_type == DiffChangeType.MISSING_VS_NULL:
                summary.missing_vs_null_count += 1
                summary.total_differences += 1
                partition_summaries[part]["missing_vs_null"] += 1
                partition_summaries[part]["total"] += 1
            elif diff.change_type == DiffChangeType.UNCHANGED:
                summary.unchanged_count += 1
                partition_summaries[part]["unchanged"] += 1

        # Calculate specialized mutant deltas
        mutant_delta = self._compute_mutant_deltas(base_data, target_data)

        # Filter out UNCHANGED items if not requested
        final_diffs = differences if self.include_unchanged else [
            d for d in differences if d.change_type != DiffChangeType.UNCHANGED
        ]

        return CheckpointDiffResult(
            base_checkpoint_id=base_checkpoint_id,
            target_checkpoint_id=target_checkpoint_id,
            base_stage=base_stage,
            target_stage=target_stage,
            base_created_at=base_created_at,
            target_created_at=target_created_at,
            summary=summary,
            partition_summaries=partition_summaries,
            differences=final_diffs,
            mutant_delta=mutant_delta
        )

    def _diff_recursive(
        self,
        base_val: Any,
        target_val: Any,
        path: str,
        differences: List[DiffItem]
    ) -> None:
        partition = _classify_partition(path)

        # 1. Check for Missing vs Null edge cases
        if base_val is _SENTINEL_MISSING and target_val is None:
            differences.append(DiffItem(
                path=path,
                partition=partition,
                change_type=DiffChangeType.MISSING_VS_NULL,
                base_value=None,
                target_value=None,
                description=f"Field '{path}' is missing in base checkpoint but explicitly null in target.",
                is_missing_in_base=True,
                is_null_in_target=True
            ))
            return

        if base_val is None and target_val is _SENTINEL_MISSING:
            differences.append(DiffItem(
                path=path,
                partition=partition,
                change_type=DiffChangeType.MISSING_VS_NULL,
                base_value=None,
                target_value=None,
                description=f"Field '{path}' is explicitly null in base checkpoint but missing in target.",
                is_null_in_base=True,
                is_missing_in_target=True
            ))
            return

        # 2. Check for pure Addition (missing in base)
        if base_val is _SENTINEL_MISSING:
            differences.append(DiffItem(
                path=path,
                partition=partition,
                change_type=DiffChangeType.ADDED,
                base_value=None,
                target_value=target_val,
                description=f"Field '{path}' added with value {repr(target_val)}",
                is_missing_in_base=True
            ))
            return

        # 3. Check for pure Removal (missing in target)
        if target_val is _SENTINEL_MISSING:
            differences.append(DiffItem(
                path=path,
                partition=partition,
                change_type=DiffChangeType.REMOVED,
                base_value=base_val,
                target_value=None,
                description=f"Field '{path}' removed (was {repr(base_val)})",
                is_missing_in_target=True
            ))
            return

        # 4. Both are dictionaries -> recurse with sorted keys
        if isinstance(base_val, dict) and isinstance(target_val, dict):
            # Deterministic sorted union of keys
            all_keys = sorted(set(base_val.keys()) | set(target_val.keys()))
            
            # Check empty vs populated dict
            if not base_val and not target_val:
                if self.include_unchanged and path:
                    differences.append(DiffItem(
                        path=path,
                        partition=partition,
                        change_type=DiffChangeType.UNCHANGED,
                        base_value={},
                        target_value={},
                        description=f"Field '{path}' is empty dict in both."
                    ))
                return

            for key in all_keys:
                sub_path = f"{path}.{key}" if path else key
                sub_base = base_val.get(key, _SENTINEL_MISSING)
                sub_target = target_val.get(key, _SENTINEL_MISSING)
                self._diff_recursive(sub_base, sub_target, sub_path, differences)
            return

        # 5. Both are lists -> compare deterministically
        if isinstance(base_val, list) and isinstance(target_val, list):
            # Check if both are empty
            if not base_val and not target_val:
                if self.include_unchanged and path:
                    differences.append(DiffItem(
                        path=path,
                        partition=partition,
                        change_type=DiffChangeType.UNCHANGED,
                        base_value=[],
                        target_value=[],
                        description=f"Field '{path}' is empty list in both."
                    ))
                return

            # Check if elements are dicts with identifiable keys (e.g., 'mutant_id' or 'name')
            if (base_val and isinstance(base_val[0], dict) and "mutant_id" in base_val[0]) or \
               (target_val and isinstance(target_val[0], dict) and "mutant_id" in target_val[0]):
                self._diff_mutant_list(base_val, target_val, path, differences)
                return

            # Positional list comparison
            max_len = max(len(base_val), len(target_val))
            for idx in range(max_len):
                sub_path = f"{path}[{idx}]"
                sub_base = base_val[idx] if idx < len(base_val) else _SENTINEL_MISSING
                sub_target = target_val[idx] if idx < len(target_val) else _SENTINEL_MISSING
                self._diff_recursive(sub_base, sub_target, sub_path, differences)
            return

        # 6. Type mismatch (e.g. string vs dict, or list vs None)
        if type(base_val) is not type(target_val):
            differences.append(DiffItem(
                path=path,
                partition=partition,
                change_type=DiffChangeType.CHANGED,
                base_value=base_val,
                target_value=target_val,
                description=f"Type changed from {type(base_val).__name__} to {type(target_val).__name__}"
            ))
            return

        # 7. Scalar comparison (str, int, float, bool, None)
        if base_val == target_val:
            if self.include_unchanged:
                differences.append(DiffItem(
                    path=path,
                    partition=partition,
                    change_type=DiffChangeType.UNCHANGED,
                    base_value=base_val,
                    target_value=target_val,
                    description=f"Field '{path}' unchanged ({repr(base_val)})"
                ))
        else:
            differences.append(DiffItem(
                path=path,
                partition=partition,
                change_type=DiffChangeType.CHANGED,
                base_value=base_val,
                target_value=target_val,
                description=f"Value changed from {repr(base_val)} to {repr(target_val)}"
            ))

    def _diff_mutant_list(
        self,
        base_list: List[Dict[str, Any]],
        target_list: List[Dict[str, Any]],
        path: str,
        differences: List[DiffItem]
    ) -> None:
        """Compares list of mutant dicts indexed by mutant_id."""
        base_map = {m.get("mutant_id"): m for m in base_list if isinstance(m, dict) and "mutant_id" in m}
        target_map = {m.get("mutant_id"): m for m in target_list if isinstance(m, dict) and "mutant_id" in m}
        all_ids = sorted(set(base_map.keys()) | set(target_map.keys()))

        partition = _classify_partition(path)
        for m_id in all_ids:
            sub_path = f"{path}[{m_id}]"
            b_item = base_map.get(m_id, _SENTINEL_MISSING)
            t_item = target_map.get(m_id, _SENTINEL_MISSING)
            self._diff_recursive(b_item, t_item, sub_path, differences)

    def _compute_mutant_deltas(self, base_data: Any, target_data: Any) -> Dict[str, List[Any]]:
        """Identifies newly killed, survived, equivalent, or generated mutants."""
        delta: Dict[str, List[Any]] = {
            "newly_generated": [],
            "newly_killed": [],
            "newly_survived": [],
            "newly_equivalent": [],
            "newly_potentially_equivalent": [],
            "status_changes": []
        }

        if not isinstance(base_data, dict) or not isinstance(target_data, dict):
            return delta

        base_mutants = base_data.get("mutant", {}).get("mutants", [])
        target_mutants = target_data.get("mutant", {}).get("mutants", [])

        if not isinstance(base_mutants, list) or not isinstance(target_mutants, list):
            return delta

        base_map = {m.get("mutant_id"): m for m in base_mutants if isinstance(m, dict) and "mutant_id" in m}
        target_map = {m.get("mutant_id"): m for m in target_mutants if isinstance(m, dict) and "mutant_id" in m}

        def _get_status(m: Dict[str, Any]) -> str:
            st = m.get("status")
            if st:
                return str(st).upper()
            return "KILLED" if m.get("killed") else "SURVIVED"

        for m_id, t_m in target_map.items():
            t_status = _get_status(t_m)
            operator = t_m.get("mutation_type") or t_m.get("operator", "")
            diff_text = t_m.get("unified_diff") or t_m.get("diff", "")
            line_no = t_m.get("line_number", 0)

            mutant_info: Dict[str, Any] = {
                "mutant_id": m_id,
                "operator": operator,
                "line_number": line_no,
                "status": t_status,
                "diff": diff_text
            }
            if t_m.get("equivalence_method"):
                mutant_info["equivalence_method"] = t_m.get("equivalence_method")
            if t_m.get("equivalence_reason"):
                mutant_info["equivalence_reason"] = t_m.get("equivalence_reason")

            if m_id not in base_map:
                delta["newly_generated"].append(mutant_info)
                if t_status == "EQUIVALENT":
                    delta["newly_equivalent"].append(mutant_info)
                elif t_status == "POTENTIALLY_EQUIVALENT":
                    delta["newly_potentially_equivalent"].append(mutant_info)
            else:
                b_m = base_map[m_id]
                b_status = _get_status(b_m)
                if b_status != t_status:
                    delta["status_changes"].append({
                        "mutant_id": m_id,
                        "from_status": b_status,
                        "to_status": t_status,
                        "equivalence_method": t_m.get("equivalence_method"),
                        "equivalence_reason": t_m.get("equivalence_reason")
                    })
                    if t_status == "KILLED":
                        delta["newly_killed"].append(mutant_info)
                    elif t_status == "SURVIVED":
                        delta["newly_survived"].append(mutant_info)
                    elif t_status == "EQUIVALENT":
                        delta["newly_equivalent"].append(mutant_info)
                    elif t_status == "POTENTIALLY_EQUIVALENT":
                        delta["newly_potentially_equivalent"].append(mutant_info)

        return delta


def compare_checkpoints(
    base_snapshot: Dict[str, Any],
    target_snapshot: Dict[str, Any],
    base_checkpoint_id: Optional[str] = None,
    target_checkpoint_id: Optional[str] = None,
    base_stage: Optional[str] = None,
    target_stage: Optional[str] = None,
    include_unchanged: bool = False
) -> CheckpointDiffResult:
    """Convenience functional entry point for comparing two checkpoint snapshots."""
    inspector = DeterministicDiffInspector(include_unchanged=include_unchanged)
    return inspector.compare(
        base_data=base_snapshot,
        target_data=target_snapshot,
        base_checkpoint_id=base_checkpoint_id,
        target_checkpoint_id=target_checkpoint_id,
        base_stage=base_stage,
        target_stage=target_stage
    )
