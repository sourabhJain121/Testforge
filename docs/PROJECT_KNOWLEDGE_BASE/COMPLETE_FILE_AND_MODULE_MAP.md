# TESTFORGE — COMPLETE FILE & MODULE MAP
## Exhaustive Codebase Inventory, Class References, Line Citations & Dependency Topography

**Document Version:** 2.0.0  
**Target Audience:** AI Models, Core Maintainers, Evaluators  
**Authoritative Location:** `docs/PROJECT_KNOWLEDGE_BASE/COMPLETE_FILE_AND_MODULE_MAP.md`

---

## 1. REPOSITORY TOP-LEVEL STRUCTURE

```
/Users/sourabh/TestForge
├── frontend/                     # HTML5/CSS3/Vanilla JS single-page web app
│   ├── index.html               # Main application layout, tabs, modal dialogs
│   ├── app.js                   # State manager, REST client, WebSocket listener
│   └── style.css                # CSS custom properties, high-contrast dark theme
├── server.py                     # FastAPI application, REST endpoints, WebSocket broadcaster
├── app.py                        # Legacy Streamlit entry point (Permanently Disabled)
├── Dockerfile                    # Multi-stage production container build (non-root testforge)
├── docker-compose.yml            # Service container definition with port 8000 mapping
├── start_testforge.sh            # One-click startup script (Uvicorn FastAPI server)
├── requirements.txt              # Production dependency specifications
├── benchmark_results.json        # Authoritative multi-target benchmark metrics
├── testforge/                    # Core Python application package (34 modules)
├── tests/                        # Pytest regression suite (43 test files, 523 tests)
├── samples/                      # Target benchmark Python modules (31 files)
└── docs/                         # Project documentation and evaluation package
    ├── EVALUATION_PACKAGE/       # Academic demonstration summaries and guides
    └── PROJECT_KNOWLEDGE_BASE/   # Master technical guides for AI and viva defense
```

---

## 2. CORE BACKEND APPLICATION MODULES (`testforge/`)

### 2.1 Orchestration & State Lifecycle

#### [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py)
- **Primary Responsibility:** Coordinates the end-to-end multi-agent hardening loop, handles timeouts, inspects cancellation tokens, and manages fallback chains.
- **Key Classes:**
  - `HardeningCancelledError` (Line 127): Raised when a running hardening job receives an abort signal.
  - `HardeningTimeoutError` (Line 132): Raised when pipeline execution exceeds the configured wall-clock timeout.
  - `TestForgeOrchestrator` (Line 137): Central controller executing the 5-stage pipeline across TargetAnalyzer, MutantGenerator, Critic, and TestGenerator.
- **Key Functions:**
  - `format_standalone_test_suite` (Line 72): Assembles individual test function ASTs into a valid, standalone executable Pytest suite.
- **Calls:** `testforge.blackboard`, `testforge.agents`, `testforge.sandbox`, `testforge.callbacks`.
- **Called By:** `server.py` (`POST /api/harden/start`, `POST /api/harden/run`).

#### [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py)
- **Primary Responsibility:** In-memory, typed, shared-state repository partitioned into five isolated namespaces. Eliminates point-to-point agent coupling.
- **Key Classes:**
  - `TargetSpace` (Line 53): Stores parsed AST, function signatures, class methods, and line counts.
  - `MutantSpace` (Line 70): Stores first-order mutant ASTs, diffs, operator types, and kill states.
  - `CriticSpace` (Line 88): Stores surviving mutant diagnostics, equivalence suspects, and testing directives.
  - `SuiteSpace` (Line 97): Stores generated test cases, scenario classifications, and validation status.
  - `MetricsSpace` (Line 111): Stores total mutants, killed mutants, surviving mutants, and mutation scores.
- **Key Functions:**
  - `_extract_safe_change_metadata` (Line 187): Sanitizes state changes for logging and audit serialization.
- **Calls:** `pydantic`, `testforge.models`.
- **Called By:** `testforge.orchestrator`, `testforge.agents`, `testforge.crew_critic`, `testforge.adk_generator`.

#### [`testforge/state.py`](file:///Users/sourabh/TestForge/testforge/state.py)
- **Primary Responsibility:** Finite State Machine (FSM) enforcing valid pipeline stage transitions.
- **Key Classes:**
  - `TaskLifecycleState` (Line 16): Enum of states (`IDLE`, `TARGET_INGESTION`, `MUTANT_GENERATION`, `BASELINE_EVALUATION`, `CRITIC_ANALYSIS`, `TEST_SYNTHESIS`, `FINAL_EVALUATION`, `COMPLETED`, `CANCELLED`, `FAILED`).
  - `StageRecord` (Line 47): Immutable timing and provenance record for a completed stage.
  - `InvalidStateTransitionError` (Line 57): Raised when an invalid state transition is attempted.
  - `TaskLifecycleFSM` (Line 183): Enforces valid state transitions and triggers lifecycle callbacks.
  - `MutantRecord` (Line 401): Typed representation of an individual mutant's execution history.

