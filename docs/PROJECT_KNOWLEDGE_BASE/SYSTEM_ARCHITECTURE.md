# TESTFORGE — SYSTEM ARCHITECTURE SPECIFICATION
## Comprehensive End-to-End Architectural Topology, Component Interconnects & Data Flows

**Document Version:** 2.0.0  
**Target Audience:** Systems Architects, Evaluators, AI Engineers  
**Authoritative Location:** `docs/PROJECT_KNOWLEDGE_BASE/SYSTEM_ARCHITECTURE.md`

---

## 1. HIGH-LEVEL ARCHITECTURAL TOPOLOGY

TestForge is organized as a modular, decoupled, event-driven system comprising six core architectural layers:
1. **Presentation Layer:** Single-Page Application (SPA) built with HTML5, CSS3, and Vanilla JavaScript, communicating via REST and WebSockets.
2. **API & Protocol Gateway:** FastAPI backend hosting REST APIs, streaming WebSockets, FastMCP tool servers, and the Linux Foundation Agent-to-Agent (A2A) discovery card.
3. **Orchestration & Coordination Layer:** Async orchestration engine executing sequential and iterative hardening pipelines with cooperative cancellation tokens.
4. **Agentic Subsystem:** Specialized agents operating under supervisor-worker and critic-reflector paradigms with framework wrappers for CrewAI and Google ADK.
5. **Shared State & Memory Layer:** Typed in-memory Blackboard architecture partitioned into five isolated namespaces with complete provenance tracking and SQLite checkpoint persistence.
6. **Execution & Security Sandbox Layer:** Subprocess execution sandbox with bounded wall-clock timeouts, AST-level import blacklisting, prompt injection sanitizers, and outbound socket egress interception.

```mermaid
graph TD
    subgraph UI ["Layer 1: Presentation (SPA)"]
        HTML["index.html"]
        CSS["style.css"]
        JS["app.js (State, DOM, WebSocket)"]
    end

    subgraph API ["Layer 2: Gateway & Protocols (server.py)"]
        FastAPI["FastAPI App (Port 8000)"]
        WS["/ws/events (WebSocket Broadcaster)"]
        A2A["/.well-known/agent-card.json (v0.3.0)"]
        MCP1["FastMCP: filesystem-samples"]
        MCP2["FastMCP: github-service"]
    end

    subgraph ORCH ["Layer 3: Orchestration (testforge/orchestrator.py)"]
        Pipeline["OrchestratorEngine"]
        Callbacks["AgentCallbackHandler"]
        CancelToken["Cooperative CancellationToken"]
    end

    subgraph AGENTS ["Layer 4: Agent Subsystem (testforge/)"]
        TA["TargetAnalyzerAgent"]
        MG["MutantGeneratorAgent"]
        CR["CrewAICriticAgent (CrewAI)"]
        TG["GoogleADKTestGenerator (Google ADK)"]
        EV["EvaluatorAgent"]
    end

    subgraph BB ["Layer 5: Blackboard & Storage (testforge/blackboard.py)"]
        TS["TargetSpace"]
        MS["MutantSpace"]
        CS["CriticSpace"]
        SS["SuiteSpace"]
        MET["MetricsSpace"]
        SQLite[("SQLite: checkpoints.db")]
    end

    subgraph SANDBOX ["Layer 6: Security & Sandbox (testforge/)"]
        Box["Subprocess Sandbox (sandbox.py)"]
        Guard["PromptGuard & AST Sanitizer (guardrails.py)"]
        NetSec["Socket Egress Interceptor (network_security.py)"]
    end

    %% Interconnects
    UI <--> |REST API / HTTP| FastAPI
    UI <--> |Live Streaming Events| WS
    FastAPI --> Pipeline
    FastAPI --> A2A
    FastAPI --> MCP1
    FastAPI --> MCP2

    Pipeline --> Callbacks
    Callbacks --> WS
    Pipeline --> CancelToken
    Pipeline --> AGENTS

    TA --> TS
    MG --> MS
    CR --> CS
    TG --> SS
    EV --> MET

    TS --> BB
    MS --> BB
    CS --> BB
    SS --> BB
    MET --> BB
    BB --> SQLite

    AGENTS --> Guard
    AGENTS --> NetSec
    EV --> Box
    Box --> NetSec
```

---

## 2. COMPONENT DEEP-DIVE & RESPONSIBILITY MATRIX

