"""
blackboard.py - Typed, Thread-Safe Blackboard Architecture for TestForge.

Partitions:
  1. TargetSpace: Target source code, symbol signatures, call graph, and blast risk metadata.
  2. MutantSpace: Injected AST mutant records, evaluation status, and surviving diffs.
  3. CriticSpace: Adversarial failure directives, mechanisms, and reflection notes.
  4. SuiteSpace: Candidate Pytest suites, baseline test suites, and provider metadata.
  5. MetricsSpace: Convergence metrics, line coverage, pass/fail rates, and iteration history.

Capabilities:
  - Strongly typed Pydantic v2 partition schemas with fail-closed validation.
  - Re-entrant thread lock (RLock) guaranteeing atomic, race-free partition mutations.
  - Monotonically increasing revision counter with immutable, sanitized change history.
  - Consistent point-in-time snapshots with deep-copy defensive isolation.
  - Priority-ordered, failure-isolated observer subscriptions with optional partition filtering.
  - Full bidirectional compatibility with TestForgeState and Phase 1 Lifecycle Callbacks.
"""

from __future__ import annotations
import copy
import time
import json
import uuid
import threading
import logging
from typing import Dict, Any, Optional, List, Callable, Set, Union, Literal
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError

from testforge.state import MutantRecord, IterationMetrics, TestForgeState
from testforge.security import redact_sensitive_data
from testforge.callbacks import CallbackRegistry, LifecycleEvent, EventType
from testforge.persistence import (
    SQLiteBlackboardStorage,
    CheckpointMetadata,
    CheckpointRecord,
    CheckpointSummary,
    CheckpointError,
    CheckpointNotFoundError,
    IncompatibleSchemaError,
    CorruptedSnapshotError,
    PersistenceWriteError,
)

logger = logging.getLogger("testforge.blackboard")


# ==============================================================================
# 1. Typed State Partition Schemas
# ==============================================================================

class TargetSpace(BaseModel):
    """Partition containing the target under test and static analysis metadata."""
    target_module_path: str = "target.py"
    target_source_code: str = ""
    target_file_path: Optional[str] = None
    target_lines: Optional[List[int]] = None
    functions: List[str] = Field(default_factory=list)
    classes: List[str] = Field(default_factory=list)
    blast_risk: str = "LOW"
    source_sha: str = ""
    line_count: int = 0
    dependencies: List[str] = Field(default_factory=list)
    is_untrusted: bool = True
    provenance: str = "ingestion"
    injection_findings: List[Dict[str, Any]] = Field(default_factory=list)


class MutantSpace(BaseModel):
    """Partition containing AST mutant records, evaluation results, and surviving diffs."""
    mutants: List[MutantRecord] = Field(default_factory=list)
    mutants_generated: int = 0
    mutants_executed: int = 0
    mutants_killed: int = 0
    mutants_survived: int = 0
    mutants_timed_out: int = 0
    mutants_invalid: int = 0
    mutants_equivalent: int = 0
    mutants_potentially_equivalent: int = 0
    mutation_execution_errors: int = 0
    current_mutation_score: float = 0.0
    raw_mutation_score: float = 0.0
    adjusted_mutation_score: float = 0.0
    surviving_mutant_diffs: List[str] = Field(default_factory=list)


class CriticSpace(BaseModel):
    """Partition containing adversarial failure directives and remediation notes."""
    critic_directives: List[str] = Field(default_factory=list)
    latest_directive: str = ""
    reflection_notes: List[str] = Field(default_factory=list)
    failure_mechanisms: Dict[str, str] = Field(default_factory=dict)
    semantic_guidance: List[Dict[str, Any]] = Field(default_factory=list)


class SuiteSpace(BaseModel):
    """Partition containing candidate, baseline, and hardened Pytest test suites."""
    test_module_path: str = "test_target.py"
    current_test_code: str = ""
    candidate_test_code: str = ""
    baseline_test_code: str = ""
    hardened_test_code: str = ""
    active_provider: str = "Google GenAI Live"
    baseline_tests_generated: int = 0
    baseline_tests_executed: int = 0
    baseline_passed: bool = False
    baseline_tests_passed: int = 0
    baseline_tests_failed: int = 0


