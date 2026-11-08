"""
orchestrator.py - Multi-Agent State Graph Orchestration & Reflection Loop.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Agent State Graph:
  1. Sandbox baseline validation (pass@1 check on clean code)
  2. TestGeneratorAgent: synthesizes initial candidate assertions via live Gemini API
  3. Sandbox candidate validation on clean target code
  4. AST Mutator: injects deterministic faults (comparison, arith, cond, return)
  5. Parallel Sandbox Runner: evaluates mutants across CPU cores concurrently
  6. Termination check: Mutation Score >= target_score or iteration >= max_iterations
  7. AdversarialCriticAgent: reasons why mutants survived and produces reflection directives
  8. Loop back to TestGeneratorAgent with surviving unified diffs and critic directives
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("testforge.orchestrator")

from rich.console import Console
from rich.table import Table

from testforge.a2a import WorkflowStage
from testforge.accel import hw_profile
from testforge.agents import AdversarialCriticAgent, TestGeneratorAgent
from testforge.blackboard import Blackboard
from testforge.callbacks import (
    CallbackRegistry,
    EventType,
    LifecycleEvent,
    TraceLoggerCallbackAdapter,
    default_callback_registry,
)
from testforge.equivalence import calculate_mutation_scores
from testforge.feature_flags import FeatureFlags
from testforge.guidance import derive_guidance_for_surviving_mutants
from testforge.logger import TraceLogger
from testforge.mcp_client import ToolSelectionDecision
from testforge.mutator import ASTMutator
from testforge.persistence import (
    CheckpointError,
    ResumptionPlan,
    SQLiteBlackboardStorage,
)
from testforge.prompt_guard import wrap_untrusted_content
from testforge.sandbox import ParallelSandboxRunner
from testforge.security import redact_sensitive_data
from testforge.state import (
    InvalidStateTransitionError,
    IterationMetrics,
    TaskLifecycleFSM,
    TaskLifecycleState,
    TestForgeState,
)

console = Console()


def format_standalone_test_suite(test_code: str, target_file_path: Optional[str] = None) -> str:
    """
    Transforms internal sandbox test code (`from target import *`, `import target`)
    into a production-ready, standalone executable Pytest file.
    Inserts a dynamic path hook and resolves the target module's import.
    """
    code = test_code.strip()
    if "```python" in code:
        parts = code.split("```python")
        code = parts[1].split("```")[0].strip()
    elif "```" in code:
        parts = code.split("```")
        code = parts[1].split("```")[0].strip()

    # Determine module name if target path provided
    module_import_name = "target"
    if target_file_path:
        norm = os.path.normpath(target_file_path)
        if os.path.isabs(norm):
            try:
                norm = os.path.relpath(norm, os.getcwd())
            except Exception:
                norm = os.path.basename(norm)
        if norm.endswith(".py"):
            norm = norm[:-3]
        module_import_name = norm.replace(os.sep, ".").replace("/", ".").lstrip(".")
        if "samples." in module_import_name:
            module_import_name = module_import_name[module_import_name.index("samples."):]

    # Replace `from target import ...` with module import
    if module_import_name != "target":
        code = re.sub(r"from\s+target\s+import\s+", f"from {module_import_name} import ", code)
        code = re.sub(r"import\s+target\s+", f"import {module_import_name} as target ", code)

    # Dynamic sys.path hook to ensure pytest runs from root or any directory
    path_hook = (
        "import os\n"
        "import sys\n"
        "sys.path.insert(0, os.path.abspath('.'))\n"
        "sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))\n"
    )

    if "sys.path.insert" not in code:
        code = path_hook + "\n" + code

    return code


import threading

from testforge.a2a import A2ABroker, A2AMessage, A2APerformative
from testforge.adk_generator import GoogleADKTestGenerator
from testforge.crew_critic import MutationQualityCriticAgent
from testforge.llm_client import HybridLLMClient


class HardeningCancelledError(Exception):
    """Raised when a hardening run is cancelled cooperatively by user request."""
    pass


class HardeningTimeoutError(Exception):
    """Raised when a hardening run exceeds its configured timeout duration."""
    pass


class TestForgeOrchestrator:
    """
    Coordinates the live multi-agent reflection loop across iterations until termination.
    Supports official Google ADK Test Generator and CrewAI Adversarial Critic via A2ABroker,
    with seamless failover, Blackboard state synchronization, and cooperative cancellation/timeout control.
    """
    __test__ = False
    def __init__(
        self,
        target_source_code: Optional[str] = None,
        initial_test_code: Optional[str] = None,
        max_iterations: int = 3,
        target_mutation_score: float = 85.0,
        model_name: str = "gemini-3.6-flash",
        trace_log_path: str = "testforge_trace.jsonl",
        api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        target_file_path: Optional[str] = None,
        engine_mode: str = "auto",
        target_lines: Optional[List[int]] = None,
        callbacks: Optional[CallbackRegistry] = None,
        blackboard: Optional[Blackboard] = None,
        mcp_client: Optional[Any] = None,
        broker: Optional[A2ABroker] = None,
        cancel_event: Optional[threading.Event] = None,
        timeout_seconds: Optional[int] = None,
        job_id: Optional[str] = None,
        checkpoint_db_path: Optional[str] = None,
        github_repo: Optional[str] = None,
        resume_checkpoint_id: Optional[str] = None,
        feature_flags: Optional[FeatureFlags] = None,
        privacy_mode: Optional[bool] = None,
    ):
        from testforge.privacy_mode import PrivacyModeManager
        privacy_mgr = PrivacyModeManager.get_instance()
        if privacy_mode is True:
            privacy_mgr.enable()
        elif privacy_mode is False:
            privacy_mgr.disable()

        self.privacy_mode = privacy_mgr.is_enabled()
        if self.privacy_mode:
            model_name = privacy_mgr.validate_model_selection(model_name)
            engine_mode = "local"

        self.target_file_path = target_file_path
        self.engine_mode = engine_mode
        self.target_lines = target_lines
        self.callbacks = callbacks or default_callback_registry
        self.feature_flags = feature_flags or FeatureFlags.from_env()
        self.mcp_client = mcp_client
        if self.mcp_client and getattr(self.mcp_client, "callbacks", None) is None:
            self.mcp_client.callbacks = self.callbacks
        self.cancel_event = cancel_event
        self.timeout_seconds = timeout_seconds
        self.job_id = job_id
        self.checkpoint_db_path = checkpoint_db_path or os.environ.get("TESTFORGE_CHECKPOINT_DB")
        self.github_repo = github_repo
        self.resume_checkpoint_id = resume_checkpoint_id
        self.resumption_plan: Optional[ResumptionPlan] = None
        self._start_time: Optional[float] = None
        self._explicit_max_iterations = max_iterations
        self._explicit_target_score = target_mutation_score
        self.is_cancelled: bool = False
        self.is_timed_out: bool = False
        self.state = TestForgeState(
            target_source_code=(target_source_code or "").strip(),
            current_test_code=(initial_test_code or "").strip(),
            max_iterations=max_iterations,
            target_mutation_score=target_mutation_score,
            hardware_info=hw_profile.summary()
        )
        self.blackboard = blackboard or Blackboard.from_testforge_state(
            self.state,
            callback_registry=self.callbacks,
            checkpoint_db_path=self.checkpoint_db_path,
        )
        self.blackboard.update_target_space(
            target_file_path=self.target_file_path,
            target_lines=self.target_lines or []
        )
        self.logger = TraceLogger(log_path=trace_log_path)
        self.sandbox = ParallelSandboxRunner(
            timeout_seconds=5,
            cancel_event=self.cancel_event,
            target_file_path=self.target_file_path
        )
        self.llm_client = HybridLLMClient(
            cloud_model=model_name,
            api_key=api_key,
            openrouter_api_key=openrouter_api_key,
            logger=self.logger,
            engine_mode=engine_mode
        )
        self.generator = TestGeneratorAgent(
            model_name=model_name,
            logger=self.logger,
            api_key=api_key,
            llm_client=self.llm_client
        )
        self.critic = AdversarialCriticAgent(
            model_name=model_name,
            logger=self.logger,
            api_key=api_key,
            llm_client=self.llm_client
        )
        # Agentic Frameworks Integration: Google ADK and CrewAI via A2A Broker
        self.broker = broker or A2ABroker(blackboard=self.blackboard, callback_registry=self.callbacks)
        self.adk_generator = GoogleADKTestGenerator(api_key=api_key)
        self.crew_critic = MutationQualityCriticAgent(api_key=api_key, verbose=False)
        from testforge.code_intelligence_agent import CodeIntelligenceAgent
        from testforge.security_agent import SecurityAgent
        self.code_intel_agent = CodeIntelligenceAgent(
            api_key=api_key,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            logger_instance=self.logger,
        )
        self.security_agent = SecurityAgent(
            api_key=api_key,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            logger_instance=self.logger,
        )
        from testforge.execution_agent import TestExecutionAgent
        from testforge.planning_agent import TestPlanningAgent
        self.planning_agent = TestPlanningAgent(
            api_key=api_key,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            logger_instance=self.logger,
        )
        self.execution_agent = TestExecutionAgent(
            sandbox_runner=self.sandbox,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            logger_instance=self.logger,
            timeout_seconds=self.timeout_seconds,
        )
        self.broker.register_handler(
            "agent:google-adk:generator",
            self.adk_generator.handle_a2a_message,
            description="Official Google ADK Test Generator Agent"
        )
        self.broker.register_handler(
            "agent:crewai:critic",
            self.crew_critic.handle_a2a_message,
            description="Official CrewAI Adversarial Critic Agent"
        )
        self.broker.register_handler(
            "agent:crewai:mutation-critic",
            self.crew_critic.handle_a2a_message,
            description="Official CrewAI Mutation & Quality Critic Agent"
        )
        self.broker.register_handler(
            "agent:crewai:cooperative-crew",
            self.crew_critic.handle_a2a_message,
            description="Official 3-Agent Cooperative Critic Crew"
        )
        self.broker.register_handler(
            "agent:google-adk:code-intelligence",
            self.code_intel_agent.handle_a2a_message,
            description="Official Google ADK Code Intelligence Agent"
        )
        self.broker.register_handler(
            "agent:google-adk:security",
            self.security_agent.handle_a2a_message,
            description="Official Google ADK Security Agent"
        )
        self.broker.register_handler(
            "agent:google-adk:test-planner",
            self.planning_agent.handle_a2a_message,
            description="Official Google ADK Test Planning Agent"
        )
        self.broker.register_handler(
            "agent:google-adk:test-execution",
            self.execution_agent.handle_a2a_message,
            description="Official Google ADK Test Execution Agent"
        )
        from testforge.reflection_agent import ReflectionRepairAgent
        self.reflection_agent = ReflectionRepairAgent(
            api_key=api_key,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            logger_instance=self.logger,
            generator=self.adk_generator,
            execution_agent=self.execution_agent,
            critic_agent=self.crew_critic,
            sandbox=self.sandbox,
            feature_flags=self.feature_flags,
        )
        self.broker.register_handler(
            "agent:google-adk:reflection-repair",
            self.reflection_agent.handle_a2a_message,
            description="Official Google ADK Reflection & Repair Agent"
        )
        from testforge.supervisor_agent import SupervisorAgent
        self.supervisor = SupervisorAgent(
            api_key=api_key,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            logger_instance=self.logger,
        )
        self.broker.register_handler(
            "agent:google-adk:supervisor",
            self.supervisor.handle_a2a_message,
            description="Official Google ADK Top-Level Supervisor Agent"
        )
        self.workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        task_id = self.job_id or self.workflow_id
        self.state.task_id = task_id
        if hasattr(self.logger, "set_context"):
            self.logger.set_context(workflow_id=self.workflow_id, correlation_id=self.workflow_id)
        self.fsm = TaskLifecycleFSM(
            task_id=task_id,
            initial_state=self.state.lifecycle_state,
            callbacks=self.callbacks,
            blackboard=self.blackboard,
        )
        self.lifecycle = self.fsm
        self.callbacks.register(
            TraceLoggerCallbackAdapter(self.logger),
            name="orchestrator_trace_adapter"
        )
        # Never-Regress Guard: tracks peak-performing suite across all iterations
        self._best_mutation_score: float = -1.0
        self._best_raw_mutation_score: float = -1.0
        self._best_adjusted_mutation_score: float = -1.0
        self._best_test_code: str = (initial_test_code or "").strip()
        self._best_iteration: int = 0
        self._best_mutants_killed: int = 0
        self._best_mutants_executed: int = 0
        self._best_mutants_survived: int = 0
        self._best_mutants_generated: int = 0
        self._best_mutants: List[Any] = []
        self._best_surviving_diffs: List[str] = []
        self._guard_restored: bool = False

    def _sync_lifecycle(
        self,
        target_state: TaskLifecycleState,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Transitions FSM and synchronizes state and blackboard partitions."""
        try:
            if self.fsm.current_state != target_state:
                if self.fsm.can_transition_to(target_state):
                    self.fsm.transition_to(target_state, reason=reason, metadata=metadata)
        except InvalidStateTransitionError as exc:
            self.logger.log_event("INVALID_LIFECYCLE_TRANSITION", {
                "from_state": exc.from_state.value if hasattr(exc.from_state, "value") else str(exc.from_state),
                "to_state": exc.to_state.value if hasattr(exc.to_state, "value") else str(exc.to_state),
                "error": str(exc),
            })
        self.state.lifecycle_state = self.fsm.current_state
        self.state.stage_durations = self.fsm.get_stage_durations()
        self.state.stage_history = self.fsm.get_history()
        if self.blackboard is not None:
            try:
                self.blackboard.update_metrics_space(
                    task_id=self.fsm.task_id,
                    lifecycle_state=self.fsm.current_state.value,
                    stage_durations=self.fsm.get_stage_durations(),
                )
            except Exception:
                pass


    def check_cancellation_or_timeout(self) -> None:
        """
        Cooperative cancellation and bounded timeout enforcement check.
        Raises HardeningCancelledError if cancel_event is set.
        Raises HardeningTimeoutError if execution duration exceeds timeout_seconds.
        """
        if self.cancel_event and self.cancel_event.is_set():
            self.is_cancelled = True
            raise HardeningCancelledError("Hardening job cancelled by user request.")
        if self.timeout_seconds is not None and self._start_time is not None:
            elapsed = time.perf_counter() - self._start_time
            if elapsed >= self.timeout_seconds:
                self.is_timed_out = True
                raise HardeningTimeoutError(
                    f"Hardening job exceeded timeout bound of {self.timeout_seconds}s (elapsed: {elapsed:.2f}s)."
                )

    def _apply_never_regress_guard(self) -> bool:
        """
        Enforces suite monotonicity by restoring the highest-scoring test suite
        and its metrics if any subsequent reflection iteration degraded the score.
        Returns True if a rollback to an earlier best suite occurred.
        """
        if self._best_iteration <= 0 or not self.state.history:
            return False

        last_metric = self.state.history[-1]
        last_score = last_metric.raw_mutation_score if last_metric.raw_mutation_score is not None else (last_metric.mutation_score or 0.0)

        if self._best_raw_mutation_score > last_score:
            console.print(
                f"  [yellow]• [Never-Regress Guard] Suite degraded in iteration {last_metric.iteration} "
                f"({last_score:.1f}% MS vs peak {self._best_raw_mutation_score:.1f}% MS from iteration {self._best_iteration}). "
                f"Restoring best-scoring suite from iteration {self._best_iteration}.[/yellow]"
            )
            self._guard_restored = True
            self.state.current_test_code = self._best_test_code
            self.state.final_mutation_score = self._best_raw_mutation_score
            self.state.mutants_killed = self._best_mutants_killed
            self.state.mutants_executed = self._best_mutants_executed
            self.state.mutants_survived = self._best_mutants_survived
            self.state.mutants_generated = self._best_mutants_generated
            self.state.mutants = list(self._best_mutants)
            self.state.surviving_mutant_diffs = list(self._best_surviving_diffs)

            self.blackboard.update_suite_space(
                current_test_code=self._best_test_code,
                hardened_test_code=self._best_test_code,
                candidate_test_code="",
            )
            self.blackboard.update_metrics_space(
                final_mutation_score=self._best_raw_mutation_score,
                raw_mutation_score=self._best_raw_mutation_score,
                adjusted_mutation_score=self._best_adjusted_mutation_score,
            )
            self.logger.log_event("NEVER_REGRESS_GUARD_TRIGGERED", {
                "restored_iteration": self._best_iteration,
                "best_score": self._best_raw_mutation_score,
                "best_adj_score": self._best_adjusted_mutation_score,
                "degraded_last_iteration": last_metric.iteration,
                "degraded_last_score": last_score,
                "killed_mutants": self._best_mutants_killed,
            })
            return True
        return False

    def _finalize_cancellation_or_timeout(self, status: str, reason: str) -> None:
        """
        Consolidates and preserves all partial metrics gathered prior to cancellation/timeout.
        """
        guard_rolled_back = self._apply_never_regress_guard()
        if not guard_rolled_back:
            self.state.mutants_generated = len(self.state.mutants)
            self.state.mutants_executed = sum(1 for m in self.state.mutants if m.status in ("KILLED", "SURVIVED", "TIMEOUT"))
            self.state.mutants_killed = sum(1 for m in self.state.mutants if m.status in ("KILLED", "TIMEOUT"))
            self.state.mutants_survived = sum(1 for m in self.state.mutants if m.status == "SURVIVED")
            self.state.mutation_execution_errors = sum(1 for m in self.state.mutants if m.status == "ERROR")
            self.state.final_mutation_score = self.state.history[-1].mutation_score if self.state.history else 0.0
        self.state.reflection_iterations_performed = len(self.state.history)

        if status == "CANCELLED":
            self._sync_lifecycle(TaskLifecycleState.CANCELLED, reason=reason)
        elif status == "TIMED_OUT":
            self._sync_lifecycle(TaskLifecycleState.TIMED_OUT, reason=reason)
        else:
            self._sync_lifecycle(TaskLifecycleState.FAILED, reason=reason)

        self.blackboard.update_metrics_space(
            terminated=True,
            termination_reason=reason,
            final_mutation_score=self.state.final_mutation_score,
            final_hardening_status=status,
            reflection_iterations_performed=self.state.reflection_iterations_performed,
        )
        self.blackboard.sync_to_state(self.state)
        self.blackboard.save_checkpoint(
            stage=status,
            job_id=self.job_id,
            workflow_id=self.workflow_id,
            status=status,
            extra_meta={
                "reason": reason,
                "iterations": len(self.state.history),
                "lifecycle_state": self.fsm.current_state.value,
                "stage_durations": self.fsm.get_stage_durations(),
            }
        )

        self.logger.log_event(
            f"PIPELINE_{status}",
            {
                "terminated": True,
                "reason": reason,
                "final_score": self.state.final_mutation_score,
                "hardening_status": status,
                "iterations_completed": len(self.state.history),
                "total_tokens_used": self.logger.get_total_tokens()
            },
            correlation_id=self.workflow_id,
            workflow_id=self.workflow_id
        )

        self.callbacks.dispatch(LifecycleEvent(
            event_type=EventType.WORKFLOW_OUTCOME,
            emitter="TestForgeOrchestrator",
            workflow_id=self.workflow_id,
            correlation_id=self.workflow_id,
            outcome=status,
            payload={
                "status": status,
                "reason": reason,
                "final_score": self.state.final_mutation_score,
                "iterations": len(self.state.history)
            }
        ))

    def resolve_mcp_tool_need(self) -> ToolSelectionDecision:
        """
        Deterministic, testable tool-selection policy.
        Identifies whether an MCP tool is required for the current task.
        """
        if not self.mcp_client:
            return ToolSelectionDecision(
                required=False,
                reason="No MCP client configured; running in standalone in-memory mode."
            )

        # 1. Missing target source code but target file path provided -> read_text_file
        if self.target_file_path and not (self.state.target_source_code and self.state.target_source_code.strip()):
            return ToolSelectionDecision(
                required=True,
                tool_name="read_text_file",
                arguments={"path": self.target_file_path},
                reason="Target source code not provided in-memory; filesystem ingestion required via MCP.",
                task_file=self.target_file_path
            )

        # 2. Target file path provided and source code present -> get_file_info (integrity & provenance)
        if self.target_file_path and self.target_file_path.strip():
            return ToolSelectionDecision(
                required=True,
                tool_name="get_file_info",
                arguments={"path": self.target_file_path},
                reason="Target file path provided; verifying file metadata and provenance via MCP.",
                task_file=self.target_file_path
            )

        # 3. GitHub repository specified
        if getattr(self, "github_repo", None):
            parts = self.github_repo.split("/", 1)
            if len(parts) == 2:
                return ToolSelectionDecision(
                    required=True,
                    tool_name="get_repository_info",
                    arguments={"owner": parts[0], "repo": parts[1]},
                    reason=f"GitHub repository metadata required for '{self.github_repo}'.",
                    task_file=self.github_repo
                )

        # 4. Pure in-memory code without file path -> No tool needed
        return ToolSelectionDecision(
            required=False,
            reason="Standalone in-memory task; no external filesystem or remote tool required."
        )

    def invoke_mcp_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0
    ) -> Optional[Any]:
        """
        Executes a registered MCP tool through the MCP client manager.
        Validates arguments and responses, records activity in lifecycle and
        observability systems, and synchronizes safe metadata to Blackboard and state.
        """
        if not self.mcp_client:
            return None

        arguments = arguments or {}
        start_time = time.perf_counter()

        # Log invocation intention in trace logger
        stage_name = self.lifecycle.current_state.value if self.lifecycle else "UNKNOWN"
        self.logger.log_event("MCP_TOOL_START", {
            "tool_name": tool_name,
            "arguments": redact_sensitive_data(arguments),
            "stage": stage_name
        }, correlation_id=self.workflow_id, workflow_id=self.workflow_id)

        res = self.mcp_client.call_tool_sync(tool_name, arguments, timeout=timeout)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Build safe summary
        summary = ""
        if res.success:
            if isinstance(res.data, str):
                summary = f"String({len(res.data)} chars)"
            elif isinstance(res.data, dict):
                summary = f"Dict({list(res.data.keys())})"
            elif isinstance(res.data, list):
                summary = f"List({len(res.data)} items)"
            else:
                summary = str(type(res.data).__name__)
        else:
            summary = str(res.error)[:150]

        # Log completion & telemetry
        self.logger.log_event("MCP_TOOL_COMPLETE", {
            "tool_name": tool_name,
            "success": res.success,
            "duration_ms": duration_ms,
            "error": res.error,
            "summary": summary,
            "stage": stage_name
        }, correlation_id=self.workflow_id, workflow_id=self.workflow_id)

        if res.success and self.blackboard:
            self.mcp_client.sync_to_blackboard(res, self.blackboard)
            self.blackboard.sync_to_state(self.state)

        # Track tool invocation telemetry on state metadata
        if not hasattr(self.state, "metadata") or self.state.metadata is None:
            self.state.metadata = {}
        invocations = self.state.metadata.setdefault("mcp_tool_invocations", [])
        invocations.append({
            "tool_name": tool_name,
            "success": res.success,
            "duration_ms": duration_ms,
            "error": res.error
        })

        return res

    def export_hardened_suite(self, output_path: str = "test_hardened.py") -> str:
        """
        Exports the final test suite formatted for standalone pytest execution.
        """
        formatted = format_standalone_test_suite(
            self.state.current_test_code,
            self.target_file_path
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        return formatted

    def validate_and_restore_checkpoint(self, checkpoint_id: str) -> ResumptionPlan:
        """
        Validates checkpoint schema, input hash, and snapshot integrity,
        then restores Blackboard partitions and sets up the resumption plan.
        """
        storage = getattr(self.blackboard, "_storage", None)
        if storage is None:
            db_path = self.checkpoint_db_path or os.environ.get("TESTFORGE_CHECKPOINT_DB")
            if not db_path:
                from server import DEFAULT_CHECKPOINT_DB_PATH
                db_path = DEFAULT_CHECKPOINT_DB_PATH
            storage = SQLiteBlackboardStorage(db_path)

        record, plan = storage.validate_checkpoint(
            checkpoint_id=checkpoint_id,
            expected_source_code=self.state.target_source_code if self.state.target_source_code else None,
            expected_task_id=self.job_id or self.workflow_id
        )

        snapshot_dict = json.loads(record.snapshot_json)
        from testforge.blackboard import BlackboardSnapshot
        snapshot = BlackboardSnapshot.model_validate(snapshot_dict)

        self.resumption_plan = plan

        # Restore Blackboard partitions
        self.blackboard.restore_from_snapshot(snapshot)
        self.blackboard.sync_to_state(self.state)

        # Apply explicit constructor parameter overrides if provided
        if getattr(self, "_explicit_max_iterations", None) is not None:
            self.state.max_iterations = self._explicit_max_iterations
            self.blackboard.update_metrics_space(max_iterations=self._explicit_max_iterations)
        if getattr(self, "_explicit_target_score", None) is not None:
            self.state.target_mutation_score = self._explicit_target_score
            self.blackboard.update_metrics_space(target_mutation_score=self._explicit_target_score)

        # Reconcile target source code & file path
        if not self.state.target_source_code and snapshot.target.target_source_code:
            self.state.target_source_code = snapshot.target.target_source_code
        if not self.target_file_path and snapshot.target.target_file_path:
            self.target_file_path = snapshot.target.target_file_path

        # If MCP client exists, ensure clean session reinitialization without dead process handles
        if self.mcp_client:
            try:
                if hasattr(self.mcp_client, "disconnect_sync"):
                    self.mcp_client.disconnect_sync()
            except Exception as e:
                logger.warning(f"Error resetting MCP client on recovery: {e}")

        self.callbacks.dispatch(LifecycleEvent(
            event_type=EventType.RECOVERY_DECISION,
            emitter="TestForgeOrchestrator",
            workflow_id=self.workflow_id,
            correlation_id=self.job_id or self.workflow_id,
            payload=plan.model_dump()
        ))
        self.logger.log_event(
            "RECOVERY_DECISION",
            plan.model_dump(),
            correlation_id=self.workflow_id,
            workflow_id=self.workflow_id
        )

        return plan

    def resume_from_checkpoint(self, checkpoint_id: str) -> TestForgeState:
        """
        Public method to resume an existing or new orchestrator from a checkpoint ID.
        """
        self.resume_checkpoint_id = checkpoint_id
        return self.run()

    def harden(self) -> TestForgeState:
        """Alias for run() - executes the autonomous test hardening pipeline."""
        return self.run()

    def run(self) -> TestForgeState:
        if self._start_time is None:
            self._start_time = time.perf_counter()
        try:
            if self.resume_checkpoint_id and not self.resumption_plan:
                self.check_cancellation_or_timeout()
                self._sync_lifecycle(
                    TaskLifecycleState.RECOVERING,
                    reason=f"Validating and restoring checkpoint {self.resume_checkpoint_id}"
                )
                plan = self.validate_and_restore_checkpoint(self.resume_checkpoint_id)
                self.check_cancellation_or_timeout()
                self._sync_lifecycle(
                    TaskLifecycleState.RECOVERED,
                    reason=f"Checkpoint {self.resume_checkpoint_id} verified. Resuming at {plan.resumes_at}"
                )

                if plan.resumes_at == "COMPLETED":
                    self._sync_lifecycle(TaskLifecycleState.COMPLETED, reason="Checkpoint already finalized.")
                    return self.state

            return self._execute_pipeline()
        except CheckpointError as exc:
            console.print(f"[bold red]❌ RECOVERY FAILED: {exc}[/bold red]\n")
            self.state.terminated = True
            self.state.termination_reason = f"Recovery failed: {exc}"
            self.state.final_hardening_status = "FAILED"
            self._sync_lifecycle(TaskLifecycleState.FAILED, reason=f"Recovery failed: {exc}")
            self.callbacks.dispatch(LifecycleEvent(
                event_type=EventType.CHECKPOINT_FAILED,
                emitter="TestForgeOrchestrator",
                workflow_id=self.workflow_id,
                correlation_id=self.job_id or self.workflow_id,
                outcome="FAILED",
                payload={"checkpoint_id": self.resume_checkpoint_id, "error": str(exc)}
            ))
            self.logger.log_event(
                "RECOVERY_FAILED",
                {"checkpoint_id": self.resume_checkpoint_id, "error": str(exc)},
                correlation_id=self.workflow_id,
                workflow_id=self.workflow_id
            )
            return self.state
        except HardeningCancelledError as exc:
            console.print(f"[bold red]🛑 HARDENING CANCELLED: {exc}[/bold red]\n")
            self.state.terminated = True
            self.state.termination_reason = str(exc)
            self.state.final_hardening_status = "CANCELLED"
            self._finalize_cancellation_or_timeout("CANCELLED", str(exc))
            return self.state
        except HardeningTimeoutError as exc:
            console.print(f"[bold red]⏱️ HARDENING TIMED OUT: {exc}[/bold red]\n")
            self.state.terminated = True
            self.state.termination_reason = str(exc)
            self.state.final_hardening_status = "TIMED_OUT"
            self._finalize_cancellation_or_timeout("TIMED_OUT", str(exc))
            return self.state
        except Exception as exc:
            console.print(f"[bold red]❌ HARDENING PIPELINE ERROR: {exc}[/bold red]\n")
            self.state.terminated = True
            self.state.termination_reason = str(exc)
            self.state.final_hardening_status = "FAILED"
            self._sync_lifecycle(TaskLifecycleState.FAILED, reason=str(exc))
            raise

    def _execute_pipeline(self) -> TestForgeState:
        self.check_cancellation_or_timeout()
        console.print("[bold cyan]==========================================================[/bold cyan]")
        console.print("[bold cyan]       TESTFORGE: AUTONOMOUS TEST HARDENING ENGINE        [/bold cyan]")
        console.print(f"[dim]Hardware: Apple Silicon M-Series | Cores: {hw_profile.cpu_count} | Workers: {hw_profile.recommended_workers}[/dim]")
        console.print(f"[bold green]Foundation Model: Google GenAI Live ({self.generator.model_name})[/bold green]")
        console.print("[bold cyan]==========================================================[/bold cyan]\n")

        # Step 0: Input Security Inspection & Prompt Injection Screening
        skip_ingestion = bool(self.resumption_plan and self.resumption_plan.resumes_at in (
            "BASELINE_SYNTHESIS", "BASELINE_VALIDATION", "REFLECTION_LOOP", "COMPLETED"
        ))

        if not skip_ingestion:
            self._sync_lifecycle(TaskLifecycleState.VALIDATING, metadata={"target_file": self.target_file_path})
            # Consult Top-Level Supervisor Agent for initial security screening approval
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.INITIALIZING,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "source_code": self.state.target_source_code,
                        "cancel_event": self.cancel_event,
                    }
                )
                self.supervisor.set_agent_executing("SecurityAgent", True)
            from testforge.security import SecurityGuardrail
            guardrail = SecurityGuardrail()
            # Authoritative evaluation via SecurityAgent (Google ADK)
            sec_res = self.security_agent.evaluate_source(
                source_code=self.state.target_source_code,
                stage="INPUT_INSPECTION",
                target_ref=self.target_file_path or "target_source_code",
                job_id=self.job_id,
                workflow_id=self.workflow_id,
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("SecurityAgent", success=sec_res.allowed, failure_reason=sec_res.remediation_notes if not sec_res.allowed else None)
            if not sec_res.allowed:
                refusal_reason = sec_res.remediation_notes or "Target code exceeded security risk threshold."
                if hasattr(self, "supervisor") and self.supervisor:
                    self.supervisor.decide_next_step(
                        WorkflowStage.SECURITY_SCREENING,
                        context={"job_id": self.job_id, "task_id": self.state.task_id}
                    )
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.SECURITY_REFUSAL,
                    emitter="SecurityAgent",
                    workflow_id=self.workflow_id,
                    correlation_id=self.workflow_id,
                    outcome="REFUSED",
                    error_code="INPUT_SECURITY_REFUSAL",
                    payload={
                        "policy": "INPUT_PROMPT_INSPECTION",
                        "risk_level": sec_res.risk_level,
                        "reason": refusal_reason,
                        "findings": sec_res.findings,
                    }
                ))
                self.state.terminated = True
                self.state.termination_reason = f"SecurityRefusal: {refusal_reason}"
                self.state.final_hardening_status = "FAILED"
                self._sync_lifecycle(TaskLifecycleState.FAILED, reason=f"SecurityRefusal: {refusal_reason}")
                console.print(f"[bold red]⛔ SECURITY REFUSAL: {refusal_reason}[/bold red]\n")
                return self.state
            if not hasattr(self.state, "metadata") or self.state.metadata is None:
                self.state.metadata = {}
            self.state.metadata["security_assessment"] = sec_res.model_dump()
        else:
            console.print("[bold cyan]⏩ Restored from checkpoint: Skipping Step 0 security inspection (already validated)[/bold cyan]")

        self.callbacks.dispatch(LifecycleEvent(
            event_type=EventType.OPERATION_START,
            emitter="TestForgeOrchestrator",
            workflow_id=self.workflow_id,
            correlation_id=self.workflow_id,
            payload={
                "operation_name": "harden_test_suite",
                "max_iterations": self.state.max_iterations,
                "target_score": self.state.target_mutation_score,
                "target_file": self.target_file_path,
                "resumed": bool(self.resumption_plan),
                "resumed_from": self.resume_checkpoint_id,
            }
        ))

        self.logger.log_event(
            "PIPELINE_START",
            {
                "max_iterations": self.state.max_iterations,
                "target_score": self.state.target_mutation_score,
                "hardware": self.state.hardware_info,
                "model_name": self.generator.model_name,
                "target_file": self.target_file_path,
                "resumed": bool(self.resumption_plan),
                "resumed_from": self.resume_checkpoint_id,
            },
            correlation_id=self.workflow_id,
            workflow_id=self.workflow_id
        )

        if not skip_ingestion:
            # Ingestion & Symbol Extraction
            self._sync_lifecycle(TaskLifecycleState.INGESTING, metadata={"target_file": self.target_file_path})

            # Deterministic MCP Tool Selection & Execution
            tool_decision = self.resolve_mcp_tool_need()
            mcp_res = None
            if tool_decision.required and tool_decision.tool_name:
                console.print(f"[cyan]🔧 Invoking MCP Tool: {tool_decision.tool_name} ({tool_decision.reason})[/cyan]")
                mcp_res = self.invoke_mcp_tool(tool_decision.tool_name, tool_decision.arguments)

                if mcp_res and mcp_res.success:
                    if tool_decision.tool_name == "read_text_file" and isinstance(mcp_res.data, str):
                        self.state.target_source_code = mcp_res.data
                        # Inspect untrusted filesystem content through security guardrail
                        sec_recheck = guardrail.inspect_input(self.state.target_source_code)
                        if not sec_recheck.allowed:
                            refusal_reason = sec_recheck.explanation or "MCP-ingested file exceeded security risk threshold."
                            self.callbacks.dispatch(LifecycleEvent(
                                event_type=EventType.SECURITY_REFUSAL,
                                emitter="TestForgeOrchestrator",
                                workflow_id=self.workflow_id,
                                correlation_id=self.workflow_id,
                                outcome="REFUSED",
                                error_code="INPUT_SECURITY_REFUSAL",
                                payload={
                                    "policy": "MCP_FILE_PROMPT_INSPECTION",
                                    "risk_level": sec_recheck.risk_level.value,
                                    "reason": refusal_reason,
                                    "findings": [f.model_dump() for f in sec_recheck.findings],
                                }
                            ))
                            self.state.terminated = True
                            self.state.termination_reason = f"SecurityRefusal: {refusal_reason}"
                            self.state.final_hardening_status = "FAILED"
                            self._sync_lifecycle(TaskLifecycleState.FAILED, reason=f"SecurityRefusal: {refusal_reason}")
                            console.print(f"[bold red]⛔ SECURITY REFUSAL: {refusal_reason}[/bold red]\n")
                            return self.state
                    elif tool_decision.tool_name == "get_file_info" and isinstance(mcp_res.data, dict):
                        self.state.metadata["target_file_metadata"] = mcp_res.data
                    elif tool_decision.tool_name == "get_repository_info" and isinstance(mcp_res.data, dict):
                        self.state.metadata["repository_info"] = mcp_res.data
                elif mcp_res and not mcp_res.success:
                    if tool_decision.tool_name == "read_text_file":
                        err_msg = f"Essential MCP file read failed: {mcp_res.error}"
                        console.print(f"[bold red]❌ {err_msg}[/bold red]\n")
                        self.state.terminated = True
                        self.state.termination_reason = err_msg
                        self.state.final_hardening_status = "FAILED"
                        self._sync_lifecycle(TaskLifecycleState.FAILED, reason=err_msg)
                        return self.state
                    else:
                        console.print(f"[yellow]⚠️ MCP tool '{tool_decision.tool_name}' failed: {mcp_res.error}. Continuing in fallback mode.[/yellow]")

            # Validate that we have target source code available before proceeding
            if not self.state.target_source_code or not self.state.target_source_code.strip():
                err_msg = "No target source code available after ingestion stage."
                console.print(f"[bold red]❌ {err_msg}[/bold red]\n")
                self.state.terminated = True
                self.state.termination_reason = err_msg
                self.state.final_hardening_status = "FAILED"
                self._sync_lifecycle(TaskLifecycleState.FAILED, reason=err_msg)
                return self.state

            # Deep AST intelligence via CodeIntelligenceAgent (Google ADK)
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.SECURITY_SCREENING,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "source_code": self.state.target_source_code,
                        "cancel_event": self.cancel_event,
                    }
                )
                self.supervisor.set_agent_executing("CodeIntelligenceAgent", True)
            intel_res = self.code_intel_agent.analyze_source(
                source_code=self.state.target_source_code,
                target_file_path=self.target_file_path,
                job_id=self.job_id,
                workflow_id=self.workflow_id,
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("CodeIntelligenceAgent", success=True)
            if not hasattr(self.state, "metadata") or self.state.metadata is None:
                self.state.metadata = {}
            self.state.metadata["code_intelligence"] = intel_res.model_dump()

            # Record handoff from SecurityAgent -> CodeIntelligenceAgent
            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": "SecurityAgent",
                "to_agent": "CodeIntelligenceAgent",
                "iteration": 0,
                "summary": "Verified security clearance; transferred source for AST intelligence and complexity analysis",
                "payload": {
                    "job_id": self.job_id,
                    "status": intel_res.analysis_status,
                    "functions_count": len(intel_res.functions),
                    "branches_count": len(intel_res.branches),
                }
            })

            # Formulate structured test plan via TestPlanningAgent (Google ADK)
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.CODE_INTELLIGENCE,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "code_intelligence": intel_res.model_dump(),
                        "cancel_event": self.cancel_event,
                    }
                )
                self.supervisor.set_agent_executing("TestPlanningAgent", True)
            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": "CodeIntelligenceAgent",
                "to_agent": "TestPlanningAgent",
                "iteration": 0,
                "summary": "Transferring AST intelligence for test scenario planning and prioritization",
                "payload": {
                    "job_id": self.job_id,
                    "status": intel_res.analysis_status,
                    "functions_count": len(intel_res.functions),
                    "branches_count": len(intel_res.branches),
                }
            })

            test_plan = self.planning_agent.plan_tests(
                code_intelligence=intel_res,
                job_id=self.job_id,
                workflow_id=self.workflow_id,
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("TestPlanningAgent", success=True)
            self.state.metadata["test_plan"] = test_plan.model_dump()

            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": "TestPlanningAgent",
                "to_agent": "TestGeneratorAgent",
                "iteration": 0,
                "summary": "Transferred prioritized test plan with nominal, boundary, and negative scenarios",
                "payload": {
                    "job_id": self.job_id,
                    "scenarios_count": len(test_plan.scenarios),
                    "boundary_targets": test_plan.boundary_targets,
                    "negative_cases": test_plan.negative_cases,
                }
            })

            # Inter-agent Handoff: TargetManagerAgent -> TestGeneratorAgent
            from testforge.agents import extract_function_signatures
            from testforge.blast_analyzer import BlastRadiusAnalyzer

            func_sigs = extract_function_signatures(self.state.target_source_code)
            func_list = [f["name"] for f in func_sigs]
            blast_data = BlastRadiusAnalyzer.analyze_impact(func_list[0] if func_list else "", self.state.target_source_code)
            blast_risk = blast_data.get("risk_category", "LOW")

            target_sp = self.blackboard.get_target_space() if self.blackboard else None
            source_sha = target_sp.source_sha if target_sp else ""
            line_count = target_sp.line_count if target_sp else 0

            self.blackboard.update_target_space(
                functions=func_list,
                blast_risk=blast_risk,
                target_source_code=self.state.target_source_code
            )
            self.blackboard.save_checkpoint(
                stage="INITIAL_INGESTION",
                job_id=self.job_id,
                workflow_id=self.workflow_id,
                status="INITIALIZED",
                extra_meta={
                    "functions": func_list,
                    "blast_risk": blast_risk,
                    "branches_count": len(intel_res.branches),
                    "source_sha": source_sha,
                    "line_count": line_count,
                    "mcp_tool_called": tool_decision.tool_name if (tool_decision and tool_decision.required) else None,
                }
            )

            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": "TargetManagerAgent",
                "to_agent": "TestGeneratorAgent",
                "iteration": 0,
                "summary": "Extracted AST symbols, call graph, and blast radius metadata",
                "payload": {
                    "functions": func_list,
                    "blast_risk": blast_risk,
                    "target_lines": self.target_lines or [],
                    "source_sha": source_sha,
                    "line_count": line_count,
                    "mcp_tool": tool_decision.tool_name if (tool_decision and tool_decision.required) else None,
                }
            })
        else:
            console.print("[bold cyan]⏩ Restored from checkpoint: Skipping Ingestion & AST Extraction[/bold cyan]")
            if self.fsm.current_state == TaskLifecycleState.RECOVERED:
                target_state_name = self.resumption_plan.target_lifecycle_state
                target_state_enum = getattr(TaskLifecycleState, target_state_name, None)
                if target_state_enum:
                    self._sync_lifecycle(target_state_enum, metadata={"resumed_from": self.resume_checkpoint_id})

        # Step 1: Synthesize initial candidate tests if none provided
        skip_baseline_synth = bool(self.resumption_plan and self.resumption_plan.resumes_at in (
            "BASELINE_VALIDATION", "REFLECTION_LOOP", "COMPLETED"
        ))

        self.check_cancellation_or_timeout()
        if not skip_baseline_synth and not self.state.current_test_code:
            self._sync_lifecycle(TaskLifecycleState.PLANNING, metadata={"action": "initial_candidate_plan"})
            self._sync_lifecycle(TaskLifecycleState.GENERATING_TESTS, metadata={"action": "initial_candidate_generation"})
            # Consult Top-Level Supervisor Agent for candidate test generation
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.TEST_PLANNING,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "test_plan": self.state.metadata.get("test_plan") if hasattr(self.state, "metadata") and self.state.metadata else None,
                        "cancel_event": self.cancel_event,
                    }
                )
                self.supervisor.set_agent_executing("TestGeneratorAgent", True)
            console.print("[yellow][Step 1/6] Synthesizing initial candidate test suite...[/yellow]")
            initial_tests = ""
            provider_used = self.generator.active_provider
            step1_corr_id = f"init_gen_{uuid.uuid4().hex[:8]}"
            t0_step1 = time.perf_counter()

            self.callbacks.dispatch(LifecycleEvent(
                event_type=EventType.AGENT_START,
                emitter="TestForgeOrchestrator",
                workflow_id=self.workflow_id,
                correlation_id=step1_corr_id,
                payload={"agent_name": "GoogleADKTestGenerator", "action": "generate_tests", "iteration": 0}
            ))

            test_plan_data = self.state.metadata.get("test_plan") if hasattr(self.state, "metadata") and self.state.metadata else None
            if self.engine_mode != "legacy":
                try:
                    req = A2AMessage(
                        correlation_id=step1_corr_id,
                        sender="agent:orchestrator",
                        recipient="agent:google-adk:generator",
                        performative=A2APerformative.REQUEST,
                        action="generate_tests",
                        payload={
                            "target_source_code": self.state.target_source_code,
                            "iteration": 0,
                            "test_plan": test_plan_data,
                        }
                    )
                    resp = self.broker.send_message(req)
                    if resp.performative == A2APerformative.INFORM and "test_code" in resp.payload:
                        initial_tests = resp.payload["test_code"]
                        provider_used = "Google ADK Generator"
                except Exception as exc:
                    console.print(f"[dim]ADK generator failover: {exc}[/dim]")

            if not initial_tests:
                initial_tests = self.generator.generate_tests(
                    source_code=self.state.target_source_code,
                    iteration=0,
                    test_plan=test_plan_data,
                )
                provider_used = self.generator.active_provider

            step1_duration = (time.perf_counter() - t0_step1) * 1000.0
            self.callbacks.dispatch(LifecycleEvent(
                event_type=EventType.AGENT_COMPLETE,
                emitter="TestForgeOrchestrator",
                workflow_id=self.workflow_id,
                correlation_id=step1_corr_id,
                outcome="SUCCESS" if initial_tests else "FAILED",
                duration_ms=round(step1_duration, 2),
                payload={
                    "agent_name": provider_used,
                    "status": "COMPLETED" if initial_tests else "EMPTY_SUITE",
                    "suite_length_chars": len(initial_tests)
                }
            ))

            self.state.current_test_code = initial_tests
            self.state.active_provider = provider_used
            self.blackboard.update_suite_space(
                current_test_code=self.state.current_test_code,
                active_provider=self.state.active_provider
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("TestGeneratorAgent", success=bool(self.state.current_test_code))
            self.blackboard.save_checkpoint(
                stage="BASELINE_SYNTHESIS",
                job_id=self.job_id,
                workflow_id=self.workflow_id,
                status="IN_PROGRESS"
            )

            # Inter-agent Handoff: TestGeneratorAgent -> SubprocessSandbox
            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": "TestGeneratorAgent",
                "to_agent": "SubprocessSandbox",
                "iteration": 0,
                "summary": "Generated candidate test suite for pass@1 clean validation",
                "payload": {
                    "test_code_preview": self.state.current_test_code[:400] + ("..." if len(self.state.current_test_code) > 400 else ""),
                    "provider_used": self.state.active_provider or self.generator.active_provider
                }
            })
        elif skip_baseline_synth:
            console.print("[bold cyan]⏩ Restored from checkpoint: Skipping Step 1 Candidate Baseline Synthesis[/bold cyan]")
            if self.fsm.current_state == TaskLifecycleState.RECOVERED:
                target_state_name = self.resumption_plan.target_lifecycle_state
                target_state_enum = getattr(TaskLifecycleState, target_state_name, None)
                if target_state_enum:
                    self._sync_lifecycle(target_state_enum, metadata={"resumed_from": self.resume_checkpoint_id})

        # Step 2: Validate baseline tests on clean target code (pass@1 check) & Step 3 Coverage
        skip_baseline_validation = bool(self.resumption_plan and self.resumption_plan.resumes_at in (
            "REFLECTION_LOOP", "COMPLETED"
        ))

        self.check_cancellation_or_timeout()
        if not skip_baseline_validation:
            self._sync_lifecycle(TaskLifecycleState.EXECUTING, metadata={"step": "baseline_validation"})
            # Consult Top-Level Supervisor Agent for sandbox execution approval
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.TEST_GENERATION,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "test_code": self.state.current_test_code,
                        "cancel_event": self.cancel_event,
                    }
                )
                self.supervisor.set_agent_executing("TestExecutionAgent", True)
            console.print("[yellow][Step 2/6] Sandbox validating test suite against clean target (pass@1 check)...[/yellow]")
            exec_res = self.execution_agent.execute_tests(
                test_code=self.state.current_test_code,
                target_code=self.state.target_source_code,
                target_file_path=self.target_file_path,
                measure_coverage=False,
                job_id=self.job_id,
                workflow_id=self.workflow_id,
                cancel_event=self.cancel_event,
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("TestExecutionAgent", success=True)
            baseline_exec = {
                "status": "PASS" if exec_res.status == "PASSED" else exec_res.status,
                "exit_code": exec_res.sandbox_metadata.get("exit_code", 0),
                "stdout": exec_res.stdout,
                "stderr": exec_res.stderr,
                "timed_out": exec_res.sandbox_metadata.get("timed_out", False),
                "has_exec_error": exec_res.sandbox_metadata.get("has_exec_error", False),
                "duration_ms": exec_res.duration_seconds * 1000.0,
                "tests_collected": exec_res.total_tests,
                "tests_passed": exec_res.passed_tests,
                "tests_failed": exec_res.failed_tests,
                "tests_errors": exec_res.error_tests,
            }

            if baseline_exec["status"] != "PASS" or baseline_exec.get("tests_passed", 0) == 0:
                self.check_cancellation_or_timeout()
                console.print(f"[red][!] Initial generated tests failed against clean code:[/red]\n{baseline_exec.get('stderr') or baseline_exec.get('stdout')}")
                self.logger.log_event("BASELINE_FAILURE", baseline_exec)
                # Re-attempt single self-repair
                self._sync_lifecycle(TaskLifecycleState.PLANNING, metadata={"step": "baseline_repair_planning"})
                console.print("[yellow][Self-Repair] Re-prompting TestGeneratorAgent to fix syntax/runtime error...[/yellow]")
                err_msg = baseline_exec.get("stderr") or baseline_exec.get("stdout") or "Tests did not pass cleanly."
                safe_err_msg = wrap_untrusted_content(err_msg, content_type="test_error", provenance="sandbox")
                repair_prompt = f"The following tests failed against clean code:\n{safe_err_msg}\nPlease produce corrected, working Pytest tests."
                self._sync_lifecycle(TaskLifecycleState.GENERATING_TESTS, metadata={"step": "baseline_repair_generation"})
                self.state.current_test_code = self.generator.generate_tests(
                    source_code=self.state.target_source_code,
                    critic_feedback=repair_prompt,
                    iteration=0
                )
                self.state.active_provider = self.generator.active_provider
                self.blackboard.update_suite_space(
                    current_test_code=self.state.current_test_code,
                    active_provider=self.state.active_provider
                )

                self.check_cancellation_or_timeout()
                self._sync_lifecycle(TaskLifecycleState.EXECUTING, metadata={"step": "baseline_repair_recheck"})
                recheck_res = self.execution_agent.execute_tests(
                    test_code=self.state.current_test_code,
                    target_code=self.state.target_source_code,
                    target_file_path=self.target_file_path,
                    measure_coverage=False,
                    job_id=self.job_id,
                    workflow_id=self.workflow_id,
                    cancel_event=self.cancel_event,
                )
                recheck = {
                    "status": "PASS" if recheck_res.status == "PASSED" else recheck_res.status,
                    "exit_code": recheck_res.sandbox_metadata.get("exit_code", 0),
                    "stdout": recheck_res.stdout,
                    "stderr": recheck_res.stderr,
                    "timed_out": recheck_res.sandbox_metadata.get("timed_out", False),
                    "has_exec_error": recheck_res.sandbox_metadata.get("has_exec_error", False),
                    "duration_ms": recheck_res.duration_seconds * 1000.0,
                    "tests_collected": recheck_res.total_tests,
                    "tests_passed": recheck_res.passed_tests,
                    "tests_failed": recheck_res.failed_tests,
                    "tests_errors": recheck_res.error_tests,
                }
                if recheck["status"] != "PASS" or recheck.get("tests_passed", 0) == 0:
                    self.check_cancellation_or_timeout()
                    console.print("[yellow][!] Self-repaired tests failed clean target check. Engaging deterministic AST synthesis...[/yellow]")
                    from testforge.agents import CodeSanitizer, extract_function_signatures
                    sigs = extract_function_signatures(self.state.target_source_code)
                    raw_ast_code = self.generator._synthesize_ast_aware_tests(
                        source_code=self.state.target_source_code,
                        signatures=sigs,
                        surviving_diffs=None
                    )
                    _, sanitized_ast, _ = CodeSanitizer.extract_and_validate(raw_ast_code)
                    self.state.current_test_code = sanitized_ast
                    self.state.active_provider = "AST Deterministic Synthesizer"
                    self.blackboard.update_suite_space(
                        current_test_code=self.state.current_test_code,
                        active_provider=self.state.active_provider
                    )
                    self.check_cancellation_or_timeout()
                    final_check_res = self.execution_agent.execute_tests(
                        test_code=self.state.current_test_code,
                        target_code=self.state.target_source_code,
                        target_file_path=self.target_file_path,
                        measure_coverage=False,
                        job_id=self.job_id,
                        workflow_id=self.workflow_id,
                        cancel_event=self.cancel_event,
                    )
                    final_check = {
                        "status": "PASS" if final_check_res.status == "PASSED" else final_check_res.status,
                        "exit_code": final_check_res.sandbox_metadata.get("exit_code", 0),
                        "stdout": final_check_res.stdout,
                        "stderr": final_check_res.stderr,
                        "timed_out": final_check_res.sandbox_metadata.get("timed_out", False),
                        "has_exec_error": final_check_res.sandbox_metadata.get("has_exec_error", False),
                        "duration_ms": final_check_res.duration_seconds * 1000.0,
                        "tests_collected": final_check_res.total_tests,
                        "tests_passed": final_check_res.passed_tests,
                        "tests_failed": final_check_res.failed_tests,
                        "tests_errors": final_check_res.error_tests,
                    }
                else:
                    final_check = recheck
            else:
                final_check = baseline_exec

            self.check_cancellation_or_timeout()

            # Record explicit baseline execution metrics
            tests_gen = len(re.findall(r"def\s+(test_\w+)\s*\(", self.state.current_test_code))
            tests_collected = final_check.get("tests_collected", 0)
            tests_passed = final_check.get("tests_passed", 0)
            tests_failed = final_check.get("tests_failed", 0)
            tests_errors = final_check.get("tests_errors", 0)
            has_exec_error = final_check.get("has_exec_error", False) or final_check.get("status") == "ERROR"
            raw_err = final_check.get("stderr") or final_check.get("stdout") or ""

            self.state.baseline_tests_generated = tests_gen
            self.state.baseline_tests_executed = tests_collected
            self.state.baseline_tests_passed = tests_passed
            self.state.baseline_tests_failed = tests_failed
            self.state.baseline_passed = (final_check["status"] == "PASS" and tests_passed > 0 and not has_exec_error)

            if not self.state.baseline_passed:
                self.state.terminated = True
                self.state.final_mutation_score = None

                # CASE 1: Tests generated, but NOT executed (collected == 0 or execution error)
                if (tests_gen > 0 and tests_collected == 0) or has_exec_error:
                    self.state.baseline_tests_executed = 0
                    self.state.baseline_tests_passed = 0
                    self.state.baseline_tests_failed = 0
                    self.state.execution_errors = tests_errors if tests_errors > 0 else 1
                    self.state.baseline_execution_error = raw_err.strip() or "Pytest failed to execute generated tests in sandbox."

                    clean_err = re.sub(r"\x1b\[[0-9;]*m", "", raw_err)
                    err_lines = [l.strip() for l in clean_err.splitlines() if l.strip()]
                    last_err = ""
                    for line in reversed(err_lines):
                        if any(k in line for k in ["Error:", "Exception:", "ModuleNotFoundError", "SyntaxError", "ImportError"]):
                            last_err = line
                            break
                    if not last_err and err_lines:
                        last_err = err_lines[-1]

                    self.state.final_hardening_status = "EXECUTION_ERROR"
                    self.state.termination_reason = f"Execution Error: Tests generated ({tests_gen}) could not be executed by Pytest: {last_err or 'Execution/Collection error'}"
                    console.print(f"[red][!] CRITICAL: {self.state.termination_reason}[/red]")
                    self._sync_lifecycle(TaskLifecycleState.FAILED, reason=self.state.termination_reason)

                # CASE 2: Tests executed, but failed assertions against clean code
                else:
                    self.state.final_hardening_status = "FAILED_BASELINE"
                    self.state.baseline_execution_error = raw_err.strip() or f"{tests_failed}/{tests_collected} tests failed against clean code."
                    self.state.termination_reason = f"Baseline validation failed: {tests_failed}/{tests_collected} tests failed against clean target code."
                    console.print(f"[red][!] CRITICAL: {self.state.termination_reason}[/red]")
                    self._sync_lifecycle(TaskLifecycleState.FAILED, reason=self.state.termination_reason)

                self.blackboard.update_suite_space(
                    baseline_tests_generated=self.state.baseline_tests_generated,
                    baseline_tests_executed=self.state.baseline_tests_executed,
                    baseline_tests_passed=self.state.baseline_tests_passed,
                    baseline_tests_failed=self.state.baseline_tests_failed,
                    baseline_passed=self.state.baseline_passed,
                    baseline_execution_error=self.state.baseline_execution_error,
                    baseline_tests_errors=self.state.execution_errors,
                )
                self.blackboard.update_metrics_space(
                    terminated=self.state.terminated,
                    termination_reason=self.state.termination_reason,
                    final_hardening_status=self.state.final_hardening_status,
                    execution_errors=self.state.execution_errors,
                    baseline_execution_error=self.state.baseline_execution_error,
                    current_mutation_score=None,
                    raw_mutation_score=None,
                    adjusted_mutation_score=None,
                )
                self.blackboard.sync_to_state(self.state)
                self.logger.log_event("PIPELINE_COMPLETE", {
                    "terminated": True,
                    "reason": self.state.termination_reason,
                    "final_score": None,
                    "hardening_status": self.state.final_hardening_status,
                    "execution_error": self.state.baseline_execution_error[:500] if hasattr(self.state, "baseline_execution_error") else None
                })
                return self.state

            self.blackboard.update_suite_space(
                baseline_tests_generated=self.state.baseline_tests_generated,
                baseline_tests_executed=self.state.baseline_tests_executed,
                baseline_tests_passed=self.state.baseline_tests_passed,
                baseline_tests_failed=self.state.baseline_tests_failed,
                baseline_passed=self.state.baseline_passed,
            )

            console.print(f"[green][✓] Candidate test suite passed on clean code ({self.state.baseline_tests_passed}/{self.state.baseline_tests_executed} tests passed).[/green]")

            # Step 3: Measure Baseline Line Coverage
            self.check_cancellation_or_timeout()
            cov_payload = self.execution_agent.execute_tests(
                test_code=self.state.current_test_code,
                target_code=self.state.target_source_code,
                target_file_path=self.target_file_path,
                measure_coverage=True,
                job_id=self.job_id,
                workflow_id=self.workflow_id,
                cancel_event=self.cancel_event,
            )
            cov_pct = cov_payload.line_coverage_pct
            branch_cov = getattr(cov_payload, "branch_coverage", 0.0)
            self.state.baseline_line_coverage = cov_pct
            self.state.lines_covered = cov_payload.lines_covered
            self.state.num_statements = cov_payload.num_statements
            self.state.baseline_branch_coverage = branch_cov
            self.state.total_branches = getattr(cov_payload, "total_branches", 0)
            self.state.covered_branches = getattr(cov_payload, "covered_branches", 0)
            self.state.missing_branches = getattr(cov_payload, "missing_branches", [])
            self.blackboard.record_coverage(
                line_coverage_pct=self.state.baseline_line_coverage,
                lines_covered=self.state.lines_covered,
                lines_total=self.state.num_statements,
                branch_coverage=self.state.baseline_branch_coverage,
                total_branches=self.state.total_branches,
                covered_branches=self.state.covered_branches,
                missing_branches=self.state.missing_branches,
            )
            console.print(
                f"[green][✓] Baseline Line Coverage: {cov_pct:.1f}% ({self.state.lines_covered}/{self.state.num_statements} lines covered) | "
                f"Branch Coverage: {branch_cov:.1f}% ({self.state.covered_branches}/{self.state.total_branches} branches covered)[/green]\n"
            )
            self.blackboard.save_checkpoint(
                stage="BASELINE_VALIDATED",
                job_id=self.job_id,
                workflow_id=self.workflow_id,
                status="IN_PROGRESS",
                extra_meta={
                    "coverage_pct": cov_pct,
                    "branch_coverage_pct": branch_cov,
                    "total_branches": self.state.total_branches,
                    "covered_branches": self.state.covered_branches,
                }
            )
        else:
            console.print("[bold cyan]⏩ Restored from checkpoint: Skipping Step 2 & 3 Sandbox Baseline Validation & Line Coverage[/bold cyan]")
            cov_pct = self.state.baseline_line_coverage or (self.blackboard.metrics.baseline_line_coverage if self.blackboard else 0.0) or 0.0
            if self.fsm.current_state == TaskLifecycleState.RECOVERED:
                self._sync_lifecycle(TaskLifecycleState.MUTATION_ANALYSIS, metadata={"resumed_from": self.resume_checkpoint_id})

        # Step 4: Iterative Reflection & Hardening Loop
        critic_directive: Optional[str] = None
        start_iteration = 1
        if self.resumption_plan and self.resumption_plan.start_iteration:
            start_iteration = self.resumption_plan.start_iteration

        for iteration in range(start_iteration, self.state.max_iterations + 1):
            self.check_cancellation_or_timeout()
            iter_start = time.perf_counter()
            self.state.current_iteration = iteration
            self.blackboard.update_metrics_space(current_iteration=iteration)
            console.print(f"[bold magenta]▶ Iteration {iteration} of {self.state.max_iterations} (Target Score: {self.state.target_mutation_score}%)[/bold magenta]")

            # A. If we have reflection feedback from previous iteration, regenerate/harden tests first
            if critic_directive and self.state.surviving_mutant_diffs:
                self._sync_lifecycle(TaskLifecycleState.PLANNING, metadata={"iteration": iteration, "step": "hardening_plan"})
                self._sync_lifecycle(TaskLifecycleState.GENERATING_TESTS, metadata={"iteration": iteration, "step": "hardening_generation"})
                if hasattr(self, "supervisor") and self.supervisor:
                    self.supervisor.set_agent_executing("ReflectionRepairAgent", True)
                console.print("  [cyan]• Hardening test assertions based on Critic reasoning...[/cyan]")
                hardened_tests = ""
                provider_used = self.generator.active_provider
                if self.engine_mode != "legacy":
                    try:
                        surviving_records = [
                            {"mutant_id": m.mutant_id, "mutation_type": m.mutation_type, "line_number": m.line_number}
                            for m in self.state.mutants if m.status == "SURVIVED"
                        ]
                        req = A2AMessage(
                            correlation_id=f"refl_{iteration}_{uuid.uuid4().hex[:8]}",
                            sender="agent:orchestrator",
                            recipient="agent:google-adk:reflection-repair",
                            performative=A2APerformative.REQUEST,
                            action="repair_tests",
                            payload={
                                "target_source_code": self.state.target_source_code,
                                "existing_test_code": self.state.current_test_code,
                                "surviving_diffs": self.state.surviving_mutant_diffs,
                                "surviving_mutants": surviving_records,
                                "iteration": iteration,
                                "max_iterations": self.state.max_iterations,
                                "target_mutation_score": self.state.target_mutation_score,
                                "task_id": self.state.task_id,
                            }
                        )
                        resp = self.broker.send_message(req)
                        if resp.performative == A2APerformative.INFORM and "retained_test_code" in resp.payload:
                            retained = resp.payload["retained_test_code"]
                            accepted = resp.payload.get("accepted", False)
                            if accepted and retained:
                                hardened_tests = retained
                                provider_used = "Google ADK Reflection & Repair"
                    except Exception as exc:
                        console.print(f"  [dim]ADK reflection repair failover: {exc}[/dim]")

                surviving_mutants_list = [m for m in self.state.mutants if m.status in ("SURVIVED", "POTENTIALLY_EQUIVALENT")]
                if not hardened_tests:
                    hardened_tests = self.generator.generate_tests(
                        source_code=self.state.target_source_code,
                        surviving_diffs=self.state.surviving_mutant_diffs,
                        critic_feedback=critic_directive,
                        iteration=iteration,
                        surviving_guidance=self.blackboard.get_critic_space().semantic_guidance
                    )
                    provider_used = self.generator.active_provider

                # Granular Candidate Test Validation: validate tests individually so one broken test doesn't discard all
                self._sync_lifecycle(TaskLifecycleState.EXECUTING, metadata={"iteration": iteration, "step": "granular_test_validation"})
                validation_res = self.sandbox.validate_and_filter_candidate_suite(
                    candidate_test_code=hardened_tests,
                    target_code=self.state.target_source_code,
                    existing_test_code=self.state.current_test_code,
                    surviving_mutants=surviving_mutants_list
                )

                if validation_res.retained_count > 0 and validation_res.retained_test_code:
                    self.state.current_test_code = validation_res.retained_test_code
                    self.state.active_provider = provider_used
                    self.blackboard.update_suite_space(
                        current_test_code=self.state.current_test_code,
                        hardened_test_code=self.state.current_test_code,
                        candidate_test_code="",
                        active_provider=self.state.active_provider
                    )
                    if validation_res.mutants_killed:
                        console.print(f"  [green]• Semantic Guidance: Candidate tests confirmed to kill {len(validation_res.mutants_killed)} surviving mutant(s).[/green]")
                    if validation_res.quarantined_count > 0:
                        console.print(f"  [green]• Granular Validation: Retained {validation_res.retained_count} valid test(s); quarantined {validation_res.quarantined_count} invalid/failing test(s).[/green]")
                    else:
                        console.print(f"  [green]• Hardened tests verified against clean code ({validation_res.retained_count} passed).[/green]")
                else:
                    console.print(f"  [yellow]• All candidate tests broke clean code or failed validation ({validation_res.quarantined_count} quarantined). Retaining previous working test suite.[/yellow]")
                    # Explicitly ensure the accepted working suite is preserved in Blackboard SuiteSpace
                    self.blackboard.update_suite_space(
                        current_test_code=self.state.current_test_code,
                        candidate_test_code="",
                    )

                # Inter-agent Handoff: TestGenerator -> SubprocessSandbox
                self.logger.log_event("AGENT_HANDOFF", {
                    "from_agent": "GoogleADKTestGenerator" if provider_used == "Google ADK Generator" else "TestGeneratorAgent",
                    "to_agent": "SubprocessSandbox",
                    "iteration": iteration,
                    "summary": f"Iteration {iteration}: Generated hardened test suite based on critic directives",
                    "payload": {
                        "test_code_preview": hardened_tests[:400] + ("..." if len(hardened_tests) > 400 else ""),
                        "provider_used": provider_used
                    }
                })

            # B. Invert AST to generate deterministic mutants
            self.check_cancellation_or_timeout()
            self._sync_lifecycle(TaskLifecycleState.MUTATION_ANALYSIS, metadata={"iteration": iteration, "step": "ast_mutation"})
            mutants = ASTMutator.mutate(self.state.target_source_code, target_lines=self.target_lines)
            self.state.mutants = mutants

            # CASE 3 / CASE 6: Baseline passes, but no mutants could be generated
            if not mutants:
                console.print("  [yellow]• No AST mutants could be generated from target code.[/yellow]")
                self.state.mutants_generated = 0
                self.state.mutants_executed = 0
                self.state.mutants_killed = 0
                self.state.mutants_survived = 0
                self.state.final_mutation_score = None
                self.state.terminated = True
                self.state.final_hardening_status = "MUTATION_GENERATION_FAILED"
                self.state.termination_reason = "Mutation Generation Failed: Target code yielded 0 AST mutants."
                self._sync_lifecycle(TaskLifecycleState.FAILED, reason=self.state.termination_reason)
                self.blackboard.update_mutant_space(
                    mutants=[],
                    mutants_generated=0,
                    mutants_executed=0,
                    mutants_killed=0,
                    mutants_survived=0,
                    current_mutation_score=None,
                    raw_mutation_score=None,
                    adjusted_mutation_score=None,
                )
                self.blackboard.update_metrics_space(
                    terminated=True,
                    termination_reason=self.state.termination_reason,
                    final_hardening_status=self.state.final_hardening_status,
                )
                self.blackboard.sync_to_state(self.state)
                self.logger.log_event("PIPELINE_COMPLETE", {
                    "terminated": True,
                    "reason": self.state.termination_reason,
                    "final_score": None,
                    "hardening_status": "MUTATION_GENERATION_FAILED"
                })
                return self.state

            if self.target_lines:
                console.print(f"  [cyan]• Git Diff-Aware Mutation injected {len(mutants)} targeted faults across lines {self.target_lines}.[/cyan]")
            else:
                console.print(f"  [cyan]• AST Mutator injected {len(mutants)} deterministic faults.[/cyan]")

            # C. Evaluate mutants across parallel sandbox workers via TestExecutionAgent
            self.check_cancellation_or_timeout()
            self._sync_lifecycle(TaskLifecycleState.EXECUTING, metadata={"iteration": iteration, "step": "mutant_evaluation"})
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.BASELINE_EXECUTION,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "baseline_passed": self.state.baseline_passed,
                        "tests_passed": self.state.baseline_tests_passed,
                        "iteration": iteration,
                        "cancel_event": self.cancel_event,
                    }
                )
                self.supervisor.set_agent_executing("TestExecutionAgent", True)
            console.print(f"  [cyan]• TestExecutionAgent evaluating mutants across {self.sandbox.max_workers} CPU workers...[/cyan]")
            evaluated_mutants = self.execution_agent.evaluate_mutants(
                test_code=self.state.current_test_code,
                mutants=mutants,
                baseline_passed=self.state.baseline_passed,
                cancel_event=self.cancel_event,
                job_id=self.job_id,
                workflow_id=self.workflow_id,
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("TestExecutionAgent", success=True)

            # D. Compute score & surviving diffs with Milestone 2 equivalence analysis
            self._sync_lifecycle(TaskLifecycleState.EVALUATING, metadata={"iteration": iteration, "step": "score_evaluation"})
            score_data = calculate_mutation_scores(evaluated_mutants)
            total = score_data["total_mutants"]
            killed = score_data["killed_mutants"]
            survived = score_data["survived_mutants"]
            timeouts = score_data["timed_out_mutants"]
            errors = score_data["execution_errors"]
            invalid = score_data["invalid_mutants"]
            if getattr(self.feature_flags, "equivalence", True):
                equivalent = score_data["equivalent_mutants"]
                potentially_equivalent = score_data["potentially_equivalent_mutants"]
                adj_score = score_data["adjusted_mutation_score"]
            else:
                equivalent = 0
                potentially_equivalent = 0
                adj_score = score_data["raw_mutation_score"]
            mutants_executed = score_data["evaluable_mutants"]
            raw_score = score_data["raw_mutation_score"]

            # CASE 4: Mutants generated, but not executed
            if mutants_executed == 0 and total > 0:
                console.print(f"  [red]• Mutants generated ({total}) but none could be executed in sandbox.[/red]")
                self.state.mutants_generated = total
                self.state.mutants_executed = 0
                self.state.mutants_killed = 0
                self.state.mutants_survived = total
                self.state.execution_errors = errors or 1
                self.state.final_mutation_score = None
                self.state.terminated = True
                self.state.final_hardening_status = "MUTATION_EXECUTION_FAILED"
                self.state.termination_reason = "Mutation Execution Failed: Mutants were generated but could not be evaluated in the sandbox."
                self._sync_lifecycle(TaskLifecycleState.FAILED, reason=self.state.termination_reason)
                self.blackboard.update_mutant_space(
                    mutants=evaluated_mutants,
                    mutants_generated=total,
                    mutants_executed=0,
                    mutants_killed=0,
                    mutants_survived=total,
                    current_mutation_score=None,
                    raw_mutation_score=None,
                    adjusted_mutation_score=None,
                )
                self.blackboard.update_metrics_space(
                    terminated=True,
                    termination_reason=self.state.termination_reason,
                    final_hardening_status=self.state.final_hardening_status,
                    execution_errors=self.state.execution_errors,
                )
                self.blackboard.sync_to_state(self.state)
                self.logger.log_event("PIPELINE_COMPLETE", {
                    "terminated": True,
                    "reason": self.state.termination_reason,
                    "final_score": None,
                    "hardening_status": "MUTATION_EXECUTION_FAILED"
                })
                return self.state

            score = raw_score
            self.state.final_mutation_score = raw_score

            # Exclude verified equivalent mutants from surviving diffs presented to the Critic
            surviving_diffs = [
                f"Mutant [{m.mutant_id}] at Line {m.line_number} ({m.mutation_type}):\n{m.unified_diff}"
                for m in evaluated_mutants if m.status in ("SURVIVED", "POTENTIALLY_EQUIVALENT")
            ]
            self.state.surviving_mutant_diffs = surviving_diffs

            self.blackboard.update_mutant_space(
                mutants=evaluated_mutants,
                mutants_generated=total,
                mutants_executed=mutants_executed,
                mutants_killed=killed,
                mutants_survived=survived,
                mutants_timed_out=timeouts,
                mutants_invalid=invalid,
                mutants_equivalent=equivalent,
                mutants_potentially_equivalent=potentially_equivalent,
                mutation_execution_errors=errors,
                current_mutation_score=raw_score,
                raw_mutation_score=raw_score,
                adjusted_mutation_score=adj_score,
                surviving_mutant_diffs=surviving_diffs,
            )

            iter_duration = time.perf_counter() - iter_start
            metric = IterationMetrics(
                iteration=iteration,
                total_mutants=total,
                killed_mutants=killed,
                survived_mutants=survived,
                timed_out_mutants=timeouts,
                execution_errors=errors,
                invalid_mutants=invalid,
                equivalent_mutants=equivalent,
                potentially_equivalent_mutants=potentially_equivalent,
                mutation_score=raw_score,
                raw_mutation_score=raw_score,
                adjusted_mutation_score=adj_score,
                line_coverage_pct=round(cov_pct, 2),
                duration_seconds=round(iter_duration, 2),
                baseline_tests_generated=self.state.baseline_tests_generated,
                baseline_tests_executed=self.state.baseline_tests_executed,
                baseline_passed=self.state.baseline_tests_passed,
                baseline_failed=self.state.baseline_tests_failed,
                lines_covered=self.state.lines_covered,
                num_statements=self.state.num_statements,
                mutants_generated=total,
                mutants_executed=mutants_executed,
                hardening_status="IN_PROGRESS"
            )
            self.state.history.append(metric)

            # Never-Regress Guard: Track the best-performing suite across all iterations
            is_first_eval = (self._best_iteration == 0)
            is_better_score = (raw_score > self._best_raw_mutation_score)
            is_tied_with_more_kills = (
                abs(raw_score - self._best_raw_mutation_score) < 1e-9
                and killed > self._best_mutants_killed
            )
            if is_first_eval or is_better_score or is_tied_with_more_kills:
                self._best_raw_mutation_score = raw_score
                self._best_adjusted_mutation_score = adj_score
                self._best_mutation_score = raw_score
                self._best_test_code = self.state.current_test_code
                self._best_iteration = iteration
                self._best_mutants_killed = killed
                self._best_mutants_executed = mutants_executed
                self._best_mutants_survived = survived
                self._best_mutants_generated = total
                self._best_mutants = list(evaluated_mutants)
                self._best_surviving_diffs = list(surviving_diffs)
            self.blackboard.update_metrics_space(
                history=self.state.history,
                raw_mutation_score=raw_score,
                adjusted_mutation_score=adj_score,
                equivalent_mutants=equivalent,
                potentially_equivalent_mutants=potentially_equivalent,
            )
            self.logger.log_event("ITERATION_EVALUATION", metric.model_dump())
            self.blackboard.save_checkpoint(
                stage=f"REFLECTION_ITERATION_{iteration}",
                job_id=self.job_id,
                workflow_id=self.workflow_id,
                status=self.state.final_hardening_status,
                extra_meta={
                    "iteration": iteration,
                    "raw_mutation_score": raw_score,
                    "adjusted_mutation_score": adj_score,
                    "killed": killed,
                    "survived": survived,
                    "equivalent": equivalent
                }
            )

            # Display table
            table = Table(title=f"Iteration {iteration} Benchmark (M2 AST & Equivalence)", show_header=True)
            table.add_column("Total Mutants", justify="center")
            table.add_column("Killed", justify="center", style="green")
            table.add_column("Survived", justify="center", style="red")
            table.add_column("Timeouts", justify="center", style="yellow")
            table.add_column("Equiv", justify="center", style="cyan")
            table.add_column("Raw Score", justify="center", style="bold")
            table.add_column("Adj Score", justify="center", style="bold green")
            table.add_column("Elapsed", justify="center")
            table.add_row(
                str(total),
                str(killed),
                str(survived),
                str(timeouts),
                str(equivalent),
                f"{raw_score:.1f}%",
                f"{adj_score:.1f}%",
                f"{iter_duration:.2f}s"
            )
            console.print(table)

            # E. Check Termination
            effective_score = max(raw_score, adj_score)
            surviving_mutant_objs = [m for m in evaluated_mutants if m.status in ("SURVIVED", "POTENTIALLY_EQUIVALENT")]
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.decide_next_step(
                    WorkflowStage.CRITIC_ASSESSMENT,
                    context={
                        "job_id": self.job_id,
                        "task_id": self.state.task_id,
                        "mutation_score": raw_score,
                        "adjusted_mutation_score": adj_score,
                        "target_mutation_score": self.state.target_mutation_score,
                        "coverage_pct": cov_pct,
                        "surviving_mutants_count": len(surviving_mutant_objs),
                        "iteration": iteration,
                        "max_iterations": self.state.max_iterations,
                        "cancel_event": self.cancel_event,
                    }
                )
            if effective_score >= self.state.target_mutation_score and cov_pct > 0.0:
                self.state.terminated = True
                self.state.termination_reason = (
                    f"Target mutation score achieved (Raw: {raw_score:.1f}%, "
                    f"Adjusted: {adj_score:.1f}% >= {self.state.target_mutation_score}% "
                    f"with {cov_pct:.1f}% line coverage, {equivalent} verified equivalent mutants excluded)."
                )
                self.state.final_hardening_status = "SUCCESS"
                self.blackboard.update_metrics_space(
                    terminated=self.state.terminated,
                    termination_reason=self.state.termination_reason,
                    final_hardening_status=self.state.final_hardening_status,
                )
                self.blackboard.sync_to_state(self.state)
                console.print(f"[bold green]✔ SUCCESS: {self.state.termination_reason}[/bold green]\n")
                break

            if not getattr(self.feature_flags, "reflection", True):
                self.state.terminated = True
                self.state.termination_reason = "Iterative reflection loop disabled via feature_flags.reflection=False."
                self.state.final_hardening_status = "SUCCESS" if effective_score >= self.state.target_mutation_score else "COMPLETED_WITHOUT_REFLECTION"
                self.blackboard.update_metrics_space(
                    terminated=self.state.terminated,
                    termination_reason=self.state.termination_reason,
                    final_hardening_status=self.state.final_hardening_status,
                )
                self.blackboard.sync_to_state(self.state)
                console.print("[yellow]⏩ Feature flag 'reflection=False': exiting after initial evaluation pass.[/yellow]\n")
                break

            if iteration == self.state.max_iterations:
                self.state.terminated = True
                self.state.termination_reason = "Maximum allowed reflection iterations reached."
                if cov_pct == 0.0:
                    self.state.final_hardening_status = "ZERO_COVERAGE_WARNING"
                elif score < self.state.target_mutation_score:
                    self.state.final_hardening_status = "TARGET_SCORE_UNREACHED"
                else:
                    self.state.final_hardening_status = "SUCCESS"
                self.blackboard.update_metrics_space(
                    terminated=self.state.terminated,
                    termination_reason=self.state.termination_reason,
                    final_hardening_status=self.state.final_hardening_status,
                )
                self.blackboard.sync_to_state(self.state)
                console.print(f"[yellow]⚠ TERMINATED: {self.state.termination_reason}[/yellow]\n")
                break

            # Inter-agent Handoff: SubprocessSandbox -> AdversarialCriticAgent
            survived_ids = [m.mutant_id for m in evaluated_mutants if m.status == "SURVIVED"]
            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": "SubprocessSandbox",
                "to_agent": "AdversarialCriticAgent",
                "iteration": iteration,
                "summary": f"Parallel sandbox evaluated {total} mutants ({killed} killed, {survived} survived). Dispatched surviving AST diffs.",
                "payload": {
                    "total_mutants": total,
                    "killed_mutants": killed,
                    "survived_mutants": survived,
                    "mutation_score": round(score, 2),
                    "surviving_mutant_ids": survived_ids
                }
            })

            # F. Adversarial Critic analyzes surviving mutants
            self.check_cancellation_or_timeout()
            self._sync_lifecycle(TaskLifecycleState.PLANNING, metadata={"iteration": iteration, "step": "critic_analysis"})
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_executing("MutationQualityCriticAgent", True)
            console.print(f"  [magenta]• Adversarial Critic analyzing {survived} surviving mutant(s)...[/magenta]")
            critic_directive = ""
            critic_agent_name = "AdversarialCriticAgent"
            if not getattr(self.feature_flags, "critic", True):
                console.print("  [yellow]• Critic disabled via feature_flags.critic=False: using direct patch directive.[/yellow]")
                critic_directive = "Direct test patch generation: assert exact boundary outputs to kill surviving mutants."
                critic_agent_name = "BypassedCritic"
            elif self.engine_mode != "legacy":
                try:
                    surviving_records = [
                        {"mutant_id": m.mutant_id, "mutation_type": m.mutation_type, "line_number": m.line_number}
                        for m in evaluated_mutants if m.status == "SURVIVED"
                    ]
                    mutant_dicts = [
                        m.dict() if hasattr(m, "dict") else (m.model_dump() if hasattr(m, "model_dump") else m.__dict__)
                        for m in evaluated_mutants
                    ]
                    req = A2AMessage(
                        correlation_id=f"critique_{iteration}_{uuid.uuid4().hex[:8]}",
                        sender="agent:orchestrator",
                        recipient="agent:crewai:mutation-critic",
                        performative=A2APerformative.REQUEST,
                        action="evaluate_quality",
                        payload={
                            "target_source_code": self.state.target_source_code,
                            "current_test_code": self.state.current_test_code,
                            "surviving_diffs": surviving_diffs,
                            "surviving_mutants": surviving_records,
                            "mutants": mutant_dicts,
                            "iteration": iteration,
                            "target_mutation_score": self.state.target_mutation_score,
                            "job_id": self.state.task_id or f"job_{uuid.uuid4().hex[:6]}",
                        }
                    )
                    resp = self.broker.send_message(req)
                    if resp.performative == A2APerformative.INFORM:
                        directive_data = resp.payload.get("directive") or resp.payload
                        analysis = directive_data.get("overall_quality_assessment") or directive_data.get("analysis", "")
                        directives_list = directive_data.get("directives", [])
                        critic_directive = analysis
                        if directives_list:
                            critic_directive += "\nDirectives:\n" + "\n".join(f"- {d}" for d in directives_list)
                        critic_agent_name = "MutationQualityCriticAgent"
                except Exception as exc:
                    console.print(f"  [dim]CrewAI critic failover: {exc}[/dim]")

            surviving_mutant_objs = [m for m in evaluated_mutants if m.status in ("SURVIVED", "POTENTIALLY_EQUIVALENT")]
            guidances = derive_guidance_for_surviving_mutants(surviving_mutant_objs, target_code=self.state.target_source_code)
            guidance_dicts = [g.dict() for g in guidances]
            self.state.surviving_guidance = guidance_dicts

            if not critic_directive:
                critic_directive = self.critic.analyze_surviving_mutants(
                    target_code=self.state.target_source_code,
                    surviving_mutant_diffs=surviving_diffs,
                    iteration=iteration,
                    surviving_mutants=surviving_mutant_objs
                )

            console.print(f"  [dim]Critic Directive: {critic_directive[:140]}...[/dim]\n")

            survived_list = [m.mutant_id for m in evaluated_mutants if m.status == "SURVIVED"]
            mechanisms = {g.mutant_id: g.behavioral_distinction for g in guidances}
            self.blackboard.update_critic_space(
                latest_directive=critic_directive,
                critic_directives=self.blackboard.get_critic_space().critic_directives + [critic_directive],
                reflection_notes=self.blackboard.get_critic_space().reflection_notes + [f"Iteration {iteration}: {len(survived_list)} surviving mutants"],
                failure_mechanisms=mechanisms,
                semantic_guidance=guidance_dicts
            )
            if hasattr(self, "supervisor") and self.supervisor:
                self.supervisor.set_agent_completed("MutationQualityCriticAgent", success=True)

            self.logger.log_event("AGENT_HANDOFF", {
                "from_agent": critic_agent_name,
                "to_agent": "GoogleADKTestGenerator" if self.engine_mode != "legacy" else "TestGeneratorAgent",
                "iteration": iteration,
                "summary": f"Diagnosed {len(survived_list)} surviving mutants. Issued adversarial directives.",
                "payload": {
                    "surviving_mutants": survived_list,
                    "critique_directives": critic_directive
                }
            })

        # Final state metrics aggregation with Never-Regress Guard
        guard_rolled_back = self._apply_never_regress_guard()
        if not guard_rolled_back:
            self.state.mutants_generated = len(self.state.mutants)
            self.state.mutants_executed = sum(1 for m in self.state.mutants if m.status in ("KILLED", "SURVIVED", "TIMEOUT"))
            self.state.mutants_killed = sum(1 for m in self.state.mutants if m.status in ("KILLED", "TIMEOUT"))
            self.state.mutants_survived = sum(1 for m in self.state.mutants if m.status == "SURVIVED")
            self.state.mutation_execution_errors = sum(1 for m in self.state.mutants if m.status == "ERROR")
            self.state.final_mutation_score = self.state.history[-1].mutation_score if self.state.history else 0.0
        self.state.reflection_iterations_performed = len(self.state.history)

        if guard_rolled_back and self.state.final_mutation_score >= self.state.target_mutation_score:
            self.state.final_hardening_status = "TARGET_REACHED"
            self.state.termination_reason = (
                f"Target Mutation Score achieved ({self.state.final_mutation_score:.1f}% >= "
                f"{self.state.target_mutation_score}% via restored optimal suite from iteration {self._best_iteration})."
            )

        raw_final = self.state.final_mutation_score or 0.0
        adj_final = getattr(self.state, "adjusted_mutation_score", None) or raw_final
        equiv_final = self.state.history[-1].equivalent_mutants if self.state.history else 0
        pot_equiv_final = self.state.history[-1].potentially_equivalent_mutants if self.state.history else 0

        self._sync_lifecycle(TaskLifecycleState.COMPLETED, reason=self.state.termination_reason)
        self.blackboard.update_metrics_space(
            terminated=self.state.terminated,
            termination_reason=self.state.termination_reason,
            final_mutation_score=self.state.final_mutation_score,
            raw_mutation_score=raw_final,
            adjusted_mutation_score=adj_final,
            equivalent_mutants=equiv_final,
            potentially_equivalent_mutants=pot_equiv_final,
            final_hardening_status=self.state.final_hardening_status,
            reflection_iterations_performed=self.state.reflection_iterations_performed,
        )
        self.blackboard.sync_to_state(self.state)
        self.blackboard.save_checkpoint(
            stage="FINALIZED",
            job_id=self.job_id,
            workflow_id=self.workflow_id,
            status=self.state.final_hardening_status,
            extra_meta={"final_mutation_score": self.state.final_mutation_score}
        )

        self.logger.log_event(
            "PIPELINE_COMPLETE",
            {
                "terminated": self.state.terminated,
                "reason": self.state.termination_reason,
                "final_score": self.state.final_mutation_score,
                "hardening_status": self.state.final_hardening_status,
                "total_tokens_used": self.logger.get_total_tokens()
            },
            correlation_id=self.workflow_id,
            workflow_id=self.workflow_id
        )

        self.callbacks.dispatch(LifecycleEvent(
            event_type=EventType.WORKFLOW_OUTCOME,
            emitter="TestForgeOrchestrator",
            workflow_id=self.workflow_id,
            correlation_id=self.workflow_id,
            outcome="SUCCESS" if self.state.final_mutation_score >= self.state.target_mutation_score else "PARTIAL",
            payload={
                "workflow_id": self.workflow_id,
                "final_mutation_score": self.state.final_mutation_score,
                "hardening_status": self.state.final_hardening_status,
                "iterations": self.state.reflection_iterations_performed,
                "terminated": self.state.terminated,
                "termination_reason": self.state.termination_reason,
                "total_tokens": self.logger.get_total_tokens()
            }
        ))

        self.callbacks.dispatch(LifecycleEvent(
            event_type=EventType.OPERATION_COMPLETE,
            emitter="TestForgeOrchestrator",
            workflow_id=self.workflow_id,
            correlation_id=self.workflow_id,
            outcome="SUCCESS" if self.state.final_mutation_score >= self.state.target_mutation_score else "PARTIAL",
            payload={
                "operation_name": "harden_test_suite",
                "final_score": self.state.final_mutation_score,
                "hardening_status": self.state.final_hardening_status,
                "terminated": self.state.terminated,
                "reason": self.state.termination_reason
            }
        ))

        return self.state
