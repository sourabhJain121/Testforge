"""
state.py - TestForge Shared Typed State Contract across Iterations.

Authors: Sourabh & Shreshth
"""

from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Union

from pydantic import BaseModel, Field


class TaskLifecycleState(str, Enum):
    """
    Canonical lifecycle states for TestForge autonomous test engineering tasks.
    Enforces strict, validated state transitions across the end-to-end pipeline.
    """
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    INGESTING = "INGESTING"
    PLANNING = "PLANNING"
    GENERATING_TESTS = "GENERATING_TESTS"
    EXECUTING = "EXECUTING"
    MUTATION_ANALYSIS = "MUTATION_ANALYSIS"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"


TERMINAL_LIFECYCLE_STATES: Set[TaskLifecycleState] = {
    TaskLifecycleState.COMPLETED,
    TaskLifecycleState.FAILED,
    TaskLifecycleState.CANCELLED,
    TaskLifecycleState.TIMED_OUT,
}


class StageRecord(BaseModel):
    """Immutable record of an individual stage entry, exit, duration, and metadata."""
    stage: TaskLifecycleState
    entered_at: float
    exited_at: Optional[float] = None
    duration_seconds: float = 0.0
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal or unsupported lifecycle transition is attempted."""
    def __init__(
        self,
        from_state: Union[TaskLifecycleState, str],
        to_state: Union[TaskLifecycleState, str],
        reason: str = ""
    ):
        self.from_state = from_state
        self.to_state = to_state
        from_val = from_state.value if isinstance(from_state, TaskLifecycleState) else str(from_state)
        to_val = to_state.value if isinstance(to_state, TaskLifecycleState) else str(to_state)
        msg = f"Invalid lifecycle state transition from '{from_val}' to '{to_val}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


VALID_LIFECYCLE_TRANSITIONS: Dict[TaskLifecycleState, Set[TaskLifecycleState]] = {
    TaskLifecycleState.CREATED: {
        TaskLifecycleState.QUEUED,
        TaskLifecycleState.VALIDATING,
        TaskLifecycleState.INGESTING,
        TaskLifecycleState.RECOVERING,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
        TaskLifecycleState.FAILED,
    },
    TaskLifecycleState.QUEUED: {
        TaskLifecycleState.VALIDATING,
        TaskLifecycleState.INGESTING,
        TaskLifecycleState.RECOVERING,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
        TaskLifecycleState.FAILED,
    },
    TaskLifecycleState.VALIDATING: {
        TaskLifecycleState.INGESTING,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.INGESTING: {
        TaskLifecycleState.PLANNING,
        TaskLifecycleState.GENERATING_TESTS,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.PLANNING: {
        TaskLifecycleState.GENERATING_TESTS,
        TaskLifecycleState.EXECUTING,
        TaskLifecycleState.EVALUATING,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.GENERATING_TESTS: {
        TaskLifecycleState.EXECUTING,
        TaskLifecycleState.PLANNING,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.EXECUTING: {
        TaskLifecycleState.MUTATION_ANALYSIS,
        TaskLifecycleState.PLANNING,
        TaskLifecycleState.GENERATING_TESTS,
        TaskLifecycleState.EVALUATING,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.MUTATION_ANALYSIS: {
        TaskLifecycleState.EXECUTING,
        TaskLifecycleState.EVALUATING,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.EVALUATING: {
        TaskLifecycleState.COMPLETED,
        TaskLifecycleState.PLANNING,
        TaskLifecycleState.MUTATION_ANALYSIS,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLING,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.CANCELLING: {
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.FAILED,
    },
    TaskLifecycleState.RECOVERING: {
        TaskLifecycleState.RECOVERED,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLED,
    },
    TaskLifecycleState.RECOVERED: {
        TaskLifecycleState.VALIDATING,
        TaskLifecycleState.INGESTING,
        TaskLifecycleState.PLANNING,
        TaskLifecycleState.GENERATING_TESTS,
        TaskLifecycleState.EXECUTING,
        TaskLifecycleState.MUTATION_ANALYSIS,
        TaskLifecycleState.EVALUATING,
        TaskLifecycleState.COMPLETED,
        TaskLifecycleState.FAILED,
        TaskLifecycleState.CANCELLED,
        TaskLifecycleState.TIMED_OUT,
    },
    TaskLifecycleState.COMPLETED: set(),
    TaskLifecycleState.FAILED: set(),
    TaskLifecycleState.CANCELLED: set(),
    TaskLifecycleState.TIMED_OUT: set(),
}


class TaskLifecycleFSM:
    """
    Thread-safe Finite State Machine governing the task lifecycle.
    Guarantees:
      - Strict validation of all transitions against canonical graph.
      - Idempotent self-transitions without resetting stage timers.
      - Precise duration measurements using monotonic high-resolution clock.
      - State non-corruption on rejected invalid transitions.
      - Terminal state immutability.
      - Synchronous notification to callbacks and blackboard partitions if configured.
    """
    def __init__(
        self,
        task_id: Optional[str] = None,
        initial_state: Union[TaskLifecycleState, str] = TaskLifecycleState.CREATED,
        callbacks: Optional[Any] = None,
        blackboard: Optional[Any] = None,
    ):
        if isinstance(initial_state, str):
            initial_state = TaskLifecycleState(initial_state)

        self.task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        self._lock = threading.RLock()
        self._callbacks = callbacks
        self._blackboard = blackboard

        self._current_state: TaskLifecycleState = initial_state
        self._created_at: float = time.time()
        self._current_entered_at: float = self._created_at
        self._current_perf: float = time.perf_counter()
        self._failure_reason: Optional[str] = None

        self._stage_durations: Dict[str, float] = {}
        self._history: List[StageRecord] = []

        self._current_record = StageRecord(
            stage=initial_state,
            entered_at=self._current_entered_at,
            metadata={"initial": True}
        )

    @property
    def current_state(self) -> TaskLifecycleState:
        with self._lock:
            return self._current_state

    @property
    def is_terminal(self) -> bool:
        with self._lock:
            return self._current_state in TERMINAL_LIFECYCLE_STATES

    @property
    def failure_reason(self) -> Optional[str]:
        with self._lock:
            return self._failure_reason

    def can_transition_to(self, target_state: Union[TaskLifecycleState, str]) -> bool:
        """Non-mutating guard check verifying whether a transition is allowed."""
        if isinstance(target_state, str):
            try:
                target_state = TaskLifecycleState(target_state)
            except ValueError:
                return False
        with self._lock:
            if target_state == self._current_state:
                return True
            return target_state in VALID_LIFECYCLE_TRANSITIONS.get(self._current_state, set())

    def transition_to(
        self,
        target_state: Union[TaskLifecycleState, str],
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskLifecycleState:
        """
        Executes a validated transition to target_state.
        Raises InvalidStateTransitionError if transition is illegal, leaving state intact.
        """
        if isinstance(target_state, str):
            target_state = TaskLifecycleState(target_state)

        with self._lock:
            # Idempotent self-transition
            if target_state == self._current_state:
                if reason and not self._current_record.reason:
                    self._current_record.reason = reason
                if metadata:
                    self._current_record.metadata.update(metadata)
                return self._current_state

            allowed = VALID_LIFECYCLE_TRANSITIONS.get(self._current_state, set())
            if target_state not in allowed:
                raise InvalidStateTransitionError(self._current_state, target_state)

            now_perf = time.perf_counter()
            now_time = time.time()
            stage_duration = round(now_perf - self._current_perf, 4)

            # Finalize outgoing stage record
            self._current_record.exited_at = now_time
            self._current_record.duration_seconds = stage_duration
            if reason and not self._current_record.reason:
                self._current_record.reason = reason
            self._history.append(self._current_record)

            stage_name = self._current_state.value
            self._stage_durations[stage_name] = round(
                self._stage_durations.get(stage_name, 0.0) + stage_duration, 4
            )

            previous_state = self._current_state
            self._current_state = target_state
            self._current_entered_at = now_time
            self._current_perf = now_perf

            if target_state in (TaskLifecycleState.FAILED, TaskLifecycleState.CANCELLED, TaskLifecycleState.TIMED_OUT):
                self._failure_reason = reason or target_state.value

            # Start new stage record
            self._current_record = StageRecord(
                stage=target_state,
                entered_at=now_time,
                reason=reason,
                metadata=metadata or {}
            )

            # Blackboard synchronization
            if self._blackboard is not None:
                try:
                    self._blackboard.update_metrics_space(
                        task_id=self.task_id,
                        lifecycle_state=target_state.value,
                        stage_durations=dict(self._stage_durations),
                    )
                except Exception:
                    pass

            # Lifecycle callback dispatch
            if self._callbacks is not None:
                try:
                    from testforge.callbacks import EventType, LifecycleEvent
                    self._callbacks.dispatch(LifecycleEvent(
                        event_type=EventType.STATE_CHANGE,
                        emitter="TaskLifecycleFSM",
                        workflow_id=self.task_id,
                        correlation_id=self.task_id,
                        payload={
                            "task_id": self.task_id,
                            "previous_state": previous_state.value,
                            "new_state": target_state.value,
                            "stage_duration_seconds": stage_duration,
                            "reason": reason,
                            "is_terminal": self.is_terminal,
                        }
                    ))
                except Exception:
                    pass

            return self._current_state

    def get_stage_durations(self) -> Dict[str, float]:
        """Returns consolidated duration map including active elapsed time in current stage."""
        with self._lock:
            durations = dict(self._stage_durations)
            current_elapsed = round(time.perf_counter() - self._current_perf, 4)
            curr_name = self._current_state.value
            durations[curr_name] = round(durations.get(curr_name, 0.0) + current_elapsed, 4)
            return durations

    def get_history(self) -> List[StageRecord]:
        """Returns ordered history of stages including a snapshot of the active stage."""
        with self._lock:
            history = list(self._history)
            curr = self._current_record.model_copy()
            curr.duration_seconds = round(time.perf_counter() - self._current_perf, 4)
            history.append(curr)
            return history

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current FSM state for API responses and persistence."""
        with self._lock:
            return {
                "task_id": self.task_id,
                "current_state": self._current_state.value,
                "is_terminal": self.is_terminal,
                "failure_reason": self._failure_reason,
                "created_at": self._created_at,
                "total_duration_seconds": round(time.time() - self._created_at, 4),
                "stage_durations": self.get_stage_durations(),
                "stage_history": [r.model_dump() for r in self.get_history()],
            }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        callbacks: Optional[Any] = None,
        blackboard: Optional[Any] = None,
    ) -> TaskLifecycleFSM:
        """Reconstitutes an FSM from serialized checkpoint metadata."""
        fsm = cls(
            task_id=data.get("task_id"),
            initial_state=TaskLifecycleState(data.get("current_state", "CREATED")),
            callbacks=callbacks,
            blackboard=blackboard,
        )
        fsm._created_at = data.get("created_at", time.time())
        fsm._failure_reason = data.get("failure_reason")
        fsm._stage_durations = data.get("stage_durations", {})
        raw_history = data.get("stage_history", [])
        fsm._history = [
            StageRecord(**item) for item in raw_history
            if item.get("exited_at") is not None
        ]
        return fsm