class MetricsSpace(BaseModel):
    """Partition containing iteration metrics, execution stats, and hardening status."""
    current_iteration: int = 0
    max_iterations: int = 3
    target_mutation_score: float = 85.0
    baseline_line_coverage: float = 0.0
    lines_covered: int = 0
    num_statements: int = 0
    history: List[IterationMetrics] = Field(default_factory=list)
    final_mutation_score: float = 0.0
    raw_mutation_score: float = 0.0
    adjusted_mutation_score: float = 0.0
    equivalent_mutants: int = 0
    potentially_equivalent_mutants: int = 0
    reflection_iterations_performed: int = 0
    final_hardening_status: str = "INITIALIZING"
    terminated: bool = False
    termination_reason: str = ""
    hardware_info: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    lifecycle_state: str = "CREATED"
    stage_durations: Dict[str, float] = Field(default_factory=dict)
    stage_history: List[Dict[str, Any]] = Field(default_factory=list)



# ==============================================================================
# 2. Events, History Entries, and Snapshots
# ==============================================================================

class BlackboardEvent(BaseModel):
    """Typed event emitted on validated partition state changes."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    revision: int
    partition: Literal["target", "mutant", "critic", "suite", "metrics"]
    event_type: str = "UPDATE"
    timestamp: float = Field(default_factory=time.time)
    safe_metadata: Dict[str, Any] = Field(default_factory=dict)


class BlackboardSnapshot(BaseModel):
    """Consistent, point-in-time snapshot across all Blackboard partitions."""
    revision: int
    timestamp: float = Field(default_factory=time.time)
    target: TargetSpace
    mutant: MutantSpace
    critic: CriticSpace
    suite: SuiteSpace
    metrics: MetricsSpace


class BlackboardSubscription:
    """Internal registration model for a Blackboard observer."""
    def __init__(
        self,
        subscription_id: str,
        handler: Callable[[BlackboardEvent], None],
        partitions: Optional[Set[str]] = None,
        priority: int = 100,
        registration_order: int = 0,
        name: Optional[str] = None,
    ):
        self.subscription_id = subscription_id
        self.handler = handler
        self.partitions = partitions  # None means all partitions
        self.priority = priority
        self.registration_order = registration_order
        self.name = name or getattr(handler, "__name__", f"sub_{subscription_id[:8]}")

    def matches(self, partition_name: str) -> bool:
        if self.partitions is None:
            return True
        return partition_name in self.partitions


# Helper to compute safe metadata without leaking full source or credentials
def _extract_safe_change_metadata(partition: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"fields_modified": sorted(list(updates.keys()))}
    for k, v in updates.items():
        if k in ("target_source_code", "current_test_code", "baseline_test_code", "hardened_test_code", "candidate_test_code"):
            meta[f"{k}_len"] = len(v) if isinstance(v, str) else 0
        elif k in ("mutants", "history", "critic_directives", "surviving_mutant_diffs", "functions", "classes"):
            meta[f"{k}_count"] = len(v) if isinstance(v, (list, dict, set)) else 0
        elif k in ("current_mutation_score", "final_mutation_score", "baseline_line_coverage"):
            meta[k] = float(v) if isinstance(v, (int, float)) else 0.0
        elif k in ("terminated", "final_hardening_status", "current_iteration", "active_provider", "blast_risk", "lifecycle_state", "task_id"):
            meta[k] = v
        elif isinstance(v, (int, float, bool, str)) and len(str(v)) <= 80:
            meta[k] = redact_sensitive_data(str(v))
    return meta


# ==============================================================================
# 3. Blackboard Controller
# ==============================================================================

class Blackboard:
    """
    Central, thread-safe, typed Blackboard state store for TestForge.
    
    Guarantees:
      - Thread Safety: Guarded by threading.RLock.
      - Strong Typing: All updates validated against Pydantic v2 schemas.
      - Atomic Updates: Validation failures never partially mutate state.
      - Defensive Copying: Reads return deep copies to prevent external in-place corruption.
      - Failure-Isolated Subscriptions: Observer exceptions never crash the pipeline.
      - History Provenance: Monotonically increasing revision numbers with safe metadata.
    """

    PARTITION_MODELS = {
        "target": TargetSpace,
        "mutant": MutantSpace,
        "critic": CriticSpace,
        "suite": SuiteSpace,
        "metrics": MetricsSpace,
    }

    def __init__(
        self,
        callback_registry: Optional[CallbackRegistry] = None,
        storage: Optional[SQLiteBlackboardStorage] = None,
        checkpoint_db_path: Optional[Union[str, Path]] = None,
        strict_persistence: bool = False,
    ):
        self._lock = threading.RLock()
        self._callback_registry = callback_registry
        self.strict_persistence = strict_persistence

        # Persistence storage
        if storage is not None:
            self._storage = storage
        elif checkpoint_db_path is not None:
            self._storage = SQLiteBlackboardStorage(
                checkpoint_db_path,
                strict_mode=strict_persistence
            )
        else:
            self._storage = None

        # Partitions
        self._target = TargetSpace()
        self._mutant = MutantSpace()
        self._critic = CriticSpace()
        self._suite = SuiteSpace()
        self._metrics = MetricsSpace()

        # Provenance & subscriptions
        self._revision: int = 0
        self._history: List[BlackboardEvent] = []
        self._subscriptions: Dict[str, BlackboardSubscription] = {}
        self._sub_counter: int = 0

    @property
    def storage(self) -> Optional[SQLiteBlackboardStorage]:
        with self._lock:
            return self._storage

    @property
    def has_persistence(self) -> bool:
        with self._lock:
            return self._storage is not None

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    # --------------------------------------------------------------------------
    # Partition Accessors (Defensive Copies)
    # --------------------------------------------------------------------------

    def get_target_space(self) -> TargetSpace:
        with self._lock:
            return self._target.model_copy(deep=True)

    def get_mutant_space(self) -> MutantSpace:
        with self._lock:
            return self._mutant.model_copy(deep=True)

    def get_critic_space(self) -> CriticSpace:
        with self._lock:
            return self._critic.model_copy(deep=True)

    def get_suite_space(self) -> SuiteSpace:
        with self._lock:
            return self._suite.model_copy(deep=True)

    def get_metrics_space(self) -> MetricsSpace:
        with self._lock:
            return self._metrics.model_copy(deep=True)

    def get_isolated_target_code(self, provenance: str = "target_space") -> str:
        """Returns the target source code safely wrapped in untrusted data delimiters."""
        from testforge.prompt_guard import wrap_untrusted_content, inspect_source_for_indirect_injections
        with self._lock:
            code = self._target.target_source_code
            scan = inspect_source_for_indirect_injections(code)
            safe_code = scan.defused_text if scan.has_injection else code
            return wrap_untrusted_content(
                safe_code,
                content_type="source_code",
                provenance=provenance
            )

    @property
    def target(self) -> TargetSpace:
        return self.get_target_space()

    @property
    def mutant(self) -> MutantSpace:
        return self.get_mutant_space()

    @property
    def critic(self) -> CriticSpace:
        return self.get_critic_space()

    @property
    def suite(self) -> SuiteSpace:
        return self.get_suite_space()

    @property
    def metrics(self) -> MetricsSpace:
        return self.get_metrics_space()

    def get_partition(
        self, partition_name: Literal["target", "mutant", "critic", "suite", "metrics"]
    ) -> BaseModel:
        """Retrieves a deep copy of the requested partition model."""
        with self._lock:
            if partition_name == "target":
                return self.get_target_space()
            elif partition_name == "mutant":
                return self.get_mutant_space()
            elif partition_name == "critic":
                return self.get_critic_space()
            elif partition_name == "suite":
                return self.get_suite_space()
            elif partition_name == "metrics":
                return self.get_metrics_space()
            else:
                raise ValueError(f"Unknown partition '{partition_name}'. Valid: {list(self.PARTITION_MODELS.keys())}")

    # --------------------------------------------------------------------------
    # Partition Mutators (Atomic, Validated, Thread-Safe)
    # --------------------------------------------------------------------------

    def update_target_space(self, **kwargs) -> TargetSpace:
        return self.update_partition("target", kwargs)  # type: ignore

    def update_mutant_space(self, **kwargs) -> MutantSpace:
        return self.update_partition("mutant", kwargs)  # type: ignore

    def update_critic_space(self, **kwargs) -> CriticSpace:
        return self.update_partition("critic", kwargs)  # type: ignore

    def update_suite_space(self, **kwargs) -> SuiteSpace:
        return self.update_partition("suite", kwargs)  # type: ignore

    def update_metrics_space(self, **kwargs) -> MetricsSpace:
        return self.update_partition("metrics", kwargs)  # type: ignore

    def update_partition(
        self,
        partition_name: Literal["target", "mutant", "critic", "suite", "metrics"],
        updates: Union[Dict[str, Any], BaseModel],
        event_type: str = "UPDATE"
    ) -> BaseModel:
        """
        Atomically applies updates to a partition after Pydantic validation.
        
        Guarantees:
          - If validation fails, raises ValidationError and stored state remains UNTOUCHED.
          - Monotonically increments revision number.
          - Appends sanitized history entry.
          - Notifies matching subscribers in deterministic priority order without holding lock.
        """
        if partition_name not in self.PARTITION_MODELS:
            raise ValueError(f"Invalid partition name '{partition_name}'. Valid: {list(self.PARTITION_MODELS.keys())}")

        update_dict = updates.model_dump() if isinstance(updates, BaseModel) else dict(updates)
        model_cls = self.PARTITION_MODELS[partition_name]

        subscribers_to_notify: List[BlackboardSubscription] = []
        event_to_dispatch: Optional[BlackboardEvent] = None

        with self._lock:
            # 1. Fetch current partition
            current_partition = getattr(self, f"_{partition_name}")
            merged_dict = current_partition.model_dump()

            # Prompt-injection defense: scan and defuse untrusted inputs across partitions
            if partition_name == "target":
                target_code = update_dict.get("target_source_code") or update_dict.get("source_code")
                if target_code:
                    update_dict["target_source_code"] = target_code
                    if "source_code" in update_dict and "source_code" not in TargetSpace.model_fields:
                        del update_dict["source_code"]
                    from testforge.prompt_guard import inspect_source_for_indirect_injections
                    scan_res = inspect_source_for_indirect_injections(target_code)
                    if scan_res.has_injection:
                        update_dict["injection_findings"] = [f.model_dump() for f in scan_res.findings]
                        if self._callback_registry:
                            self._callback_registry.dispatch(LifecycleEvent(
                                event_type=EventType.ERROR,
                                emitter="Blackboard[TargetSpace]",
                                payload={"error_type": "PromptInjectionDetected", "findings": [f.model_dump() for f in scan_res.findings]}
                            ))
            elif partition_name == "critic":
                from testforge.prompt_guard import sanitize_critic_directive
                if "critic_directive" in update_dict and "latest_directive" not in update_dict:
                    update_dict["latest_directive"] = update_dict.pop("critic_directive")
                if "latest_directive" in update_dict and update_dict["latest_directive"]:
                    is_clean, clean_d, _ = sanitize_critic_directive(update_dict["latest_directive"])
                    update_dict["latest_directive"] = clean_d
                    if "critic_directives" not in update_dict:
                        existing = list(merged_dict.get("critic_directives", []))
                        existing.append(clean_d)
                        update_dict["critic_directives"] = existing
                if "critic_directives" in update_dict and isinstance(update_dict["critic_directives"], list):
                    sanitized_dirs = []
                    for d in update_dict["critic_directives"]:
                        is_clean, clean_d, _ = sanitize_critic_directive(d)
                        sanitized_dirs.append(clean_d if not is_clean else d)
                    update_dict["critic_directives"] = sanitized_dirs

            merged_dict.update(update_dict)

            # 2. Validate merged dictionary (atomic fail-closed check)
            # Will raise ValidationError if invalid, leaving self._<partition> completely unmodified
            validated_partition = model_cls.model_validate(merged_dict)

            # 3. Commit mutation
            setattr(self, f"_{partition_name}", validated_partition)
            self._revision += 1

            # 4. Record sanitized history entry
            safe_meta = _extract_safe_change_metadata(partition_name, update_dict)
            event_to_dispatch = BlackboardEvent(
                revision=self._revision,
                partition=partition_name,
                event_type=event_type,
                timestamp=time.time(),
                safe_metadata=safe_meta,
            )
            self._history.append(event_to_dispatch)

            # 5. Snapshot matching subscribers under lock
            matching = [
                sub for sub in self._subscriptions.values()
                if sub.matches(partition_name)
            ]
            matching.sort(key=lambda s: (-s.priority, s.registration_order))
            subscribers_to_notify = matching

            result_copy = validated_partition.model_copy(deep=True)

        # 6. Dispatch notifications OUTSIDE lock to avoid deadlocks
        if event_to_dispatch:
            for sub in subscribers_to_notify:
                try:
                    sub.handler(event_to_dispatch)
                except Exception as exc:
                    logger.error(f"Blackboard observer '{sub.name}' failed on partition '{partition_name}': {exc}", exc_info=True)

            # 7. Bridge to Phase 1 Lifecycle Callback Registry if attached
            if self._callback_registry:
                try:
                    self._callback_registry.dispatch(
                        LifecycleEvent(
                            event_type=EventType.STATE_CHANGE,
                            emitter="Blackboard",
                            payload={
                                "component": "blackboard",
                                "partition": partition_name,
                                "revision": event_to_dispatch.revision,
                                "event_type": event_type,
                            },
                            metadata=event_to_dispatch.safe_metadata,
                        )
                    )
                except Exception as exc:
                    logger.warning(f"Failed to bridge Blackboard event to CallbackRegistry: {exc}")

        return result_copy

    # --------------------------------------------------------------------------
    # Snapshot & History
    # --------------------------------------------------------------------------

    def get_snapshot(self) -> BlackboardSnapshot:
        """Returns a consistent point-in-time snapshot of all partitions."""
        with self._lock:
            return BlackboardSnapshot(
                revision=self._revision,
                timestamp=time.time(),
                target=self._target.model_copy(deep=True),
                mutant=self._mutant.model_copy(deep=True),
                critic=self._critic.model_copy(deep=True),
                suite=self._suite.model_copy(deep=True),
                metrics=self._metrics.model_copy(deep=True),
            )

    def get_history(self) -> List[BlackboardEvent]:
        """Returns an immutable copy of the state-change history."""
        with self._lock:
            return [e.model_copy(deep=True) for e in self._history]

    # --------------------------------------------------------------------------
    # Persistent SQLite Checkpointing
    # --------------------------------------------------------------------------

    def save_checkpoint(
        self,
        stage: str,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Saves a consistent point-in-time snapshot to the configured SQLite persistence store.
        Returns the saved checkpoint_id, or None if persistence is disabled.
        
        Guarantees:
          - Deep-copies point-in-time snapshot under lock.
          - Redacts all credentials and secrets before disk write.
          - Dispatches CHECKPOINT_SAVED on success.
          - In-memory state remains intact if database write fails (when strict_persistence=False).
        """
        with self._lock:
            if self._storage is None:
                return None
            snapshot = self.get_snapshot()

        try:
            metadata = self._storage.save_checkpoint(
                snapshot=snapshot,
                stage=stage,
                job_id=job_id,
                workflow_id=workflow_id,
                status=status,
                extra_meta=extra_meta,
                checkpoint_id=checkpoint_id,
            )

            # Dispatch CHECKPOINT_SAVED callback outside lock
            if self._callback_registry:
                try:
                    self._callback_registry.dispatch(
                        LifecycleEvent(
                            event_type=EventType.CHECKPOINT_SAVED,
                            emitter="Blackboard",
                            workflow_id=workflow_id or "unknown_wf",
                            correlation_id=job_id or "unknown_job",
                            payload={
                                "checkpoint_id": metadata.checkpoint_id,
                                "stage": stage,
                                "revision": metadata.revision,
                                "job_id": job_id,
                                "status": metadata.status,
                            },
                            metadata=metadata.metrics_summary,
                        )
                    )
                except Exception as exc:
                    logger.warning(f"Failed to dispatch CHECKPOINT_SAVED callback: {exc}")

            return metadata.checkpoint_id
        except Exception as exc:
            logger.error(f"Failed to save checkpoint (stage='{stage}'): {exc}", exc_info=True)
            if self._callback_registry:
                try:
                    self._callback_registry.dispatch(
                        LifecycleEvent(
                            event_type=EventType.CHECKPOINT_FAILED,
                            emitter="Blackboard",
                            workflow_id=workflow_id or "unknown_wf",
                            correlation_id=job_id or "unknown_job",
                            outcome="FAILED",
                            payload={
                                "stage": stage,
                                "error": str(exc),
                                "job_id": job_id,
                            },
                        )
                    )
                except Exception:
                    pass
            if self.strict_persistence:
                raise PersistenceWriteError(f"Checkpoint save failed: {exc}") from exc
            return None

    def restore_from_snapshot(
        self,
        snapshot: BlackboardSnapshot,
    ) -> None:
        """
        Atomically restores all Blackboard partitions from a validated BlackboardSnapshot.
        
        Guarantees:
          - Validates all partition structures via Pydantic model copies.
          - Monotonically advances revision number past the prior revision.
          - Records a RESTORE event in provenance history.
          - Dispatches CHECKPOINT_RESTORED lifecycle event if callback registry attached.
        """
        with self._lock:
            # 1. Validate partitions
            self._target = snapshot.target.model_copy(deep=True)
            self._mutant = snapshot.mutant.model_copy(deep=True)
            self._critic = snapshot.critic.model_copy(deep=True)
            self._suite = snapshot.suite.model_copy(deep=True)
            self._metrics = snapshot.metrics.model_copy(deep=True)

            # 2. Advance revision monotonically
            self._revision = max(self._revision, snapshot.revision) + 1

            # 3. Append history event
            restore_event = BlackboardEvent(
                revision=self._revision,
                partition="metrics",
                event_type="RESTORE",
                timestamp=time.time(),
                safe_metadata={
                    "restored_from_revision": snapshot.revision,
                    "target_module": self._target.target_module_path,
                    "iteration": self._metrics.current_iteration,
                    "hardening_status": self._metrics.final_hardening_status,
                },
            )
            self._history.append(restore_event)

        # 4. Dispatch callback outside lock
        if self._callback_registry:
            try:
                self._callback_registry.dispatch(
                    LifecycleEvent(
                        event_type=EventType.CHECKPOINT_RESTORED,
                        emitter="Blackboard",
                        payload={
                            "revision": self._revision,
                            "restored_revision": snapshot.revision,
                            "status": self._metrics.final_hardening_status,
                        },
                        metadata=restore_event.safe_metadata,
                    )
                )
            except Exception as exc:
                logger.warning(f"Failed to dispatch CHECKPOINT_RESTORED callback: {exc}")

    def restore_checkpoint(self, checkpoint_id: str) -> BlackboardSnapshot:
        """
        Restores Blackboard partition state from a saved SQLite checkpoint.
        
        Raises CheckpointNotFoundError, IncompatibleSchemaError, CorruptedSnapshotError.
        """
        if self._storage is None:
            raise CheckpointError("Cannot restore checkpoint: persistence is not enabled on this Blackboard instance.")

        record = self._storage.load_checkpoint(checkpoint_id)
        try:
            snapshot_dict = json.loads(record.snapshot_json)
            snapshot = BlackboardSnapshot.model_validate(snapshot_dict)
        except Exception as exc:
            raise CorruptedSnapshotError(f"Corrupted snapshot in checkpoint '{checkpoint_id}': {exc}") from exc

        self.restore_from_snapshot(snapshot)
        return snapshot

    def list_checkpoints(
        self,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CheckpointSummary]:
        """Lists available checkpoints matching optional criteria."""
        if self._storage is None:
            return []
        return self._storage.list_checkpoints(
            job_id=job_id,
            workflow_id=workflow_id,
            limit=limit,
            offset=offset
        )

    def close(self) -> None:
        """Closes the underlying SQLite storage connection if open."""
        with self._lock:
            if self._storage is not None:
                self._storage.close()

    # --------------------------------------------------------------------------
    # Observer Subscriptions
    # --------------------------------------------------------------------------

    def subscribe(
        self,
        handler: Callable[[BlackboardEvent], None],
        partitions: Optional[Union[str, List[str], Set[str]]] = None,
        priority: int = 100,
        name: Optional[str] = None,
    ) -> str:
        """
        Registers an observer for partition changes.
        Returns unique subscription ID for unregistering.
        """
        if not callable(handler):
            raise TypeError(f"Subscriber handler must be callable, got {type(handler)}")

        part_set: Optional[Set[str]] = None
        if partitions is not None:
            if isinstance(partitions, str):
                part_set = {partitions}
            else:
                part_set = set(partitions)
            for p in part_set:
                if p not in self.PARTITION_MODELS:
                    raise ValueError(f"Cannot subscribe to unknown partition '{p}'. Valid: {list(self.PARTITION_MODELS.keys())}")

        sub_id = str(uuid.uuid4())
        with self._lock:
            self._sub_counter += 1
            subscription = BlackboardSubscription(
                subscription_id=sub_id,
                handler=handler,
                partitions=part_set,
                priority=priority,
                registration_order=self._sub_counter,
                name=name,
            )
            self._subscriptions[sub_id] = subscription

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Removes an active observer subscription."""
        with self._lock:
            return self._subscriptions.pop(subscription_id, None) is not None

    def clear_subscriptions(self):
        """Clears all observer subscriptions."""
        with self._lock:
            self._subscriptions.clear()
            self._sub_counter = 0

    @property
    def subscription_count(self) -> int:
        with self._lock:
            return len(self._subscriptions)

    # --------------------------------------------------------------------------
    # TestForgeState Interoperability
    # --------------------------------------------------------------------------

    def to_testforge_state(self) -> TestForgeState:
        """Constructs an equivalent TestForgeState from current partitions."""
        with self._lock:
            return TestForgeState(
                target_module_path=self._target.target_module_path,
                test_module_path=self._suite.test_module_path,
                target_source_code=self._target.target_source_code,
                current_test_code=self._suite.current_test_code,
                current_iteration=self._metrics.current_iteration,
                max_iterations=self._metrics.max_iterations,
                target_mutation_score=self._metrics.target_mutation_score,
                baseline_line_coverage=self._metrics.baseline_line_coverage,
                lines_covered=self._metrics.lines_covered,
                num_statements=self._metrics.num_statements,
                baseline_tests_generated=self._suite.baseline_tests_generated,
                baseline_tests_executed=self._suite.baseline_tests_executed,
                baseline_passed=self._suite.baseline_passed,
                baseline_tests_passed=self._suite.baseline_tests_passed,
                baseline_tests_failed=self._suite.baseline_tests_failed,
                mutants_generated=self._mutant.mutants_generated,
                mutants_executed=self._mutant.mutants_executed,
                mutants_killed=self._mutant.mutants_killed,
                mutants_survived=self._mutant.mutants_survived,
                mutation_execution_errors=self._mutant.mutation_execution_errors,
                final_mutation_score=self._metrics.final_mutation_score,
                reflection_iterations_performed=self._metrics.reflection_iterations_performed,
                final_hardening_status=self._metrics.final_hardening_status,
                mutants=[m.model_copy(deep=True) for m in self._mutant.mutants],
                history=[h.model_copy(deep=True) for h in self._metrics.history],
                surviving_mutant_diffs=list(self._mutant.surviving_mutant_diffs),
                reflection_notes=list(self._critic.reflection_notes),
                terminated=self._metrics.terminated,
                termination_reason=self._metrics.termination_reason,
                hardware_info=dict(self._metrics.hardware_info),
                active_provider=self._suite.active_provider,
            )

    @classmethod
    def from_testforge_state(
        cls,
        state: TestForgeState,
        callback_registry: Optional[CallbackRegistry] = None,
        storage: Optional[SQLiteBlackboardStorage] = None,
        checkpoint_db_path: Optional[Union[str, Path]] = None,
        strict_persistence: bool = False,
    ) -> "Blackboard":
        """Factory creating a Blackboard populated with an existing TestForgeState."""
        bb = cls(
            callback_registry=callback_registry,
            storage=storage,
            checkpoint_db_path=checkpoint_db_path,
            strict_persistence=strict_persistence,
        )

        with bb._lock:
            # 1. TargetSpace
            bb._target = TargetSpace(
                target_module_path=state.target_module_path,
                target_source_code=state.target_source_code,
            )

            # 2. MutantSpace
            bb._mutant = MutantSpace(
                mutants=[m.model_copy(deep=True) for m in state.mutants],
                mutants_generated=state.mutants_generated or len(state.mutants),
                mutants_executed=state.mutants_executed,
                mutants_killed=state.mutants_killed,
                mutants_survived=state.mutants_survived,
                mutation_execution_errors=state.mutation_execution_errors,
                current_mutation_score=state.final_mutation_score,
                surviving_mutant_diffs=list(state.surviving_mutant_diffs),
            )

            # 3. CriticSpace
            bb._critic = CriticSpace(
                reflection_notes=list(state.reflection_notes),
            )

            # 4. SuiteSpace
            bb._suite = SuiteSpace(
                test_module_path=state.test_module_path,
                current_test_code=state.current_test_code,
                active_provider=state.active_provider,
                baseline_tests_generated=state.baseline_tests_generated,
                baseline_tests_executed=state.baseline_tests_executed,
                baseline_passed=state.baseline_passed,
                baseline_tests_passed=state.baseline_tests_passed,
                baseline_tests_failed=state.baseline_tests_failed,
            )

            # 5. MetricsSpace
            bb._metrics = MetricsSpace(
                current_iteration=state.current_iteration,
                max_iterations=state.max_iterations,
                target_mutation_score=state.target_mutation_score,
                baseline_line_coverage=state.baseline_line_coverage,
                lines_covered=state.lines_covered,
                num_statements=state.num_statements,
                history=[h.model_copy(deep=True) for h in state.history],
                final_mutation_score=state.final_mutation_score,
                reflection_iterations_performed=state.reflection_iterations_performed,
                final_hardening_status=state.final_hardening_status,
                terminated=state.terminated,
                termination_reason=state.termination_reason,
                hardware_info=dict(state.hardware_info),
                task_id=state.task_id,
                lifecycle_state=state.lifecycle_state.value if hasattr(state.lifecycle_state, "value") else str(state.lifecycle_state),
                stage_durations=dict(state.stage_durations),
                stage_history=[r.model_dump() for r in state.stage_history],
            )

            bb._revision = 1
            bb._history.append(
                BlackboardEvent(
                    revision=1,
                    partition="target",
                    event_type="INITIALIZE",
                    safe_metadata={"source": "from_testforge_state"},
                )
            )

        return bb

    def sync_to_state(self, state: TestForgeState) -> None:
        """Synchronizes current Blackboard partition state into a TestForgeState instance."""
        with self._lock:
            state.target_module_path = self._target.target_module_path
            state.test_module_path = self._suite.test_module_path
            state.target_source_code = self._target.target_source_code
            state.current_test_code = self._suite.current_test_code
            state.current_iteration = self._metrics.current_iteration
            state.max_iterations = self._metrics.max_iterations
            state.target_mutation_score = self._metrics.target_mutation_score
            state.baseline_line_coverage = self._metrics.baseline_line_coverage
            state.lines_covered = self._metrics.lines_covered
            state.num_statements = self._metrics.num_statements
            state.baseline_tests_generated = self._suite.baseline_tests_generated
            state.baseline_tests_executed = self._suite.baseline_tests_executed
            state.baseline_passed = self._suite.baseline_passed
            state.baseline_tests_passed = self._suite.baseline_tests_passed
            state.baseline_tests_failed = self._suite.baseline_tests_failed
            state.mutants_generated = self._mutant.mutants_generated
            state.mutants_executed = self._mutant.mutants_executed
            state.mutants_killed = self._mutant.mutants_killed
            state.mutants_survived = self._mutant.mutants_survived
            state.mutation_execution_errors = self._mutant.mutation_execution_errors
            state.final_mutation_score = self._metrics.final_mutation_score
            state.reflection_iterations_performed = self._metrics.reflection_iterations_performed
            state.final_hardening_status = self._metrics.final_hardening_status
            state.mutants = [m.model_copy(deep=True) for m in self._mutant.mutants]
            state.history = [h.model_copy(deep=True) for h in self._metrics.history]
            state.surviving_mutant_diffs = list(self._mutant.surviving_mutant_diffs)
            state.reflection_notes = list(self._critic.reflection_notes)
            state.terminated = self._metrics.terminated
            state.termination_reason = self._metrics.termination_reason
            state.hardware_info = dict(self._metrics.hardware_info)
            state.active_provider = self._suite.active_provider
            if self._metrics.task_id:
                state.task_id = self._metrics.task_id
            if self._metrics.lifecycle_state:
                try:
                    from testforge.state import TaskLifecycleState
                    state.lifecycle_state = TaskLifecycleState(self._metrics.lifecycle_state)
                except Exception:
                    pass
            state.stage_durations = dict(self._metrics.stage_durations)
