"""
tests/test_task_lifecycle.py - Comprehensive Unit and Integration Tests
for TestForge Canonical Task Lifecycle State Machine (GAP-01).

Covers:
  1. Successful linear lifecycle progression.
  2. Rejection of invalid transitions without state corruption.
  3. Failure with recorded failure reasons.
  4. Distinct cancellation vs timeout outcomes.
  5. Terminal-state immutability.
  6. Stage timing and duration accumulation.
  7. Idempotent self-transitions without resetting timers.
  8. Concurrent thread-safe transition attempts.
  9. Recovery-related transitions.
  10. Consistency between lifecycle state and emitted EventType.STATE_CHANGE callbacks.
  11. Checkpoint and Blackboard synchronization.
  12. FSM serialization and deserialization (to_dict / from_dict).
  13. Orchestrator live execution through lifecycle stages.
  14. Server API endpoints exposing lifecycle_state and stage_durations.
"""

import threading
import time

import pytest
from fastapi.testclient import TestClient

from server import JOB_LOCK, JOBS, app
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType, LifecycleEvent
from testforge.orchestrator import TestForgeOrchestrator
from testforge.state import (
    TERMINAL_LIFECYCLE_STATES,
    VALID_LIFECYCLE_TRANSITIONS,
    InvalidStateTransitionError,
    TaskLifecycleFSM,
    TaskLifecycleState,
    TestForgeState,
)

# ==============================================================================
# 1. State Machine Unit Tests
# ==============================================================================

