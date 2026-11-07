"""
test_blackboard.py - Unit and Integration Tests for Typed Blackboard Architecture.

Covers:
  1. Construction with default partition state.
  2. Valid partition updates.
  3. Pydantic validation failures.
  4. Invalid updates leaving existing state unchanged (atomic rollback).
  5. Partition isolation.
  6. Snapshot consistency.
  7. History ordering and monotonic revision increments.
  8. Subscriber registration.
  9. Subscriber unregistration.
  10. Filtering subscriptions by partition.
  11. Deterministic subscriber notification order (priority + FIFO).
  12. Subscriber exception isolation.
  13. Concurrent updates from multiple threads (race-free execution).
  14. Defensive copies preventing in-place external mutation.
  15. Safe metadata that does not expose full source code or credentials.
  16. Integration with the existing orchestrator.
  17. Compatibility with the existing TestForgeState API.
"""

import threading
import time

import pytest
from pydantic import ValidationError

from testforge.blackboard import (
    Blackboard,
    BlackboardEvent,
    BlackboardSnapshot,
    CriticSpace,
    MetricsSpace,
    MutantSpace,
    SuiteSpace,
    TargetSpace,
)
from testforge.callbacks import CallbackRegistry, EventType
from testforge.state import IterationMetrics, MutantRecord, TestForgeState


class TestBlackboardCore:
    def test_construction_with_default_partition_state(self):
        bb = Blackboard()
        assert bb.revision == 0
        assert len(bb.get_history()) == 0

        target = bb.get_target_space()
        assert isinstance(target, TargetSpace)
        assert target.target_module_path == "target.py"
        assert target.target_source_code == ""

        mutant = bb.get_mutant_space()
        assert isinstance(mutant, MutantSpace)
        assert len(mutant.mutants) == 0

        critic = bb.get_critic_space()
        assert isinstance(critic, CriticSpace)
        assert len(critic.critic_directives) == 0

        suite = bb.get_suite_space()
        assert isinstance(suite, SuiteSpace)
        assert suite.current_test_code == ""

        metrics = bb.get_metrics_space()
        assert isinstance(metrics, MetricsSpace)
        assert metrics.current_iteration == 0
        assert metrics.terminated is False

    def test_valid_partition_updates(self):
        bb = Blackboard()
        updated_target = bb.update_target_space(
            target_source_code="def add(a, b): return a + b\n",
            functions=["add"],
            blast_risk="MEDIUM"
        )
        assert bb.revision == 1
        assert updated_target.functions == ["add"]
        assert updated_target.blast_risk == "MEDIUM"

        target_check = bb.get_target_space()
        assert target_check.target_source_code == "def add(a, b): return a + b\n"
        assert target_check.functions == ["add"]

    def test_pydantic_validation_failures(self):
        bb = Blackboard()
        # Passing an invalid type that cannot be coerced (e.g. dict for target_source_code string)
        with pytest.raises(ValidationError):
            bb.update_target_space(target_lines="not_a_list")

    def test_invalid_updates_leave_existing_state_unchanged(self):
        bb = Blackboard()
        bb.update_metrics_space(current_iteration=2, target_mutation_score=90.0)
        assert bb.revision == 1

        # Attempt invalid update: history expects List[IterationMetrics], passing string
        with pytest.raises(ValidationError):
            bb.update_metrics_space(history="invalid_history_type")

        # Verify state was untouched and revision was NOT incremented
        assert bb.revision == 1
        metrics = bb.get_metrics_space()
        assert metrics.current_iteration == 2
        assert metrics.target_mutation_score == 90.0
        assert len(metrics.history) == 0

    def test_partition_isolation(self):
        bb = Blackboard()
        bb.update_target_space(target_source_code="def sub(a, b): return a - b")
        bb.update_suite_space(current_test_code="def test_sub(): pass")

        target = bb.get_target_space()
        suite = bb.get_suite_space()
        mutant = bb.get_mutant_space()

        assert target.target_source_code == "def sub(a, b): return a - b"
        assert suite.current_test_code == "def test_sub(): pass"
        # Mutant space must remain unaffected defaults
        assert len(mutant.mutants) == 0

    def test_snapshot_consistency(self):
        bb = Blackboard()
        bb.update_target_space(functions=["foo", "bar"])
        bb.update_mutant_space(mutants_generated=5, mutants_killed=4)
        bb.update_metrics_space(current_iteration=1)

        snapshot = bb.get_snapshot()
        assert isinstance(snapshot, BlackboardSnapshot)
        assert snapshot.revision == bb.revision
        assert snapshot.target.functions == ["foo", "bar"]
        assert snapshot.mutant.mutants_generated == 5
        assert snapshot.mutant.mutants_killed == 4
        assert snapshot.metrics.current_iteration == 1

    def test_history_ordering_and_revision_increments(self):
        bb = Blackboard()
        bb.update_target_space(target_file_path="src/app.py")
        bb.update_suite_space(active_provider="TestRunner")
        bb.update_metrics_space(current_iteration=1)

        history = bb.get_history()
        assert len(history) == 3
        assert [h.revision for h in history] == [1, 2, 3]
        assert [h.partition for h in history] == ["target", "suite", "metrics"]

    def test_defensive_copies_prevent_external_mutation(self):
        bb = Blackboard()
        bb.update_target_space(functions=["func_a"])

        target_copy = bb.get_target_space()
        # Mutating the returned copy directly
        target_copy.functions.append("malicious_func")

        # Internal state in Blackboard must remain unaltered
        fresh_target = bb.get_target_space()
        assert "malicious_func" not in fresh_target.functions
        assert fresh_target.functions == ["func_a"]

    def test_safe_metadata_sanitization(self):
        bb = Blackboard()
        large_source = "def secret_algo():\n" + ("    x = 1\n" * 50)
        secret_note = "api_key='sk-1234567890abcdef12345678'"

        bb.update_target_space(target_source_code=large_source)
        bb.update_critic_space(latest_directive=secret_note)

        history = bb.get_history()
        assert len(history) == 2

        # Target entry should record length, NOT dump entire code
        target_meta = history[0].safe_metadata
        assert "target_source_code_len" in target_meta
        assert "def secret_algo()" not in str(target_meta)

        # Critic entry should redact sensitive tokens
        critic_meta = history[1].safe_metadata
        assert "sk-1234567890abcdef12345678" not in str(critic_meta)
        assert "[REDACTED_SECRET]" in str(critic_meta)


