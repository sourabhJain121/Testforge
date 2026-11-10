# Phase 4D: Official Agent2Agent (A2A) Protocol Interoperability

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Course:** Autonomous Agentic AI  
**Author:** TestForge Agentic Upgrade  
**Status:** Completed & Verified  

---

## 1. Executive Summary

Phase 4D establishes genuine, protocol-compliant agent-to-agent interoperability for TestForge, bridging the architectural gap between the internal custom message broker (`testforge/a2a.py`) and the official **Agent-to-Agent (A2A) Protocol specification (v0.3.0)**.

Prior to Phase 4D, agents communicated in-process using Python method calls and an internal message broker. While structured and type-safe, this did not fulfill the university requirement for true wire-protocol multi-agent communication. Phase 4D introduces:
1. **Official Protocol Implementation**: Backed by `a2a-sdk==0.3.26` (the official SDK dependency used by `google-adk`).
2. **Standard Agent Discovery**: Standard `AgentCard` exposed at `/.well-known/agent-card.json` and `/.well-known/agent.json`.
3. **A2A Server Architecture**: An ASGI Starlette application (`testforge/a2a_protocol.py`) implementing official JSON-RPC request handlers and standard task lifecycle semantics.
4. **Official Client Boundary**: Standard client communication via `a2a.client` (`A2ACardResolver`, `ClientFactory`, `BaseClient`) sending typed requests over HTTP.
5. **Cross-Framework Integration**: Seamless translation from A2A wire messages into internal `A2AMessage` envelopes routed to the Google ADK Test Generator (`agent:google-adk:generator`) and CrewAI Adversarial Critic (`agent:crewai:critic`), synchronizing validated test artifacts to the typed Blackboard `SuiteSpace`.
6. **Defense-in-Depth Security**: Prompt injection screening prior to agent dispatch, AST syntax and safety verification via `CodeSanitizer`, and strict credential redaction.

---

## 2. Protocol Specification & SDK Alignment

### 2.1 Specification Details
- **Protocol Name:** Agent-to-Agent (A2A) Protocol
- **Protocol Version:** `0.3.0`
- **Official SDK:** `a2a-sdk` (v0.3.26 installed in isolated environment `venv_313`)
- **Underlying Transport:** JSON-RPC 2.0 over HTTP / ASGI (`TransportProtocol.jsonrpc`)
- **Input Modes Supported:** `["text", "json"]`
- **Output Modes Supported:** `["text", "json"]`
- **Streaming Mode:** Supported / configurable (default non-streaming for deterministic task-level aggregation)

### 2.2 Wire Endpoints Exposed
| Endpoint | Method | Protocol Role | Description |
|---|---|---|---|
| `/.well-known/agent-card.json` | `GET` | Discovery | Official discovery document declaring agent identity, skills, and transport. |
| `/.well-known/agent.json` | `GET` | Discovery Alias | Canonical discovery alias ensuring cross-version compatibility. |
| `/` | `POST` | JSON-RPC | A2A JSON-RPC 2.0 endpoint handling `message/send`, task updates, and queries. |
| `/health` | `GET` | Observability | Health check endpoint returning protocol version and agent readiness. |

---

## 3. Architecture & Boundary Design

```
+-----------------------------------------------------------------------------------+
|                            A2A Protocol Client Boundary                           |
|  - A2ACardResolver: Queries /.well-known/agent-card.json                          |
|  - ClientFactory: Instantiates official Client over JSON-RPC Transport            |
|  - TestForgeA2AClient: Sends typed Message envelopes and consumes Task artifacts |
+------------------------------------------+----------------------------------------+
                                           | HTTP / ASGI JSON-RPC 2.0
                                           v
+-----------------------------------------------------------------------------------+
|                        TestForge A2A Server (Starlette App)                       |
|  - A2AStarletteApplication + DefaultRequestHandler + InMemoryTaskStore            |
+------------------------------------------+----------------------------------------+
                                           | RequestContext + EventQueue
                                           v
+-----------------------------------------------------------------------------------+
|                       TestForgeA2AExecutor (AgentExecutor)                        |
|  1. Extracts message payload and intent                                           |
|  2. SecurityGuardrail.inspect_prompt(): blocks prompt injections                  |
|  3. Publishes TaskStatusUpdateEvent(state=TaskState.working)                     |
|  4. Translates to internal A2AMessage & routes to A2ABroker                       |
|  5. CodeSanitizer.extract_and_validate(): AST validation                         |
|  6. Updates Blackboard SuiteSpace on success                                      |
|  7. Publishes TaskArtifactUpdateEvent & TaskStatusUpdateEvent(completed/failed)   |
+------------------------------------------+----------------------------------------+
                                           | Internal A2AMessage
                                           v
+-----------------------------------------------------------------------------------+
|                       Internal A2ABroker (In-Process Hub)                         |
|         +--------------------------------+--------------------------------+       |
|         |                                                                 |       |
|         v                                                                 v       |
|   Google ADK Generator                                           CrewAI Critic    |
|   (agent:google-adk:generator)                                   (agent:crewai:   |
|   - LlmAgent / Runner                                             critic)         |
|   - ADKModelBridge                                               - Agent / Task   |
|   - Generates Unit Tests                                         - CrewAILLMBridge|
|                                                                  - Critique AST   |
+-----------------------------------------------------------------------------------+
```