class TestTaskLifecycleFSM:
    def test_initial_state(self):
        fsm = TaskLifecycleFSM(task_id="task_test_01")
        assert fsm.task_id == "task_test_01"
        assert fsm.current_state == TaskLifecycleState.CREATED
        assert not fsm.is_terminal
        assert fsm.failure_reason is None
        assert len(fsm.get_history()) == 1
        assert fsm.get_history()[0].stage == TaskLifecycleState.CREATED

    def test_successful_linear_lifecycle(self):
        """Verifies full normal happy-path lifecycle progression."""
        fsm = TaskLifecycleFSM(task_id="task_happy_path")
        
        stages = [
            TaskLifecycleState.VALIDATING,
            TaskLifecycleState.INGESTING,
            TaskLifecycleState.PLANNING,
            TaskLifecycleState.GENERATING_TESTS,
            TaskLifecycleState.EXECUTING,
            TaskLifecycleState.MUTATION_ANALYSIS,
            TaskLifecycleState.EVALUATING,
            TaskLifecycleState.COMPLETED,
        ]
        
        for stage in stages:
            assert fsm.can_transition_to(stage)
            fsm.transition_to(stage, metadata={"step": stage.value.lower()})
            assert fsm.current_state == stage

        assert fsm.is_terminal
        assert fsm.current_state == TaskLifecycleState.COMPLETED
        
        durations = fsm.get_stage_durations()
        assert "CREATED" in durations
        assert "VALIDATING" in durations
        assert "INGESTING" in durations
        assert "PLANNING" in durations
        assert "GENERATING_TESTS" in durations
        assert "EXECUTING" in durations
        assert "MUTATION_ANALYSIS" in durations
        assert "EVALUATING" in durations
        assert "COMPLETED" in durations

    def test_rejection_of_invalid_transition_without_corruption(self):
        """Verifies that illegal transitions raise InvalidStateTransitionError and state remains unchanged."""
        fsm = TaskLifecycleFSM(task_id="task_invalid")
        assert fsm.current_state == TaskLifecycleState.CREATED
        
        # Cannot jump from CREATED directly to COMPLETED or EXECUTING
        assert not fsm.can_transition_to(TaskLifecycleState.COMPLETED)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            fsm.transition_to(TaskLifecycleState.COMPLETED)
        
        assert "Invalid lifecycle state transition from 'CREATED' to 'COMPLETED'" in str(exc_info.value)
        # Ensure state was not corrupted
        assert fsm.current_state == TaskLifecycleState.CREATED
        assert not fsm.is_terminal

    def test_terminal_state_immutability(self):
        """Verifies that once in a terminal state, no further transitions are permitted."""
        for terminal in TERMINAL_LIFECYCLE_STATES:
            fsm = TaskLifecycleFSM(task_id=f"task_{terminal.value}", initial_state=terminal)
            assert fsm.is_terminal
            
            # Attempt transitions to all possible states
            for target in TaskLifecycleState:
                if target == terminal:
                    # Idempotent self-transition is allowed
                    assert fsm.can_transition_to(target)
                else:
                    assert not fsm.can_transition_to(target)
                    with pytest.raises(InvalidStateTransitionError):
                        fsm.transition_to(target)
                    assert fsm.current_state == terminal

    def test_failure_with_explicit_reason(self):
        """Verifies that transitioning to FAILED preserves the explicit failure reason."""
        fsm = TaskLifecycleFSM(task_id="task_fail")
        fsm.transition_to(TaskLifecycleState.VALIDATING)
        
        reason = "SecurityRefusal: Forbidden ast call 'eval' detected in source."
        fsm.transition_to(TaskLifecycleState.FAILED, reason=reason)
        
        assert fsm.current_state == TaskLifecycleState.FAILED
        assert fsm.is_terminal
        assert fsm.failure_reason == reason
        
        history = fsm.get_history()
        failed_record = [r for r in history if r.stage == TaskLifecycleState.FAILED][0]
        assert failed_record.reason == reason

    def test_cancellation_vs_timeout_distinction(self):
        """Verifies that CANCELLED and TIMED_OUT are distinct terminal outcomes with specific reasons."""
        fsm_cancel = TaskLifecycleFSM(task_id="task_cancel")
        fsm_cancel.transition_to(TaskLifecycleState.VALIDATING)
        fsm_cancel.transition_to(TaskLifecycleState.CANCELLING, reason="User initiated cancel")
        fsm_cancel.transition_to(TaskLifecycleState.CANCELLED, reason="Cancellation finalized")
        assert fsm_cancel.current_state == TaskLifecycleState.CANCELLED
        assert fsm_cancel.is_terminal
        assert "Cancellation finalized" in fsm_cancel.failure_reason

        fsm_timeout = TaskLifecycleFSM(task_id="task_timeout")
        fsm_timeout.transition_to(TaskLifecycleState.VALIDATING)
        fsm_timeout.transition_to(TaskLifecycleState.TIMED_OUT, reason="Job exceeded 300s budget")
        assert fsm_timeout.current_state == TaskLifecycleState.TIMED_OUT
        assert fsm_timeout.is_terminal
        assert "exceeded 300s" in fsm_timeout.failure_reason

    def test_idempotent_self_transitions(self):
        """Verifies transitioning to the same state is a safe no-op that preserves timing."""
        fsm = TaskLifecycleFSM(task_id="task_idempotent")
        fsm.transition_to(TaskLifecycleState.VALIDATING)
        
        time.sleep(0.01)
        dur1 = fsm.get_stage_durations()["VALIDATING"]
        
        # Idempotent call
        fsm.transition_to(TaskLifecycleState.VALIDATING, metadata={"extra": "data"})
        assert fsm.current_state == TaskLifecycleState.VALIDATING
        
        # State duration continues to accumulate monotonically
        time.sleep(0.01)
        dur2 = fsm.get_stage_durations()["VALIDATING"]
        assert dur2 >= dur1

    def test_recovery_lifecycle_path(self):
        """Verifies that recovery from checkpoint follows CREATED -> RECOVERING -> RECOVERED -> resume stage."""
        fsm = TaskLifecycleFSM(task_id="task_recover")
        assert fsm.can_transition_to(TaskLifecycleState.RECOVERING)
        fsm.transition_to(TaskLifecycleState.RECOVERING, reason="Loading snapshot from SQLite checkpoint")
        
        assert fsm.can_transition_to(TaskLifecycleState.RECOVERED)
        fsm.transition_to(TaskLifecycleState.RECOVERED, reason="Snapshot verified and state restored")
        
        # From RECOVERED, can resume at PLANNING, EXECUTING, or MUTATION_ANALYSIS
        assert fsm.can_transition_to(TaskLifecycleState.MUTATION_ANALYSIS)
        fsm.transition_to(TaskLifecycleState.MUTATION_ANALYSIS, reason="Resuming mutation testing")
        assert fsm.current_state == TaskLifecycleState.MUTATION_ANALYSIS

    def test_concurrent_transitions_thread_safe(self):
        """Verifies that concurrent transition attempts under lock do not corrupt internal state."""
        fsm = TaskLifecycleFSM(task_id="task_concurrent")
        fsm.transition_to(TaskLifecycleState.VALIDATING)
        fsm.transition_to(TaskLifecycleState.INGESTING)
        fsm.transition_to(TaskLifecycleState.PLANNING)
        fsm.transition_to(TaskLifecycleState.GENERATING_TESTS)
        fsm.transition_to(TaskLifecycleState.EXECUTING)
        
        # 10 threads concurrently trying valid next transition to MUTATION_ANALYSIS or self-transition
        errors = []
        def worker():
            try:
                for _ in range(20):
                    if fsm.can_transition_to(TaskLifecycleState.MUTATION_ANALYSIS):
                        try:
                            fsm.transition_to(TaskLifecycleState.MUTATION_ANALYSIS)
                        except InvalidStateTransitionError:
                            pass
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert fsm.current_state == TaskLifecycleState.MUTATION_ANALYSIS

    def test_serialization_and_deserialization(self):
        """Verifies to_dict and from_dict roundtrip fidelity."""
        fsm = TaskLifecycleFSM(task_id="task_serde")
        fsm.transition_to(TaskLifecycleState.VALIDATING)
        fsm.transition_to(TaskLifecycleState.INGESTING)
        
        data = fsm.to_dict()
        assert data["task_id"] == "task_serde"
        assert data["current_state"] == "INGESTING"
        assert not data["is_terminal"]
        assert "VALIDATING" in data["stage_durations"]
        assert "INGESTING" in data["stage_durations"]
        
        reconstituted = TaskLifecycleFSM.from_dict(data)
        assert reconstituted.task_id == "task_serde"
        assert reconstituted.current_state == TaskLifecycleState.INGESTING
        assert not reconstituted.is_terminal