class TestBlackboardSubscriptions:
    def test_subscriber_registration_and_notification(self):
        bb = Blackboard()
        received_events = []

        def handler(event: BlackboardEvent):
            received_events.append(event)

        sub_id = bb.subscribe(handler)
        assert isinstance(sub_id, str)
        assert bb.subscription_count == 1

        bb.update_target_space(functions=["test_func"])
        assert len(received_events) == 1
        assert received_events[0].partition == "target"
        assert received_events[0].revision == 1

    def test_subscriber_unregistration(self):
        bb = Blackboard()
        events = []

        sub_id = bb.subscribe(lambda e: events.append(e))
        bb.update_suite_space(active_provider="Provider1")
        assert len(events) == 1

        unsubbed = bb.unsubscribe(sub_id)
        assert unsubbed is True
        assert bb.subscription_count == 0

        # Updates after unregistering must not invoke handler
        bb.update_suite_space(active_provider="Provider2")
        assert len(events) == 1

    def test_filtering_subscriptions_by_partition(self):
        bb = Blackboard()
        mutant_events = []
        metrics_events = []

        bb.subscribe(lambda e: mutant_events.append(e), partitions={"mutant"})
        bb.subscribe(lambda e: metrics_events.append(e), partitions={"metrics"})

        bb.update_mutant_space(mutants_generated=10)
        assert len(mutant_events) == 1
        assert len(metrics_events) == 0

        bb.update_metrics_space(current_iteration=2)
        assert len(mutant_events) == 1
        assert len(metrics_events) == 1

    def test_deterministic_subscriber_notification_order(self):
        bb = Blackboard()
        call_log = []

        bb.subscribe(lambda e: call_log.append("low"), priority=10)
        bb.subscribe(lambda e: call_log.append("high"), priority=200)
        bb.subscribe(lambda e: call_log.append("med_1"), priority=100)
        bb.subscribe(lambda e: call_log.append("med_2"), priority=100)

        bb.update_target_space(blast_risk="HIGH")
        assert call_log == ["high", "med_1", "med_2", "low"]

    def test_subscriber_exception_isolation(self):
        bb = Blackboard()
        success_log = []

        def failing_subscriber(e: BlackboardEvent):
            raise RuntimeError("Observer explosion!")

        def healthy_subscriber(e: BlackboardEvent):
            success_log.append(e.revision)

        # High priority failing subscriber, lower priority healthy subscriber
        bb.subscribe(failing_subscriber, priority=200)
        bb.subscribe(healthy_subscriber, priority=100)

        # Update should NOT crash; healthy subscriber must execute; state must be intact
        bb.update_metrics_space(target_mutation_score=95.0)

        assert bb.get_metrics_space().target_mutation_score == 95.0
        assert len(success_log) == 1
        assert success_log[0] == 1