class MutantRecord(BaseModel):
    mutant_id: str = Field(..., description="Deterministic unique identifier, e.g. 'MUT_COMP_OP_001'")
    mutation_type: str = Field(..., description="Mutation operator category e.g. COMP_OP, ARITH_OP, CONST_VAL, etc.")
    line_number: int
    original_code_snippet: str
    mutated_code_snippet: str
    unified_diff: str
    status: Literal[
        "PENDING", "KILLED", "SURVIVED", "TIMEOUT", "ERROR",
        "INVALID", "EQUIVALENT", "POTENTIALLY_EQUIVALENT", "UNKNOWN"
    ] = "PENDING"
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0

    # Milestone 2: Equivalent-mutant analysis metadata
    equivalence_status: Optional[str] = Field(default=None, description="EQUIVALENT, POTENTIALLY_EQUIVALENT, NOT_EQUIVALENT, UNKNOWN")
    equivalence_method: Optional[str] = Field(default=None, description="Analysis heuristic or method employed")
    equivalence_reason: Optional[str] = Field(default=None, description="Human-readable justification for classification")
    equivalence_confidence: Optional[str] = Field(default=None, description="HIGH, MEDIUM, LOW, NONE")
    is_executed: bool = Field(default=False, description="Whether mutant was physically executed in sandbox")
    is_valid_syntax: bool = Field(default=True, description="Whether AST unparse produces valid parseable Python")
    original_expression: Optional[str] = Field(default=None, description="Source expression prior to mutation")
    mutated_expression: Optional[str] = Field(default=None, description="Transformed expression post-mutation")


