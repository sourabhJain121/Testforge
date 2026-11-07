"""
a2a.py - Typed, Validated Agent-to-Agent (A2A) Message Contract and Broker.

This module implements a custom in-process typed A2A message broker and contract
inspired by FIPA-ACL and modern multi-agent communication patterns, tailored for
TestForge's in-memory multi-framework pipeline. It is an internal agent contract
and message broker rather than an external HTTP wire protocol.

Architecture:
  1. A2APerformative: Formal communicative acts (REQUEST, INFORM, AGREE, REFUSE, FAILURE, PROPOSE).
  2. A2AMessage: Strongly-typed Pydantic message envelope preserving correlation IDs,
     trace metadata, sender/recipient identities, and deep-copy isolation.
  3. Typed Payloads: Constrained schemas for critique requests, structured directives,
     and failure mechanisms (e.g. CriticDirectivePayload, A2ACritiqueRequestPayload).
  4. A2ABroker: In-process message exchange with handler registration, sender/recipient
     authorization, AST/Prompt security guardrail inspection, bounded execution timeouts,
     lifecycle callback emission, and thread-safe Blackboard partition synchronization.
"""

from __future__ import annotations

import copy
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Union

from pydantic import BaseModel, Field, ValidationError, model_validator

from testforge.callbacks import (
    CallbackRegistry,
    EventType,
    LifecycleEvent,
    _scrub_value,
)
from testforge.security import SecurityGuardrail, redact_sensitive_data

logger = logging.getLogger("testforge.a2a")


# ==============================================================================
# 1. Communicative Acts (Performatives) and Envelope
# ==============================================================================

class A2APerformative(str, Enum):
    """FIPA-ACL inspired communicative acts for agent deliberation."""
    REQUEST = "REQUEST"       # Sender requests recipient to execute an action
    INFORM = "INFORM"         # Sender provides verified results/facts
    AGREE = "AGREE"           # Recipient accepts request and commits to execute
    REFUSE = "REFUSE"         # Recipient or Broker refuses execution (auth, security, policy)
    FAILURE = "FAILURE"       # Execution failed during operation (timeout, exception, error)
    PROPOSE = "PROPOSE"       # Sender proposes candidate directives or assertions


class A2AMessage(BaseModel):
    """
    Standardized typed message envelope for inter-agent communication.
    Guarantees structural validation, immutable logging semantics, and correlation tracing.
    """
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    correlation_id: str = Field(..., description="Unique trace identifier spanning an entire reflection cycle")
    sender: str = Field(..., description="Identity URI of sending entity (e.g., 'agent:orchestrator', 'agent:crewai:critic')")
    recipient: str = Field(..., description="Identity URI of target entity (e.g., 'agent:crewai:critic', 'agent:adk:generator')")
    performative: A2APerformative = Field(..., description="Communicative act")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of message creation")
    action: str = Field(..., description="Operational action identifier, e.g. 'diagnose_mutants', 'generate_tests'")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Typed structured payload data")
    headers: Dict[str, Any] = Field(default_factory=dict, description="Operational headers, route flags, and credentials metadata")

    @model_validator(mode="before")
    @classmethod
    def deepcopy_containers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "payload" in data and isinstance(data["payload"], (dict, list)):
                data["payload"] = copy.deepcopy(data["payload"])
            if "headers" in data and isinstance(data["headers"], (dict, list)):
                data["headers"] = copy.deepcopy(data["headers"])
        return data

    @model_validator(mode="after")
    def validate_non_empty_identifiers(self) -> "A2AMessage":
        for field_name in ("correlation_id", "sender", "recipient", "action"):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"A2AMessage field '{field_name}' must be a non-empty string.")
        return self

    def create_response(
        self,
        performative: A2APerformative,
        payload: Dict[str, Any],
        action: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> "A2AMessage":
        """
        Creates a properly correlated response envelope swapping sender and recipient.
        """
        resp_headers = dict(self.headers)
        if headers:
            resp_headers.update(headers)

        return A2AMessage(
            correlation_id=self.correlation_id,
            sender=self.recipient,
            recipient=self.sender,
            performative=performative,
            action=action or self.action,
            payload=copy.deepcopy(payload),
            headers=resp_headers,
        )

    def scrubbed_copy(self) -> "A2AMessage":
        """Returns a defensive copy with credentials and sensitive values redacted."""
        return A2AMessage(
            message_id=self.message_id,
            correlation_id=self.correlation_id,
            sender=self.sender,
            recipient=self.recipient,
            performative=self.performative,
            timestamp=self.timestamp,
            action=self.action,
            payload=_scrub_value(copy.deepcopy(self.payload)),
            headers=_scrub_value(copy.deepcopy(self.headers)),
        )


# ==============================================================================
# 2. Typed Payloads
# ==============================================================================

class CriticDirectivePayload(BaseModel):
    """
    Structured critique output generated by the adversarial critic agent.
    Provides verified failure mechanisms and prescriptive test directives.
    """
    analysis: str = Field(..., description="Concise diagnostic reasoning on why mutants survived")
    target_mutants: List[str] = Field(default_factory=list, description="IDs of surviving mutants analyzed")
    directives: List[str] = Field(default_factory=list, description="Prescriptive assertions and boundary directives")
    failure_mechanisms: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of mutant_id to root cause failure mechanism"
    )
    raw_mutation_score: Optional[float] = Field(None, description="Raw mutation score")
    raw_branch_coverage: Optional[float] = Field(None, description="Raw branch coverage")
    raw_dimensions: Dict[str, float] = Field(default_factory=dict, description="Raw TQS dimensions")
    composite_tqs: Optional[float] = Field(None, description="Composite TQS score")


# Alias for compatibility with design terminology
A2ACritiqueDirectivePayload = CriticDirectivePayload


class A2ACritiqueRequestPayload(BaseModel):
    """Payload sent to request mutant diagnosis from the adversarial critic."""
    target_source_code: str = Field(..., description="Clean Python source code under test")
    surviving_mutants: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized surviving MutantRecords")
    surviving_diffs: List[str] = Field(default_factory=list, description="Unified AST diffs of surviving mutants")
    iteration: int = Field(default=1, ge=1, description="Current reflection iteration index")


class A2ACritiqueResponsePayload(BaseModel):
    """Envelope payload wrapping critique execution results."""
    directive: CriticDirectivePayload
    execution_time_sec: float = 0.0
    critic_agent: str = "agent:crewai:critic"


class GeneratedTestPayload(BaseModel):
    """
    Structured test generation output produced by the Google ADK Generator Agent.
    Strictly distinguishes intended mutant coverage from measured execution results.
    """
    test_code: str = Field(..., description="Syntactically valid Python Pytest test suite code")
    target_function: Optional[str] = Field(None, description="Primary function or behavior under test")
    covered_mutants: List[str] = Field(
        default_factory=list,
        description="IDs of supplied surviving mutants targeted by the generated tests"
    )
    test_rationale: str = Field(default="", description="Concise explanation of proposed test assertions and boundary checks")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made about input types and domain bounds")
    warnings: List[str] = Field(default_factory=list, description="Known test limitations or potential edge-case ambiguities")
    generation_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-sensitive metadata such as iteration, model, and AST verification status"
    )

    @model_validator(mode="after")
    def validate_test_code_not_empty(self) -> "GeneratedTestPayload":
        if not self.test_code or not self.test_code.strip():
            raise ValueError("Generated test_code cannot be empty or whitespace.")
        return self