#### [`testforge/persistence.py`](file:///Users/sourabh/TestForge/testforge/persistence.py)
- **Primary Responsibility:** SQLite persistence manager for saving and resuming Blackboard state snapshots.
- **Key Classes:**
  - `CheckpointError` (Line 45), `CheckpointNotFoundError` (Line 50), `CorruptedSnapshotError` (Line 60).
  - `PersistenceManager` / `CheckpointRepository`: Manages schema creation and JSON-serialized state transactions in `qa_artifacts/testforge_checkpoints.db`.
- **Key Functions:**
  - `compute_source_hash` (Line 689): Generates SHA-256 fingerprint of target source code.
  - `determine_resumption_plan` (Line 694): Determines which pipeline stages can be skipped upon checkpoint restore.

---

### 2.2 Agent Implementations & Framework Bridges

#### [`testforge/agents.py`](file:///Users/sourabh/TestForge/testforge/agents.py)
- **Primary Responsibility:** Core agent definitions, AST signature extraction, granular scenario test synthesis, and offline fallback generation.
- **Key Classes:**
  - `CodeSanitizer` (Line 47): Strips dangerous imports and malformed code blocks.
  - `TestGeneratorAgent` (Line 353): Synthesizes granular unit test functions (`test_*_normal`, `test_*_boundary`, `test_*_negative`, `test_*_exception`) using AST metadata and domain heuristics.
  - `AdversarialCriticAgent` (Line 944): Evaluates surviving mutants and emits diagnostic guidance.
- **Key Functions:**
  - `extract_function_signatures` (Line 78): Parses AST to extract function names, arguments, defaults, and `is_method` flags.
  - `call_groq_api` (Line 100), `call_ollama_local` (Line 140): Optional live LLM API connectors.
  - `execute_multi_provider_generation` (Line 175): Cascading fallback provider (Groq -> Ollama -> Deterministic AST Generator).
  - `execute_genai_with_retry_and_fallback` (Line 331): Retries with exponential backoff before triggering offline synthesis.

#### [`testforge/crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py)
- **Primary Responsibility:** Integrates the CrewAI framework to wrap mutant survival critique in a structured multi-agent task.
- **Key Classes:**
  - `CrewAILLMBridge` (Line 61): Custom LLM adapter enabling CrewAI to run with live LLMs or deterministic local fallbacks.
  - `CrewAICriticAgent` (Line 194): Constructs a CrewAI `Agent` with `role="Senior Mutation Testing Critic"` and executes a `Task` returning a strongly-typed `CriticDirectivePayload`.

#### [`testforge/adk_generator.py`](file:///Users/sourabh/TestForge/testforge/adk_generator.py)
- **Primary Responsibility:** Integrates Google Agent Development Kit (ADK) constructs with an explicit tool registry for test synthesis.
- **Key Classes:**
  - `WorkflowCycleResult` (Line 77): Holds results of an ADK generation cycle.
  - `ADKModelBridge` (Line 95): Adapter interfacing with Google GenAI / ADK.
  - `GoogleADKTestGenerator` (Line 316): ADK-based generator executing against surviving mutant directives.
  - `GeneratorCriticWorkflow` (Line 577): Bi-directional generator-critic iterative loop.

#### [`testforge/adk_engine.py`](file:///Users/sourabh/TestForge/testforge/adk_engine.py)
- **Primary Responsibility:** Google ADK tool registry and context models.
- **Key Classes:**
  - `ToolDefinition` (Line 33): Schema describing a tool available to the ADK agent.
  - `ToolCallResult` (Line 42): Strongly-typed output of an ADK tool invocation.
  - `ADKContext` (Line 53): Execution context passed across ADK tool calls.
  - `ADKToolRegistry` (Line 63): Registry maintaining tool bindings (`inspect_target_ast`, `get_surviving_mutants`, `read_critic_guidance`, `synthesize_scenario_test`).

---

### 2.3 Mutation Engine & AST Analysis

#### [`testforge/mutator.py`](file:///Users/sourabh/TestForge/testforge/mutator.py)
- **Primary Responsibility:** Generates first-order Abstract Syntax Tree mutants using systematic operator replacement.
- **Key Classes:**
  - `MutationTransformer` (Line 37): Subclasses `ast.NodeTransformer` to locate mutation sites and generate modified AST copies.
  - `ASTMutator` (Line 342): High-level engine managing mutant compilation, line number mapping, and diff generation.