class IterationMetrics(BaseModel):
    iteration: int
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timed_out_mutants: int
    execution_errors: int = 0
    invalid_mutants: int = 0
    equivalent_mutants: int = 0
    potentially_equivalent_mutants: int = 0
    mutation_score: float = 0.0  # Maintained as primary raw score for backward compatibility
    raw_mutation_score: float = 0.0
    adjusted_mutation_score: float = 0.0
    line_coverage_pct: float = 0.0
    duration_seconds: float = 0.0
    # Explicit operational execution metrics
    baseline_tests_generated: int = 0
    baseline_tests_executed: int = 0
    baseline_passed: int = 0
    baseline_failed: int = 0
    lines_covered: int = 0
    num_statements: int = 0
    mutants_generated: int = 0
    mutants_executed: int = 0
    hardening_status: str = "IN_PROGRESS"


class TestForgeState(BaseModel):
    __test__ = False
    target_module_path: str = "target.py"
    test_module_path: str = "test_target.py"
    target_source_code: str = ""
    current_test_code: str = ""

    current_iteration: int = 0
    max_iterations: int = 3
    target_mutation_score: float = 85.0

    baseline_line_coverage: float = 0.0
    lines_covered: int = 0
    num_statements: int = 0
    baseline_branch_coverage: float = 0.0
    total_branches: int = 0
    covered_branches: int = 0
    missing_branches: List[Any] = Field(default_factory=list)

    # Explicit baseline execution metrics
    baseline_tests_generated: int = 0
    baseline_tests_executed: int = 0
    baseline_passed: bool = False
    baseline_tests_passed: int = 0
    baseline_tests_failed: int = 0
    baseline_execution_error: Optional[str] = None
    execution_errors: int = 0

    # Explicit mutation testing metrics
    mutants_generated: int = 0
    mutants_executed: int = 0
    mutants_killed: int = 0
    mutants_survived: int = 0
    mutation_execution_errors: int = 0
    final_mutation_score: Optional[float] = None
    reflection_iterations_performed: int = 0
    final_hardening_status: str = "INITIALIZING"

    mutants: List[MutantRecord] = Field(default_factory=list)
    history: List[IterationMetrics] = Field(default_factory=list)

    surviving_mutant_diffs: List[str] = Field(default_factory=list)
    surviving_guidance: List[Dict[str, Any]] = Field(default_factory=list)
    reflection_notes: List[str] = Field(default_factory=list)

    terminated: bool = False
    termination_reason: str = ""
    hardware_info: Dict[str, Any] = Field(default_factory=dict)
    active_provider: str = "Google GenAI Live"

    # Canonical Lifecycle Tracking
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    lifecycle_state: TaskLifecycleState = TaskLifecycleState.CREATED
    stage_durations: Dict[str, float] = Field(default_factory=dict)
    stage_history: List[StageRecord] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