# ==============================================================================
# 2. Callbacks and Blackboard Integration
# ==============================================================================

class TestLifecycleIntegration:
    def test_event_dispatch_on_transition(self):
        """Verifies that every transition dispatches an EventType.STATE_CHANGE callback."""
        registry = CallbackRegistry()
        events_captured = []
        
        def listener(evt: LifecycleEvent):
            events_captured.append(evt)
            
        registry.register(listener, event_types={EventType.STATE_CHANGE})
        
        fsm = TaskLifecycleFSM(task_id="task_event_test", callbacks=registry)
        fsm.transition_to(TaskLifecycleState.VALIDATING, reason="Starting input check")
        fsm.transition_to(TaskLifecycleState.INGESTING, reason="Parsing symbols")
        
        assert len(events_captured) == 2
        evt1 = events_captured[0]
        assert evt1.event_type == EventType.STATE_CHANGE
        assert evt1.payload["previous_state"] == "CREATED"
        assert evt1.payload["new_state"] == "VALIDATING"
        assert evt1.payload["reason"] == "Starting input check"

        evt2 = events_captured[1]
        assert evt2.payload["previous_state"] == "VALIDATING"
        assert evt2.payload["new_state"] == "INGESTING"

    def test_blackboard_metrics_synchronization(self):
        """Verifies that FSM updates automatically reflect in Blackboard MetricsSpace."""
        bb = Blackboard()
        fsm = TaskLifecycleFSM(task_id="task_bb_test", blackboard=bb)
        
        fsm.transition_to(TaskLifecycleState.VALIDATING)
        metrics = bb.get_metrics_space()
        assert metrics.task_id == "task_bb_test"
        assert metrics.lifecycle_state == "VALIDATING"
        
        fsm.transition_to(TaskLifecycleState.INGESTING)
        metrics = bb.get_metrics_space()
        assert metrics.lifecycle_state == "INGESTING"
        assert "VALIDATING" in metrics.stage_durations


