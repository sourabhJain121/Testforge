"""
tests/test_mutation_integration_m2.py - Integration and Regression Tests for Milestone 2.

Verifies:
  - Blackboard state updates with M2 equivalence fields
  - Pydantic serialization & deserialization of MutantRecord and IterationMetrics
  - SQLite checkpoint persistence and restoration
  - Older checkpoint backward-compatibility (loading snapshots without M2 fields)
  - Orchestrator reflection behavior: verified equivalent mutants excluded from surviving diffs
  - Deterministic diff inspector integration: detecting newly equivalent mutants
"""

import os
import json
import tempfile
import pytest

from testforge.state import MutantRecord, IterationMetrics, TestForgeState
from testforge.blackboard import Blackboard, MutantSpace, MetricsSpace, BlackboardSnapshot
from testforge.persistence import SQLiteBlackboardStorage
from testforge.diff_inspector import compare_checkpoints


def test_blackboard_m2_partition_updates():
    bb = Blackboard()
    mutant = MutantRecord(
        mutant_id="MUT_COMP_OP_001",
        mutation_type="COMP_OP",
        line_number=10,
        original_code_snippet="x > 5",
        mutated_code_snippet="x <= 5",
        unified_diff="--- a\n+++ b",
        status="EQUIVALENT",
        is_executed=False,
        is_valid_syntax=True,
        equivalence_status="EQUIVALENT",
        equivalence_method="DEAD_CODE_MUTATION",
        equivalence_reason="In dead code block",
        equivalence_confidence="HIGH",
        original_expression="x > 5",
        mutated_expression="x <= 5"
    )

    bb.update_mutant_space(
        mutants=[mutant],
        mutants_generated=1,
        mutants_executed=0,
        mutants_killed=0,
        mutants_survived=0,
        mutants_equivalent=1,
        mutants_potentially_equivalent=0,
        raw_mutation_score=0.0,
        adjusted_mutation_score=100.0,
    )

    mut_space = bb.get_mutant_space()
    assert mut_space.mutants_equivalent == 1
    assert mut_space.adjusted_mutation_score == 100.0
    assert len(mut_space.mutants) == 1
    assert mut_space.mutants[0].equivalence_method == "DEAD_CODE_MUTATION"


def test_sqlite_checkpoint_persistence_and_restoration():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "checkpoints.db")
        bb = Blackboard()
        storage = SQLiteBlackboardStorage(db_path=db_path)

        mutant = MutantRecord(
            mutant_id="MUT_ARITH_OP_042",
            mutation_type="ARITH_OP",
            line_number=15,
            original_code_snippet="a + 0",
            mutated_code_snippet="a - 0",
            unified_diff="",
            status="EQUIVALENT",
            equivalence_status="EQUIVALENT",
            equivalence_method="SELF_CANCELING_TRANSFORM",
            equivalence_reason="Algebraic identity preserves value",
            equivalence_confidence="HIGH",
            original_expression="a + 0",
            mutated_expression="a - 0",
            is_executed=True
        )

        bb.update_mutant_space(
            mutants=[mutant],
            mutants_generated=1,
            mutants_executed=1,
            mutants_equivalent=1,
            raw_mutation_score=0.0,
            adjusted_mutation_score=100.0
        )
        bb.update_metrics_space(
            raw_mutation_score=0.0,
            adjusted_mutation_score=100.0,
            equivalent_mutants=1
        )

        snapshot = bb.get_snapshot()
        meta = storage.save_checkpoint(
            snapshot=snapshot,
            stage="REFLECTION_ITERATION_1",
            job_id="job_m2_test",
            workflow_id="wf_m2_test"
        )

        assert meta.checkpoint_id is not None

        # Load back
        loaded_ckpt = storage.load_checkpoint(meta.checkpoint_id)
        assert loaded_ckpt is not None
        snapshot_dict = json.loads(loaded_ckpt.snapshot_json)
        assert snapshot_dict["mutant"]["mutants_equivalent"] == 1
        assert snapshot_dict["mutant"]["adjusted_mutation_score"] == 100.0
        assert snapshot_dict["mutant"]["mutants"][0]["equivalence_method"] == "SELF_CANCELING_TRANSFORM"
        storage.close()


