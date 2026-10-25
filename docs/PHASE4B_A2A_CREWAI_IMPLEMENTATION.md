# Phase 4B Implementation Report: Typed A2A Contract & Genuine CrewAI Adversarial Critic

**Project**: TestForge — Autonomous Agentic Unit Test Hardening System  
**Course**: CSE3101 - Agentic AI  
**Author**: Sourabh  
**Target Milestone**: Phase 4B — A2A Contract, A2A Broker, Genuine CrewAI Critic, Blackboard & Callback Integration  
**Date**: October 2026  
**Status**: Verified & Passing All Regression Gates

---

## 1. Executive Summary

Phase 4B establishes the formal multi-agent coordination layer for TestForge:
1. **Typed A2A Message Contract (`testforge/a2a.py`)**: A Pydantic v2-validated message envelope (`A2AMessage`) and communicative act specification (`A2APerformative`) inspired by FIPA-ACL.
2. **In-Process Message Broker (`A2ABroker`)**: Manages handler registration, sender/recipient authorization, prompt injection inspection via `SecurityGuardrail`, execution timeouts via thread pools, lifecycle callback dispatches, and atomic synchronization with Blackboard partitions (`CriticSpace`).
3. **Genuine CrewAI Adversarial Critic (`testforge/crew_critic.py`)**: Uses installed `crewai.Agent`, `crewai.Task`, and `crewai.Crew` classes. Bridges CrewAI execution to TestForge's hybrid LLM infrastructure via a custom `crewai.llms.base_llm.BaseLLM` adapter (`CrewAILLMBridge`), supporting controlled test doubles, offline deterministic AST analysis, and optional live Gemini execution.
4. **Blackboard & Callback Integration**: Validated critique results update `CriticSpace` atomically (`latest_directive`, `failure_mechanisms`, `reflection_notes`, `critic_directives`) and preserve legacy `TestForgeState` compatibility. Callbacks emit `AGENT_HANDOFF` and `OPERATION_COMPLETE` with credential redaction.
5. **Phase Scope Notice**: As specified in the architecture plan, the **Google ADK Generator Agent remains incomplete** and will be implemented in Phase 4C.

---

## 2. Architecture & File Inventory

### 2.1 Files Created or Modified
| File | Status | Description |
|---|---|---|
| `testforge/a2a.py` | **Created** | Typed A2A envelope, performatives (`REQUEST`, `INFORM`, `REFUSE`, `FAILURE`, etc.), typed payloads (`CriticDirectivePayload`, `A2ACritiqueRequestPayload`), and `A2ABroker`. |
| `testforge/crew_critic.py` | **Created** | Genuine CrewAI Critic agent (`Agent`, `Task`, `Crew`), `CrewAILLMBridge` (subclass of `crewai.llms.base_llm.BaseLLM`), and A2A message handler. |
| `testforge/callbacks.py` | **Modified** | Added `AGENT_HANDOFF = "AGENT_HANDOFF"` to `EventType` and added `AgentHandoffPayload` model. |
| `testforge/security.py` | **Modified** | Enhanced `INJ_SYSTEM_OVERRIDE` regex pattern to handle chained modifier sequences (e.g. "previous developer instructions"). |
| `tests/test_a2a.py` | **Created** | 16 focused unit and integration tests covering envelopes, performatives, timeouts, authorization, security rejection, and Blackboard sync. |
| `tests/test_crew_critic.py` | **Created** | 9 focused unit and integration tests covering genuine CrewAI instantiation, kickoff, structured output, mock LLMs, and A2A broker dispatch. |
| `docs/PHASE4B_A2A_CREWAI_IMPLEMENTATION.md` | **Created** | Implementation report and verification documentation. |

---

## 3. Typed A2A Message Contract & Broker

### 3.1 Custom In-Process Broker Clarification
> [!IMPORTANT]
> `A2ABroker` and `A2AMessage` provide an **in-process, typed message-passing abstraction** inspired by FIPA-ACL and modern multi-agent communication patterns, tailored for TestForge's in-memory multi-framework pipeline. This is not an external HTTP wire protocol or web server.