# ==============================================================================
# 3. Live Orchestrator Execution Lifecycle Test
# ==============================================================================

class TestOrchestratorLifecycle:
    def test_orchestrator_runs_through_lifecycle(self):
        """Executes a real orchestrator run and verifies FSM progression to COMPLETED."""
        sample_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        existing_test = "def test_add():\n    assert add(1, 2) == 3\n"
        
        orchestrator = TestForgeOrchestrator(
            target_source_code=sample_code,
            initial_test_code=existing_test,
            max_iterations=1,
            target_mutation_score=50.0,
            engine_mode="legacy",
        )
        
        assert orchestrator.fsm.current_state == TaskLifecycleState.CREATED
        final_state = orchestrator.run()
        
        assert orchestrator.fsm.current_state == TaskLifecycleState.COMPLETED
        assert orchestrator.fsm.is_terminal
        assert final_state.lifecycle_state == TaskLifecycleState.COMPLETED
        
        # Verify stage history contains expected sequence
        history = orchestrator.fsm.get_history()
        stages_visited = [r.stage.value for r in history]
        
        assert "VALIDATING" in stages_visited
        assert "INGESTING" in stages_visited
        assert "EXECUTING" in stages_visited
        assert "MUTATION_ANALYSIS" in stages_visited
        assert "EVALUATING" in stages_visited
        assert "COMPLETED" in stages_visited


# ==============================================================================
# 4. Server API Endpoint Lifecycle Exposure
# ==============================================================================

class TestServerApiLifecycle:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_api_status_includes_lifecycle_state(self, client):
        """Verifies that /api/harden/status/{job_id} returns lifecycle_state and stage_durations."""
        payload = {
            "target_file_path": "samples/discount.py",
            "target_source_code": "def discount(amt):\n    return amt * 0.9\n",
            "max_iterations": 1,
            "timeout_seconds": 60,
        }
        res = client.post("/api/harden/start", json=payload)
        assert res.status_code == 200
        job_id = res.json()["job_id"]
        
        # Poll status
        status_res = client.get(f"/api/harden/status/{job_id}")
        assert status_res.status_code == 200
        data = status_res.json()
        
        assert "lifecycle_state" in data
        assert "stage_durations" in data
        assert data["lifecycle_state"] in [s.value for s in TaskLifecycleState]

    def test_api_cancellation_reflects_cancelled_lifecycle(self, client):
        """Verifies that cancelling a job updates lifecycle_state to CANCELLED."""
        job_id = "test_cancel_api_job"
        cancel_evt = threading.Event()
        with JOB_LOCK:
            JOBS[job_id] = {
                "job_id": job_id,
                "status": "QUEUED",
                "lifecycle_state": TaskLifecycleState.CREATED.value,
                "created_at": time.time(),
                "target_file_path": "samples/discount.py",
                "max_iterations": 1,
                "target_mutation_score": 85.0,
                "engine_mode": "auto",
                "model_name": "gemini-3.6-flash",
                "timeout_seconds": 60,
                "_cancel_event": cancel_evt,
                "_orchestrator": None,
            }

        cancel_res = client.post(f"/api/harden/cancel/{job_id}")
        assert cancel_res.status_code == 200
        cancel_data = cancel_res.json()
        assert cancel_data["current_status"] == "CANCELLED"
        assert cancel_data["lifecycle_state"] == "CANCELLED"

        status_res = client.get(f"/api/harden/status/{job_id}")
        assert status_res.status_code == 200
        data = status_res.json()
        assert data["status"] == "CANCELLED"
        assert data["lifecycle_state"] == "CANCELLED"