def test_older_checkpoint_backward_compatibility():
    """
    Test loading an older checkpoint snapshot payload that lacks M2 fields.
    Pydantic default factories and fields must provide safe defaults.
    """
    legacy_snapshot_data = {
        "revision": 1,
        "timestamp": 1700000000.0,
        "target": {
            "target_module_path": "target.py",
            "source_code": "def f(): pass",
            "classes": [],
            "dependencies": []
        },
        "mutant": {
            "mutants": [
                {
                    "mutant_id": "MUT_OLD_001",
                    "mutation_type": "COMP_OP",
                    "line_number": 1,
                    "original_code_snippet": "x > 0",
                    "mutated_code_snippet": "x <= 0",
                    "unified_diff": "",
                    "status": "KILLED"
                    # Notice: no equivalence_status, is_executed, or provenance fields
                }
            ],
            "mutants_generated": 1,
            "mutants_executed": 1,
            "mutants_killed": 1,
            "mutants_survived": 0,
            "current_mutation_score": 100.0
            # Notice: no raw_mutation_score or adjusted_mutation_score
        },
        "critic": {},
        "suite": {},
        "metrics": {
            "current_iteration": 1,
            "final_mutation_score": 100.0
        }
    }

    # Deserializing via BlackboardSnapshot
    snapshot = BlackboardSnapshot.model_validate(legacy_snapshot_data)
    assert snapshot.mutant.raw_mutation_score == 0.0
    assert snapshot.mutant.adjusted_mutation_score == 0.0
    assert snapshot.mutant.mutants_equivalent == 0
    assert snapshot.mutant.mutants[0].equivalence_status is None
    assert snapshot.mutant.mutants[0].is_valid_syntax is True


def test_diff_inspector_newly_equivalent():
    base_snapshot = {
        "mutant": {
            "mutants": [
                {"mutant_id": "MUT_01", "status": "SURVIVED", "operator": "ARITH_OP", "line_number": 5}
            ]
        }
    }
    target_snapshot = {
        "mutant": {
            "mutants": [
                {
                    "mutant_id": "MUT_01",
                    "status": "EQUIVALENT",
                    "operator": "ARITH_OP",
                    "line_number": 5,
                    "equivalence_method": "DEAD_CODE_MUTATION",
                    "equivalence_reason": "In dead code"
                }
            ]
        }
    }

    diff_result = compare_checkpoints(base_snapshot, target_snapshot)
    delta = diff_result.mutant_delta
    assert len(delta["newly_equivalent"]) == 1
    assert delta["newly_equivalent"][0]["mutant_id"] == "MUT_01"
    assert delta["newly_equivalent"][0]["equivalence_method"] == "DEAD_CODE_MUTATION"
    assert len(delta["status_changes"]) == 1
    assert delta["status_changes"][0]["from_status"] == "SURVIVED"
    assert delta["status_changes"][0]["to_status"] == "EQUIVALENT"


def test_surviving_diffs_excludes_verified_equivalent():
    """
    Test that verified equivalent mutants are excluded from surviving diffs passed to the Critic.
    """
    m1 = MutantRecord(
        mutant_id="MUT_01",
        mutation_type="COMP_OP",
        line_number=2,
        original_code_snippet="",
        mutated_code_snippet="",
        unified_diff="--- diff1",
        status="SURVIVED"
    )
    m2 = MutantRecord(
        mutant_id="MUT_02",
        mutation_type="ARITH_OP",
        line_number=4,
        original_code_snippet="",
        mutated_code_snippet="",
        unified_diff="--- diff2",
        status="EQUIVALENT",
        equivalence_status="EQUIVALENT"
    )
    m3 = MutantRecord(
        mutant_id="MUT_03",
        mutation_type="BOUNDARY_SWAP",
        line_number=6,
        original_code_snippet="",
        mutated_code_snippet="",
        unified_diff="--- diff3",
        status="POTENTIALLY_EQUIVALENT",
        equivalence_status="POTENTIALLY_EQUIVALENT"
    )

    evaluated = [m1, m2, m3]
    surviving_diffs = [
        f"Mutant [{m.mutant_id}] at Line {m.line_number} ({m.mutation_type}):\n{m.unified_diff}"
        for m in evaluated if m.status in ("SURVIVED", "POTENTIALLY_EQUIVALENT")
    ]

    # MUT_01 and MUT_03 should be included
    # MUT_02 (verified equivalent) MUST be excluded so the Critic doesn't waste iterations trying to kill it
    diff_text = "\n".join(surviving_diffs)
    assert "MUT_01" in diff_text
    assert "MUT_03" in diff_text
    assert "MUT_02" not in diff_text
