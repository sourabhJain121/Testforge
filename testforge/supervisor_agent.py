"""
supervisor_agent.py - Dedicated Google ADK Top-Level Supervisor Agent for TestForge.

System: Autonomous Multi-Agent Hardening Engine
Role: 8-Agent Architecture Component #1 (Master Workflow Coordinator)

Responsibilities:
  1. Global Workflow Governance:
     - Coordinates all 8 specialist agents in the TestForge ecosystem.
     - Formulates structured, validated decisions using Blackboard state and specialist findings.
  2. Authoritative Deterministic Guardrails:
     - Deterministic policy strictly governs security clearance, sandbox execution permissions,
       cancellation, timeout limits, iteration bounds, state transition validation, and non-regression.
     - Model deliberation is constrained to permissible actions and cannot override deterministic blocks.
  3. Structured Decision Protocol:
     - Emits strongly-typed SupervisorDecisionPayload for every stage transition.
     - Accurately reports whether decisions derived from deterministic policy or model reasoning.
  4. Reliable Transition Validation:
     - Enforces an explicit, bounded state machine preventing recursive loops or invalid state jumps.
  5. Truthful Observability:
     - Maintains dynamic runtime status (registered, instantiated, available, participating,
       executing, completed, failed, skipped) for all 8 agents.
"""

from __future__ import annotations

import os

# Suppress OpenTelemetry detachment crashes across thread and async generator boundaries
os.environ.setdefault("OTEL_PYTHON_CONTEXT", "contextvars_context")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import asyncio
import concurrent.futures
import json
import logging
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple, Union

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from testforge.a2a import (
    A2AErrorPayload,
    A2AMessage,
    A2APerformative,
    SupervisorAction,
    SupervisorDecisionPayload,
    WorkflowStage,
)
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType, LifecycleEvent
from testforge.llm_client import HybridLLMClient
from testforge.logger import TraceLogger
from testforge.prompt_guard import (
    get_defensive_system_instruction,
)

logger = logging.getLogger("testforge.supervisor_agent")


