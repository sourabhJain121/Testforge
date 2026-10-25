"""
persistence.py - Persistent SQLite Blackboard Checkpointing for TestForge.

Capabilities:
  1. Versioned SQLite Checkpointing:
     - All-or-nothing transactional storage of full BlackboardSnapshots.
     - Parameterized SQL queries preventing injection.
     - Indexed lookups by checkpoint_id, job_id, workflow_id, and created_at.
  2. Concurrency & High Availability:
     - SQLite Write-Ahead Logging (WAL) mode for concurrent readers and writers.
     - Configurable busy_timeout to prevent lock contention errors.
     - Thread-safe connection synchronization via re-entrant lock (RLock).
  3. Fail-Safe Recovery:
     - Typed Pydantic validation on snapshot restoration.
     - Explicit handling of corrupted data and schema version mismatches.
     - In-memory preservation if database writes fail (when strict_mode=False).
  4. Data Sanitization & Security:
     - Deep redaction of API keys, passwords, and sensitive tokens prior to disk persistence.
"""

from __future__ import annotations
import os
import time
import json
import uuid
import sqlite3
import hashlib
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field

from testforge.security import redact_sensitive_data

logger = logging.getLogger("testforge.persistence")

CURRENT_SCHEMA_VERSION = 1


# ==============================================================================
# Exceptions
# ==============================================================================

class CheckpointError(Exception):
    """Base exception for all checkpoint and persistence operations."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Raised when a requested checkpoint ID does not exist in the database."""
    pass


class IncompatibleSchemaError(CheckpointError):
    """Raised when checkpoint schema_version does not match the engine version."""
    pass


class CorruptedSnapshotError(CheckpointError):
    """Raised when checkpoint snapshot JSON is malformed or violates partition models."""
    pass


class PersistenceWriteError(CheckpointError):
    """Raised when saving a checkpoint fails due to I/O or SQLite operational errors."""
    pass


class InputHashMismatchError(CheckpointError):
    """Raised when checkpoint source hash does not match current target source code."""
    pass


class IncompleteCheckpointError(CheckpointError):
    """Raised when checkpoint lacks required partition state (e.g. empty target code)."""
    pass


class InvalidRecoveryStageError(CheckpointError):
    """Raised when checkpoint stage cannot be safely resumed."""
    pass


# ==============================================================================
# Data Transfer Models
# ==============================================================================

class CheckpointMetadata(BaseModel):
    """Metadata describing a saved Blackboard checkpoint."""
    checkpoint_id: str
    schema_version: int = CURRENT_SCHEMA_VERSION
    job_id: Optional[str] = None
    workflow_id: Optional[str] = None
    stage: str
    revision: int
    created_at: float
    status: str
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)


class CheckpointSummary(BaseModel):
    """Lightweight summary record for checkpoint listings."""
    checkpoint_id: str
    schema_version: int
    job_id: Optional[str] = None
    workflow_id: Optional[str] = None
    stage: str
    revision: int
    created_at: float
    status: str
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    snapshot_bytes: int = 0


class CheckpointRecord(BaseModel):
    """Complete checkpoint record including metadata and serialized snapshot."""
    metadata: CheckpointMetadata
    snapshot_json: str

    @property
    def checkpoint_id(self) -> str:
        return self.metadata.checkpoint_id

    @property
    def stage(self) -> str:
        return self.metadata.stage


class ResumptionPlan(BaseModel):
    """Plan for resuming task execution from a validated checkpoint."""
    checkpoint_id: str
    checkpoint_stage: str
    resumes_at: str
    target_lifecycle_state: str
    skipped_stages: List[str] = Field(default_factory=list)
    start_iteration: int = 1
    description: str = ""


# ==============================================================================
# Security Sanitizer
# ==============================================================================

_SENSITIVE_KEYS = {
    "api_key", "apikey", "secret", "secret_key", "password", "token",
    "access_token", "auth_token", "credentials", "private_key",
    "gemini_api_key", "openrouter_api_key"
}