| Layer | Module / File | Primary Class / Symbol | Exact Responsibility |
| :--- | :--- | :--- | :--- |
| **API** | `server.py` | `app = FastAPI(...)` | Exposes REST endpoints, manages WebSocket life-cycle, hosts static assets, mounts A2A discovery card, and delegates pipeline jobs. |
| **Orchestration** | `testforge/orchestrator.py` | `OrchestratorEngine` | Drives multi-stage hardening loops, manages step timeouts, executes fallback chains, and checks cancellation tokens. |
| **Callbacks** | `testforge/callbacks.py` | `AgentCallbackHandler` | Captures lifecycle events (`on_agent_start`, `on_tool_start`, `on_mutation_pass`) and pushes JSON events to queues. |
| **Blackboard** | `testforge/blackboard.py` | `Blackboard` | Thread-safe, typed state repository with 5 isolated namespaces (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`). |
| **Checkpoints** | `testforge/checkpoints.py` | `CheckpointManager` | Serializes Blackboard state snapshots to SQLite (`checkpoints.db`) with run resumption and AST diff generation. |
| **Target Analyzer** | `testforge/agents.py` | `TargetAnalyzerAgent` | Decomposes Python source code using AST visitors into classes, functions, argument types, and control flow graphs. |
| **Mutant Generator** | `testforge/agents.py`<br>`testforge/mutator.py` | `MutantGeneratorAgent`<br>`ASTMutator` | Injects first-order syntactic mutations (`InvertNegatives`, `ComparisonOpReplacement`, `ArithmeticOpReplacement`, `ConditionInversion`). |
| **Critic Agent** | `testforge/crewai_critic.py` | `CrewAICriticAgent` | Wraps CrewAI task/agent execution to analyze surviving mutants, diagnose coverage gaps, and author targeted test directives. |
| **Test Generator** | `testforge/adk_generator.py`<br>`testforge/agents.py` | `GoogleADKTestGenerator`<br>`TestGeneratorAgent` | Utilizes Google ADK tool registries and AST schema heuristics to synthesize scenario tests (`normal`, `boundary`, `negative`, `exception`). |
| **Evaluator** | `testforge/agents.py` | `EvaluatorAgent` | Runs generated test suites against all first-order mutants, classifies outcomes, and calculates mutation scores. |
| **Execution Sandbox** | `testforge/sandbox.py` | `IsolatedSandbox` | Executes pytest in an isolated subprocess with memory bounds, bounded execution timeouts, and strict error containment. |
| **Network Security** | `testforge/network_security.py` | `NetworkSecurityContext` | Monkeys-patches low-level socket connections during testing runs to actively block unauthorized outbound TCP/HTTP egress. |
| **Guardrails** | `testforge/guardrails.py` | `SecurityGuardrails` | Sanitizes untrusted user inputs, detects prompt injection payloads, and enforces AST-level import blacklisting. |
| **FastMCP Servers** | `testforge/mcp_servers.py` | `mcp_filesystem`, `mcp_github` | Official FastMCP instances exposing standard MCP tool interfaces for filesystem inspection and GitHub repository reading. |
| **A2A Protocol** | `server.py`<br>`testforge/a2a.py` | `AgentCard` schema | Publishes metadata at `/.well-known/agent-card.json` conforming to Linux Foundation Agent-to-Agent discovery v0.3.0. |

---

## 3. BLACKBOARD DATA FLOW & STATE PARTITIONS

The Blackboard pattern eliminates direct point-to-point agent dependencies. Each agent writes exclusively to its dedicated partition and consumes verified data from preceding partitions.

```mermaid
graph LR
    subgraph BB ["In-Memory Blackboard (testforge/blackboard.py)"]
        direction TB
        TSpace["1. TargetSpace<br>• AST Source Tree<br>• Function Signatures<br>• Class Methods<br>• Type Annotations"]
        MSpace["2. MutantSpace<br>• First-Order Mutants<br>• Operator Enums<br>• Line Numbers<br>• AST Diff Snippets"]
        CSpace["3. CriticSpace<br>• Surviving Mutant Diffs<br>• Equivalence Suspects<br>• Testing Directives<br>• Suggested Boundary Values"]
        SSpace["4. SuiteSpace<br>• Synthesized Test Code<br>• Granular Scenarios<br>• Assertion Schemas<br>• Pytest Fixtures"]
        MetricsSpace["5. MetricsSpace<br>• Total Mutants<br>• Mutants Killed<br>• Mutants Survived<br>• Mutation Score %"]
    end

    TAgent[TargetAnalyzerAgent] -->|Write| TSpace
    TSpace -->|Read| MAgent[MutantGeneratorAgent]
    MAgent -->|Write| MSpace
    MSpace -->|Read Baseline Results| CAgent[CrewAICriticAgent]
    CAgent -->|Write| CSpace
    CSpace -->|Read Guidance| TGAgent[GoogleADKTestGenerator]
    TSpace -->|Read Signatures| TGAgent
    TGAgent -->|Write| SSpace
    SSpace -->|Read Suite| EVAgent[EvaluatorAgent]
    MSpace -->|Read Mutants| EVAgent
    EVAgent -->|Write Final Scores| MetricsSpace
    MetricsSpace -->|Snapshot| DB[(SQLite: checkpoints.db)]
```

---

## 4. END-TO-END EXECUTION FLOW & STATE MACHINE

```mermaid
stateDiagram-v2
    [*] --> Idle: Server Initialized (Port 8000)
    
    Idle --> Ingestion: POST /api/ingest/upload OR /api/ingest/sample
    Ingestion --> ASTValidation: Validate Python AST
    
    ASTValidation --> SyntaxError: Parsing Fails (SyntaxError)
    SyntaxError --> Idle: Return 400 with Line/Col Info
    
    ASTValidation --> Analysis: POST /api/harden/start
    state HardeningPipeline {
        [*] --> TargetAnalysis
        TargetAnalysis --> MutantGeneration: TargetSpace Written
        MutantGeneration --> BaselineEvaluation: MutantSpace Written (N Mutants)
        
        BaselineEvaluation --> MutantEvaluationLoop
        state MutantEvaluationLoop {
            [*] --> SandboxExec
            SandboxExec --> CheckTimeout
            CheckTimeout --> ClassifyOutcome: Killed / Survived / Errored
        }
        
        MutantEvaluationLoop --> CriticDiagnosis: Baseline Score Calculated
        CriticDiagnosis --> TestSynthesis: CriticSpace Directives Emitted
        TestSynthesis --> HardenedEvaluation: SuiteSpace Tests Synthesized
        
        HardenedEvaluation --> ScoreVerification: Hardened Score > Baseline Score?
        ScoreVerification --> CheckpointPersistence: Save Run to SQLite
    }

    HardeningPipeline --> PipelineCompleted: Success Event Broadcast
    HardeningPipeline --> PipelineCancelled: POST /api/harden/cancel/{job_id}
    
    PipelineCompleted --> Idle: UI Renders Results & Diff Viewer
    PipelineCancelled --> Idle: Partial State Preserved, Status=CANCELLED
```

---

## 5. TEST GENERATION AND MUTATION ALGORITHM

```mermaid
flowchart TD
    Start([Input Source Code]) --> ParseAST[Parse Abstract Syntax Tree ast.parse]
    ParseAST --> ExtractEntities[Extract Callables, Classes, Arguments & Types]
    
    subgraph MutationPhase ["Mutant Generation Engine (ASTMutator)"]
        ExtractEntities --> MutateCompare[Mutate Comparisons: == to !=, < to <=, > to >=]
        ExtractEntities --> MutateMath[Mutate Arithmetic: + to -, * to //]
        ExtractEntities --> MutateLogic[Mutate Logic: and to or, not X to X]
        ExtractEntities --> MutateBoundaries[Mutate Constants: 0 to 1, 1 to 0, N to N+1]
        MutateCompare --> CollectMutants[Compile First-Order Mutant ASTs]
        MutateMath --> CollectMutants
        MutateLogic --> CollectMutants
        MutateBoundaries --> CollectMutants
    end

    CollectMutants --> RunBaseline[Execute Baseline Pytest Suite in Sandbox]
    RunBaseline --> EvaluateSurvivors{Did Mutants Survive?}
    
    EvaluateSurvivors -- No (100% Score) --> FinalMetrics[Compute Final Metrics]
    EvaluateSurvivors -- Yes (Survivors > 0) --> CrewAICritic[CrewAI Critic Analyzes Surviving Diffs]
    
    subgraph SynthesisPhase ["Targeted Test Synthesis (ADK & Generator)"]
        CrewAICritic --> FormulateDirectives[Formulate Test Directives & Boundary Suggestions]
        FormulateDirectives --> GenNormal[Synthesize Normal Execution Tests test_*_normal]
        FormulateDirectives --> GenBoundary[Synthesize Boundary Condition Tests test_*_boundary]
        FormulateDirectives --> GenNegative[Synthesize Negative Argument Tests test_*_negative]
        FormulateDirectives --> GenException[Synthesize Exception Tests pytest.raises]
        GenNormal --> AssembleSuite[Assemble Granular Pytest Suite]
        GenBoundary --> AssembleSuite
        GenNegative --> AssembleSuite
        GenException --> AssembleSuite
    end

    AssembleSuite --> ReRunSandbox[Execute Hardened Suite Against All Mutants]
    ReRunSandbox --> ComputeDelta[Calculate Mutation Score Delta and Killed Jump]
    ComputeDelta --> FinalMetrics
    FinalMetrics --> StoreDB[(Save SQLite Checkpoint)]
```

---

## 6. FAILURE CONTAINMENT & SECURITY ARCHITECTURE

```mermaid
flowchart LR
    subgraph UntrustedZone ["Untrusted Input Ingestion"]
        Upload[File Upload / Webhook]
        Prompt[LLM Prompts / Guidance]
    end

    subgraph DefenseLayer ["Multi-Layer Guardrails"]
        Sanitizer["1. PromptGuard & AST Sanitizer<br>• Blacklist: os, sys, subprocess, pty<br>• Filter: {{...}}, <script>, SQLi patterns"]
        Subprocess["2. Subprocess Sandbox<br>• Strict Wall-Clock Timeout (e.g. 5.0s)<br>• Memory Cap (RLIMIT_AS)<br>• Ephemeral Directory Isolation"]
        SocketTrap["3. Socket Egress Interceptor<br>• Patches socket.create_connection<br>• Blocks 0.0.0.0/0 egress<br>• Whitelists 127.0.0.1:8000 only"]
    end

    subgraph SafeCore ["TestForge Application Core"]
        Engine["Orchestrator & Agents"]
        Storage["checkpoints.db"]
    end

    UntrustedZone --> DefenseLayer
    Sanitizer --> Engine
    Engine --> Subprocess
    Subprocess --> SocketTrap
    SocketTrap --> Storage
```