- **Supported Mutation Operators:**
  - `ComparisonOpReplacement`: Replaces `==` with `!=`, `<` with `<=`, `>` with `>=`, `is` with `is not`.
  - `ArithmeticOpReplacement`: Replaces `+` with `-`, `*` with `//`, `%` with `*`.
  - `InvertNegatives`: Replaces `-x` with `+x`.
  - `ConditionInversion`: Inverts boolean logic (`and` <-> `or`, `if X` <-> `if not X`).
  - `BoundaryModifier`: Adjusts numeric literals by $\pm 1$.

#### [`testforge/equivalence.py`](file:///Users/sourabh/TestForge/testforge/equivalence.py)
- **Primary Responsibility:** Detects and flags equivalent mutant suspects using AST pattern analysis.
- **Key Classes:**
  - `EquivalenceClassification` (Line 28): Enum (`EQUIVALENT`, `SURVIVED`, `KILLED`, `UNKNOWN`).
  - `EquivalenceConfidence` (Line 35): Confidence score (`HIGH`, `MEDIUM`, `LOW`).
  - `EquivalenceMethod` (Line 42): Detection method (`DEAD_CODE`, `ALGEBRAIC_IDENTITY`, `SEMANTIC_EQUIVALENCE`).
  - `EquivalenceResult` (Line 51): Pydantic model storing detection findings.
  - `DeadCodeVisitor` (Line 59): AST visitor identifying mutations in unreachable code branches.
- **Key Functions:**
  - `calculate_mutation_scores` (Line 298): Computes adjusted mutation score accounting for equivalent mutants.

#### [`testforge/blast_analyzer.py`](file:///Users/sourabh/TestForge/testforge/blast_analyzer.py)
- **Primary Responsibility:** Analyzes impact radius of functions and classes across call graphs.
- **Key Classes:**
  - `ASTCallGraphVisitor` (Line 23): Maps internal function call graphs.
  - `BlastRadiusAnalyzer` (Line 66): Computes downstream fan-out and impact scores for target modifications.

---

### 2.4 Protocols, Tooling & External Integrations

#### [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py) & [`testforge/mcp_servers.py`](file:///Users/sourabh/TestForge/testforge/mcp_servers.py)
- **Primary Responsibility:** FastMCP server implementations for tool integration.
- **Key Functions:**
  - `_is_path_safe` (Line 49): Validates that filesystem requests do not traverse outside designated directories (`..` attack prevention).
  - `create_filesystem_server` (Line 83): Creates FastMCP server with tools: `list_directory`, `get_file_info`, `read_text_file`.
  - `create_github_server` (Line 175): Creates FastMCP server with tool: `get_repository_info`.

#### [`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py) & [`testforge/a2a_protocol.py`](file:///Users/sourabh/TestForge/testforge/a2a_protocol.py)
- **Primary Responsibility:** Implements Agent-to-Agent (A2A) protocol schemas and endpoint dispatch.
- **Key Classes:**
  - `A2APerformative` (Line 46): FIPA-ACL inspired communicative acts (`REQUEST`, `INFORM`, `PROPOSE`, `REFUSE`).
  - `A2AMessage` (Line 56): Typed envelope for inter-agent messages.
  - `TestForgeA2AExecutor` (Line 165): Handles incoming A2A JSON-RPC requests.
- **Key Functions:**
  - `build_testforge_agent_card` (Line 98): Generates the Linux Foundation A2A v0.3.0 compliant JSON schema served at `/.well-known/agent-card.json`.

---

### 2.5 Security, Sandboxing & Observability

#### [`testforge/sandbox.py`](file:///Users/sourabh/TestForge/testforge/sandbox.py)
- **Primary Responsibility:** Executes tests against target mutants in an isolated subprocess.
- **Key Classes:**
  - `ParallelSandboxRunner` (Line 174): Executes test suites across worker processes with bounded timeouts.
  - `TestValidationStatus` (Line 404): Status enum (`PASSED`, `FAILED`, `SYNTAX_ERROR`, `TIMEOUT`).
  - `CandidateSuiteValidationResult` (Line 428): Aggregated outcome of a test suite execution.
  - `GranularTestValidator` (Line 444): Validates that individual generated test functions execute cleanly before admitting them into the final suite.