### 3.2 Message Envelope Schema (`A2AMessage`)
```python
class A2APerformative(str, Enum):
    REQUEST = "REQUEST"       # Sender requests recipient to execute an action
    INFORM = "INFORM"         # Sender provides verified results/facts
    AGREE = "AGREE"           # Recipient accepts request and commits to execute
    REFUSE = "REFUSE"         # Recipient or Broker refuses execution (auth, security, policy)
    FAILURE = "FAILURE"       # Execution failed during operation (timeout, exception, error)
    PROPOSE = "PROPOSE"       # Sender proposes candidate directives or assertions

class A2AMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    correlation_id: str
    sender: str
    recipient: str
    performative: A2APerformative
    timestamp: float = Field(default_factory=time.time)
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
```

### 3.3 Core Broker Responsibilities (`A2ABroker`)
1. **Registration & Authorization**: Agents register with `register_handler(agent_id, handler, allowed_actions, allowed_senders)`. Unregistered recipients, unauthorized senders, or disallowed actions immediately return an `A2APerformative.REFUSE` envelope without executing agent code.
2. **Defensive Isolation**: Deep-copies incoming and outgoing payloads preventing concurrent or post-dispatch mutation.
3. **Security Guardrail Inspection**: Scans payload string fields using `SecurityGuardrail().inspect_prompt()`. If prompt injection or instruction override is detected (risk level HIGH/CRITICAL), execution is blocked and an `A2APerformative.REFUSE` envelope is returned with refusal reason `PROMPT_INJECTION_DETECTED`. The Blackboard is left untouched.
4. **Execution Timeouts**: Handler calls run via `concurrent.futures.ThreadPoolExecutor` bounded by a configurable timeout (`timeout_sec`, default 45.0s). If timeout expires, a `FAILURE` envelope with `refusal_reason="TIMEOUT"` is returned.
5. **Credential Redaction**: Raw API keys, tokens, and bearer credentials in headers or payloads are redacted (`[REDACTED_SECRET]`) prior to entering broker history or lifecycle logs.
6. **Blackboard Partition Sync**: Successful `INFORM` messages containing valid `CriticDirectivePayload` data are validated and merged atomically into `blackboard.get_critic_space()`.

---

## 4. Genuine CrewAI Adversarial Critic Implementation

### 4.1 Framework Architecture
`testforge/crew_critic.py` executes official CrewAI classes:
- **`crewai.Agent`**:
  - `role`: `"Senior Adversarial Mutation Testing Critic & Security Auditor"`
  - `goal`: `"Analyze surviving Python AST mutants, identify unexercised logic boundaries, and formulate precise, adversarial testing directives that kill surviving mutants."`
  - `backstory`: `"An elite test architect with deep expertise in mutation analysis, boundary value analysis, and edge-case fuzzing. Specializes in finding gaps left by ordinary unit tests."`
- **`crewai.Task`**:
  - Configured with `output_pydantic=CriticDirectivePayload`, enforcing Pydantic structural validation at the framework level.
- **`crewai.Crew`**:
  - Encapsulates agent and task execution, invoked via `crew.kickoff()`.
  - Configured with `share_crew=False` and telemetry opt-out (`CREWAI_TELEMETRY_OPT_OUT=true`, `OTEL_SDK_DISABLED=true`) to guarantee zero interactive CLI prompts during automated execution.