### 3.1 Architectural Separation of Concerns
1. **External Boundary (Official A2A Wire Protocol):**
   - Strictly conforms to `a2a-sdk` data structures: `AgentCard`, `AgentSkill`, `Message`, `Role`, `TextPart`, `Part`, `Task`, `TaskStatus`, `TaskState`, `Artifact`.
   - Interacts with remote clients or external tools solely through HTTP JSON-RPC 2.0.
2. **Internal Adapter (`A2ABroker`):**
   - Preserves existing high-speed, thread-safe in-memory message passing between Google ADK and CrewAI.
   - Enforces deep-copy isolation, thread safety, bounded execution timeouts, and lifecycle callbacks.
3. **Shared Memory (`Blackboard`):**
   - Shared partitioned state (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`).
   - The protocol executor updates `SuiteSpace` (`current_test_code`, `hardened_test_code`) **only** when generated code passes AST validation.

---

## 4. Agent Capabilities & Discovery

### 4.1 Agent Card Schema
The server exposes an `AgentCard` describing TestForge's agentic testing suite:
- **Name:** `testforge-agent-system`
- **Version:** `1.0.0`
- **Protocol Version:** `0.3.0`
- **Preferred Transport:** `jsonrpc`
- **Input Modes:** `["text", "json"]`
- **Output Modes:** `["text", "json"]`
- **Provider:** `TestForge Autonomous Systems` (`https://github.com/sourabhJain121/Testforge`)

### 4.2 Declared Skills
1. **`unit-test-generation`**:
   - *Description:* Generates syntactically valid Python unit tests targeting surviving mutants using Google ADK.
   - *Tags:* `["testing", "adk", "generation", "python"]`
2. **`mutation-critique`**:
   - *Description:* Performs adversarial critique of test suites and surviving mutation diffs using CrewAI.
   - *Tags:* `["critique", "crewai", "mutation-testing"]`
3. **`hardening-workflow`**:
   - *Description:* Executes a complete generator-critic hardening cycle updating the typed Blackboard.
   - *Tags:* `["hardening", "workflow", "blackboard"]`

### 4.3 Redaction and Privacy Guarantee
The generated `AgentCard` and all protocol error responses are strictly sanitized:
- No file paths (`/Users/`, `/home/`) are exposed.
- No API keys (`api_key`, `secret`, `token`) are exposed.
- Internal exception stack traces are masked into standardized error descriptions.

---

## 5. Protocol Message and Task Lifecycle

### 5.1 Request Flow
A client submits a standard A2A JSON-RPC request to `POST /`:
```json
{
  "jsonrpc": "2.0",
  "id": "req-98fbc102",
  "method": "message/send",
  "params": {
    "message": {
      "message_id": "msg-01",
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "{\"action\": \"generate_tests\", \"target_source_code\": \"def add(a, b): return a + b\", \"surviving_mutants\": [{\"id\": \"MUT_01\"}]}"
        }
      ],
      "metadata": {
        "skill_id": "unit-test-generation"
      }
    }
  }
}
```

### 5.2 Lifecycle State Transitions
The server emits a deterministic sequence of A2A events:
1. **Submitted**: A2A server accepts request and initializes `Task(state=submitted)`.
2. **Working**: `TestForgeA2AExecutor` publishes `TaskStatusUpdateEvent(state=working)`.
3. **Artifact Production**: Once agent execution and AST validation succeed, the executor publishes:
   - `TaskArtifactUpdateEvent(artifact=Artifact(name="generated_test.py", parts=[TextPart(text=...)]))`
4. **Terminal Completion**:
   - On success: `TaskStatusUpdateEvent(state=completed, final=True)`.
   - On failure / rejection: `TaskStatusUpdateEvent(state=failed, message=..., final=True)`.

### 5.3 Error and Security Semantics
If a prompt injection or policy violation is detected:
- The executor catches the violation at the protocol boundary.
- An `EventType.ERROR` lifecycle event is dispatched (`error_type="SECURITY_VIOLATION"`).
- A protocol-valid `TaskStatusUpdateEvent(state=failed, message="Security Refusal: ...", final=True)` is returned.
- No internal agent is invoked, and the Blackboard remains unmodified.

---

## 6. Verification and Regression Results

### 6.1 Focused Protocol Tests (`tests/test_a2a_protocol.py`)
A comprehensive test suite containing 15 test cases verifies all aspects of protocol interoperability:

| Test Name | Focus | Result |
|---|---|---|
| `test_agent_card_structure_and_skills` | AgentCard schema, version, capabilities, skills | **PASSED** |
| `test_agent_card_contains_no_sensitive_secrets` | Credential/path scrubbing in public card | **PASSED** |
| `test_well_known_agent_card_discovery_endpoint` | HTTP GET `/.well-known/agent-card.json` and `.well-known/agent.json` | **PASSED** |
| `test_official_card_resolver_client` | Resolution via official `A2ACardResolver` | **PASSED** |
| `test_test_generation_protocol_roundtrip` | Protocol roundtrip generating tests + Blackboard sync | **PASSED** |
| `test_critique_protocol_roundtrip` | Protocol roundtrip diagnosing mutants via CrewAI | **PASSED** |
| `test_raw_protocol_message_execution` | Raw A2A `Message` envelope dispatch | **PASSED** |
| `test_prompt_injection_blocked_at_protocol_boundary` | SecurityGuardrail refusal at wire boundary | **PASSED** |
| `test_missing_source_code_fails_gracefully` | Protocol failure on missing parameters | **PASSED** |
| `test_unsupported_action_fails_gracefully` | Unknown skill/action rejected | **PASSED** |
| `test_invalid_ast_generated_code_rejected` | CodeSanitizer rejects invalid AST before Blackboard | **PASSED** |
| `test_internal_agent_failure_reports_failure` | Internal failures report `TaskState.failed` | **PASSED** |
| `test_health_check_endpoint` | GET `/health` protocol status check | **PASSED** |
| `test_adk_generator_real_handler_via_a2a_protocol` | Real Google ADK generator invoked via protocol | **PASSED** |
| `test_crewai_critic_real_handler_via_a2a_protocol` | Real CrewAI critic invoked via protocol | **PASSED** |

**Focused Suite Execution:**
```
pytest tests/test_a2a_protocol.py -v
Result: 15 passed in 3.21s (Exit code: 0)
```

### 6.2 Regression Battery Results

| Test Target | Tests Run | Result | Duration | Exit Code |
|---|---|---|---|---|
| `tests/test_a2a_protocol.py` | 15 | 15 Passed | 3.21s | 0 |
| `tests/test_a2a.py` | 16 | 16 Passed | 0.81s | 0 |
| `tests/test_adk_generator.py` | 14 | 14 Passed | 0.85s | 0 |
| `tests/test_crew_critic.py` | 9 | 9 Passed | 0.77s | 0 |
| `tests/test_blackboard.py` | 18 | 18 Passed | 0.12s | 0 |
| `tests/test_security.py` | 28 | 28 Passed | 0.14s | 0 |
| `tests/test_callbacks.py` | 12 | 12 Passed | 0.08s | 0 |
| `tests/test_mcp.py` | 22 | 22 Passed | 11.61s | 0 |
| **Complete `tests/` Suite** | **158** | **158 Passed** | **2m 38s** | **0** |
| **Standalone `test_hardened.py`** | **21** | **21 Passed** | **0.15s** | **0** |
| **`python -m pip check`** | - | **Clean (0 broken)** | **0.30s** | **0** |

---

## 7. Protocol Distinction Matrix

To ensure absolute transparency regarding protocol claims:

| Layer / Behavior | Mechanism Used | Verified Evidence |
|---|---|---|
| **Wire Protocol Interoperability** | Official `a2a-sdk==0.3.26` Starlette application | Standard JSON-RPC 2.0 requests over HTTP/ASGI verified via `A2ACardResolver` and `ClientFactory` |
| **Agent Discovery** | Official `AgentCard` specification | Discovered at `/.well-known/agent-card.json` with declared skills and capabilities |
| **Internal Routing** | In-process `A2ABroker` adapter | Type-safe dispatch to `agent:google-adk:generator` and `agent:crewai:critic` |
| **Test Generation Agent** | Genuine Google ADK (`LlmAgent`, `Runner`, `InMemorySessionService`) | Structured generation targeting surviving mutants |
| **Critique Agent** | Genuine CrewAI (`Agent`, `Task`, `Crew`) | Multi-agent critique producing prescriptive directives |
| **Model Inference in Tests** | Controlled Model Bridges (`ADKModelBridge`, `CrewAILLMBridge`) | Deterministic, offline test doubles verifying protocol handling without paid API costs |
| **Shared State Synchronization** | Typed `Blackboard` (`SuiteSpace`, `CriticSpace`) | Atomically updated only upon AST and security verification |

---

## 8. Preserved Constraints Confirmation

- **Requirements File:** `requirements.txt` was **not modified**.
- **Host Environment:** Host Python 3.14 `.venv` was **not touched**.
- **Isolated Environment:** Installed `a2a-sdk==0.3.26` exclusively into `venv_313` upon explicit user approval; dependency tree remains completely clean (`pip check`: clean).
- **Git State:** No commits or pushes made. All pre-existing user files and working tree modifications are preserved.
- **Scope Limit:** Phase 4D scope strictly maintained. No premature benchmarking, deployment, or Phase 5 work was started.
