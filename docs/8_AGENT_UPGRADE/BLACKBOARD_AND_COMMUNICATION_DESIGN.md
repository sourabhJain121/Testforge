# Blackboard Architecture & Inter-Agent Communication Design

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** FACTUAL AUDIT & DESIGN SPECIFICATION COMPLETED  

---

## 1. Existing Blackboard Audit ([`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py))

### 1.1 Existing Storage & Concurrency Mechanisms
- **State Partitioning:** Currently structured into **5 typed spaces**:
  1. `TargetSpace`: Source code, functions, classes, call graph, blast risk, line count, SHA.
  2. `MutantSpace`: List of `MutantRecord` objects, surviving diffs, equivalent mutant tracking.
  3. `CriticSpace`: Critic directives, reflection notes, failure mechanisms, semantic guidance.
  4. `SuiteSpace`: Candidate test code, current test code, hardened test code, provider metadata.
  5. `MetricsSpace`: Convergence metrics, line coverage %, mutation score %, iteration history.
- **Thread Safety:** State transitions are guarded by `threading.RLock()`. All partition mutations are atomic; failed validations reject changes without corrupting memory.
- **Defensive Copying:** Partition getters (`get_target_space()`, etc.) and snapshot methods return deep copies (`copy.deepcopy`), preventing external state mutation.
- **Event-Driven Observer System:** Priority-ordered observer registration supporting partition filtering (`BlackboardSubscription`).
- **Persistence Layer:** Integrated with `SQLiteBlackboardStorage` ([`testforge/persistence.py`](file:///Users/sourabh/TestForge/testforge/persistence.py)). Checkpoints store full `BlackboardSnapshot` records in SQLite using Write-Ahead Logging (WAL) and parameterized queries.

### 1.2 Existing Deficiencies for 8-Agent Coordination

1. **No Partition for Test Plans (`PlanSpace`):**
   Test scenario definitions, equivalence classes, and boundary condition targets are currently generated ad-hoc within the generation prompt or AST synthesizer, leaving no persisted planning artifact.
2. **No Partition for Security Assessments (`SecuritySpace`):**
   Prompt injection findings, AST policy violations, and secret scrubbing decisions are currently stored as ephemeral callback events rather than a dedicated Blackboard partition.
3. **Execution Conflated with Metrics (`ExecutionSpace`):**
   `SuiteSpace` holds code, while `MetricsSpace` holds summary percentages. Detailed execution results (per-test pass/fail status, execution times, stdout/stderr, quarantined assertions) are not cleanly encapsulated in a dedicated execution partition.

---

## 2. Proposed 8-Partition Blackboard Architecture

To support all 8 agents seamlessly, the Blackboard will expand to **8 strongly-typed Pydantic v2 partitions**:

```
+---------------------------------------------------------------------------------------+
|                                  TESTFORGE BLACKBOARD                                 |
|                               (threading.RLock Protected)                             |
+---------------------------------------------------------------------------------------+
|  1. TargetSpace     | Source code, AST signatures, call graphs, blast radius          |
|  2. PlanSpace       | Test scenarios, boundary cases, equivalence partitions, budget  |
|  3. SuiteSpace      | Candidate, baseline, and hardened Pytest suites                 |
|  4. ExecutionSpace  | Granular test execution results, pass@1 status, line coverage   |
|  5. MutantSpace     | Deterministic AST mutants, kill statuses, equivalent mutants    |
|  6. CriticSpace     | CrewAI adversarial directives, failure mechanisms, guidance     |
|  7. SecuritySpace   | Input/output security inspections, AST safety, sanitizations    |
|  8. MetricsSpace    | Iteration history, convergence scores, token & cost metrics     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             SQLite Blackboard Storage (WAL)                           |
|                      Checkpoints, State Resumption, Audit Logs                        |
+---------------------------------------------------------------------------------------+
```

### 2.1 Partition Schemas & Agent Ownership

| Partition Name | Primary Writer Agent | Reader Agents | Data Encapsulated |
| :--- | :--- | :--- | :--- |
| **`TargetSpace`** | Code Intelligence Agent | Supervisor, Planning, Generation, Security, Critic | Target code, AST call graph, function signatures, blast risk, line counts. |
| **`PlanSpace`** *(NEW)* | Test Planning Agent | Supervisor, Test Generation, Reflection & Repair | Prioritized test scenarios, boundary definitions, mock requirements, test budgets. |
| **`SuiteSpace`** | Test Generation Agent,<br>Reflection & Repair Agent | Test Execution Agent, Security Agent, Supervisor | Baseline test code, candidate test code, hardened test code, active provider. |
| **`ExecutionSpace`** *(NEW)* | Test Execution Agent | Supervisor, Critic, Reflection & Repair | Granular per-test results (`PASSED`, `FAILED`, `ERROR`), stdout/stderr, line coverage breakdown. |
| **`MutantSpace`** | Mutation & Quality Critic Agent | Supervisor, Reflection & Repair Agent | Injected AST mutants, killed mutant IDs, surviving mutant IDs, equivalent mutant classifications. |
| **`CriticSpace`** | Mutation & Quality Critic Agent (CrewAI) | Supervisor, Reflection & Repair Agent | Structured critique directives, diagnosed failure mechanisms, semantic guidance. |
| **`SecuritySpace`** *(NEW)* | Security Agent | Supervisor, All Agents | Input screening results, AST policy findings, defused prompt injections, credential redaction logs. |
| **`MetricsSpace`** | Supervisor Agent | Cockpit Web UI, Telemetry, Evaluator | Convergence scores, raw/adjusted mutation score, line coverage %, token usage, elapsed time. |

---

## 3. Inter-Agent Communication & Handoff Protocols

Inter-agent communication combines two complementary protocols:

### 3.1 Asynchronous Shared State (Blackboard Read/Write)
- Agents read their prerequisites from Blackboard partitions and commit their outputs as atomic partition updates.
- Emits `BlackboardEvent(revision, partition, safe_metadata)` to notify observers.

### 3.2 Synchronous Point-to-Point Handoffs (A2A Broker)
For direct task dispatch (e.g. Supervisor requesting a critique from CrewAI Critic), communication is mediated by `A2ABroker` ([`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py)):
- **Envelope:** `A2AMessage(message_id, correlation_id, sender, recipient, performative, action, payload)`.
- **Performatives:**
  - `REQUEST`: Supervisor dispatches work to an agent.
  - `INFORM`: Agent returns validated payload.
  - `REFUSE`: Security Agent or Broker rejects unsafe request.
  - `FAILURE`: Operation timed out or failed with traceback.
- **Safety Inspection:** The broker inspects payload text for prompt injections via `SecurityGuardrail` before delivering to recipient handlers.
- **Blackboard Synchronization:** Successful agent responses are automatically committed to the designated Blackboard partition.

---

## 4. State Persistence, Job Isolation & Reproducibility

### 4.1 SQLite Transactional Checkpointing
- Every major workflow transition triggers `blackboard.save_checkpoint(stage, job_id, workflow_id, status)`.
- Full `BlackboardSnapshot` containing all 8 partitions is serialized as JSON and written into SQLite with a SHA-256 hash ensuring data integrity.

### 4.2 Job & Task Isolation
- Multi-tenancy and parallel execution are isolated by unique `workflow_id` (`wf_<uuid12>`) and `job_id`.
- The database indexes checkpoints by `(job_id, workflow_id, created_at)`, allowing clean isolation and resumption of interrupted jobs.

### 4.3 Deterministic Resumption Plan
- If a pipeline fails or is cancelled, `TestForgeOrchestrator.validate_and_restore_checkpoint(checkpoint_id)` reconstructs the full Blackboard state.
- Resumption skips already-completed stages (e.g. skips Ingestion and Clean Baseline Validation if restarting from Mutation Analysis).

---

## 5. Phase 2 Implementation & Verification Summary

### 5.1 Concrete Implementation Details
- **`testforge/blackboard.py`**:
  - Implemented `PlanSpace`, `ExecutionSpace`, and `SecuritySpace` models inheriting from Pydantic `BaseModel`.
  - Expanded `BlackboardEvent.partition` Literal to support all 8 partition names: `"target"`, `"mutant"`, `"critic"`, `"suite"`, `"metrics"`, `"plan"`, `"execution"`, `"security"`.
  - Updated `BlackboardSnapshot` with `plan`, `execution`, and `security` fields using `Field(default_factory=...)` to ensure automatic backward-compatibility with legacy snapshots.
  - Added accessors (`get_plan_space()`, `get_execution_space()`, `get_security_space()`, and properties `plan`, `execution`, `security`) and mutators (`update_plan_space()`, `update_execution_space()`, `update_security_space()`).
- **`testforge/persistence.py`**:
  - Incremented `CURRENT_SCHEMA_VERSION = 2`.
  - Added `SUPPORTED_SCHEMA_VERSIONS = {1, 2}` allowing legacy version 1 checkpoints to deserialize with default models for the three new partitions without data corruption or rejection.
- **`testforge/a2a.py`**:
  - Defined 4 typed communication contracts:
    1. `TestPlanPayload` (Producer: Test Planning Agent; Consumers: Supervisor, Test Generation, Reflection & Repair).
    2. `TestExecutionPayload` (Producer: Test Execution Agent; Consumers: Supervisor, Critic, Reflection & Repair).
    3. `SecurityEvaluationPayload` (Producer: Security Agent; Consumers: Supervisor, All Agents).
    4. `RepairRequestPayload` (Producer: Supervisor / Critic Agents; Consumer: Reflection & Repair Agent).
  - Added broker synchronization helpers (`_sync_planner_to_blackboard`, `_sync_execution_to_blackboard`, `_sync_security_to_blackboard`) in `A2ABroker`.
- **`tests/test_blackboard_8space_expansion.py`**:
  - 12 focused verification tests verifying all 8 partitions, backward-compatible loading of schema 1 snapshots, concurrent updates, Pydantic validation rejection of invalid payloads, and automatic A2A broker synchronization.
  - Test result: **12 passed in 0.13s**.
- **Full System Regression**:
  - Test result: **654 passed in 272.77s** across all test suites. Zero regressions.