def _run_coroutine_sync(coro: Any) -> Any:
    """Safely executes an async coroutine synchronously across thread boundaries."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)


# ==============================================================================
# 1. State Machine Definition: Allowed Workflow Transitions
# ==============================================================================

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    WorkflowStage.INITIALIZING.value: {
        WorkflowStage.SECURITY_SCREENING.value,
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.SECURITY_SCREENING.value: {
        WorkflowStage.CODE_INTELLIGENCE.value,
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.CODE_INTELLIGENCE.value: {
        WorkflowStage.TEST_PLANNING.value,
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.TEST_PLANNING.value: {
        WorkflowStage.TEST_GENERATION.value,
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.TEST_GENERATION.value: {
        WorkflowStage.BASELINE_EXECUTION.value,
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.BASELINE_EXECUTION.value: {
        WorkflowStage.TEST_GENERATION.value,     # Self-repair retry on syntax/collection error
        WorkflowStage.MUTATION_ANALYSIS.value,   # Baseline passed cleanly
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.MUTATION_ANALYSIS.value: {
        WorkflowStage.CRITIC_ASSESSMENT.value,
        WorkflowStage.CONVERGED.value,           # 0 mutants generated / trivial target
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.CRITIC_ASSESSMENT.value: {
        WorkflowStage.CONVERGED.value,           # Score >= target satisfied
        WorkflowStage.REFLECTION_REPAIR.value,   # Score < target, survivors present
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.REFLECTION_REPAIR.value: {
        WorkflowStage.MUTATION_ANALYSIS.value,   # Candidate verified, re-evaluating mutants
        WorkflowStage.CRITIC_ASSESSMENT.value,   # Re-critique
        WorkflowStage.CONVERGED.value,           # Score converged after repair
        WorkflowStage.FAILED.value,
        WorkflowStage.CANCELLED.value,
    },
    WorkflowStage.CONVERGED.value: set(),        # Terminal state
    WorkflowStage.FAILED.value: set(),           # Terminal state
    WorkflowStage.CANCELLED.value: set(),        # Terminal state
}

# Mapping from selected supervisor action to corresponding specialist agent
ACTION_TO_AGENT_MAP: Dict[str, str] = {
    SupervisorAction.SCREEN_SECURITY.value: "agent:google-adk:security",
    SupervisorAction.ANALYZE_CODE.value: "agent:google-adk:code-intelligence",
    SupervisorAction.PLAN_TESTS.value: "agent:google-adk:test-planner",
    SupervisorAction.GENERATE_TESTS.value: "agent:google-adk:generator",
    SupervisorAction.EXECUTE_TESTS.value: "agent:google-adk:test-execution",
    SupervisorAction.EVALUATE_CRITIQUE.value: "agent:crewai:mutation-critic",
    SupervisorAction.REFLECT_AND_REPAIR.value: "agent:google-adk:reflection-repair",
    SupervisorAction.RETRY_STEP.value: "agent:google-adk:generator",
    SupervisorAction.STOP_CONVERGED.value: "agent:google-adk:supervisor",
    SupervisorAction.STOP_MAX_ITERATIONS.value: "agent:google-adk:supervisor",
    SupervisorAction.STOP_CANCELLED.value: "agent:google-adk:supervisor",
    SupervisorAction.STOP_SECURITY_REFUSAL.value: "agent:google-adk:supervisor",
    SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value: "agent:google-adk:supervisor",
}

# The 8 canonical cognitive agents in the TestForge architecture
CANONICAL_EIGHT_AGENTS = [
    "SupervisorAgent",
    "CodeIntelligenceAgent",
    "TestPlanningAgent",
    "TestGeneratorAgent",
    "TestExecutionAgent",
    "MutationQualityCriticAgent",
    "SecurityAgent",
    "ReflectionRepairAgent",
]


# ==============================================================================
# 2. Google ADK Model Bridge for Supervisor Deliberation
# ==============================================================================

class SupervisorModelBridge(BaseLlm):
    """
    Subclass of official Google ADK BaseLlm bridging ADK LlmAgent / Runner
    to the top-level supervisor deliberation.
    """
    __test__ = False
    model: str = "custom/testforge-supervisor"

    def __init__(
        self,
        model: str = "custom/testforge-supervisor",
        api_key: Optional[str] = None,
        llm_client: Optional[HybridLLMClient] = None,
        use_live_llm: Optional[bool] = None,
        mock_response: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ):
        super().__init__(model=model, **kwargs)
        env_live = os.environ.get("TESTFORGE_LIVE_LLM", "0").lower() in ("1", "true", "yes")
        live_flag = use_live_llm if use_live_llm is not None else env_live
        object.__setattr__(self, "_api_key", api_key or os.environ.get("GEMINI_API_KEY", "").strip())
        object.__setattr__(self, "_llm_client", llm_client)
        object.__setattr__(self, "_use_live_llm", live_flag)
        object.__setattr__(self, "_mock_response", mock_response)

    def set_mock_response(self, response: Optional[Union[str, Dict[str, Any]]]) -> None:
        """Sets a deterministic mock response for testing."""
        object.__setattr__(self, "_mock_response", response)

    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        """Executes asynchronous LLM generation for ADK Runner."""
        mock = getattr(self, "_mock_response", None)
        if mock is not None:
            output_text = json.dumps(mock) if isinstance(mock, dict) else str(mock)
            content = types.Content(
                role="model",
                parts=[types.Part(text=output_text)],
            )
            yield LlmResponse(content=content, turn_complete=True)
            return

        prompt_parts = []
        if llm_request.contents:
            for c in llm_request.contents:
                if hasattr(c, "parts") and c.parts:
                    for p in c.parts:
                        if hasattr(p, "text") and p.text:
                            prompt_parts.append(p.text)
        prompt_text = "\n\n".join(prompt_parts)

        use_live = getattr(self, "_use_live_llm", False)
        api_key = getattr(self, "_api_key", "")
        llm_client = getattr(self, "_llm_client", None)

        if use_live and (api_key or llm_client):
            try:
                client = llm_client or HybridLLMClient(
                    cloud_model="gemini-3.6-flash",
                    api_key=api_key,
                )
                system_instruction = get_defensive_system_instruction(
                    "You are the Principal AI Workflow Supervisor for TestForge. "
                    "Analyze current pipeline state and evidence to propose the next workflow action. "
                    "Respond strictly with valid JSON adhering to SupervisorDecisionPayload."
                )
                resp_str = client.generate(
                    prompt=prompt_text,
                    system_instruction=system_instruction,
                    temperature=0.1,
                    agent_name="SupervisorAgent",
                )
                content = types.Content(
                    role="model",
                    parts=[types.Part(text=resp_str)],
                )
                yield LlmResponse(content=content, turn_complete=True)
                return
            except Exception as exc:
                logger.warning(f"SupervisorModelBridge live call failed, falling back to deterministic synthesis: {exc}")

        # Deterministic fallback response
        fallback_json = json.dumps({
            "selected_action": "CONTINUE",
            "reason": "Deterministic supervisor policy fallback.",
            "is_deterministic": True
        })
        content = types.Content(
            role="model",
            parts=[types.Part(text=fallback_json)],
        )
        yield LlmResponse(content=content, turn_complete=True)


# ==============================================================================
# 3. Top-Level Supervisor Agent Implementation
# ==============================================================================

class SupervisorAgent:
    """
    Google ADK Top-Level Supervisor Agent for TestForge.

    Orchestrates the 8 canonical specialist agents:
      1. Supervisor Agent (Self)
      2. Code Intelligence Agent (Google ADK)
      3. Test Planning Agent (Google ADK)
      4. Test Generation Agent (Google ADK / Hybrid LLM)
      5. Test Execution Agent (Google ADK / Sandbox)
      6. Mutation & Quality Critic Agent (CrewAI)
      7. Security Agent (Google ADK)
      8. Reflection & Repair Agent (Google ADK)

    Guarantees:
      - Deterministic policy is authoritative over LLM reasoning at all times.
      - Never allows LLM reasoning to bypass security rejections, cancellation, timeouts,
        iteration limits, or non-regression rules.
      - Emits strongly-typed SupervisorDecisionPayload for all transitions.
      - Accurately tracks dynamic runtime status for all 8 agents.
    """
    __test__ = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        blackboard: Optional[Blackboard] = None,
        callbacks: Optional[CallbackRegistry] = None,
        logger_instance: Optional[TraceLogger] = None,
        use_live_llm: Optional[bool] = None,
        mock_response: Optional[Union[str, Dict[str, Any]]] = None,
        max_retries_per_step: int = 1,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.blackboard = blackboard
        self.callbacks = callbacks
        self.logger = logger_instance
        self.max_retries_per_step = max_retries_per_step
        self.agent_id = "agent:google-adk:supervisor"

        # Model bridge & Google ADK setup
        self.model_bridge = SupervisorModelBridge(
            api_key=self.api_key,
            use_live_llm=use_live_llm,
            mock_response=mock_response,
        )
        self.session_service = InMemorySessionService()
        self.adk_agent = LlmAgent(
            name="SupervisorAgent",
            model=self.model_bridge,
            description=(
                "TestForge Top-Level Workflow Supervisor. Evaluates job state, enforces "
                "authoritative deterministic policies, and directs specialist agents."
            ),
            instruction=(
                "You are the master coordinator for TestForge unit test hardening. "
                "Analyze job state, specialist findings, and decide the next permitted action."
            ),
        )
        self.runner = Runner(
            agent=self.adk_agent,
            session_service=self.session_service,
            app_name="TestForgeSupervisor",
        )

        # Dynamic runtime agent tracking
        self._agent_status_map: Dict[str, Dict[str, Any]] = {
            name: {
                "name": name,
                "registered": True,
                "instantiated": True,
                "available": True,
                "participating": False,
                "executing": False,
                "completed": False,
                "failed": False,
                "skipped": False,
                "last_stage": None,
                "last_active_at": None,
                "failure_reason": None,
            }
            for name in CANONICAL_EIGHT_AGENTS
        }

        # Step retry counts
        self._step_retry_counts: Dict[str, int] = {}
        # Decision history
        self._decision_history: List[SupervisorDecisionPayload] = []

    # --------------------------------------------------------------------------
    # 4. State Machine Transition Validation
    # --------------------------------------------------------------------------

    def validate_transition(
        self,
        current_stage: Union[WorkflowStage, str],
        proposed_stage: Union[WorkflowStage, str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Deterministically validates whether a proposed state transition is permissible.
        Prevents invalid loops, out-of-order jumps, and unauthorized restarts.
        """
        curr = current_stage.value if isinstance(current_stage, WorkflowStage) else str(current_stage)
        prop = proposed_stage.value if isinstance(proposed_stage, WorkflowStage) else str(proposed_stage)

        if curr not in ALLOWED_TRANSITIONS:
            return False, f"Unknown current workflow stage: '{curr}'"

        allowed = ALLOWED_TRANSITIONS[curr]
        if prop not in allowed:
            return False, (
                f"Invalid workflow transition: Cannot transition from '{curr}' to '{prop}'. "
                f"Permitted next stages are: {sorted(list(allowed)) or 'None (Terminal)'}"
            )

        return True, None

    # --------------------------------------------------------------------------
    # 5. Core Decision Engine: Deterministic Policies & Model Reasoning
    # --------------------------------------------------------------------------

    def decide_next_step(
        self,
        current_stage: Union[WorkflowStage, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> SupervisorDecisionPayload:
        """
        Evaluates the current job state, enforces authoritative deterministic policies,
        and produces a strongly-typed SupervisorDecisionPayload.

        Policy Precedence:
          1. Cancellation Token -> STOP_CANCELLED (Deterministic)
          2. Timeout Expiration -> STOP_UNRECOVERABLE_FAILURE (Deterministic)
          3. Security Refusal -> STOP_SECURITY_REFUSAL (Deterministic)
          4. Convergence Criteria -> STOP_CONVERGED (Deterministic)
          5. Iteration Budget Exhaustion -> STOP_MAX_ITERATIONS (Deterministic)
          6. Sandbox/Execution Error -> RETRY_STEP or STOP_UNRECOVERABLE_FAILURE (Deterministic)
          7. Standard Pipeline Transitions -> Specialized Agent Actions (Deterministic Heuristic / ADK)
        """
        ctx = context or {}
        curr_str = current_stage.value if isinstance(current_stage, WorkflowStage) else str(current_stage)
        wf_id = ctx.get("workflow_id")
        task_id = ctx.get("task_id") or wf_id or ctx.get("job_id") or "task_default"
        job_id = ctx.get("job_id") or wf_id or task_id
        iteration = ctx.get("iteration", 0)
        source_code = ctx.get("source_code", "")

        # ----------------------------------------------------------------------
        # Priority 1: Cancellation check (Strictly Deterministic)
        # ----------------------------------------------------------------------
        cancel_event = ctx.get("cancel_event")
        if (cancel_event and hasattr(cancel_event, "is_set") and cancel_event.is_set()) or ctx.get("is_cancelled"):
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.STOP_CANCELLED.value,
                target_agent="agent:google-adk:supervisor",
                reason="Job cancellation token was triggered. Deterministic stop enforced.",
                is_deterministic=True,
                iteration=iteration,
            ))

        # ----------------------------------------------------------------------
        # Priority 2: Timeout check (Strictly Deterministic)
        # ----------------------------------------------------------------------
        timeout_seconds = ctx.get("timeout_seconds")
        start_time = ctx.get("start_time")
        if timeout_seconds and start_time and (time.time() - start_time) > timeout_seconds:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value,
                target_agent="agent:google-adk:supervisor",
                reason=f"Pipeline execution exceeded timeout limit of {timeout_seconds}s.",
                is_deterministic=True,
                iteration=iteration,
            ))

        # ----------------------------------------------------------------------
        # Priority 3: Security screening evaluation (Strictly Deterministic)
        # ----------------------------------------------------------------------
        sec_space = self.blackboard.get_security_space() if self.blackboard else None
        if sec_space and not sec_space.allowed:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.STOP_SECURITY_REFUSAL.value,
                target_agent="agent:google-adk:supervisor",
                reason=f"SecurityAgent rejected target: {sec_space.findings or 'High-risk security policy violation'}",
                evidence_references={"security_findings": sec_space.findings, "risk_level": sec_space.risk_level},
                is_deterministic=True,
                iteration=iteration,
            ))

        # ----------------------------------------------------------------------
        # Priority 4: Stage-Specific Policy Transitions
        # ----------------------------------------------------------------------

        # A. INITIALIZING -> SECURITY_SCREENING
        if curr_str == WorkflowStage.INITIALIZING.value:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.SCREEN_SECURITY.value,
                target_agent="agent:google-adk:security",
                reason="Initial input code screening required before any execution or analysis.",
                required_inputs=["target_source_code"],
                expected_output="SecurityEvaluationPayload",
                is_deterministic=True,
                iteration=0,
            ))

        # B. SECURITY_SCREENING -> CODE_INTELLIGENCE
        if curr_str == WorkflowStage.SECURITY_SCREENING.value:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.ANALYZE_CODE.value,
                target_agent="agent:google-adk:code-intelligence",
                reason="Security cleared. Delegating target code for AST parsing and complexity analysis.",
                required_inputs=["target_source_code", "target_file_path"],
                expected_output="CodeIntelligencePayload",
                is_deterministic=True,
                iteration=0,
            ))

        # C. CODE_INTELLIGENCE -> TEST_PLANNING
        if curr_str == WorkflowStage.CODE_INTELLIGENCE.value:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.PLAN_TESTS.value,
                target_agent="agent:google-adk:test-planner",
                reason="AST analysis complete. Formulating structured nominal, boundary, and negative scenarios.",
                required_inputs=["code_intelligence"],
                expected_output="TestPlanPayload",
                is_deterministic=True,
                iteration=0,
            ))

        # D. TEST_PLANNING -> TEST_GENERATION
        if curr_str == WorkflowStage.TEST_PLANNING.value:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.GENERATE_TESTS.value,
                target_agent="agent:google-adk:generator",
                reason="Test plan formulated. Delegating initial pytest suite synthesis.",
                required_inputs=["target_source_code", "test_plan"],
                expected_output="Generated test suite string",
                is_deterministic=True,
                iteration=0,
            ))

        # E. TEST_GENERATION -> BASELINE_EXECUTION
        if curr_str == WorkflowStage.TEST_GENERATION.value:
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.EXECUTE_TESTS.value,
                target_agent="agent:google-adk:test-execution",
                reason="Candidate test suite synthesized. Executing pass@1 validation against clean target in sandbox.",
                required_inputs=["current_test_code", "target_source_code"],
                expected_output="TestExecutionPayload (pass@1 validation & line coverage)",
                is_deterministic=True,
                iteration=iteration,
            ))

        # F. BASELINE_EXECUTION -> Evaluates pass@1 & line coverage
        if curr_str == WorkflowStage.BASELINE_EXECUTION.value:
            baseline_passed = ctx.get("baseline_passed", False)
            tests_passed = ctx.get("tests_passed", 0)

            if not baseline_passed or tests_passed == 0:
                # Check retry budget for baseline repair
                step_key = "baseline_repair"
                retries = self._step_retry_counts.get(step_key, 0)
                if retries < self.max_retries_per_step:
                    self._step_retry_counts[step_key] = retries + 1
                    return self._record_decision(SupervisorDecisionPayload(
                        task_id=task_id,
                        job_id=job_id,
                        current_stage=curr_str,
                        selected_action=SupervisorAction.RETRY_STEP.value,
                        target_agent="agent:google-adk:generator",
                        reason=f"Baseline tests failed clean target validation. Initiating bounded self-repair (attempt {retries + 1}/{self.max_retries_per_step}).",
                        required_inputs=["target_source_code", "sandbox_stderr"],
                        expected_output="Corrected test suite string",
                        is_deterministic=True,
                        iteration=0,
                        retry_count=retries + 1,
                    ))
                else:
                    return self._record_decision(SupervisorDecisionPayload(
                        task_id=task_id,
                        job_id=job_id,
                        current_stage=curr_str,
                        selected_action=SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value,
                        target_agent="agent:google-adk:supervisor",
                        reason=f"Baseline tests failed clean validation and exhausted self-repair budget ({self.max_retries_per_step} attempts).",
                        is_deterministic=True,
                        iteration=0,
                    ))

            # Baseline passed cleanly -> advance to MUTATION_ANALYSIS
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.EXECUTE_TESTS.value,
                target_agent="agent:google-adk:test-execution",
                reason="Baseline validated cleanly on target. Proceeding to parallel AST mutant evaluation.",
                required_inputs=["current_test_code", "mutants"],
                expected_output="Evaluated mutant records",
                is_deterministic=True,
                iteration=iteration,
            ))

        # G. MUTATION_ANALYSIS -> Evaluates mutant counts & advances to CRITIC_ASSESSMENT
        if curr_str == WorkflowStage.MUTATION_ANALYSIS.value:
            total_mutants = ctx.get("total_mutants", 0)
            mutants_executed = ctx.get("mutants_executed", 0)
            if total_mutants > 0 and mutants_executed == 0:
                return self._record_decision(SupervisorDecisionPayload(
                    task_id=task_id,
                    job_id=job_id,
                    current_stage=curr_str,
                    selected_action=SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value,
                    target_agent="agent:google-adk:supervisor",
                    reason="Mutants were generated but could not be executed in the sandbox.",
                    is_deterministic=True,
                    iteration=iteration,
                ))

            # Normal path -> CRITIC_ASSESSMENT
            return self._record_decision(SupervisorDecisionPayload(
                task_id=task_id,
                job_id=job_id,
                current_stage=curr_str,
                selected_action=SupervisorAction.EVALUATE_CRITIQUE.value,
                target_agent="agent:crewai:mutation-critic",
                reason="Mutants evaluated. Delegating mutation score calculation and AST test quality audit.",
                required_inputs=["mutants", "target_source_code", "current_test_code"],
                expected_output="MutationQualityCriticPayload",
                is_deterministic=True,
                iteration=iteration,
            ))

        # H. CRITIC_ASSESSMENT / REFLECTION_REPAIR -> Convergence or Repair Decision
        if curr_str in (WorkflowStage.CRITIC_ASSESSMENT.value, WorkflowStage.REFLECTION_REPAIR.value):
            score = ctx.get("mutation_score", 0.0)
            adj_score = ctx.get("adjusted_mutation_score", score)
            target_score = ctx.get("target_mutation_score", 85.0)
            cov_pct = ctx.get("coverage_pct", 100.0)
            surviving_count = ctx.get("surviving_mutants_count", 0)
            max_iterations = ctx.get("max_iterations", 3)

            effective_score = max(score, adj_score)

            # Check convergence condition
            if effective_score >= target_score and cov_pct > 0.0:
                return self._record_decision(SupervisorDecisionPayload(
                    task_id=task_id,
                    job_id=job_id,
                    current_stage=curr_str,
                    selected_action=SupervisorAction.STOP_CONVERGED.value,
                    target_agent="agent:google-adk:supervisor",
                    reason=f"Target mutation score satisfied: {effective_score:.1f}% >= {target_score:.1f}% with {cov_pct:.1f}% coverage.",
                    evidence_references={"mutation_score": effective_score, "target_score": target_score, "coverage": cov_pct},
                    is_deterministic=True,
                    iteration=iteration,
                ))

            # Check zero surviving mutants
            if surviving_count == 0 and cov_pct > 0.0:
                return self._record_decision(SupervisorDecisionPayload(
                    task_id=task_id,
                    job_id=job_id,
                    current_stage=curr_str,
                    selected_action=SupervisorAction.STOP_CONVERGED.value,
                    target_agent="agent:google-adk:supervisor",
                    reason="All generated mutants killed. No surviving mutants remain.",
                    is_deterministic=True,
                    iteration=iteration,
                ))

            # Check iteration budget exhaustion
            if iteration >= max_iterations:
                return self._record_decision(SupervisorDecisionPayload(
                    task_id=task_id,
                    job_id=job_id,
                    current_stage=curr_str,
                    selected_action=SupervisorAction.STOP_MAX_ITERATIONS.value,
                    target_agent="agent:google-adk:supervisor",
                    reason=f"Maximum allowed reflection iterations reached ({iteration}/{max_iterations}). Final score: {effective_score:.1f}%.",
                    evidence_references={"final_score": effective_score, "iterations": iteration},
                    is_deterministic=True,
                    iteration=iteration,
                ))

            # If not converged and budget remains, attempt ADK model deliberation for repair strategy
            deliberated_action = self._deliberate_repair_action(
                task_id=task_id,
                job_id=job_id,
                curr_str=curr_str,
                iteration=iteration,
                score=effective_score,
                target_score=target_score,
                surviving_count=surviving_count,
            )
            return self._record_decision(deliberated_action)

        # Fallback default decision
        return self._record_decision(SupervisorDecisionPayload(
            task_id=task_id,
            job_id=job_id,
            current_stage=curr_str,
            selected_action=SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value,
            target_agent="agent:google-adk:supervisor",
            reason=f"No permissible action rule matched for stage '{curr_str}'.",
            is_deterministic=True,
            iteration=iteration,
        ))

    # --------------------------------------------------------------------------
    # 6. Deliberation via Google ADK Runner (with Deterministic Safety Fallback)
    # --------------------------------------------------------------------------

    def _deliberate_repair_action(
        self,
        task_id: str,
        job_id: str,
        curr_str: str,
        iteration: int,
        score: float,
        target_score: float,
        surviving_count: int,
    ) -> SupervisorDecisionPayload:
        """
        Invokes Google ADK Runner for exploratory deliberation regarding test repair,
        strictly wrapped by deterministic fallbacks.
        """
        user_msg_text = (
            f"Job {job_id} at Stage {curr_str}, Iteration {iteration}. "
            f"Current mutation score: {score:.1f}% vs Target: {target_score:.1f}%. "
            f"Surviving mutants: {surviving_count}. Decide if pipeline should request "
            f"reflection and repair or stop."
        )
        user_msg = types.Content(role="user", parts=[types.Part(text=user_msg_text)])

        try:
            session_id = f"sup_sess_{job_id}_{iteration}"
            user_id = f"user_{job_id}"

            async def _run_adk() -> str:
                try:
                    await self.session_service.create_session(
                        session_id=session_id,
                        user_id=user_id,
                        app_name="TestForgeSupervisor",
                    )
                except Exception:
                    pass  # Session may already exist
                result_text = ""
                try:
                    async for event in self.runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=user_msg,
                    ):
                        if hasattr(event, "content") and event.content:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    result_text = part.text
                except (GeneratorExit, ValueError, Exception) as gen_err:
                    logger.debug(f"ADK runner async generator ended or encountered context detachment: {gen_err}")
                return result_text

            model_text = _run_coroutine_sync(_run_adk())

            # Parse model output
            if model_text:
                json_match = re.search(r"\{.*\}", model_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    action_cand = parsed.get("selected_action")
                    if action_cand in (SupervisorAction.REFLECT_AND_REPAIR.value, "REFLECT_AND_REPAIR"):
                        return SupervisorDecisionPayload(
                            task_id=task_id,
                            job_id=job_id,
                            current_stage=curr_str,
                            selected_action=SupervisorAction.REFLECT_AND_REPAIR.value,
                            target_agent="agent:google-adk:reflection-repair",
                            reason=parsed.get("reason", "Model reasoned that reflection repair is viable to eliminate surviving mutants."),
                            required_inputs=["surviving_mutants", "critic_directive", "current_test_code"],
                            expected_output="RepairDirectivePayload and candidate repaired suite",
                            is_deterministic=False,  # Truthfully attribute to model reasoning
                            iteration=iteration,
                        )
        except Exception as exc:
            logger.info(f"ADK Supervisor deliberation used deterministic fallback: {exc}")

        # Authoritative deterministic fallback: Request reflection and repair
        return SupervisorDecisionPayload(
            task_id=task_id,
            job_id=job_id,
            current_stage=curr_str,
            selected_action=SupervisorAction.REFLECT_AND_REPAIR.value,
            target_agent="agent:google-adk:reflection-repair",
            reason=f"Deterministic policy: Score {score:.1f}% < {target_score:.1f}% with {surviving_count} surviving mutants. Initiating reflection repair loop.",
            required_inputs=["surviving_mutants", "critic_directive", "current_test_code"],
            expected_output="RepairDirectivePayload and candidate repaired suite",
            is_deterministic=True,
            iteration=iteration,
        )

    def _record_decision(self, decision: SupervisorDecisionPayload) -> SupervisorDecisionPayload:
        """Stores decision locally, synchronizes to Blackboard, and emits lifecycle callback."""
        self._decision_history.append(decision)

        # Update dynamic agent status map
        target_name = decision.target_agent.split(":")[-1].replace("-", " ").title().replace(" ", "")
        for name in CANONICAL_EIGHT_AGENTS:
            if name.lower() in target_name.lower():
                self._agent_status_map[name]["participating"] = True
                self._agent_status_map[name]["last_stage"] = decision.current_stage
                self._agent_status_map[name]["last_active_at"] = decision.decision_timestamp

        # Blackboard sync
        if self.blackboard and hasattr(self.blackboard, "record_supervisor_decision"):
            self.blackboard.record_supervisor_decision(decision)

        # Trace logger
        if self.logger:
            self.logger.log_event("SUPERVISOR_DECISION", decision.model_dump())

        # Callback dispatch
        if self.callbacks:
            self.callbacks.dispatch(LifecycleEvent(
                event_type=EventType.OPERATION_COMPLETE,
                emitter="SupervisorAgent",
                workflow_id=decision.job_id or decision.task_id,
                correlation_id=decision.task_id or decision.job_id,
                payload={
                    "operation_name": f"supervisor_decision_{decision.selected_action}",
                    "current_stage": decision.current_stage,
                    "target_agent": decision.target_agent,
                    "is_deterministic": decision.is_deterministic,
                    "reason": decision.reason,
                }
            ))

        return decision

    # --------------------------------------------------------------------------
    # 7. Agent Status & Observability Tracking
    # --------------------------------------------------------------------------

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Returns truthful runtime status for a named canonical agent."""
        if agent_name in self._agent_status_map:
            return dict(self._agent_status_map[agent_name])
        return {
            "name": agent_name,
            "registered": False,
            "instantiated": False,
            "available": False,
            "participating": False,
            "executing": False,
            "completed": False,
            "failed": False,
            "skipped": False,
        }

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Returns status for all 8 canonical architecture agents."""
        return [dict(self._agent_status_map[name]) for name in CANONICAL_EIGHT_AGENTS]

    def set_agent_executing(self, agent_name: str, executing: bool = True) -> None:
        """Updates executing flag for an agent during active workflow processing."""
        for name in CANONICAL_EIGHT_AGENTS:
            if name.lower() == agent_name.lower() or name.lower() in agent_name.lower():
                self._agent_status_map[name]["executing"] = executing
                if executing:
                    self._agent_status_map[name]["participating"] = True
                    self._agent_status_map[name]["last_active_at"] = time.time()
                break

    def set_agent_completed(self, agent_name: str, success: bool = True, failure_reason: Optional[str] = None) -> None:
        """Marks an agent completed or failed upon finishing a stage."""
        for name in CANONICAL_EIGHT_AGENTS:
            if name.lower() == agent_name.lower() or name.lower() in agent_name.lower():
                self._agent_status_map[name]["executing"] = False
                if success:
                    self._agent_status_map[name]["completed"] = True
                else:
                    self._agent_status_map[name]["failed"] = True
                    self._agent_status_map[name]["failure_reason"] = failure_reason
                break

    # --------------------------------------------------------------------------
    # 8. Inter-Agent A2A Message Handling
    # --------------------------------------------------------------------------

    def handle_a2a_message(self, message: A2AMessage) -> A2AMessage:
        """
        Official A2A entrypoint for the Top-Level Supervisor Agent.
        Supported actions:
          - 'decide_next': Evaluates current stage and outputs next supervisor decision.
          - 'validate_transition': Validates state machine transition.
          - 'get_status': Queries dynamic status of all 8 agents.
        """
        payload = message.payload or {}
        action = message.action

        if action in ("decide_next", "decide"):
            curr_stage = payload.get("current_stage", WorkflowStage.INITIALIZING.value)
            decision = self.decide_next_step(curr_stage, context=payload)
            return A2AMessage(
                correlation_id=message.correlation_id,
                sender=self.agent_id,
                recipient=message.sender,
                performative=A2APerformative.INFORM,
                action="supervisor_decision",
                payload=decision.model_dump(),
            )

        if action in ("validate_transition", "check_transition"):
            curr = payload.get("current_stage", "")
            prop = payload.get("proposed_stage", "")
            allowed, reason = self.validate_transition(curr, prop)
            return A2AMessage(
                correlation_id=message.correlation_id,
                sender=self.agent_id,
                recipient=message.sender,
                performative=A2APerformative.INFORM if allowed else A2APerformative.REFUSE,
                action="transition_validation",
                payload={
                    "allowed": allowed,
                    "from_stage": curr,
                    "to_stage": prop,
                    "reason": reason or "Transition permitted by state machine.",
                },
            )

        if action in ("get_status", "agent_status"):
            return A2AMessage(
                correlation_id=message.correlation_id,
                sender=self.agent_id,
                recipient=message.sender,
                performative=A2APerformative.INFORM,
                action="agent_status_report",
                payload={
                    "agents": self.get_all_agents_status(),
                    "total_agents": len(CANONICAL_EIGHT_AGENTS),
                    "decisions_count": len(self._decision_history),
                },
            )

        return A2AMessage(
            correlation_id=message.correlation_id,
            sender=self.agent_id,
            recipient=message.sender,
            performative=A2APerformative.FAILURE,
            action="error",
            payload=A2AErrorPayload(
                error_code="UNSUPPORTED_ACTION",
                error_message=f"SupervisorAgent does not support action '{action}'.",
                source_component=self.agent_id,
            ).model_dump(),
        )