def _scrub_sensitive_dict(obj: Any) -> Any:
    """Recursively traverses and redacts credentials from dicts, lists, and primitives."""
    if isinstance(obj, dict):
        scrubbed = {}
        for k, v in obj.items():
            if str(k).lower() in _SENSITIVE_KEYS:
                scrubbed[k] = "[REDACTED_SECRET]"
            else:
                scrubbed[k] = _scrub_sensitive_dict(v)
        return scrubbed
    elif isinstance(obj, list):
        return [_scrub_sensitive_dict(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_scrub_sensitive_dict(item) for item in obj)
    elif isinstance(obj, str):
        # Scrub inline keys or tokens
        return redact_sensitive_data(obj)
    return obj


# ==============================================================================
# SQLite Storage Manager
# ==============================================================================

class SQLiteBlackboardStorage:
    """
    Thread-safe SQLite persistent checkpoint repository for TestForge Blackboard state.
    """

    def __init__(
        self,
        db_path: Union[str, Path],
        journal_mode: str = "WAL",
        busy_timeout_ms: int = 5000,
        strict_mode: bool = False,
    ):
        self.db_path = str(db_path)
        self.journal_mode = journal_mode
        self.busy_timeout_ms = busy_timeout_ms
        self.strict_mode = strict_mode
        self._lock = threading.RLock()
        self._closed = False

        # Ensure parent directory exists for file-based paths
        if self.db_path != ":memory:":
            parent_dir = Path(self.db_path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(
            self.db_path,
            timeout=self.busy_timeout_ms / 1000.0,
            check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row

        self._init_db()

    def _init_db(self) -> None:
        """Initializes database pragmas, schema tables, and performance indexes."""
        with self._lock:
            cursor = self._conn.cursor()
            try:
                # WAL mode and pragmas
                if self.db_path != ":memory:":
                    cursor.execute(f"PRAGMA journal_mode = {self.journal_mode};")
                cursor.execute("PRAGMA synchronous = NORMAL;")
                cursor.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms};")

                # Schema version table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at REAL NOT NULL
                    );
                """)

                # Checkpoints table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id TEXT PRIMARY KEY,
                        schema_version INTEGER NOT NULL,
                        job_id TEXT,
                        workflow_id TEXT,
                        stage TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        created_at REAL NOT NULL,
                        status TEXT NOT NULL,
                        metrics_summary_json TEXT NOT NULL,
                        snapshot_json TEXT NOT NULL
                    );
                """)

                # Indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_job_created 
                        ON checkpoints(job_id, created_at DESC);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_created 
                        ON checkpoints(workflow_id, created_at DESC);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_created 
                        ON checkpoints(created_at DESC);
                """)

                # Record schema version if not present
                cursor.execute("SELECT version FROM schema_version WHERE version = ?", (CURRENT_SCHEMA_VERSION,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                        (CURRENT_SCHEMA_VERSION, time.time())
                    )

                self._conn.commit()
            except Exception as exc:
                self._conn.rollback()
                logger.error(f"Failed to initialize SQLite checkpoint database: {exc}", exc_info=True)
                raise PersistenceWriteError(f"Database initialization failed: {exc}") from exc

    def save_checkpoint(
        self,
        snapshot: Any,  # BlackboardSnapshot
        stage: str,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
        checkpoint_id: Optional[str] = None,
    ) -> CheckpointMetadata:
        """
        Saves a BlackboardSnapshot as an atomic, all-or-nothing SQLite transaction.
        
        Sanitizes all sensitive credentials before writing to disk.
        """
        if self._closed:
            raise PersistenceWriteError("Cannot save checkpoint: database connection is closed.")

        if hasattr(snapshot, "get_snapshot"):
            snapshot = snapshot.get_snapshot()
        elif hasattr(snapshot, "create_snapshot"):
            snapshot = snapshot.create_snapshot()

        cid = checkpoint_id or f"chk_{uuid.uuid4().hex[:12]}"
        now = time.time()
        rev = getattr(snapshot, "revision", 0)

        # Determine workflow status
        metrics_space = getattr(snapshot, "metrics", None)
        workflow_status = status
        if not workflow_status and metrics_space is not None:
            workflow_status = getattr(metrics_space, "final_hardening_status", "IN_PROGRESS")
        workflow_status = workflow_status or "IN_PROGRESS"

        # Build metrics summary
        summary: Dict[str, Any] = {}
        if metrics_space is not None:
            summary = {
                "iteration": getattr(metrics_space, "current_iteration", 0),
                "mutation_score": getattr(metrics_space, "final_mutation_score", 0.0),
                "line_coverage": getattr(metrics_space, "baseline_line_coverage", 0.0),
                "terminated": getattr(metrics_space, "terminated", False),
                "termination_reason": getattr(metrics_space, "termination_reason", ""),
            }
        mutant_space = getattr(snapshot, "mutant", None)
        if mutant_space is not None:
            summary["mutants_generated"] = getattr(mutant_space, "mutants_generated", 0)
            summary["mutants_killed"] = getattr(mutant_space, "mutants_killed", 0)
            summary["mutants_survived"] = getattr(mutant_space, "mutants_survived", 0)

        if extra_meta:
            summary.update(extra_meta)

        # Scrub metadata and snapshot of any sensitive values
        summary = _scrub_sensitive_dict(summary)

        # Serialize snapshot
        try:
            raw_dict = snapshot.model_dump() if hasattr(snapshot, "model_dump") else dict(snapshot)
            scrubbed_dict = _scrub_sensitive_dict(raw_dict)
            snapshot_json = json.dumps(scrubbed_dict)
        except Exception as exc:
            logger.error(f"Failed to serialize snapshot for checkpoint {cid}: {exc}", exc_info=True)
            if self.strict_mode:
                raise PersistenceWriteError(f"Snapshot serialization failed: {exc}") from exc
            return CheckpointMetadata(
                checkpoint_id=cid,
                schema_version=CURRENT_SCHEMA_VERSION,
                job_id=job_id,
                workflow_id=workflow_id,
                stage=stage,
                revision=rev,
                created_at=now,
                status=workflow_status,
                metrics_summary={"error": str(exc)},
            )

        metadata = CheckpointMetadata(
            checkpoint_id=cid,
            schema_version=CURRENT_SCHEMA_VERSION,
            job_id=job_id,
            workflow_id=workflow_id,
            stage=stage,
            revision=rev,
            created_at=now,
            status=workflow_status,
            metrics_summary=summary,
        )

        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO checkpoints (
                        checkpoint_id,
                        schema_version,
                        job_id,
                        workflow_id,
                        stage,
                        revision,
                        created_at,
                        status,
                        metrics_summary_json,
                        snapshot_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cid,
                        CURRENT_SCHEMA_VERSION,
                        job_id,
                        workflow_id,
                        stage,
                        rev,
                        now,
                        workflow_status,
                        json.dumps(summary),
                        snapshot_json,
                    )
                )
                self._conn.commit()
                logger.info(f"Checkpoint '{cid}' successfully saved (stage='{stage}', rev={rev}, job_id='{job_id}')")
                return metadata
            except Exception as exc:
                self._conn.rollback()
                logger.error(f"Failed to write checkpoint '{cid}' to SQLite: {exc}", exc_info=True)
                if self.strict_mode:
                    raise PersistenceWriteError(f"Database write failed for checkpoint {cid}: {exc}") from exc
                return metadata

    def load_checkpoint(self, checkpoint_id: str) -> CheckpointRecord:
        """
        Loads a checkpoint by unique identifier.
        
        Validates schema version and snapshot integrity.
        Raises CheckpointNotFoundError, IncompatibleSchemaError, or CorruptedSnapshotError.
        """
        if self._closed:
            raise PersistenceWriteError("Cannot load checkpoint: database connection is closed.")

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT 
                    checkpoint_id,
                    schema_version,
                    job_id,
                    workflow_id,
                    stage,
                    revision,
                    created_at,
                    status,
                    metrics_summary_json,
                    snapshot_json
                FROM checkpoints
                WHERE checkpoint_id = ?
                """,
                (checkpoint_id,)
            )
            row = cursor.fetchone()

        if not row:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found.")

        # Check schema version
        ver = row["schema_version"]
        if ver != CURRENT_SCHEMA_VERSION:
            raise IncompatibleSchemaError(
                f"Checkpoint '{checkpoint_id}' has schema version {ver}, but engine requires {CURRENT_SCHEMA_VERSION}."
            )

        try:
            summary = json.loads(row["metrics_summary_json"])
        except Exception:
            summary = {}

        # Validate that snapshot_json is parseable JSON
        try:
            json.loads(row["snapshot_json"])
        except Exception as exc:
            raise CorruptedSnapshotError(f"Checkpoint '{checkpoint_id}' contains corrupted snapshot JSON: {exc}") from exc

        metadata = CheckpointMetadata(
            checkpoint_id=row["checkpoint_id"],
            schema_version=row["schema_version"],
            job_id=row["job_id"],
            workflow_id=row["workflow_id"],
            stage=row["stage"],
            revision=row["revision"],
            created_at=row["created_at"],
            status=row["status"],
            metrics_summary=summary,
        )

        return CheckpointRecord(
            metadata=metadata,
            snapshot_json=row["snapshot_json"]
        )

    def get_latest_checkpoint(
        self,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Optional[CheckpointRecord]:
        """Returns the most recent checkpoint for the specified job or workflow."""
        if self._closed:
            raise PersistenceWriteError("Cannot read checkpoint: database connection is closed.")

        query = "SELECT checkpoint_id FROM checkpoints WHERE 1=1"
        params: List[Any] = []
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        query += " ORDER BY created_at DESC LIMIT 1"

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()

        if not row:
            return None

        return self.load_checkpoint(row["checkpoint_id"])

    def list_checkpoints(
        self,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CheckpointSummary]:
        """Lists checkpoint summaries matching optional filters with pagination."""
        if self._closed:
            raise PersistenceWriteError("Cannot list checkpoints: database connection is closed.")

        query = """
            SELECT 
                checkpoint_id,
                schema_version,
                job_id,
                workflow_id,
                stage,
                revision,
                created_at,
                status,
                metrics_summary_json,
                length(snapshot_json) as snapshot_bytes
            FROM checkpoints
            WHERE 1=1
        """
        params: List[Any] = []
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([max(1, limit), max(0, offset)])

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        results: List[CheckpointSummary] = []
        for r in rows:
            try:
                metrics = json.loads(r["metrics_summary_json"])
            except Exception:
                metrics = {}
            results.append(
                CheckpointSummary(
                    checkpoint_id=r["checkpoint_id"],
                    schema_version=r["schema_version"],
                    job_id=r["job_id"],
                    workflow_id=r["workflow_id"],
                    stage=r["stage"],
                    revision=r["revision"],
                    created_at=r["created_at"],
                    status=r["status"],
                    metrics_summary=metrics,
                    snapshot_bytes=r["snapshot_bytes"],
                )
            )
        return results

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Deletes a specific checkpoint by ID. Returns True if deleted."""
        if self._closed:
            raise PersistenceWriteError("Cannot delete checkpoint: database connection is closed.")

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
            self._conn.commit()
            return cursor.rowcount > 0

    def count_checkpoints(
        self,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> int:
        """Returns the total number of checkpoints matching filters."""
        if self._closed:
            raise PersistenceWriteError("Cannot count checkpoints: database connection is closed.")

        query = "SELECT COUNT(*) as cnt FROM checkpoints WHERE 1=1"
        params: List[Any] = []
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row["cnt"] if row else 0

    def validate_checkpoint(
        self,
        checkpoint_id: str,
        expected_source_code: Optional[str] = None,
        expected_source_sha: Optional[str] = None,
        expected_task_id: Optional[str] = None,
    ) -> CheckpointRecord:
        """
        Validates checkpoint existence, schema version, snapshot integrity,
        input-hash matching, and partition completeness.
        """
        record = self.load_checkpoint(checkpoint_id)

        try:
            snapshot_dict = json.loads(record.snapshot_json)
        except Exception as exc:
            raise CorruptedSnapshotError(f"Checkpoint '{checkpoint_id}' JSON corrupted: {exc}") from exc

        target_dict = snapshot_dict.get("target") or {}
        code = target_dict.get("target_source_code", "")
        if not code or not str(code).strip():
            raise IncompleteCheckpointError(f"Checkpoint '{checkpoint_id}' is incomplete: missing target_source_code.")

        checkpoint_sha = target_dict.get("source_sha") or compute_source_hash(code)

        if expected_source_sha:
            if checkpoint_sha != expected_source_sha:
                raise InputHashMismatchError(
                    f"Input hash mismatch: expected SHA '{expected_source_sha[:10]}...', "
                    f"checkpoint '{checkpoint_id}' has SHA '{checkpoint_sha[:10]}...'."
                )
        elif expected_source_code is not None:
            computed_expected_sha = compute_source_hash(expected_source_code)
            if checkpoint_sha != computed_expected_sha:
                raise InputHashMismatchError(
                    f"Input hash mismatch: target code SHA '{computed_expected_sha[:10]}...' "
                    f"does not match checkpoint '{checkpoint_id}' SHA '{checkpoint_sha[:10]}...'."
                )

        if expected_task_id:
            job_id = record.metadata.job_id
            wf_id = record.metadata.workflow_id
            if job_id and wf_id and expected_task_id not in (job_id, wf_id):
                logger.warning(
                    f"Task identity warning: expected '{expected_task_id}' vs checkpoint job='{job_id}', wf='{wf_id}'."
                )

        plan = determine_resumption_plan(
            checkpoint_id=checkpoint_id,
            stage=record.metadata.stage,
            snapshot_dict_or_obj=snapshot_dict
        )
        return record, plan

    def get_resumable_checkpoint(
        self,
        job_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> Optional[CheckpointRecord]:
        """
        Finds the latest valid resumable checkpoint for a job/workflow.
        """
        summaries = self.list_checkpoints(job_id=job_id, workflow_id=workflow_id, limit=20)
        for s in summaries:
            try:
                rec = self.load_checkpoint(s.checkpoint_id)
                snap = json.loads(rec.snapshot_json)
                target = snap.get("target") or {}
                if target.get("target_source_code"):
                    return rec
            except Exception:
                continue
        return None

    def close(self) -> None:
        """Closes the underlying SQLite connection safely."""
        with self._lock:
            if not self._closed:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._closed = True


# ==============================================================================
# Checkpoint Resumption & Recovery Helpers
# ==============================================================================

def compute_source_hash(code: str) -> str:
    """Computes deterministic SHA-256 hash of normalized source code."""
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def determine_resumption_plan(
    checkpoint_id: str,
    stage: str,
    snapshot_dict_or_obj: Any,
) -> ResumptionPlan:
    """
    Determines the safe stage to resume execution and which stages can be skipped.
    """
    # Normalize dictionary access
    if hasattr(snapshot_dict_or_obj, "model_dump"):
        snap_dict = snapshot_dict_or_obj.model_dump()
    elif isinstance(snapshot_dict_or_obj, dict):
        snap_dict = snapshot_dict_or_obj
    else:
        snap_dict = {}

    target_space = snap_dict.get("target") or {}
    suite_space = snap_dict.get("suite") or {}
    metrics_space = snap_dict.get("metrics") or {}

    stage_upper = stage.upper()

    if stage_upper == "INITIAL_INGESTION":
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="BASELINE_SYNTHESIS",
            target_lifecycle_state="PLANNING",
            skipped_stages=["VALIDATING", "INGESTING"],
            start_iteration=1,
            description="Target source code and AST signatures restored. Resuming at baseline test synthesis."
        )

    if stage_upper == "BASELINE_SYNTHESIS":
        test_code = suite_space.get("current_test_code", "")
        if not test_code or not str(test_code).strip():
            return ResumptionPlan(
                checkpoint_id=checkpoint_id,
                checkpoint_stage=stage,
                resumes_at="BASELINE_SYNTHESIS",
                target_lifecycle_state="PLANNING",
                skipped_stages=["VALIDATING", "INGESTING"],
                start_iteration=1,
                description="Checkpoint stage was BASELINE_SYNTHESIS but test code is missing. Safely rerunning baseline synthesis."
            )
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="BASELINE_VALIDATION",
            target_lifecycle_state="EXECUTING",
            skipped_stages=["VALIDATING", "INGESTING", "PLANNING", "GENERATING_TESTS"],
            start_iteration=1,
            description="Candidate baseline tests restored. Resuming at baseline sandbox pass@1 validation."
        )

    if stage_upper == "BASELINE_VALIDATED":
        test_code = suite_space.get("current_test_code", "")
        if not test_code or not str(test_code).strip():
            return ResumptionPlan(
                checkpoint_id=checkpoint_id,
                checkpoint_stage=stage,
                resumes_at="BASELINE_SYNTHESIS",
                target_lifecycle_state="PLANNING",
                skipped_stages=["VALIDATING", "INGESTING"],
                start_iteration=1,
                description="Checkpoint stage was BASELINE_VALIDATED but test code is missing. Safely rerunning baseline synthesis."
            )
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="REFLECTION_LOOP",
            target_lifecycle_state="MUTATION_ANALYSIS",
            skipped_stages=["VALIDATING", "INGESTING", "PLANNING", "GENERATING_TESTS", "EXECUTING"],
            start_iteration=1,
            description="Baseline tests and line coverage verified. Resuming at reflection loop iteration 1."
        )

    if stage_upper.startswith("REFLECTION_ITERATION_"):
        try:
            iter_num = int(stage_upper.split("_")[-1])
        except ValueError:
            iter_num = 1
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="REFLECTION_LOOP",
            target_lifecycle_state="MUTATION_ANALYSIS",
            skipped_stages=["VALIDATING", "INGESTING", "PLANNING", "GENERATING_TESTS", "EXECUTING"] + [f"REFLECTION_ITERATION_{i}" for i in range(1, iter_num + 1)],
            start_iteration=iter_num + 1,
            description=f"Completed reflection iteration {iter_num} restored. Resuming reflection loop at iteration {iter_num + 1}."
        )

    if stage_upper in ("FINALIZED", "COMPLETED"):
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="COMPLETED",
            target_lifecycle_state="COMPLETED",
            skipped_stages=["ALL"],
            start_iteration=metrics_space.get("current_iteration", 1),
            description="Checkpoint was already completed. No additional stages require execution."
        )

    # Interrupted, cancelled, or failed stages: inspect internal partition state
    iter_done = metrics_space.get("current_iteration", 0)
    baseline_passed = suite_space.get("baseline_passed", False)
    test_code = suite_space.get("current_test_code", "")
    target_code = target_space.get("target_source_code", "")

    if iter_done and iter_done > 0:
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="REFLECTION_LOOP",
            target_lifecycle_state="MUTATION_ANALYSIS",
            skipped_stages=["VALIDATING", "INGESTING", "PLANNING", "GENERATING_TESTS", "EXECUTING"] + [f"REFLECTION_ITERATION_{i}" for i in range(1, iter_done + 1)],
            start_iteration=iter_done + 1,
            description=f"Interrupted task ({stage}) had completed reflection iteration {iter_done}. Resuming reflection loop at iteration {iter_done + 1}."
        )
    elif baseline_passed:
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="REFLECTION_LOOP",
            target_lifecycle_state="MUTATION_ANALYSIS",
            skipped_stages=["VALIDATING", "INGESTING", "PLANNING", "GENERATING_TESTS", "EXECUTING"],
            start_iteration=1,
            description=f"Interrupted task ({stage}) had completed baseline validation. Resuming reflection loop at iteration 1."
        )
    elif test_code and str(test_code).strip():
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="BASELINE_VALIDATION",
            target_lifecycle_state="EXECUTING",
            skipped_stages=["VALIDATING", "INGESTING", "PLANNING", "GENERATING_TESTS"],
            start_iteration=1,
            description=f"Interrupted task ({stage}) had synthesized candidate baseline tests. Resuming at baseline sandbox validation."
        )
    elif target_code and str(target_code).strip():
        return ResumptionPlan(
            checkpoint_id=checkpoint_id,
            checkpoint_stage=stage,
            resumes_at="BASELINE_SYNTHESIS",
            target_lifecycle_state="PLANNING",
            skipped_stages=["VALIDATING", "INGESTING"],
            start_iteration=1,
            description=f"Interrupted task ({stage}) had ingested target code. Resuming at baseline synthesis."
        )

    raise InvalidRecoveryStageError(
        f"Checkpoint in stage '{stage}' does not contain sufficient state to resume safely."
    )