class A2ATestGenerationRequestPayload(BaseModel):
    """Typed request payload sent to the Google ADK generator via A2A."""
    target_source_code: str = Field(..., description="Target Python source code under test")
    existing_test_code: Optional[str] = Field(None, description="Current Pytest code from SuiteSpace")
    surviving_diffs: List[str] = Field(default_factory=list, description="AST unified diffs of surviving mutants")
    surviving_mutants: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized surviving MutantRecords")
    critic_directive: Optional[str] = Field(None, description="Adversarial directives from CrewAI critic")
    iteration: int = Field(default=1, ge=1, description="Current reflection iteration index")
    target_function: Optional[str] = Field(None, description="Specific target function name if localized")


class A2AErrorPayload(BaseModel):
    """Standardized error payload returned on refusal or execution failure."""
    error: str = Field(..., description="Human-readable description of error or refusal")
    refusal_reason: Optional[str] = Field(None, description="Standardized refusal code (e.g. UNAUTHORIZED, PROMPT_INJECTION)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic metadata")


# ==============================================================================
# Phase 2 & 3: 8-Agent Modular Architecture Communication Contracts
# ==============================================================================

class CodeIntelligencePayload(BaseModel):
    """
    Structured code analysis findings produced by the Code Intelligence Agent.
    
    Producer Agent: Code Intelligence Agent (Google ADK + Python AST)
    Consumer Agent: Supervisor Agent (Google ADK), Test Planning Agent (Google ADK), Security Agent (Google ADK)
    """
    __test__ = False
    task_id: str = Field(..., description="Unique task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    target_module: str = Field(default="", description="Target Python module path or name")
    target_file_path: Optional[str] = Field(None, description="Filesystem path of the target file under test")
    source_sha: str = Field(default="", description="Cryptographic SHA-256 hash of the target source code")
    functions: List[Dict[str, Any]] = Field(default_factory=list, description="Discovered functions and signatures")
    classes: List[Dict[str, Any]] = Field(default_factory=list, description="Discovered classes and methods")
    branches: List[Dict[str, Any]] = Field(default_factory=list, description="Discovered branch points and conditional predicates")
    exception_paths: List[Dict[str, Any]] = Field(default_factory=list, description="Explicit exception raising/handling paths")
    dependencies: List[str] = Field(default_factory=list, description="External module and package imports")
    complexity_risk: Dict[str, Any] = Field(default_factory=dict, description="Cyclomatic complexity and blast radius assessment")
    suggested_testing_targets: List[str] = Field(default_factory=list, description="Prioritized functions/methods to test")
    analysis_status: Literal["SUCCESS", "PARTIAL", "FAILED", "SYNTAX_ERROR"] = Field(
        default="SUCCESS", description="Outcome of code intelligence analysis"
    )
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Detailed AST locations, line numbers, and metric evidence")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    agent_id: str = Field(default="agent:google-adk:code-intelligence", description="Identifier of analyzing agent")

    @model_validator(mode="after")
    def validate_code_intelligence_invariants(self) -> "CodeIntelligencePayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("CodeIntelligencePayload requires a non-empty task_id or job_id.")
        return self


class TestPlanPayload(BaseModel):
    """
    Structured test scenario plan generated by the Test Planning Agent.
    
    Producer Agent: Test Planning Agent (Google ADK)
    Consumer Agent: Supervisor Agent (Google ADK), Test Generation Agent (Google ADK), Reflection & Repair Agent (Google ADK)
    """
    __test__ = False
    task_id: str = Field(..., description="Unique task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    target_module: str = Field(..., description="Target Python module path or name")
    source_sha: str = Field(default="", description="Cryptographic SHA-256 hash of the target source code")
    target_file_path: Optional[str] = Field(None, description="Filesystem path of the target file under test")
    scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="Structured scenario specifications")
    boundary_targets: List[str] = Field(default_factory=list, description="Target boundary and edge-condition values")
    negative_cases: List[str] = Field(default_factory=list, description="Negative input and exception targets")
    mock_dependencies: List[str] = Field(default_factory=list, description="Dependencies or external interfaces requiring isolation/mocking")
    allocated_test_budget: int = Field(default=10, ge=1, description="Allocated target test count")
    planning_rationale: str = Field(default="", description="Architectural rationale for proposed test structure")
    status: Literal["PLANNED", "PARTIAL", "FAILED"] = Field(default="PLANNED", description="Planning status")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    planner_agent: str = Field(default="agent:google-adk:test-planner", description="Identifier of the planner agent")
    cot_reasoning_trace: List[Dict[str, Any]] = Field(default_factory=list, description="Step-by-step chain-of-thought boundary derivation trace")

    @model_validator(mode="after")
    def validate_plan_invariants(self) -> "TestPlanPayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("TestPlanPayload requires a non-empty task_id or job_id.")
        if not self.target_module or not self.target_module.strip():
            raise ValueError("TestPlanPayload requires a non-empty target_module.")
        if self.allocated_test_budget < 1:
            raise ValueError("allocated_test_budget must be at least 1.")
        return self


class TestExecutionPayload(BaseModel):
    """
    Structured test execution outcome and telemetry emitted by the Test Execution Agent.
    
    Producer Agent: Test Execution Agent (Google ADK + MCP Tools)
    Consumer Agent: Supervisor Agent (Google ADK), Mutation & Quality Critic Agent (CrewAI), Reflection & Repair Agent (Google ADK)
    """
    __test__ = False
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}", description="Unique execution run ID")
    task_id: str = Field(..., description="Associated task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    status: Literal["NOT_STARTED", "RUNNING", "PASSED", "FAILED", "ERROR", "TIMEOUT"] = Field(
        default="PASSED", description="Overall execution status"
    )
    total_tests: int = Field(default=0, ge=0, description="Total tests collected and executed")
    passed_tests: int = Field(default=0, ge=0, description="Tests passing cleanly")
    failed_tests: int = Field(default=0, ge=0, description="Tests failing assertions")
    skipped_tests: int = Field(default=0, ge=0, description="Tests skipped")
    error_tests: int = Field(default=0, ge=0, description="Tests producing syntax or collection errors")
    line_coverage_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Achieved line coverage percentage (0.0 to 100.0)")
    branch_coverage: float = Field(default=0.0, ge=0.0, le=100.0, description="Achieved branch coverage percentage (0.0 to 100.0)")
    branch_coverage_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Branch coverage percentage alias")
    total_branches: int = Field(default=0, ge=0, description="Total branch arcs identified")
    covered_branches: int = Field(default=0, ge=0, description="Covered branch arcs")
    missing_branches: List[Any] = Field(default_factory=list, description="Missing branch arcs details")
    lines_covered: int = Field(default=0, ge=0, description="Number of source lines executed")
    num_statements: int = Field(default=0, ge=0, description="Total statements in target module")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Execution duration in seconds")
    test_results: List[Dict[str, Any]] = Field(default_factory=list, description="Per-test status records")
    failures: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed failure traces and error messages")
    quarantined_tests: List[str] = Field(default_factory=list, description="Tests quarantined due to flakiness or errors")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    sandbox_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution runtime metadata (cores, workers, mode)")

    @model_validator(mode="after")
    def validate_execution_invariants(self) -> "TestExecutionPayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("TestExecutionPayload requires a non-empty task_id or job_id.")
        if self.line_coverage_pct < 0.0 or self.line_coverage_pct > 100.0:
            raise ValueError("line_coverage_pct must be between 0.0 and 100.0.")
        return self


