"""
tests/test_coverage_hardening.py - Comprehensive Unit & Integration Tests Strengthening TestForge.

Addresses priority areas identified in test audit:
1. Blackboard Concurrency & State Rollback Edge Cases
2. FastMCP Filesystem & Network Error Handling
3. SQLite Checkpoint Persistence Schema Integrity & Corruption Recovery
4. Task Cancellation Idempotency & Lifecycle FSM
5. Granular AST Test Validation & Weak Assertion Rejection
6. API Error Scenarios (400, 404, 422) in server.py
7. Equivalent Mutant Analyzer & Dead Code Triage
8. Pydantic Model Validation Boundaries
"""

import os
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp.exceptions import ToolError

from server import app
from testforge.blackboard import (
    Blackboard,
    BlackboardSnapshot,
    CriticSpace,
    MetricsSpace,
    MutantSpace,
    SuiteSpace,
    TargetSpace,
)
from testforge.equivalence import EquivalenceClassification, EquivalentMutantAnalyzer, calculate_mutation_scores
from testforge.mcp_server import create_filesystem_server
from testforge.orchestrator import TestForgeOrchestrator
from testforge.persistence import (
    CheckpointNotFoundError,
    CorruptedSnapshotError,
    IncompatibleSchemaError,
    SQLiteBlackboardStorage,
)
from testforge.sandbox import GranularTestValidator, ParallelSandboxRunner
from testforge.state import MutantRecord, TestForgeState

# ============================================================================
# 1. Blackboard Concurrency & State Integrity Tests
# ============================================================================

