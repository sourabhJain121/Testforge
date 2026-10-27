# TestForge — Complete Repository Architecture & Subsystem Mapping

**Audit Date:** 2026-10-27  
**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Architectural Overview

TestForge is an autonomous agentic unit-test hardening and mutation-guided repair platform. It connects a FastAPI backend serving a modern HTML5/CSS3/JavaScript web interface with an iterative multi-agent reflection loop, an in-memory topic-partitioned Blackboard, an atomic SQLite checkpoint store, Model Context Protocol (FastMCP) tool servers, and Agent-to-Agent (A2A) discovery endpoints.

```text
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                       |
|               (frontend/index.html, frontend/app.js, frontend/style.css)                |
|   - Mode A/B/C Ingestion       - Interactive SVG Blast Radius Graph                     |
|   - Real-Time WebSocket Feed   - Hardening Controls & Progress Indicator                |
|   - Checkpoint Diff Inspector  - MCP Tool Status Panel & A2A AgentCard Modal            |
+--------------------------------------------+--------------------------------------------+
                                             | HTTP REST / WebSocket (/ws/events)
                                             v
+-----------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION (server.py)                           |
|   - REST Endpoints (/api/harden, /api/ingest, /api/analysis, /api/mcp/status, /readyz)  |
|   - WebSocket Streaming Hub (testforge/websocket_hub.py)                                |
|   - A2A AgentCard Endpoint (/.well-known/agent.json, /.well-known/agent-card.json)      |
|   - Static Files Mount (/static -> frontend/)                                           |
+--------------------------------------------+--------------------------------------------+
                                             |
                      +----------------------+----------------------+
                      |                                             |
                      v                                             v
+------------------------------------------+  +-------------------------------------------+
|  BLACKBOARD & PERSISTENCE                |  |  EXTERNAL PROTOCOLS & INTEGRATIONS        |
|  - Blackboard (testforge/blackboard.py)  |  |  - FastMCP Server (testforge/mcp_server.py)|
|    Partitioned Pub/Sub State Store       |  |    (Filesystem & GitHub stdio JSON-RPC)   |
|  - SQLite Storage                        |  |  - FastMCP Client (testforge/mcp_client.py)|
|    (testforge/persistence.py)            |  |  - A2A Task Server (testforge/a2a.py)     |
|    Checkpoints, Rollback, Resumption     |  |  - Google ADK Engine (adk_engine.py)      |
|  - State Models (testforge/state.py)     |  |  - CrewAI Critic (crew_critic.py)         |
+---------------------+--------------------+  +---------------------+---------------------+
                      |                                             |
                      +----------------------+----------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                         AGENTIC TEST HARDENING PIPELINE                                 |
|                                                                                         |
|   +-----------------------+              +------------------------------------------+   |
|   |  TargetManagerAgent   |              |          ParallelSandboxRunner           |   |
|   |  (AST Ingestion)      |              |  - Granular Test Validation (clean ref)  |   |
|   +-----------+-----------+              |  - Parallel AST Mutant Evaluation        |   |
|               |                          +--------------------+---------------------+   |
|               v                                               |                         |
|   +-----------------------+                                   v                         |
|   |  TestGeneratorAgent   | <======= (Surviving AST Diffs) ===+                         |
|   |  - Zero-Shot Prompt   |                                   |                         |
|   |  - Reflection Prompt  |                                   v                         |
|   |  - AST Fallback Synth |              +--------------------+---------------------+   |
|   +-----------+-----------+              |          AdversarialCriticAgent          |   |
|               |                          |  - Synthesizes Adversary Directives      |   |
|               +--- (Candidate Tests) --> |  - Guides Targeted Reflection Hardening  |   |
|                                          +------------------------------------------+   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Directory and Component Map

| Subsystem | Key Files | Functionality |
|---|---|---|
| **Core Entry Points** | `server.py`<br>`app.py` | FastAPI application, Uvicorn runner, routes, and Streamlit alternative. |
| **Frontend UI** | `frontend/index.html`<br>`frontend/app.js`<br>`frontend/style.css` | 5-tab user interface with SVG blast radius call graph, checkpoint diff inspector, live WebSocket stream, and A2A modal. |
| **Agents & Orchestration** | `testforge/orchestrator.py`<br>`testforge/agents.py`<br>`testforge/ingestion.py`<br>`testforge/guidance.py` | Full multi-pass hardening pipeline, candidate generation, surviving mutant guidance, and code sanitization. |
| **Mutator & Sandbox** | `testforge/mutator.py`<br>`testforge/sandbox.py`<br>`testforge/equivalence.py` | AST mutation operators (`BinOp`, `Compare`, `Constant`, `IfCondition`), granular candidate validator, parallel execution sandbox. |
| **State & Persistence** | `testforge/blackboard.py`<br>`testforge/state.py`<br>`testforge/persistence.py` | In-memory pub/sub blackboard, Pydantic state models (`TestForgeState`, `MutantRecord`), SQLite atomic checkpoint storage. |
| **Protocols (MCP & A2A)** | `testforge/mcp_server.py`<br>`testforge/mcp_client.py`<br>`testforge/a2a.py`<br>`testforge/a2a_protocol.py` | FastMCP stdio tool servers (Filesystem & GitHub), MCP client, A2A AgentCard discovery and task server. |
| **Security & Guardrails** | `testforge/security.py` | Prompt injection inspection (`INJ_*`), static AST policy enforcement (`SEC_AST_*`), credential scrubbing. |
| **Observability & Hub** | `testforge/logger.py`<br>`testforge/callbacks.py`<br>`testforge/websocket_hub.py` | Structured JSONL trace logger with correlation IDs, typed lifecycle events, and real-time WebSocket event broadcaster. |
| **Framework Integrations** | `testforge/crew_critic.py`<br>`testforge/adk_generator.py`<br>`testforge/adk_engine.py` | CrewAI agent wrapper, Google ADK workflow engine, and GenAI SDK integration. |
| **Evaluation Corpus** | `testforge/corpus/runner.py`<br>`testforge/corpus/fixtures/*` | 5 reference fixtures, defect variants, multi-strategy empirical benchmark runner. |