#### [`testforge/network_security.py`](file:///Users/sourabh/TestForge/testforge/network_security.py)
- **Primary Responsibility:** Outbound socket egress interception and SSRF protection.
- **Key Classes:**
  - `SSRFSecurityError` (Line 61): Raised when an unauthorized IP/domain connection is attempted.
  - `PayloadTooLargeError` (Line 66): Raised when an HTTP download exceeds size thresholds.
  - `SafeGitHubRedirectHandler` (Line 196): Enforces redirect safety on external repository fetching.
- **Key Functions:**
  - `validate_url_hostname` (Line 110): Blocks private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8).
  - `bounded_read` (Line 267): Reads stream up to a maximum byte limit to prevent memory exhaustion.

#### [`testforge/prompt_guard.py`](file:///Users/sourabh/TestForge/testforge/prompt_guard.py)
- **Primary Responsibility:** Defends against indirect prompt injection in target source code and comments.
- **Key Classes:**
  - `InjectionFinding` (Line 66), `InjectionScanResult` (Line 76): Scans source code for instruction overrides (e.g. `Ignore previous instructions`).
- **Key Functions:**
  - `wrap_untrusted_content` (Line 84): Wraps ingested target code in strict XML boundaries (`<untrusted_source_code>`).
  - `sanitize_critic_directive` (Line 286): Strips dangerous directives from Critic recommendations.

#### [`testforge/callbacks.py`](file:///Users/sourabh/TestForge/testforge/callbacks.py) & [`testforge/websocket_hub.py`](file:///Users/sourabh/TestForge/testforge/websocket_hub.py)
- **Primary Responsibility:** Real-time event streaming and monitoring.
- **Key Classes:**
  - `EventType` (Line 33): Enum of lifecycle events (`PIPELINE_START`, `AGENT_START`, `AGENT_COMPLETE`, `MUTANT_PASS`, `CRITIC_DIAGNOSTIC`, `SUITE_VALIDATED`, `CHECKPOINT_SAVED`).
  - `AgentCallbackHandler` (Line 80): Hooks into agent execution to emit structured payloads.
  - `WebSocketEventHub` (Line 29): Manages active WebSocket connections and broadcasts JSON events to the frontend.

---

## 3. PRESENTATION LAYER MODULES (`frontend/`)

- [`frontend/index.html`](file:///Users/sourabh/TestForge/frontend/index.html):
  - Responsive single-page layout featuring a sticky header with live WebSocket status pill, system metrics bar, and tab navigation.
  - Six primary tabs: Overview, Interactive Sandbox, Target Analysis, Mutant Inspector, Test Studio, and Observability & Benchmarks.
  - Active Job Cancellation button (`#cancel-job-btn`) and Checkpoint Diff modal viewer.
- [`frontend/app.js`](file:///Users/sourabh/TestForge/frontend/app.js):
  - Single state store managing `currentJobId`, `activeTab`, `targetCode`, `mutantsList`, and `testResults`.
  - WebSocket handler connecting to `/ws/events` with auto-reconnect backoff and terminal streaming.
  - REST client making typed `fetch` requests to `/api/harden/start`, `/api/harden/status`, `/api/harden/cancel`, `/api/samples`, and `/api/checkpoints`.
- [`frontend/style.css`](file:///Users/sourabh/TestForge/frontend/style.css):
  - Custom CSS variables for consistent dark-theme styling (`--bg-primary: #0f172a`, `--accent-teal: #14b8a6`, `--accent-cyan: #06b6d4`).
  - Responsive media queries for desktop (1920x1080), laptop (1280x800), tablet (768x1024), and mobile (375x667).

---

## 4. GATEWAY SERVER (`server.py`)

- **Primary Route Definitions:**
  - `GET /`: Serves `frontend/index.html`.
  - `GET /healthz`: Health probe returning `{"status": "healthy", "version": "2.0.0"}`.
  - `GET /.well-known/agent-card.json`: Serves A2A discovery card (protocol v0.3.0).
  - `GET /api/samples`: Lists available target modules in `samples/`.
  - `POST /api/ingest/upload`: Accepts user `.py` file uploads with size and syntax validation.
  - `POST /api/harden/start`: Spawns async background hardening pipeline returning `job_id`.
  - `GET /api/harden/status/{job_id}`: Polls real-time job progress, current stage, and mutation metrics.
  - `POST /api/harden/cancel/{job_id}`: Signals cooperative cancellation token to halt running pipeline.
  - `GET /api/checkpoints`: Lists historical checkpoints from `qa_artifacts/testforge_checkpoints.db`.
  - `GET /api/checkpoints/diff`: Generates line-by-line diff between two checkpoint runs.
  - `GET /api/mcp/status`: Reports health and tool registrations for FastMCP servers.
  - `GET /ws/events`: WebSocket endpoint streaming real-time JSON lifecycle events.