### 4.2 LLM Integration Model (`CrewAILLMBridge`)
Because the isolated environment does not contain `litellm` (which would require external dependency changes), `CrewAILLMBridge` subclasses CrewAI's official base class `crewai.llms.base_llm.BaseLLM`:
```python
class CrewAILLMBridge(BaseLLM):
    def call(self, messages: Any, **kwargs: Any) -> str: ...
    async def acall(self, messages: Any, **kwargs: Any) -> str: ...
    def supports_function_calling(self) -> bool: return False
```
- **Controlled Test Doubles**: Accepts `mock_response` (dict or JSON string) for deterministic offline unit testing.
- **Offline Deterministic Fallback**: Analyzes AST mutant diffs for comparison inversions (`>`, `<`, `==`), boundary thresholds (`0`, `0.0`), and arithmetic swaps (`+`, `-`), returning structured JSON matching `CriticDirectivePayload`.
- **Live Google GenAI Execution**: If `use_live_llm=True` (or `TESTFORGE_LIVE_LLM=1`) and `GEMINI_API_KEY` is present, routes requests through `HybridLLMClient` to `gemini-3.6-flash`.
- **Zero Paid API Requirement for Tests**: Tests run entirely offline using controlled mock responses or deterministic synthesis in 0.02s without network access.

### 4.3 Structured Output Schema (`CriticDirectivePayload`)
```python
class CriticDirectivePayload(BaseModel):
    analysis: str = Field(..., description="Diagnostic reasoning on why mutants survived")
    target_mutants: List[str] = Field(default_factory=list, description="IDs of surviving mutants analyzed")
    directives: List[str] = Field(default_factory=list, description="Prescriptive assertions and boundary directives")
    failure_mechanisms: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of mutant_id to root cause failure mechanism"
    )
```

---

## 5. Blackboard State & Callback Mapping

### 5.1 Blackboard Partition Updates
Upon validated critique receipt:
- `blackboard.update_critic_space(...)`:
  - `latest_directive`: Sets formatted primary analysis and prescribed directives.
  - `critic_directives`: Appends new directive to the revision history list.
  - `failure_mechanisms`: Merges mutant-to-mechanism dictionary.
  - `reflection_notes`: Appends correlation ID and mutant count note.
- `sync_to_state(state)`: Propagates updated `reflection_notes` and metrics to legacy `TestForgeState`.

### 5.2 Callback Lifecycle Integration
- **`AGENT_HANDOFF`**: Emitted when dispatching a request from `agent:orchestrator` to `agent:crewai:critic`.
- **`OPERATION_COMPLETE`**: Emitted upon response validation with execution duration.
- **`ERROR`**: Emitted on timeouts, authorization failures, or prompt injection blocks.
- **Exception Isolation**: Handlers registered in `CallbackRegistry` execute within defensive exception wrappers; subscriber exceptions cannot crash the broker or corrupt Blackboard partitions.

---

## 6. Security & Guardrails

1. **Prompt Injection Inspection**:
   - Every message dispatched through `A2ABroker` is evaluated by `SecurityGuardrail().inspect_prompt()` across candidate fields (`target_source_code`, `prompt`, `directives`, `text`).
   - Injection attempts return `performative=A2APerformative.REFUSE` with `refusal_reason="PROMPT_INJECTION_DETECTED"`.
   - Blackboard state remains untouched upon security refusal.
2. **Secret Redaction**:
   - `A2AMessage.scrubbed_copy()` redacts `sk-`, `ghp_`, `AIza`, bearer tokens, and sensitive key names (`api_key`, `secret`, `password`, `token`) prior to recording messages in broker history.
3. **Known Limitation Notice**:
   > [!WARNING]
   > Pattern-based prompt injection detection is a heuristic defense-in-depth layer, not an impenetrable cryptographic security boundary. It catches known prompt-injection primitives and instruction overrides, but must be accompanied by execution sandboxing and AST validation.

---

## 7. Verification Evidence & Regression Test Results

All tests were executed in the isolated Python 3.13 environment (`/Users/sourabh/.gemini/antigravity-ide/brain/05f0de02-c90e-40d7-bf92-0819372e0bac/scratch/venv_313/bin/python`).