class TestBlackboardHardening:
    """Verifies concurrency safety, partition isolation, and subscriber mechanics."""

    def test_concurrent_partition_updates(self):
        """Verifies multi-threaded concurrent writes to Blackboard partitions do not corrupt state."""
        bb = Blackboard()
        thread_count = 10
        writes_per_thread = 20

        def worker(tid: int):
            for i in range(writes_per_thread):
                bb.update_suite_space(current_test_code=f"# thread {tid} write {i}")
                bb.update_critic_space(latest_directive=f"directive_{tid}_{i}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Both partitions should have valid, uncorrupted strings
        suite = bb.get_suite_space()
        critic = bb.get_critic_space()
        assert suite.current_test_code.startswith("# thread ")
        assert critic.latest_directive.startswith("directive_")

    def test_partition_subscription_and_unsubscription(self):
        """Verifies event callbacks fire on partition updates and can be cleanly unsubscribed."""
        bb = Blackboard()
        events_received = []

        sub_id = bb.subscribe(lambda event: events_received.append(event))
        assert sub_id is not None

        bb.update_metrics_space(target_mutation_score=85.0)
        assert len(events_received) == 1
        assert events_received[0].partition == "metrics"

        # Unsubscribe and verify no further events are received
        bb.unsubscribe(sub_id)
        bb.update_metrics_space(target_mutation_score=95.0)
        assert len(events_received) == 1

    def test_clear_all_subscriptions(self):
        """Verifies clearing all subscriptions prevents stale subscriber invocation."""
        bb = Blackboard()
        counter = {"count": 0}

        bb.subscribe(lambda e: counter.__setitem__("count", counter["count"] + 1))
        bb.subscribe(lambda e: counter.__setitem__("count", counter["count"] + 1))

        bb.update_target_space(blast_risk="LOW")
        assert counter["count"] == 2

        bb.clear_subscriptions()
        bb.update_target_space(blast_risk="HIGH")
        assert counter["count"] == 2


# ============================================================================
# 2. SQLite Persistence Integrity, Corruption & Schema Validation
# ============================================================================

class TestPersistenceHardening:
    """Verifies SQLite persistence error branches, corruption detection, and schema fences."""

    def test_load_non_existent_checkpoint_raises_not_found(self):
        """Verifies loading an unknown checkpoint raises CheckpointNotFoundError."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test_chk.db"
            storage = SQLiteBlackboardStorage(db_path)
            with pytest.raises(CheckpointNotFoundError) as exc_info:
                storage.load_checkpoint("chk_unknown_999999")
            assert "not found" in str(exc_info.value)

    def test_detect_corrupted_snapshot_json(self):
        """Verifies corrupted JSON in the SQLite table is detected and raises CorruptedSnapshotError."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "corrupt.db"
            storage = SQLiteBlackboardStorage(db_path)
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute(
                    "INSERT INTO checkpoints (checkpoint_id, schema_version, stage, revision, created_at, status, metrics_summary_json, snapshot_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("chk_corrupted_payload", 1, "INITIAL", 0, 100.0, "RUNNING", "{}", "{corrupted_raw_bytes:")
                )
                conn.commit()

            with pytest.raises(CorruptedSnapshotError) as exc_info:
                storage.validate_checkpoint("chk_corrupted_payload")
            assert "corrupted snapshot JSON" in str(exc_info.value)

    def test_detect_incompatible_schema_version(self):
        """Verifies forward/incompatible schema versions are rejected by validate_checkpoint."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "schema.db"
            storage = SQLiteBlackboardStorage(db_path)
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute(
                    "INSERT INTO checkpoints (checkpoint_id, schema_version, stage, revision, created_at, status, metrics_summary_json, snapshot_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("chk_future_schema", 999, "INITIAL", 0, 100.0, "RUNNING", "{}", "{}")
                )
                conn.commit()

            with pytest.raises(IncompatibleSchemaError) as exc_info:
                storage.validate_checkpoint("chk_future_schema")
            assert "schema version 999" in str(exc_info.value)

    def test_checkpoint_lifecycle_save_load_delete(self):
        """Verifies round-trip save, load, and deletion of snapshot records."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "lifecycle.db"
            storage = SQLiteBlackboardStorage(db_path)
            bb = Blackboard(storage=storage)
            bb.update_target_space(blast_risk="MEDIUM", source_sha="abcdef123456")

            snap = bb.get_snapshot()
            meta = storage.save_checkpoint(snap, stage="INGESTION")

            assert storage.count_checkpoints() == 1
            record = storage.load_checkpoint(meta.checkpoint_id)
            assert record.metadata.checkpoint_id == meta.checkpoint_id
            assert record.metadata.stage == "INGESTION"

            # Delete checkpoint
            deleted = storage.delete_checkpoint(meta.checkpoint_id)
            assert deleted is True
            assert storage.count_checkpoints() == 0


# ============================================================================
# 3. FastMCP Filesystem Security & Bounded Tool Execution
# ============================================================================

class TestMCPToolsHardening:
    """Verifies FastMCP filesystem sandbox boundaries, sensitive pattern filtering, and metadata tools."""

    @pytest.mark.anyio
    async def test_mcp_rejects_directory_traversal(self):
        """Verifies FastMCP read_text_file rejects paths outside permitted root."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            server = create_filesystem_server(root)
            with pytest.raises(ToolError) as exc_info:
                await server.call_tool("read_text_file", {"path": "../../../etc/passwd"})
            assert "escapes permitted root" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_mcp_rejects_sensitive_credentials_file(self):
        """Verifies FastMCP read_text_file forbids accessing .env or secret config."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            env_file = root / ".env"
            env_file.write_text("API_KEY=supersecret")
            server = create_filesystem_server(root)

            with pytest.raises(ToolError) as exc_info:
                await server.call_tool("read_text_file", {"path": ".env"})
            assert "strictly forbidden" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_mcp_list_directory_filters_sensitive_entries(self):
        """Verifies list_directory hides sensitive credentials while showing safe files."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / ".env").write_text("SECRET=1")
            (root / "safe_module.py").write_text("x = 10\n")
            server = create_filesystem_server(root)

            res = await server.call_tool("list_directory", {"path": "."})
            entries = res[1]["result"]
            names = [e["name"] for e in entries]

            assert ".env" not in names
            assert "safe_module.py" in names

    @pytest.mark.anyio
    async def test_mcp_get_file_info_metadata(self):
        """Verifies get_file_info calculates SHA-256 and line count accurately."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            sample = root / "sample.py"
            sample.write_text("def a(): pass\ndef b(): pass\n")
            server = create_filesystem_server(root)

            res = await server.call_tool("get_file_info", {"path": "sample.py"})
            info = res[1]["result"]

            assert info["is_file"] is True
            assert info["line_count"] == 2
            assert len(info["sha256"]) == 64


# ============================================================================
# 4. AST Test Quality & Weak Assertion Validation
# ============================================================================

class TestASTGranularValidation:
    """Verifies GranularTestValidator catches weak or vacuous tests and identifies helper assertions."""

    def test_rejects_tests_without_meaningful_assertions(self):
        """Verifies test functions that perform simple assignments or trivial assert True are flagged."""
        code = (
            "import pytest\n"
            "def test_vacuous():\n"
            "    x = 1 + 2\n"
            "    y = x * 3\n"
            "def test_assert_constant():\n"
            "    assert True\n"
            "def test_real():\n"
            "    assert 1 + 1 == 2\n"
        )
        preamble, test_nodes, warnings = GranularTestValidator.split_test_module(code)
        assert len(test_nodes) == 3

        name_to_node = {node.name: node for node in test_nodes}
        # Vacuous test (no assertions) -> False
        assert GranularTestValidator.has_meaningful_assertions(name_to_node["test_vacuous"]) is False
        # Trivial constant assertion -> False (correctly rejected by GranularTestValidator!)
        assert GranularTestValidator.has_meaningful_assertions(name_to_node["test_assert_constant"]) is False
        # Meaningful comparison assertion -> True
        assert GranularTestValidator.has_meaningful_assertions(name_to_node["test_real"]) is True

    def test_recognizes_assertions_within_custom_helpers(self):
        """Verifies test functions delegating checks to helper functions are recognized."""
        code = (
            "def custom_verify(result, expected):\n"
            "    assert result == expected\n"
            "def test_delegate():\n"
            "    custom_verify(2 + 2, 4)\n"
        )
        preamble, test_nodes, _ = GranularTestValidator.split_test_module(code)
        import ast
        helper_tree = ast.parse(preamble)
        helpers = {n.name: n for n in helper_tree.body if isinstance(n, ast.FunctionDef)}

        assert GranularTestValidator.has_meaningful_assertions(test_nodes[0], helper_defs=helpers) is True


# ============================================================================
# 5. Task Cancellation & Orchestrator Lifecycle FSM
# ============================================================================

class TestOrchestratorLifecycleHardening:
    """Verifies task cancellation, pre-cancellation flags, and idempotent status checks."""

    def test_pre_cancelled_orchestrator_terminates_immediately(self):
        """Verifies that an orchestrator started with a set cancel_event halts before executing loops."""
        cancel_ev = threading.Event()
        cancel_ev.set()

        orch = TestForgeOrchestrator(
            target_source_code="def sub(a, b): return a - b\n",
            initial_test_code="def test_sub(): assert sub(5, 3) == 2\n",
            cancel_event=cancel_ev,
            max_iterations=1
        )
        state = orch.run()
        assert state.terminated is True
        assert "cancelled" in state.termination_reason.lower()

    def test_check_cancellation_or_timeout_returns_bool(self):
        """Verifies check_cancellation_or_timeout method raises on cancellation and succeeds when clear."""
        from testforge.orchestrator import HardeningCancelledError
        cancel_ev = threading.Event()
        orch = TestForgeOrchestrator(
            target_source_code="def f(): pass\n",
            cancel_event=cancel_ev,
            max_iterations=1
        )
        # Not cancelled yet - check passes cleanly without raising
        orch.check_cancellation_or_timeout()

        # Trigger cancellation - check raises HardeningCancelledError
        cancel_ev.set()
        with pytest.raises(HardeningCancelledError):
            orch.check_cancellation_or_timeout()
        assert orch.is_cancelled is True


# ============================================================================
# 6. Equivalent Mutant Analyzer & Dead Code Triage
# ============================================================================

class TestEquivalenceAnalysisHardening:
    """Verifies EquivalentMutantAnalyzer dead code detection and score adjustments."""

    def test_dead_code_mutant_classified_as_equivalent(self):
        """Verifies mutants planted in unreachable code lines are classified as EQUIVALENT."""
        code = (
            "def compute(x):\n"
            "    return x * 2\n"
            "    # unreachable dead code below\n"
            "    z = x + 10\n"
        )
        analyzer = EquivalentMutantAnalyzer()
        mutant = MutantRecord(
            mutant_id="M_dead_001",
            mutation_type="ARITH_OP",
            line_number=4,
            original_code_snippet="z = x + 10",
            mutated_code_snippet="z = x - 10",
            unified_diff="",
            status="SURVIVED"
        )
        result = analyzer.analyze_mutant(mutant, code)
        assert result.status == EquivalenceClassification.EQUIVALENT

    def test_mutation_score_formula_with_mixed_outcomes(self):
        """Verifies calculate_mutation_scores with killed, survived, timed_out, and equivalent mutants."""
        mutants = [
            MutantRecord(mutant_id="M1", mutation_type="A", line_number=1, original_code_snippet="", mutated_code_snippet="", unified_diff="", status="KILLED"),
            MutantRecord(mutant_id="M2", mutation_type="A", line_number=2, original_code_snippet="", mutated_code_snippet="", unified_diff="", status="TIMEOUT"),
            MutantRecord(mutant_id="M3", mutation_type="A", line_number=3, original_code_snippet="", mutated_code_snippet="", unified_diff="", status="SURVIVED"),
            MutantRecord(mutant_id="M4", mutation_type="A", line_number=4, original_code_snippet="", mutated_code_snippet="", unified_diff="", status="EQUIVALENT"),
        ]
        res = calculate_mutation_scores(mutants)
        # 4 total, 2 caught (1 killed + 1 timeout), 1 survived, 1 equivalent
        # Raw: 2 / 4 = 50.0%
        # Adjusted: 2 / (4 - 1) = 2 / 3 = 66.67%
        assert res["total_mutants"] == 4
        assert res["killed_mutants"] == 1
        assert res["timed_out_mutants"] == 1
        assert res["survived_mutants"] == 1
        assert res["equivalent_mutants"] == 1
        assert res["raw_mutation_score"] == 50.0
        assert res["adjusted_mutation_score"] == pytest.approx(66.67, abs=0.01)


# ============================================================================
# 7. FastAPI Backend Error Handling (400, 404, 422)
# ============================================================================

class TestAPIErrorHandlingHardening:
    """Verifies FastAPI HTTP contract error codes and rejection of invalid payloads."""

    def test_get_non_existent_job_status_returns_404(self):
        """Verifies GET /api/harden/status/{job_id} on unknown id returns 404."""
        client = TestClient(app)
        resp = client.get("/api/harden/status/job_unreal_99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_cancel_non_existent_job_returns_404(self):
        """Verifies POST /api/harden/cancel/{job_id} on unknown id returns 404."""
        client = TestClient(app)
        resp = client.post("/api/harden/cancel/job_unreal_99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_start_hardening_missing_required_fields_returns_400(self):
        """Verifies POST /api/harden/start without required source code returns 400."""
        client = TestClient(app)
        resp = client.post("/api/harden/start", json={"model_name": "gemini-2.0-flash"})
        assert resp.status_code == 400
        assert "required" in resp.json()["detail"].lower()

    def test_get_non_existent_checkpoint_returns_404(self):
        """Verifies GET /api/checkpoints/{checkpoint_id} on missing id returns 404."""
        client = TestClient(app)
        resp = client.get("/api/checkpoints/chk_missing_0000")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ============================================================================
# 8. Branch & Condition/Decision Coverage Hardening (GAP-003)
# ============================================================================

class TestBranchCoverageHardening:
    """Verifies --cov-branch branch arcs measurement, fallback calculations, and Blackboard propagation."""

    def test_sandbox_measure_coverage_branch_arcs_discount(self):
        """Verifies branch coverage on multi-branch code with partial and full branch coverage."""
        sandbox = ParallelSandboxRunner(timeout_seconds=5)
        with open("samples/discount.py", "r", encoding="utf-8") as f:
            discount_code = f.read()

        # 1. Partial branch coverage test suite (only hits positive, small quantity, non-member)
        partial_test = """
from target import calculate_discount
def test_partial():
    assert calculate_discount(100.0, 2, False) == 100.0
"""
        line_pct, cov_info = sandbox.measure_coverage(partial_test, discount_code)
        assert line_pct > 0.0
        assert cov_info["total_branches"] == 6
        assert cov_info["covered_branches"] < 6
        assert cov_info["branch_coverage_percent"] < 100.0
        assert cov_info["branch_coverage"] == cov_info["branch_coverage_percent"]
        assert len(cov_info["missing_branches"]) > 0

        # 2. Complete branch coverage test suite (exercises all 6 branch paths)
        full_test = """
from target import calculate_discount
def test_zero_price():
    assert calculate_discount(0.0, 5, True) == 0.0

def test_full_discount():
    assert calculate_discount(100.0, 10, True) == 80.0

def test_no_discount():
    assert calculate_discount(100.0, 1, False) == 100.0
"""
        line_pct_full, cov_info_full = sandbox.measure_coverage(full_test, discount_code)
        assert line_pct_full == 100.0
        assert cov_info_full["total_branches"] == 6
        assert cov_info_full["covered_branches"] == 6
        assert cov_info_full["branch_coverage_percent"] == 100.0
        assert len(cov_info_full["missing_branches"]) == 0

    def test_sandbox_measure_coverage_straight_line_code_default_100(self):
        """Straight-line code with zero branches defaults cleanly to 100.0% branch coverage."""
        sandbox = ParallelSandboxRunner(timeout_seconds=5)
        straight_code = "def add(a, b): return a + b\n"
        test_code = "from target import add\ndef test_add(): assert add(1, 2) == 3\n"

        line_pct, cov_info = sandbox.measure_coverage(test_code, straight_code)
        assert line_pct == 100.0
        assert cov_info["total_branches"] == 0
        assert cov_info["covered_branches"] == 0
        assert cov_info["branch_coverage_percent"] == 100.0

    def test_blackboard_record_coverage_updates_execution_and_metrics(self):
        """Verifies Blackboard.record_coverage updates ExecutionSpace and MetricsSpace in sync."""
        bb = Blackboard()
        missing = [[9, 10], [13, 14]]
        res = bb.record_coverage(
            line_coverage_pct=85.0,
            lines_covered=17,
            lines_total=20,
            branch_coverage=66.67,
            total_branches=6,
            covered_branches=4,
            missing_branches=missing,
        )

        exec_space = bb.get_execution_space()
        metrics_space = bb.get_metrics_space()

        # Verify ExecutionSpace
        assert exec_space.line_coverage_pct == 85.0
        assert exec_space.branch_coverage == 66.67
        assert exec_space.branch_coverage_pct == 66.67
        assert exec_space.total_branches == 6
        assert exec_space.covered_branches == 4
        assert exec_space.missing_branches == missing

        # Verify MetricsSpace
        assert metrics_space.baseline_line_coverage == 85.0
        assert metrics_space.branch_coverage == 66.67
        assert metrics_space.total_branches == 6
        assert metrics_space.covered_branches == 4
        assert metrics_space.missing_branches == missing

    def test_testforge_state_branch_coverage_serialization_roundtrip(self):
        """Verifies TestForgeState sync_to_state and from_testforge_state preserves branch coverage."""
        bb = Blackboard()
        bb.record_coverage(
            line_coverage_pct=92.5,
            lines_covered=37,
            lines_total=40,
            branch_coverage=80.0,
            total_branches=10,
            covered_branches=8,
            missing_branches=[[15, 18]],
        )

        state = bb.to_state()
        assert state.baseline_line_coverage == 92.5
        assert state.baseline_branch_coverage == 80.0
        assert state.total_branches == 10
        assert state.covered_branches == 8
        assert state.missing_branches == [[15, 18]]

        # Roundtrip back into a new Blackboard instance
        bb2 = Blackboard.from_testforge_state(state)
        assert bb2.metrics.branch_coverage == 80.0
        assert bb2.metrics.total_branches == 10
        assert bb2.metrics.covered_branches == 8
        assert bb2.metrics.missing_branches == [[15, 18]]

    def test_api_status_exposes_branch_coverage(self):
        """Verifies GET /api/harden/status/{job_id} exposes branch coverage metrics in Blackboard summary."""
        import server
        client = TestClient(app)
        test_jid = "job_test_branch_cov_api"
        
        bb = Blackboard()
        bb.record_coverage(
            line_coverage_pct=90.0,
            lines_covered=18,
            lines_total=20,
            branch_coverage=83.33,
            total_branches=6,
            covered_branches=5,
            missing_branches=[[12, 14]],
        )

        with server.JOB_LOCK:
            server.JOBS[test_jid] = {
                "job_id": test_jid,
                "status": "COMPLETED",
                "final_state": {
                    "baseline_line_coverage": 90.0,
                    "baseline_branch_coverage": 83.33,
                    "branch_coverage": 83.33,
                    "total_branches": 6,
                    "covered_branches": 5,
                    "final_mutation_score": 100.0,
                }
            }

        try:
            resp = client.get(f"/api/harden/status/{test_jid}")
            assert resp.status_code == 200
            data = resp.json()
            fs = data.get("final_state", {})
            assert fs.get("branch_coverage") == 83.33
            assert fs.get("total_branches") == 6
            assert fs.get("covered_branches") == 5

            bb_summary = data.get("blackboard_summary", {})
            spaces = bb_summary.get("spaces", {})
            assert "ExecutionSpace" in spaces
            assert spaces["ExecutionSpace"]["branch_coverage"] == 83.33
            assert spaces["MetricsSpace"]["branch_coverage"] == 83.33
        finally:
            with server.JOB_LOCK:
                server.JOBS.pop(test_jid, None)