class TestBlackboardConcurrency:
    def test_concurrent_updates_from_multiple_threads(self):
        bb = Blackboard()
        num_threads = 8
        updates_per_thread = 25
        errors = []

        def worker(thread_idx: int):
            try:
                for i in range(updates_per_thread):
                    bb.update_metrics_space(
                        current_iteration=thread_idx * 100 + i,
                        lines_covered=i
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        expected_total_revisions = num_threads * updates_per_thread
        assert bb.revision == expected_total_revisions
        assert len(bb.get_history()) == expected_total_revisions


class TestBlackboardInterop:
    def test_to_and_from_testforge_state(self):
        original_state = TestForgeState(
            target_source_code="def calculate(x): return x * 2",
            current_test_code="def test_calc(): assert calculate(2) == 4",
            current_iteration=2,
            target_mutation_score=90.0,
            final_mutation_score=88.5,
            baseline_passed=True,
            surviving_mutant_diffs=["diff 1"],
            reflection_notes=["note 1"]
        )

        bb = Blackboard.from_testforge_state(original_state)
        assert bb.get_target_space().target_source_code == original_state.target_source_code
        assert bb.get_suite_space().current_test_code == original_state.current_test_code
        assert bb.get_metrics_space().current_iteration == 2
        assert bb.get_mutant_space().surviving_mutant_diffs == ["diff 1"]

        # Convert back to TestForgeState
        converted = bb.to_testforge_state()
        assert converted.target_source_code == original_state.target_source_code
        assert converted.current_test_code == original_state.current_test_code
        assert converted.current_iteration == original_state.current_iteration
        assert converted.target_mutation_score == original_state.target_mutation_score
        assert converted.final_mutation_score == original_state.final_mutation_score
        assert converted.baseline_passed == original_state.baseline_passed
        assert converted.surviving_mutant_diffs == original_state.surviving_mutant_diffs

    def test_sync_to_state(self):
        bb = Blackboard()
        state = TestForgeState()

        bb.update_target_space(target_source_code="def foo(): pass")
        bb.update_suite_space(current_test_code="def test_foo(): pass")
        bb.update_metrics_space(final_hardening_status="SUCCESS", final_mutation_score=100.0)

        bb.sync_to_state(state)
        assert state.target_source_code == "def foo(): pass"
        assert state.current_test_code == "def test_foo(): pass"
        assert state.final_hardening_status == "SUCCESS"
        assert state.final_mutation_score == 100.0

    def test_orchestrator_integration(self, tmp_path):
        from testforge.orchestrator import TestForgeOrchestrator

        target_code = "def multiply(x, y): return x * y\n"
        initial_test = "from target import multiply\ndef test_multiply(): assert multiply(3, 4) == 12\n"
        trace_file = str(tmp_path / "orch_bb_trace.jsonl")

        bb = Blackboard()
        events_captured = []
        bb.subscribe(lambda e: events_captured.append(e))

        orch = TestForgeOrchestrator(
            target_source_code=target_code,
            initial_test_code=initial_test,
            max_iterations=1,
            target_mutation_score=50.0,
            trace_log_path=trace_file,
            blackboard=bb
        )

        final_state = orch.run()

        # Check that orchestrator used the injected blackboard
        assert orch.blackboard is bb
        assert bb.revision > 0
        assert len(events_captured) > 0
        partitions_updated = {e.partition for e in events_captured}
        assert "target" in partitions_updated
        assert "suite" in partitions_updated
        assert "metrics" in partitions_updated

        # Check synchronization with final state
        assert final_state.final_hardening_status == bb.get_metrics_space().final_hardening_status
        assert final_state.current_test_code == bb.get_suite_space().current_test_code
