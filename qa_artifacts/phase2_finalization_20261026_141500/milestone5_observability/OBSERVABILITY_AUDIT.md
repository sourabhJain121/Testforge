# Milestone 5: Observability & Provenance Audit Report

**Date:** 2026-10-26  
**Artifact Directory:** `qa_artifacts/phase2_finalization_20261026_141500/milestone5_observability/`  
**Auditor:** TestForge Core Engineering  

---

## 1. Executive Summary

TestForge's observability, tracing, and provenance architecture was audited against production engineering standards:
1. Structured JSONL logging with persistent correlation IDs and workflow identifiers across all agents.
2. Lifecycle state events: CREATED, QUEUED, RUNNING, CANCELLED, TIMED_OUT, COMPLETED, FAILED.
3. Fine-grained mutant provenance linking each mutant to mutation operator, AST diff, surviving guidance, candidate test, sandbox execution, and kill status.
4. Model vs. Fallback attribution: Distinguishes between live model providers (`gemini-2.5`, `qwen2.5-coder:7b`) and deterministic synthesis fallbacks (`OFFLINE_DETERMINISTIC_SYNTHESIS`, `DETERMINISTIC_BASELINE`).
5. Real-time streaming via WebSocket hub (`/ws/events`).
6. Zero credential leakage: Automatic regex-based scrubbing of secrets before trace persistence.
7. Observer fault isolation: Logging handler or callback failures cannot disrupt the primary pipeline.

---

## 2. Observability Subsystems & Architecture

### 2.1 TraceLogger & Structured Records (`testforge/logger.py`)
- Standardized schema for all trace events:
  - `timestamp`: Epoch floating point timestamp.
  - `workflow_id`: Unique identifier per hardening session or benchmark run.
  - `correlation_id`: Stable identifier propagating across agent-to-agent deliberations.
  - `event_type`: Typed enum (`OPERATION_START`, `AGENT_START`, `AGENT_COMPLETE`, `SECURITY_REFUSAL`, `VALIDATION_FAILURE`, `WORKFLOW_OUTCOME`).
  - `emitter`: Name of the emitting component (`TestForgeOrchestrator`, `TestGeneratorAgent`, `AdversarialCriticAgent`, `FastMCPServer`).
  - `payload`: Structured dictionary with scrubbed parameters, duration, and metrics.

### 2.2 Lifecycle State Transitions (`testforge/state.py`)
- Managed by `TaskLifecycleState` state machine:
  - `CREATED` -> Initial job definition.
  - `QUEUED` -> Awaiting worker thread execution in background pool.
  - `RUNNING` -> Active orchestration across pipeline stages (AST analysis, test synthesis, mutation evaluation, reflection).
  - `COMPLETED` -> Successful target score attainment or loop completion.
  - `CANCELLED` -> User requested cooperative cancellation.
  - `TIMED_OUT` -> Bounded execution limit reached.
  - `FAILED` -> Unrecoverable exception caught and recorded.

### 2.3 Mutant Provenance Architecture (`testforge/state.py`, `testforge/sandbox.py`)
- Each evaluated mutant maintains complete lifecycle provenance:
  - `mutant_id`: Stable hash identifier (e.g. `MUT-TASK-001`).
  - `operator`: AST mutation rule applied (`BinOp`, `Compare`, `Constant`, `IfCondition`).
  - `lineno` / `col_offset`: Exact line and column coordinates in the target code.
  - `original_source` vs `mutated_source`: Concrete AST diff.
  - `surviving_guidance`: Synthesized adversary directives from `AdversarialCriticAgent`.
  - `killing_test`: Specific candidate test function that killed the mutant (or `None` if survived).
  - `status`: `KILLED`, `SURVIVED`, `EQUIVALENT`, or `INVALID`.

### 2.4 Model Attribution & Integrity
- Benchmark and trace logs record the actual generator mode:
  - Live model execution records `model_name` (e.g., `Local Ollama:qwen2.5-coder:7b`) and token counts.
  - Fallback execution explicitly records `execution_mode: "OFFLINE_DETERMINISTIC_SYNTHESIS"` and disclaimer noting zero live tokens consumed.
  - Never fabricates token usage or falsely claims live LLM generation.

---

## 3. Audit Findings & Verification Status

| Ref ID | Observability Dimension | Requirement | Implementation Evidence | Status |
|---|---|---|---|:---:|
| **OBS-01** | Structured Logging | JSONL logging with correlation IDs | `testforge/logger.py:TraceLogger` | **VERIFIED PASS** |
| **OBS-02** | Correlation Propagation | Trace correlation across agents & tools | `testforge/callbacks.py:LifecycleEvent` | **VERIFIED PASS** |
| **OBS-03** | Lifecycle Monitoring | Typed event dispatch for all state transitions | `testforge/state.py:TaskLifecycleState` | **VERIFIED PASS** |
| **OBS-04** | Security Refusal Auditing | Refusal events logged with rule ID & risk | `testforge/callbacks.py:SecurityRefusalPayload` | **VERIFIED PASS** |
| **OBS-05** | Provenance Tracking | Full mutation-to-test lineage | `testforge/state.py:MutantRecord` | **VERIFIED PASS** |
| **OBS-06** | Secret Scrubbing | Automated scrubbing before log write | `testforge/logger.py:redact_sensitive_data` | **VERIFIED PASS** |
| **OBS-07** | Observer Fault Isolation | Handler exceptions do not crash pipeline | `testforge/callbacks.py:CallbackRegistry.dispatch` | **VERIFIED PASS** |
| **OBS-08** | Real-Time Streaming | WebSocket streaming of live events | `testforge/websocket_hub.py` | **VERIFIED PASS** |