class SecurityEvaluationPayload(BaseModel):
    """
    Continuous security assessment finding record emitted by the Security Agent.
    
    Producer Agent: Security Agent (Google ADK)
    Consumer Agent: Supervisor Agent (Google ADK), All Agents (gatekeeping tool/generation requests)
    """
    __test__ = False
    evaluation_id: str = Field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:8]}", description="Unique evaluation ID")
    task_id: str = Field(..., description="Associated task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    target_ref: str = Field(default="", description="Reference to evaluated file, prompt, or artifact")
    assessment_stage: Literal["INPUT_INSPECTION", "AST_SAFETY", "DIRECTIVE_SANITIZATION", "TOOL_PERMISSION"] = Field(
        default="INPUT_INSPECTION", description="Pipeline stage being audited"
    )
    status: Literal["PASSED", "WARNING", "BLOCKED", "REFUSED"] = Field(
        default="PASSED", description="Security verdict"
    )
    allowed: bool = Field(default=True, description="Whether operation is authorized to proceed")
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="SAFE", description="Assessed risk classification"
    )
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed security findings and rule violations")
    defused_text: Optional[str] = Field(None, description="Defused text if prompt injection was neutralized")
    redacted_credentials: List[str] = Field(default_factory=list, description="List of sensitive tokens/keys redacted")
    remediation_notes: Optional[str] = Field(None, description="Guidance for remediating detected issues")
    created_at: float = Field(default_factory=time.time, description="Timestamp of evaluation")
    evaluator_agent: str = Field(default="agent:google-adk:security", description="Identifier of security agent")

    @model_validator(mode="after")
    def validate_security_invariants(self) -> "SecurityEvaluationPayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("SecurityEvaluationPayload requires a non-empty task_id or job_id.")
        if self.status in ("BLOCKED", "REFUSED") and self.allowed:
            raise ValueError(f"When status is '{self.status}', allowed must be False.")
        return self


class MutationQualityCriticPayload(BaseModel):
    """
    Structured adversarial critique, mutation score verification, and test quality findings
    emitted by the Mutation & Quality Critic Agent (CrewAI).

    Producer Agent: Mutation & Quality Critic Agent (CrewAI)
    Consumer Agent: Supervisor Agent (Google ADK), Test Generation Agent (Google ADK),
                    Reflection & Repair Agent (Google ADK)
    """
    __test__ = False
    task_id: str = Field(..., description="Unique task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    source_sha: str = Field(default="", description="Cryptographic SHA-256 hash of the target source code")
    test_sha: str = Field(default="", description="Cryptographic SHA-256 hash of the test suite code")
    mutation_run_id: Optional[str] = Field(None, description="Identifier of the associated sandbox mutation run")
    mutation_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Measured mutation score percentage")
    denominator: int = Field(default=0, ge=0, description="Total actionable mutants (killed + survived + timed out)")
    killed_mutants: List[str] = Field(default_factory=list, description="IDs of confirmed killed mutants")
    survived_mutants: List[str] = Field(default_factory=list, description="IDs of surviving mutants")
    timed_out_mutants: List[str] = Field(default_factory=list, description="IDs of mutants causing execution timeout")
    invalid_mutants: List[str] = Field(default_factory=list, description="IDs of invalid or non-compiling mutants")
    equivalent_mutants: List[str] = Field(default_factory=list, description="IDs of confirmed or potentially equivalent mutants")
    assertion_quality_findings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Findings from AST test quality analysis (weak, tautological, or missing assertions)"
    )
    missing_scenario_findings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Discrepancies between planned scenarios and implemented test assertions"
    )
    recommended_improvements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Actionable, boundary-focused test modifications and new assertions"
    )
    directives: List[str] = Field(
        default_factory=list,
        description="Flat list of prescriptive test directives"
    )
    failure_mechanisms: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of mutant_id to verified root cause failure mechanism"
    )
    overall_quality_assessment: str = Field(default="", description="Executive quality diagnosis")
    test_quality_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Composite multi-dimensional Test Quality Score (TQS)")
    composite_tqs: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Composite multi-dimensional Test Quality Score (TQS) alias")
    quality_dimensions: Dict[str, float] = Field(default_factory=dict, description="Component dimensional scores (assertion strength, mutation effectiveness, etc.)")
    raw_dimensions: Dict[str, float] = Field(default_factory=dict, description="Raw component dimensional scores before composite weighting")
    tqs_weights: Dict[str, float] = Field(default_factory=dict, description="Weights used in TQS calculation")
    raw_mutation_score: Optional[float] = Field(default=None, description="Raw unadjusted mutation score")
    raw_branch_coverage: Optional[float] = Field(default=None, description="Raw measured branch coverage")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score in the evaluation (0.0 to 1.0)")
    evidence_references: Dict[str, Any] = Field(
        default_factory=dict,
        description="Traceability references (mutant line numbers, AST node types, diff snippets)"
    )
    should_iterate: bool = Field(default=False, description="Whether reflection loop should continue hardening")
    critic_agent: str = Field(default="agent:crewai:mutation-critic", description="Identifier of critic agent")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")

    @model_validator(mode="after")
    def validate_critic_invariants(self) -> "MutationQualityCriticPayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("MutationQualityCriticPayload requires a non-empty task_id or job_id.")
        if self.mutation_score < 0.0 or self.mutation_score > 100.0:
            raise ValueError("mutation_score must be between 0.0 and 100.0.")
        return self

    def to_directive_payload(self) -> CriticDirectivePayload:
        """Converts to a backward-compatible CriticDirectivePayload."""
        dirs = list(self.directives)
        for imp in self.recommended_improvements:
            if isinstance(imp, dict) and "directive" in imp:
                dirs.append(imp["directive"])
            elif isinstance(imp, str):
                dirs.append(imp)
        return CriticDirectivePayload(
            analysis=self.overall_quality_assessment or f"Critic analyzed {len(self.survived_mutants)} surviving mutant(s).",
            target_mutants=list(self.survived_mutants),
            directives=dirs,
            failure_mechanisms=dict(self.failure_mechanisms),
            raw_mutation_score=self.raw_mutation_score if self.raw_mutation_score is not None else self.mutation_score,
            raw_branch_coverage=self.raw_branch_coverage,
            raw_dimensions=self.raw_dimensions or self.quality_dimensions,
            composite_tqs=self.composite_tqs if self.composite_tqs is not None else self.test_quality_score,
        )


