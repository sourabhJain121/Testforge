# TestForge — Protocol & Integration Audit

**Audit Date:** 2026-10-27 01:19:00 IST  
**Artifact Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Model Context Protocol (MCP) Verification (MUST 2)

TestForge integrates the official Model Context Protocol (`mcp-python` v1.28.0) via `testforge/mcp_server.py` and `testforge/mcp_client.py`:
- **Server Registration:** FastMCP transports instantiated over stdio JSON-RPC 2.0.
- **Server 1 (`testforge-filesystem`):**
  - Bounded by project root (`samples_dir`).
  - 3 tools: `read_text_file`, `list_directory`, `get_file_info`.
  - Confirmed: Ingesting target source files triggers `get_file_info` to record provenance and SHA-256 fingerprint.
- **Server 2 (`testforge-github`):**
  - Tool: `get_repository_info`.
  - Gracefully handles rate-limiting for unauthenticated public repo queries.
- **Verification Evidence:** `pytest tests/test_mcp.py tests/test_orchestration_mcp.py` passes 100%.

---

## 2. Official A2A Protocol Implementation (MUST 6)

- **Standard Compliance:** TestForge implements the official `a2a-sdk` specification v0.3.0.
- **Discovery Endpoint (`/.well-known/agent.json`):**
  - Delivers valid JSON schema with `name: "TestForge Agent"`, `version: "2.0.0"`, `capabilities`, `skills`, and supported interaction protocols.
- **Agent Handlers Registered:**
  - `agent:google-adk:generator`
  - `agent:crewai:critic`
- **Verification Evidence:** `pytest tests/test_a2a_protocol.py tests/test_a2a.py` passes 100%.

---

## 3. Dual Framework Orchestration (MUST 7)

- **Framework Boundary:** Exactly two agent frameworks are permitted and integrated: Google ADK and CrewAI.
- **Google ADK Generator (`testforge/adk_generator.py`):**
  - Formulates structured prompts, manages test generation iterations, and emits `GeneratedTestPayload`.
- **CrewAI Critic (`testforge/crew_critic.py`):**
  - Constructs multi-agent reasoning tasks analyzing surviving mutants, emitting `CriticDirectivePayload`.
- **Verification Evidence:** Zero third-party agent frameworks (e.g. LangChain, AutoGen) are imported or executed.