### 7.1 Test Summary
| Test Suite | Command | Total | Passed | Failed | Duration | Exit Code |
|---|---|---|---|---|---|---|
| **Focused A2A Tests** | `pytest tests/test_a2a.py -v` | 16 | 16 | 0 | 1.09s | 0 |
| **Focused CrewAI Critic Tests** | `pytest tests/test_crew_critic.py -v -W ignore` | 9 | 9 | 0 | 1.32s | 0 |
| **Existing Blackboard Tests** | `pytest tests/test_blackboard.py -v` | 18 | 18 | 0 | 1.52s | 0 |
| **Existing Security & Callbacks** | `pytest tests/test_security.py tests/test_callbacks.py -v` | 40 | 40 | 0 | 1.54s | 0 |
| **Complete Test Suite (`tests/`)** | `pytest tests/ -v -W ignore` | 129 | 129 | 0 | 150.25s | 0 |
| **Hardened Test Suite** | `pytest test_hardened.py -v -W ignore` | 21 | 21 | 0 | 0.02s | 0 |
| **Package Dependency Check** | `pip check` | N/A | Clean | 0 | 0.22s | 0 |

### 7.2 Detailed Test Breakdown
- **`tests/test_a2a.py` (16 passed)**:
  - Valid envelope creation and immutability.
  - Rejection of empty/whitespace identifiers and unsupported performatives.
  - Correlation ID preservation and sender/recipient swapping in responses.
  - Credential redaction in payloads and headers.
  - Registration, unregistration, and listing of agent handlers.
  - Rejection of unregistered recipients, unauthorized senders, and unauthorized actions.
  - Prompt injection interception leaving Blackboard untouched.
  - Bounded timeout handling (`FAILURE`, `TIMEOUT`).
  - Handler exception redaction (`[REDACTED_SECRET]`).
  - Atomic Blackboard `CriticSpace` synchronization.
  - Callback event dispatching and failure isolation.
- **`tests/test_crew_critic.py` (9 passed)**:
  - Instantiation of genuine `crewai.Agent` with role, goal, and backstory.
  - Zero-mutant fast path bypassing unnecessary LLM execution.
  - Genuine CrewAI `crew.kickoff()` execution returning `CriticDirectivePayload`.
  - Controlled mock LLM response execution.
  - Filtering of hallucinated mutant IDs to known survivors.
  - Graceful fallback upon malformed LLM output without uncaught exceptions.
  - A2A message handling for `diagnose_mutants`.
  - Rejection of unsupported actions (`REFUSE`).
  - End-to-end broker dispatch, CrewAI execution, callback emission, and Blackboard synchronization.

---

## 8. Credentials & Live LLM Execution

- **Automated Tests**: Require **zero** credentials, zero network access, and zero paid API calls. All test suites pass 100% deterministically using controlled doubles and local AST analysis.
- **Live LLM Execution**:
  - Live model execution uses Google GenAI (`gemini-3.6-flash`) via `HybridLLMClient`.
  - Requires `GEMINI_API_KEY` set in the environment and `TESTFORGE_LIVE_LLM=1` (or `use_live_llm=True`).
  - If keys are missing or 503/429 quotas are exceeded, the system falls back to the deterministic AST critic without pipeline crashes.

---

## 9. Deviations & Next Steps

### 9.1 Deviations from Phase 4A Architecture Design
1. **In-Process Broker rather than Wire Protocol**: Documented explicitly that `A2ABroker` is an in-process message dispatcher rather than an external wire protocol.
2. **`BaseLLM` Adapter for CrewAI**: Because `litellm` is not installed in the isolated environment, we subclassed `crewai.llms.base_llm.BaseLLM` (`CrewAILLMBridge`) instead of configuring `crewai.LLM` through LiteLLM. This preserved dependency compatibility while executing genuine CrewAI classes.

### 9.2 Deferred to Phase 4C
- **Google ADK Generator Agent**: Integration of `google.adk.Agent` / `google.adk.Runner` as the code synthesis agent communicating over the A2A broker will be executed in Phase 4C after Phase 4B review and acceptance.