class RepairRequestPayload(BaseModel):
    """
    Targeted test assertion repair and mutant-killing request sent to the Reflection & Repair Agent.
    
    Producer Agent: Supervisor Agent (Google ADK) or Mutation & Quality Critic Agent (CrewAI)
    Consumer Agent: Reflection & Repair Agent (Google ADK)
    """
    request_id: str = Field(default_factory=lambda: f"rep_{uuid.uuid4().hex[:8]}", description="Unique repair request ID")
    task_id: str = Field(..., description="Associated task or job identifier")
    iteration: int = Field(default=1, ge=1, description="Current reflection loop iteration index")
    target_source_code: str = Field(..., description="Target Python source code under test")
    existing_test_code: str = Field(..., description="Current test code requiring repair or hardening")
    surviving_mutants: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized surviving MutantRecords")
    surviving_diffs: List[str] = Field(default_factory=list, description="AST unified diffs of surviving mutants")
    critic_directives: List[str] = Field(default_factory=list, description="Prescriptive directives formulated by the Critic")
    failing_tests: List[str] = Field(default_factory=list, description="Names of tests failing clean validation")
    target_mutation_score: float = Field(default=85.0, ge=0.0, le=100.0, description="Target mutation score percentage")
    current_mutation_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Current mutation score percentage")
    repair_strategy: Literal["ASSERTION_HARDENING", "BOUNDARY_SYNTHESIS", "QUARANTINE_REMOVAL", "REGRESSION_REPAIR"] = Field(
        default="ASSERTION_HARDENING", description="Targeted repair strategy"
    )

    @model_validator(mode="after")
    def validate_repair_invariants(self) -> "RepairRequestPayload":
        if not self.task_id or not self.task_id.strip():
            raise ValueError("RepairRequestPayload requires a non-empty task_id.")
        if not self.target_source_code or not self.target_source_code.strip():
            raise ValueError("RepairRequestPayload requires non-empty target_source_code.")
        if not self.existing_test_code or not self.existing_test_code.strip():
            raise ValueError("RepairRequestPayload requires non-empty existing_test_code.")
        return self


