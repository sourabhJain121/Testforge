"""
test_checkpoint_diff.py - Unit tests for Deterministic Blackboard Checkpoint Diff Inspector.

Covers:
  - Added, removed, and changed scalar fields
  - Nested dictionary additions, removals, and changes
  - List element changes and mutant-id keying
  - Missing vs explicit Null (None) discrimination
  - Empty object ({}) vs missing object
  - Key ordering independence (deterministic output)
  - Malformed or heterogeneous payloads
  - Partition categorization
  - Mutant delta calculation (newly generated, killed, survived)
"""

import json

import pytest

from testforge.diff_inspector import (
    DeterministicDiffInspector,
    DiffChangeType,
    compare_checkpoints,
)


class TestDeterministicDiffInspector:

    def test_added_field(self):
        base = {"target": {"file_path": "sample.py"}}
        target = {"target": {"file_path": "sample.py", "line_count": 42}}

        result = compare_checkpoints(base, target)
        assert result.summary.added_count == 1
        assert result.summary.removed_count == 0
        assert result.summary.changed_count == 0
        diff = result.differences[0]
        assert diff.path == "target.line_count"
        assert diff.change_type == DiffChangeType.ADDED
        assert diff.target_value == 42
        assert diff.partition == "target"

    def test_removed_field(self):
        base = {"metrics": {"mutation_score": 85.0, "coverage": 90.0}}
        target = {"metrics": {"mutation_score": 85.0}}

        result = compare_checkpoints(base, target)
        assert result.summary.removed_count == 1
        diff = result.differences[0]
        assert diff.path == "metrics.coverage"
        assert diff.change_type == DiffChangeType.REMOVED
        assert diff.base_value == 90.0
        assert diff.partition == "metrics"

    def test_changed_scalar_value(self):
        base = {"metrics": {"mutation_score": 50.0}}
        target = {"metrics": {"mutation_score": 85.0}}

        result = compare_checkpoints(base, target)
        assert result.summary.changed_count == 1
        diff = result.differences[0]
        assert diff.path == "metrics.mutation_score"
        assert diff.change_type == DiffChangeType.CHANGED
        assert diff.base_value == 50.0
        assert diff.target_value == 85.0

    def test_nested_dictionary_changes(self):
        base = {
            "critic": {
                "review": {
                    "approved": False,
                    "iteration": 1,
                    "notes": "Add more edge cases"
                }
            }
        }
        target = {
            "critic": {
                "review": {
                    "approved": True,
                    "iteration": 2,
                    "notes": "All mutants killed"
                }
            }
        }

        result = compare_checkpoints(base, target)
        assert result.summary.changed_count == 3
        paths = [d.path for d in result.differences]
        assert "critic.review.approved" in paths
        assert "critic.review.iteration" in paths
        assert "critic.review.notes" in paths

    def test_missing_vs_null_discrimination(self):
        """
        Crucial requirement: Explicitly distinguish between a field missing
        versus a field explicitly set to null (None).
        """
        # Case 1: missing in base, explicitly null in target
        base1 = {"suite": {}}
        target1 = {"suite": {"test_module_path": None}}
        res1 = compare_checkpoints(base1, target1)
        assert res1.summary.missing_vs_null_count == 1
        diff1 = res1.differences[0]
        assert diff1.path == "suite.test_module_path"
        assert diff1.change_type == DiffChangeType.MISSING_VS_NULL
        assert diff1.is_missing_in_base is True
        assert diff1.is_null_in_target is True

        # Case 2: explicitly null in base, missing in target
        base2 = {"suite": {"test_module_path": None}}
        target2 = {"suite": {}}
        res2 = compare_checkpoints(base2, target2)
        assert res2.summary.missing_vs_null_count == 1
        diff2 = res2.differences[0]
        assert diff2.is_null_in_base is True
        assert diff2.is_missing_in_target is True

        # Case 3: explicitly null in both -> unchanged
        base3 = {"suite": {"test_module_path": None}}
        target3 = {"suite": {"test_module_path": None}}
        res3 = compare_checkpoints(base3, target3, include_unchanged=True)
        assert res3.summary.missing_vs_null_count == 0
        assert res3.summary.unchanged_count == 1

    def test_empty_object_vs_missing_object(self):
        base = {"target": {}}
        target = {}

        result = compare_checkpoints(base, target)
        assert result.summary.removed_count == 1
        diff = result.differences[0]
        assert diff.path == "target"
        assert diff.change_type == DiffChangeType.REMOVED
        assert diff.base_value == {}

    def test_dictionary_key_ordering_invariance(self):
        """
        Diff results must be deterministic regardless of dictionary insertion order.
        """
        base1 = {"a": 1, "b": 2, "c": 3}
        target1 = {"c": 3, "b": 20, "a": 1}

        base2 = {"c": 3, "a": 1, "b": 2}
        target2 = {"a": 1, "c": 3, "b": 20}

        res1 = compare_checkpoints(base1, target1)
        res2 = compare_checkpoints(base2, target2)

        assert res1.summary.model_dump() == res2.summary.model_dump()
        assert [d.model_dump() for d in res1.differences] == [d.model_dump() for d in res2.differences]

    def test_list_changes_positional(self):
        base = {"tags": ["a", "b"]}
        target = {"tags": ["a", "c", "d"]}

        result = compare_checkpoints(base, target)
        # tags[1] changed from 'b' to 'c', tags[2] added 'd'
        assert result.summary.total_differences >= 2
        paths = [d.path for d in result.differences]
        assert "tags[1]" in paths
        assert "tags[2]" in paths

    def test_mutant_list_diff_and_transitions(self):
        base = {
            "mutant": {
                "mutants": [
                    {"mutant_id": "m1", "operator": "AOR", "line_number": 10, "killed": False, "diff": "- a + b\n+ a - b"},
                    {"mutant_id": "m2", "operator": "ROR", "line_number": 15, "killed": True, "diff": "- x > 0\n+ x >= 0"},
                ]
            }
        }
        target = {
            "mutant": {
                "mutants": [
                    {"mutant_id": "m1", "operator": "AOR", "line_number": 10, "killed": True, "diff": "- a + b\n+ a - b"},
                    {"mutant_id": "m3", "operator": "COR", "line_number": 20, "killed": False, "diff": "- and\n+ or"},
                ]
            }
        }

        result = compare_checkpoints(base, target)
        delta = result.mutant_delta

        # m1 transitioned from SURVIVED to KILLED
        assert len(delta["newly_killed"]) == 1
        assert delta["newly_killed"][0]["mutant_id"] == "m1"

        # m3 is newly generated
        assert len(delta["newly_generated"]) == 1
        assert delta["newly_generated"][0]["mutant_id"] == "m3"

        # m2 was removed in target
        removed_diffs = [d for d in result.differences if d.change_type == DiffChangeType.REMOVED]
        assert any("m2" in d.path for d in removed_diffs)

    def test_malformed_data_handling(self):
        """Heterogeneous data, mixed types, non-dict root."""
        base = {"data": [1, 2, 3]}
        target = {"data": "not a list anymore"}

        result = compare_checkpoints(base, target)
        assert result.summary.changed_count == 1
        assert result.differences[0].change_type == DiffChangeType.CHANGED

    def test_partition_categorization(self):
        base = {
            "metadata": {"stage": "INIT"},
            "target": {"module": "mod_a"},
            "suite": {"tests": 0},
            "mutant": {"count": 0},
            "metrics": {"score": 0.0},
            "critic": {"approved": False},
            "unknown_partition": {"val": 1}
        }
        target = {
            "metadata": {"stage": "HARDENED"},
            "target": {"module": "mod_b"},
            "suite": {"tests": 5},
            "mutant": {"count": 10},
            "metrics": {"score": 90.0},
            "critic": {"approved": True},
            "unknown_partition": {"val": 2}
        }

        result = compare_checkpoints(base, target)
        assert result.summary.changed_count == 7
        assert "metadata" in result.partition_summaries
        assert "target" in result.partition_summaries
        assert "suite" in result.partition_summaries
        assert "mutant" in result.partition_summaries
        assert "metrics" in result.partition_summaries
        assert "critic" in result.partition_summaries
        assert "other" in result.partition_summaries