class RepairDirectivePayload(BaseModel):
    """
    Actionable, structured repair directives produced by the Reflection & Repair Agent.
    Instructs the Test Generation Agent on targeted assertions, boundary values,
    and quarantine removals without regenerating unaffected tests.

    Producer Agent: Reflection & Repair Agent (Google ADK)
    Consumer Agent: Test Generation Agent (Google ADK)
    """
    __test__ = False
    directive_id: str = Field(default_factory=lambda: f"dir_{uuid.uuid4().hex[:8]}", description="Unique directive ID")
    task_id: str = Field(..., description="Associated task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    iteration: int = Field(default=1, ge=1, description="Current reflection loop iteration index")
    strategy: Literal[
        "ASSERTION_HARDENING",
        "BOUNDARY_SYNTHESIS",
        "EXCEPTION_COVERAGE",
        "QUARANTINE_REMOVAL",
        "REGRESSION_REPAIR"
    ] = Field(default="ASSERTION_HARDENING", description="Primary repair strategy")
    target_function: Optional[str] = Field(None, description="Specific target function under repair")
    targeted_mutants: List[str] = Field(default_factory=list, description="IDs of surviving mutants to eliminate")
    missing_scenarios: List[str] = Field(default_factory=list, description="Specific missing scenarios from PlanSpace")
    prescribed_assertions: List[Dict[str, Any]] = Field(default_factory=list, description="Concrete boundary or invariant checks")
    failing_tests_to_quarantine: List[str] = Field(default_factory=list, description="Tests to remove or replace")
    rationale: str = Field(default="", description="Diagnostic rationale for the repair")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    created_at: float = Field(default_factory=time.time, description="Timestamp of directive creation")

    @model_validator(mode="after")
    def validate_directive_invariants(self) -> "RepairDirectivePayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("RepairDirectivePayload requires a non-empty task_id or job_id.")
        return self


class RepairResultPayload(BaseModel):
    """
    Verification outcome of a repair iteration emitted by the Reflection & Repair Agent.
    Guarantees strict non-regression: candidates are rejected if mutation score, coverage,
    or execution validity decreases compared to the best verified suite.

    Producer Agent: Reflection & Repair Agent (Google ADK)
    Consumer Agent: Supervisor Agent (Google ADK), Orchestrator
    """
    __test__ = False
    repair_id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}", description="Unique repair result ID")
    task_id: str = Field(..., description="Associated task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    iteration: int = Field(default=1, ge=1, description="Current reflection loop iteration index")
    source_sha: str = Field(default="", description="SHA-256 hash of target source code")
    previous_test_sha: str = Field(default="", description="SHA-256 hash of previous verified test suite")
    candidate_test_sha: str = Field(default="", description="SHA-256 hash of candidate repaired test suite")
    accepted: bool = Field(default=False, description="Whether candidate suite was accepted as new best verified suite")
    rejection_reason: Optional[str] = Field(None, description="Detailed explanation if candidate was rejected")
    previous_mutation_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Mutation score prior to repair")
    candidate_mutation_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Measured mutation score of candidate")
    previous_test_count: int = Field(default=0, ge=0, description="Test count before repair")
    candidate_test_count: int = Field(default=0, ge=0, description="Test count in candidate suite")
    previous_line_coverage: float = Field(default=0.0, ge=0.0, le=100.0, description="Line coverage % before repair")
    candidate_line_coverage: float = Field(default=0.0, ge=0.0, le=100.0, description="Line coverage % of candidate suite")
    retained_test_code: str = Field(default="", description="Verified test suite code retained after comparison")
    mutants_killed: List[str] = Field(default_factory=list, description="Mutant IDs confirmed killed by the repair")
    quarantined_tests: List[str] = Field(default_factory=list, description="Failing or invalid tests quarantined during repair")
    should_iterate: bool = Field(default=False, description="Whether further reflection iterations are recommended")
    stop_reason: Optional[str] = Field(None, description="Reason if reflection loop should stop")
    created_at: float = Field(default_factory=time.time, description="Timestamp of evaluation")

    @model_validator(mode="after")
    def validate_result_invariants(self) -> "RepairResultPayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("RepairResultPayload requires a non-empty task_id or job_id.")
        return self


class ReflectionDecisionPayload(BaseModel):
    """
    High-level decision emitted by the Reflection & Repair Agent regarding
    loop convergence, stopping conditions, or remediation priorities.
    """
    __test__ = False
    decision_id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}", description="Unique decision ID")
    task_id: str = Field(..., description="Associated task or job identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    iteration: int = Field(default=1, ge=1, description="Current reflection iteration index")
    decision: Literal["CONTINUE_REPAIR", "STOP_TARGET_REACHED", "STOP_MAX_ITERATIONS", "STOP_NO_IMPROVEMENT", "STOP_CANCELLED"] = Field(
        default="CONTINUE_REPAIR", description="Categorical reflection decision"
    )
    should_repair: bool = Field(default=True, description="Whether a repair attempt should proceed")
    rationale: str = Field(default="", description="Reasoning supporting the decision")
    targeted_mutants: List[str] = Field(default_factory=list, description="Prioritized surviving mutants to target")
    evidence_references: Dict[str, Any] = Field(default_factory=dict, description="Traceability references")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")


class WorkflowStage(str, Enum):
    """Authoritative workflow stages governing TestForge multi-agent execution."""
    INITIALIZING = "INITIALIZING"
    SECURITY_SCREENING = "SECURITY_SCREENING"
    CODE_INTELLIGENCE = "CODE_INTELLIGENCE"
    TEST_PLANNING = "TEST_PLANNING"
    TEST_GENERATION = "TEST_GENERATION"
    BASELINE_EXECUTION = "BASELINE_EXECUTION"
    MUTATION_ANALYSIS = "MUTATION_ANALYSIS"
    CRITIC_ASSESSMENT = "CRITIC_ASSESSMENT"
    REFLECTION_REPAIR = "REFLECTION_REPAIR"
    CONVERGED = "CONVERGED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SupervisorAction(str, Enum):
    """Permitted discrete workflow actions issued by the Top-Level Supervisor Agent."""
    SCREEN_SECURITY = "SCREEN_SECURITY"
    ANALYZE_CODE = "ANALYZE_CODE"
    PLAN_TESTS = "PLAN_TESTS"
    GENERATE_TESTS = "GENERATE_TESTS"
    EXECUTE_TESTS = "EXECUTE_TESTS"
    EVALUATE_CRITIQUE = "EVALUATE_CRITIQUE"
    REFLECT_AND_REPAIR = "REFLECT_AND_REPAIR"
    RETRY_STEP = "RETRY_STEP"
    STOP_CONVERGED = "STOP_CONVERGED"
    STOP_MAX_ITERATIONS = "STOP_MAX_ITERATIONS"
    STOP_CANCELLED = "STOP_CANCELLED"
    STOP_SECURITY_REFUSAL = "STOP_SECURITY_REFUSAL"
    STOP_UNRECOVERABLE_FAILURE = "STOP_UNRECOVERABLE_FAILURE"


class SupervisorDecisionPayload(BaseModel):
    """
    Strongly-typed decision contract emitted by the Google ADK Top-Level Supervisor Agent.
    Dictates the next permitted specialist agent action, validates workflow transitions,
    and enforces authoritative deterministic policies over LLM reasoning.

    Producer Agent: Supervisor Agent (Google ADK)
    Consumer Agent: TestForgeOrchestrator, A2ABroker, Wiretap
    """
    __test__ = False
    decision_id: str = Field(default_factory=lambda: f"sup_dec_{uuid.uuid4().hex[:8]}", description="Unique decision ID")
    task_id: str = Field(..., description="Associated task identifier")
    job_id: Optional[str] = Field(None, description="Job identifier alias")
    current_stage: str = Field(default="INITIALIZING", description="Current workflow stage name")
    selected_action: str = Field(..., description="Selected next workflow action")
    target_agent: str = Field(..., description="Target specialist agent assigned to execute action")
    reason: str = Field(default="", description="Explanatory rationale for the decision")
    required_inputs: List[str] = Field(default_factory=list, description="Required input keys/references")
    expected_output: str = Field(default="", description="Expected output artifact description")
    evidence_references: Dict[str, Any] = Field(default_factory=dict, description="References to supporting evidence")
    decision_timestamp: float = Field(default_factory=time.time, description="Timestamp of decision creation")
    is_deterministic: bool = Field(default=True, description="Whether decision was derived from deterministic policy vs model deliberation")
    iteration: int = Field(default=0, ge=0, description="Current workflow iteration number")
    retry_count: int = Field(default=0, ge=0, description="Retry count for the current step")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Supplemental decision metadata")

    @model_validator(mode="after")
    def validate_supervisor_invariants(self) -> "SupervisorDecisionPayload":
        if not self.task_id and self.job_id:
            self.task_id = self.job_id
        elif self.task_id and not self.job_id:
            self.job_id = self.task_id
        if not self.task_id or not self.task_id.strip():
            raise ValueError("SupervisorDecisionPayload requires a non-empty task_id or job_id.")
        return self


class WorkflowTransitionRecord(BaseModel):
    """Structured audit trail record for state transitions validated by the Supervisor."""
    __test__ = False
    transition_id: str = Field(default_factory=lambda: f"trans_{uuid.uuid4().hex[:8]}")
    from_stage: str
    to_stage: str
    action: str
    allowed: bool
    reason: str = ""
    timestamp: float = Field(default_factory=time.time)


# ==============================================================================
# 3. Agent Handler Registration Model
# ==============================================================================

class AgentHandlerRegistration:
    """Internal registration model for named A2A agent handlers."""
    def __init__(
        self,
        agent_id: str,
        handler: Callable[[A2AMessage], A2AMessage],
        allowed_actions: Optional[Set[str]] = None,
        allowed_senders: Optional[Set[str]] = None,
        description: str = "",
    ):
        self.agent_id = agent_id
        self.handler = handler
        self.allowed_actions = allowed_actions
        self.allowed_senders = allowed_senders
        self.description = description

    def is_action_allowed(self, action: str) -> bool:
        if self.allowed_actions is None:
            return True
        return action in self.allowed_actions

    def is_sender_allowed(self, sender: str) -> bool:
        if self.allowed_senders is None:
            return True
        return sender in self.allowed_senders


# ==============================================================================
# 4. A2A Message Broker Implementation
# ==============================================================================

class A2ABroker:
    """
    In-process A2A Message Broker for multi-agent coordination.

    Features:
      - Validates all incoming and outgoing envelopes via Pydantic.
      - Authorizes sender, recipient, and action permissions.
      - Enforces input security guardrails (prompt injection inspection).
      - Executes agent handlers inside bounded timeouts.
      - Emits typed lifecycle callback events for handoffs and errors.
      - Synchronizes validated critique results to Blackboard CriticSpace.
      - Guarantees deep-copy isolation preventing accidental message mutation.
      - Redacts credentials and sensitive tokens from history and logs.
    """
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        callback_registry: Optional[CallbackRegistry] = None,
        security_guardrail: Optional[SecurityGuardrail] = None,
        default_timeout_sec: float = 45.0,
    ):
        self._blackboard = blackboard
        self._callbacks = callback_registry
        self._security = security_guardrail or SecurityGuardrail()
        self._default_timeout_sec = default_timeout_sec
        self._handlers: Dict[str, AgentHandlerRegistration] = {}
        self._history: List[A2AMessage] = []
        self._lock = threading.RLock()

    # --------------------------------------------------------------------------
    # Registration Management
    # --------------------------------------------------------------------------

    def register_handler(
        self,
        agent_id: str,
        handler: Callable[[A2AMessage], A2AMessage],
        allowed_actions: Optional[Union[List[str], Set[str]]] = None,
        allowed_senders: Optional[Union[List[str], Set[str]]] = None,
        description: str = "",
    ) -> None:
        """Registers a named agent handler with authorization policies."""
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be a non-empty string.")
        if not callable(handler):
            raise TypeError(f"Handler for agent '{agent_id}' must be callable.")

        actions_set = set(allowed_actions) if allowed_actions is not None else None
        senders_set = set(allowed_senders) if allowed_senders is not None else None

        with self._lock:
            self._handlers[agent_id] = AgentHandlerRegistration(
                agent_id=agent_id,
                handler=handler,
                allowed_actions=actions_set,
                allowed_senders=senders_set,
                description=description,
            )
            logger.info(f"Registered A2A agent handler: '{agent_id}' (actions={actions_set})")

    def unregister_handler(self, agent_id: str) -> bool:
        """Unregisters a previously registered agent handler."""
        with self._lock:
            if agent_id in self._handlers:
                del self._handlers[agent_id]
                logger.info(f"Unregistered A2A agent handler: '{agent_id}'")
                return True
            return False

    def list_handlers(self) -> List[str]:
        """Returns registered agent handler IDs."""
        with self._lock:
            return list(self._handlers.keys())

    # --------------------------------------------------------------------------
    # Message Dispatch & Execution
    # --------------------------------------------------------------------------

    def send_message(
        self,
        message: A2AMessage,
        timeout_sec: Optional[float] = None,
    ) -> A2AMessage:
        """
        Dispatches an A2AMessage through authorization, security inspection,
        handler execution with timeout, and Blackboard synchronization.
        """
        if not isinstance(message, A2AMessage):
            raise TypeError(f"Expected A2AMessage instance, got {type(message).__name__}")

        timeout = timeout_sec if timeout_sec is not None else self._default_timeout_sec

        # 1. Store defensive copy of incoming request
        in_msg = message.model_copy(deep=True)
        self._record_message(in_msg)

        # 2. Authorize Recipient
        with self._lock:
            registration = self._handlers.get(in_msg.recipient)

        if not registration:
            err_msg = f"Recipient agent '{in_msg.recipient}' is not registered."
            logger.warning(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "recipient": in_msg.recipient},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.REFUSE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="UNREGISTERED_RECIPIENT",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # 3. Authorize Sender
        if not registration.is_sender_allowed(in_msg.sender):
            err_msg = f"Sender '{in_msg.sender}' is not authorized to contact '{in_msg.recipient}'."
            logger.warning(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "sender": in_msg.sender, "recipient": in_msg.recipient},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.REFUSE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="UNAUTHORIZED_SENDER",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # 4. Authorize Action
        if not registration.is_action_allowed(in_msg.action):
            err_msg = f"Action '{in_msg.action}' is not permitted for recipient '{in_msg.recipient}'."
            logger.warning(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "action": in_msg.action, "recipient": in_msg.recipient},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.REFUSE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="UNAUTHORIZED_ACTION",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # 5. Security Guardrail Inspection (Prompt Injection)
        prompt_inspection_text = self._extract_text_for_security_scan(in_msg.payload)
        if prompt_inspection_text:
            sec_res = self._security.inspect_prompt(prompt_inspection_text)
            if not sec_res.allowed:
                reason = f"Security guardrail rejected message payload: {sec_res.explanation}"
                logger.warning(f"A2ABroker blocked message due to security violation: {reason}")
                findings_dump = [f.model_dump() for f in sec_res.findings]
                self._dispatch_callback(
                    EventType.ERROR,
                    emitter="broker:security",
                    payload={"error": reason, "findings": findings_dump},
                )
                resp = in_msg.create_response(
                    performative=A2APerformative.REFUSE,
                    payload=A2AErrorPayload(
                        error=reason,
                        refusal_reason="PROMPT_INJECTION_DETECTED",
                        details={"findings": findings_dump, "risk_level": sec_res.risk_level.value},
                    ).model_dump(),
                    action=in_msg.action,
                )
                self._record_message(resp)
                return resp

        # 6. Dispatch AGENT_HANDOFF start event
        self._dispatch_callback(
            EventType.AGENT_HANDOFF,
            emitter="broker",
            payload={
                "from_agent": in_msg.sender,
                "to_agent": in_msg.recipient,
                "action": in_msg.action,
                "correlation_id": in_msg.correlation_id,
                "summary": f"Dispatching '{in_msg.action}' to '{in_msg.recipient}'",
            },
        )

        # 7. Execute Handler with Bounded Timeout
        t0 = time.perf_counter()
        raw_response: Optional[A2AMessage] = None

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(registration.handler, in_msg.model_copy(deep=True))
                raw_response = future.result(timeout=timeout)
        except FuturesTimeoutError:
            err_msg = f"Handler execution for '{in_msg.recipient}' timed out after {timeout:.2f}s."
            logger.error(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "timeout_sec": timeout},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.FAILURE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="TIMEOUT",
                    details={"timeout_sec": timeout},
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp
        except Exception as exc:
            safe_err = redact_sensitive_data(str(exc))
            err_msg = f"Handler for '{in_msg.recipient}' raised unhandled exception: {safe_err}"
            logger.error(err_msg, exc_info=True)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.FAILURE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="HANDLER_EXCEPTION",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        elapsed_sec = time.perf_counter() - t0

        # 8. Validate Response Envelope
        if not isinstance(raw_response, A2AMessage):
            err_msg = f"Handler returned invalid object of type {type(raw_response).__name__}, expected A2AMessage."
            logger.error(err_msg)
            resp = in_msg.create_response(
                performative=A2APerformative.FAILURE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="INVALID_RESPONSE_TYPE",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # Guarantee correlation ID match
        if raw_response.correlation_id != in_msg.correlation_id:
            logger.warning(
                f"Handler changed correlation_id from '{in_msg.correlation_id}' to "
                f"'{raw_response.correlation_id}'. Overriding to enforce correlation invariant."
            )
            raw_response.correlation_id = in_msg.correlation_id

        # 9. Blackboard Partition Synchronization (CriticSpace, SuiteSpace, PlanSpace, ExecutionSpace, SecuritySpace)
        if (
            self._blackboard is not None
            and raw_response.performative == A2APerformative.INFORM
        ):
            if in_msg.recipient in ("agent:crewai:critic", "agent:crewai:mutation-critic"):
                self._sync_critique_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:generator", "agent:adk:generator"):
                self._sync_generator_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:test-planner", "agent:adk:planner", "agent:test-planner"):
                self._sync_planner_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:test-execution", "agent:adk:execution", "agent:test-execution"):
                self._sync_execution_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:security", "agent:adk:security", "agent:security"):
                self._sync_security_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:code-intelligence", "agent:adk:code-intelligence", "agent:code-intelligence"):
                self._sync_code_intelligence_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:reflection-repair", "agent:adk:reflection-repair", "agent:reflection-repair"):
                self._sync_reflection_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:supervisor", "agent:adk:supervisor", "agent:supervisor"):
                self._sync_supervisor_to_blackboard(raw_response)

        # 10. Dispatch Success Event
        self._dispatch_callback(
            EventType.OPERATION_COMPLETE,
            emitter="broker",
            payload={
                "operation_name": f"a2a_{in_msg.action}",
                "status": raw_response.performative.value,
                "duration_sec": elapsed_sec,
                "correlation_id": in_msg.correlation_id,
            },
        )

        resp_copy = raw_response.model_copy(deep=True)
        self._record_message(resp_copy)
        return resp_copy

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------

    def _sync_critique_to_blackboard(self, response: A2AMessage) -> None:
        """Validates critique payload and safely updates Blackboard CriticSpace."""
        try:
            payload_data = response.payload

            # Check if payload contains MutationQualityCriticPayload directly
            is_mutation_payload = (
                isinstance(payload_data, dict)
                and (
                    "overall_quality_assessment" in payload_data
                    or "killed_mutants" in payload_data
                    or "mutation_run_id" in payload_data
                    or ("mutation_score" in payload_data and "denominator" in payload_data)
                )
            )

            if is_mutation_payload:
                mut_obj = MutationQualityCriticPayload.model_validate(payload_data)
                primary_directive = mut_obj.overall_quality_assessment
                if mut_obj.directives:
                    directives_list = "\n".join(f"- {d}" for d in mut_obj.directives)
                    primary_directive = (
                        f"{primary_directive}\n\nPrescribed Directives:\n{directives_list}"
                        if primary_directive
                        else directives_list
                    )

                existing_critic = self._blackboard.get_critic_space()
                new_directives = list(existing_critic.critic_directives)
                if primary_directive:
                    new_directives.append(primary_directive)

                new_mechanisms = dict(existing_critic.failure_mechanisms)
                new_mechanisms.update(mut_obj.failure_mechanisms)

                new_notes = list(existing_critic.reflection_notes)
                new_notes.append(
                    f"CrewAI MutationQualityCritic analyzed {len(mut_obj.survived_mutants)} surviving mutant(s), "
                    f"score: {mut_obj.mutation_score:.1f}% (correlation: {response.correlation_id})"
                )

                self._blackboard.update_critic_space(
                    latest_directive=primary_directive or "Quality critique completed",
                    critic_directives=new_directives,
                    failure_mechanisms=new_mechanisms,
                    reflection_notes=new_notes,
                    job_id=mut_obj.job_id or mut_obj.task_id,
                    mutation_run_id=mut_obj.mutation_run_id,
                    mutation_score=mut_obj.mutation_score,
                    quality_assessment=mut_obj.overall_quality_assessment,
                    assertion_quality_findings=mut_obj.assertion_quality_findings,
                    missing_scenario_findings=mut_obj.missing_scenario_findings,
                    recommended_improvements=mut_obj.recommended_improvements,
                    should_iterate=mut_obj.should_iterate,
                    overall_verdict="ACTIONABLE" if mut_obj.should_iterate else "SATISFIED",
                    critic_agent=mut_obj.critic_agent,
                    evaluated_at=time.time(),
                )
                logger.info("Synchronized validated CrewAI MutationQualityCriticPayload to Blackboard CriticSpace.")
                return

            # Check if payload contains CriticDirectivePayload directly or nested
            if "directive" in payload_data and isinstance(payload_data["directive"], dict):
                directive_obj = CriticDirectivePayload.model_validate(payload_data["directive"])
            else:
                directive_obj = CriticDirectivePayload.model_validate(payload_data)

            # Format directive string
            primary_directive = directive_obj.analysis
            if directive_obj.directives:
                directives_list = "\n".join(f"- {d}" for d in directive_obj.directives)
                primary_directive = f"{primary_directive}\n\nPrescribed Directives:\n{directives_list}"

            # Safely fetch existing critic space
            existing_critic = self._blackboard.get_critic_space()
            new_directives = list(existing_critic.critic_directives)
            if primary_directive:
                new_directives.append(primary_directive)

            new_mechanisms = dict(existing_critic.failure_mechanisms)
            new_mechanisms.update(directive_obj.failure_mechanisms)

            new_notes = list(existing_critic.reflection_notes)
            new_notes.append(
                f"CrewAI Critic analyzed {len(directive_obj.target_mutants)} mutant(s) "
                f"(correlation: {response.correlation_id})"
            )

            # Update Blackboard CriticSpace atomically
            self._blackboard.update_critic_space(
                latest_directive=primary_directive,
                critic_directives=new_directives,
                failure_mechanisms=new_mechanisms,
                reflection_notes=new_notes,
            )
            logger.info("Synchronized validated CrewAI critique to Blackboard CriticSpace.")
        except ValidationError as val_err:
            logger.error(f"Failed to validate CriticDirectivePayload for Blackboard sync: {val_err}")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing critique to Blackboard: {exc}", exc_info=True)

    def _sync_generator_to_blackboard(self, response: A2AMessage) -> None:
        """Validates generated test payload and safely updates Blackboard SuiteSpace."""
        try:
            from testforge.agents import CodeSanitizer
            payload_data = response.payload
            test_code = payload_data.get("test_code", "")
            if not test_code or not isinstance(test_code, str):
                logger.error("Generated test payload missing 'test_code' string for Blackboard sync.")
                return

            is_valid, sanitized_code, err = CodeSanitizer.extract_and_validate(test_code, enforce_security=True)
            if not is_valid:
                logger.error(f"Generated test code failed AST validation/security inspection: {err}")
                return

            existing_current = self._blackboard.get_suite_space().current_test_code
            updates = {
                "candidate_test_code": sanitized_code,
                "active_provider": "Google ADK Generator",
            }
            # Only populate current_test_code if no accepted suite exists yet (initial baseline).
            # If an accepted suite already exists, it must NOT be overwritten until validated.
            if not existing_current or not existing_current.strip():
                updates["current_test_code"] = sanitized_code

            self._blackboard.update_suite_space(**updates)
            logger.info("Synchronized candidate Google ADK test code to Blackboard SuiteSpace.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing generator output to Blackboard: {exc}", exc_info=True)

    def _sync_planner_to_blackboard(self, response: A2AMessage) -> None:
        """Validates test plan payload and updates Blackboard PlanSpace."""
        try:
            payload_data = response.payload
            plan = TestPlanPayload.model_validate(payload_data)
            self._blackboard.update_plan_space(
                task_id=plan.task_id,
                source_module=plan.target_module,
                source_sha=plan.source_sha,
                target_file_path=plan.target_file_path,
                scenarios=plan.scenarios,
                boundary_conditions=plan.boundary_targets,
                negative_cases=plan.negative_cases,
                allocated_test_budget=plan.allocated_test_budget,
                strategy_notes=plan.planning_rationale,
                planning_status="PLANNED",
                planner_agent=plan.planner_agent,
            )
            logger.info(f"Synchronized TestPlanPayload ({len(plan.scenarios)} scenarios) to Blackboard PlanSpace.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing plan to Blackboard: {exc}", exc_info=True)

    def _sync_execution_to_blackboard(self, response: A2AMessage) -> None:
        """Validates test execution payload and updates Blackboard ExecutionSpace."""
        try:
            payload_data = response.payload
            exec_res = TestExecutionPayload.model_validate(payload_data)
            self._blackboard.update_execution_space(
                execution_id=exec_res.execution_id,
                task_id=exec_res.task_id,
                status=exec_res.status,
                total_tests=exec_res.total_tests,
                passed_tests=exec_res.passed_tests,
                failed_tests=exec_res.failed_tests,
                skipped_tests=exec_res.skipped_tests,
                error_tests=exec_res.error_tests,
                line_coverage_pct=exec_res.line_coverage_pct,
                branch_coverage=exec_res.branch_coverage,
                branch_coverage_pct=exec_res.branch_coverage_pct or exec_res.branch_coverage,
                total_branches=exec_res.total_branches,
                covered_branches=exec_res.covered_branches,
                missing_branches=exec_res.missing_branches,
                lines_covered=exec_res.lines_covered,
                duration_seconds=exec_res.duration_seconds,
                failures=exec_res.failures,
                quarantined_tests=exec_res.quarantined_tests,
                stdout=exec_res.stdout,
                stderr=exec_res.stderr,
                sandbox_metadata=exec_res.sandbox_metadata,
            )
            logger.info(f"Synchronized TestExecutionPayload ({exec_res.passed_tests}/{exec_res.total_tests} passed) to Blackboard ExecutionSpace.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing execution results to Blackboard: {exc}", exc_info=True)

    def _sync_security_to_blackboard(self, response: A2AMessage) -> None:
        """Validates security evaluation payload and updates Blackboard SecuritySpace."""
        try:
            payload_data = response.payload
            sec_res = SecurityEvaluationPayload.model_validate(payload_data)
            self._blackboard.update_security_space(
                assessment_id=sec_res.evaluation_id,
                task_id=sec_res.task_id,
                status=sec_res.status,
                risk_level=sec_res.risk_level,
                allowed=sec_res.allowed,
                applied_policies=[sec_res.assessment_stage],
                findings=sec_res.findings,
                defused_injection_count=1 if sec_res.defused_text else 0,
                redacted_secret_count=len(sec_res.redacted_credentials),
                remediation_recommendations=[sec_res.remediation_notes] if sec_res.remediation_notes else [],
                evaluator_agent=sec_res.evaluator_agent,
            )
            logger.info(f"Synchronized SecurityEvaluationPayload (verdict: {sec_res.status}) to Blackboard SecuritySpace.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing security evaluation to Blackboard: {exc}", exc_info=True)

    def _sync_code_intelligence_to_blackboard(self, response: A2AMessage) -> None:
        """Validates code intelligence payload and updates Blackboard TargetSpace and PlanSpace."""
        try:
            payload_data = response.payload
            intel = CodeIntelligencePayload.model_validate(payload_data)
            func_names = [f["name"] if isinstance(f, dict) and "name" in f else str(f) for f in intel.functions]
            class_names = [c["name"] if isinstance(c, dict) and "name" in c else str(c) for c in intel.classes]
            blast_risk = intel.complexity_risk.get("risk_category", "LOW")

            self._blackboard.update_target_space(
                functions=func_names,
                classes=class_names,
                dependencies=intel.dependencies,
                blast_risk=blast_risk,
                source_sha=intel.source_sha,
                target_file_path=intel.target_file_path,
                branches=intel.branches,
                exception_paths=[p["exception_type"] if isinstance(p, dict) and "exception_type" in p else str(p) for p in intel.exception_paths],
                complexity_risk=intel.complexity_risk,
                suggested_testing_targets=intel.suggested_testing_targets,
            )
            # If boundary conditions were identified, seed them into PlanSpace
            boundary_conditions = []
            for b in intel.branches:
                if isinstance(b, dict) and b.get("boundary_values"):
                    boundary_conditions.extend([str(v) for v in b["boundary_values"]])
            if boundary_conditions:
                self._blackboard.update_plan_space(
                    task_id=intel.task_id,
                    source_module=intel.target_module or "target",
                    boundary_conditions=list(dict.fromkeys(boundary_conditions)),
                )
            logger.info(f"Synchronized CodeIntelligencePayload ({len(func_names)} functions, {len(intel.branches)} branches) to Blackboard.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing code intelligence to Blackboard: {exc}", exc_info=True)

    def _sync_reflection_to_blackboard(self, response: A2AMessage) -> None:
        """Validates repair result payload and safely updates Blackboard SuiteSpace."""
        try:
            payload_data = response.payload
            if not isinstance(payload_data, dict):
                return
            if "accepted" in payload_data or "retained_test_code" in payload_data:
                res_obj = RepairResultPayload.model_validate(payload_data)
                if res_obj.accepted and res_obj.retained_test_code:
                    self._blackboard.update_suite_space(
                        current_test_code=res_obj.retained_test_code,
                        hardened_test_code=res_obj.retained_test_code,
                        candidate_test_code="",
                        active_provider="Google ADK Reflection & Repair",
                    )
                    logger.info(f"Synchronized accepted repaired test suite ({res_obj.candidate_test_count} tests, score: {res_obj.candidate_mutation_score:.1f}%) to Blackboard.")
                else:
                    logger.info(f"Reflection repair candidate was rejected ({res_obj.rejection_reason}). Preserving verified suite.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing repair result to Blackboard: {exc}", exc_info=True)

    def _sync_supervisor_to_blackboard(self, response: A2AMessage) -> None:
        """Validates supervisor decision payload and safely updates Blackboard MetricsSpace."""
        try:
            payload_data = response.payload
            if not isinstance(payload_data, dict):
                return
            if "selected_action" in payload_data or "current_stage" in payload_data:
                dec = SupervisorDecisionPayload.model_validate(payload_data)
                if hasattr(self._blackboard, "record_supervisor_decision"):
                    self._blackboard.record_supervisor_decision(dec)
                logger.info(f"Synchronized Supervisor decision ({dec.selected_action} -> {dec.target_agent}) to Blackboard.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing supervisor decision to Blackboard: {exc}", exc_info=True)

    def _extract_text_for_security_scan(self, payload: Dict[str, Any]) -> str:
        """Extracts text candidate fields from payload to inspect for prompt injection."""
        text_parts = []
        for key in ("target_source_code", "analysis", "directive", "prompt", "text", "context"):
            val = payload.get(key)
            if isinstance(val, str):
                text_parts.append(val)
        # Also inspect directive lists
        directives = payload.get("directives")
        if isinstance(directives, list):
            for d in directives:
                if isinstance(d, str):
                    text_parts.append(d)
        return "\n\n".join(text_parts)

    def _dispatch_callback(self, event_type: EventType, emitter: str, payload: Dict[str, Any]) -> None:
        """Safely dispatches lifecycle callbacks without allowing subscriber exceptions to escape."""
        if not self._callbacks:
            return
        try:
            event = LifecycleEvent(
                event_type=event_type,
                emitter=emitter,
                payload=_scrub_value(copy.deepcopy(payload)),
            )
            self._callbacks.dispatch(event)
        except Exception as exc:
            logger.warning(f"A2ABroker failed to dispatch callback event {event_type}: {exc}")

    def _record_message(self, msg: A2AMessage) -> None:
        """Records scrubbed message into broker history."""
        with self._lock:
            self._history.append(msg.scrubbed_copy())

    def get_history(self) -> List[A2AMessage]:
        """Returns deep-copied immutable history of dispatched messages."""
        with self._lock:
            return [m.model_copy(deep=True) for m in self._history]

    def clear_history(self) -> None:
        """Clears message history."""
        with self._lock:
            self._history.clear()
