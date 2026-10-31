# Stage 9: Phase 2 Evaluation Master Checklist

**Project:** TestForge  
**Evaluation Scope:** Phase 2 Academic & Technical Review  
**Stack:** FastAPI Backend + Vanilla JS Frontend (`http://127.0.0.1:8000/`)  

---

## 1. What to Show Live in the Running UI (`http://127.0.0.1:8000/`)

| Feature / Capability | Demonstration Action | What Evaluator Observes |
|---|---|---|
| **FastAPI-Only Architecture** | Open `http://127.0.0.1:8000/` and show port 8501 is unbound. | Instant page load, dark theme UI, zero Streamlit dependencies. |
| **Target Ingestion & AST Parsing** | Select sample `samples/discount.py` and click **Ingest & Parse Target**. | Real-time parsing, line count, class/function inventory, AST validation. |
| **Syntax Error Containment** | Upload `samples/uploaded_08_syntax_error.py`. | UI cleanly captures line 1 syntax error without server crash or unhandled 500. |
| **Blast Radius Dependency Graph** | Switch to **Mutations & Blast Radius** tab, click **Calculate Blast Radius**. | Interactive graph rendering target function, upstream callers, downstream callees. |
| **FastMCP Tool Discovery** | Click **Inspect MCP Tools** in top-right header. | Modal lists active MCP tools (`read_file_tool`, `list_dir_tool`, `fetch_github_file_tool`). |
| **Autonomous Test Generation** | Switch to **Workspace & Pipeline**, click **Start Hardening Pipeline**. | Event stream logs state transitions via WebSocket; tests generated and executed. |
| **AST Mutation Evaluation** | View mutation score card after pipeline run. | Displays total mutants generated, killed count, survival count, and mutation score. |
| **Blackboard State Inspection** | Switch to **Blackboard & Agents** tab. | Shows partitioned spaces (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`). |
| **A2A Agent Card Discovery** | Navigate browser to `http://127.0.0.1:8000/.well-known/agent-card.json`. | RFC/A2A-compliant Agent Card JSON declaring capabilities and protocol version `0.3.0`. |

---

## 2. What to Show via Source Code Walkthrough

| Subsystem | Source Code Path | Key Implementation Concepts to Highlight |
|---|---|---|
| **Partitioned Blackboard** | `testforge/blackboard.py` | `TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`; thread-safe `threading.RLock()`; subscription callback dispatch. |
| **FastMCP Tools** | `testforge/mcp_server.py`, `testforge/mcp_client.py` | FastMCP server factories, tool schema decorators, permitted root sandbox restriction. |
| **Pydantic Structured Outputs** | `testforge/state.py`, `testforge/ingestion.py` | `MutantRecord`, `IngestionAnalysis`, `HardeningRunPayload`, strict validation rules. |
| **CrewAI Critic Agent** | `testforge/crew_critic.py` | Integration with CrewAI `1.15.28`, critic task prompting on surviving mutants, deterministic fallback synthesis. |
| **Google ADK Integration** | `testforge/adk_engine.py`, `testforge/adk_generator.py` | Google ADK tool registry, context scoping, and sandboxed test generation. |
| **4-Tier LLM Fallback Chain** | `testforge/llm.py`, `testforge/agents.py` | Gemini -> OpenRouter -> Ollama -> AST Deterministic Synthesizer. Guarantees zero runtime failure. |
| **Network Security & SSRF** | `testforge/network_security.py` | Private IP blocking (RFC 1918), AWS/GCP metadata filtering, GitHub domain whitelist, 5MB streaming bounds. |
| **Indirect Prompt Injection** | `testforge/prompt_guard.py` | Comment/docstring scanner, directive defusal, untrusted content tag wrappers (`<untrusted_content>`). |
| **Subprocess Execution Sandbox** | `testforge/sandbox.py` | `ParallelSandboxRunner`, temporary isolated scratch directories, execution timeouts. |
| **SQLite Checkpoints & Rollback** | `testforge/persistence.py`, `testforge/diff_inspector.py` | SQLite schema, snapshot serializations, state diffing, and restoration. |

---

## 3. What to Show via Saved Evidence & Benchmark Artifacts

| Verification Evidence | File Location | Key Metrics & Data Points |
|---|---|---|
| **Full Regression Results** | `qa_artifacts/pre_phase2_readiness/04_REGRESSION_RESULTS.md` | **523 / 523 passed** (100%), 0 failures, 208.58s runtime, exit code 0. |
| **Security Test Results** | `qa_artifacts/pre_phase2_readiness/02_SECURITY_AND_FAILURE_AUDIT.md` | **84 / 84 passed** (100%), 0 failures: SSRF, download limits, prompt injections. |
| **Quality Benchmark Results** | `qa_artifacts/pre_phase2_readiness/03_TEST_QUALITY_BENCHMARK.md` | 6 modules benchmarked, 100% test pass rate, up to 72% mutation score, <10ms generation. |
| **End-to-End Core Workflow** | `qa_artifacts/pre_phase2_readiness/stage2_core_workflow_results.json` | 240 LOC target, 11 callables, 258 mutants generated, 26/26 tests passed in 242ms. |
| **Frontend Acceptance Screenshots** | `qa_artifacts/pre_phase2_readiness/screenshots/` | 18 timestamped PNG screenshots across Desktop, Tablet, and Mobile viewports. |
| **Structured Trace Logs** | `testforge_trace.jsonl` | 33,389+ real execution events logged with correlation IDs and timestamps. |
| **Pre-Phase 2 Safe Backup** | `/Users/sourabh/TestForge_backups/backup_pre_phase2_20261030_153421/` | Full repository backup preserved outside workspace with verified exit code 0. |

---

## 4. Known Limitations to Transparently Acknowledge Upfront

Being transparent about system limitations demonstrates engineering rigor and academic integrity:

1. **Local Evaluation Environment (Cloud Deployment Boundary):**
   - *Status:* Container definitions (`Dockerfile`, `docker-compose.yml`) are verified and complete, but no live public cloud URL is deployed, as all evaluation is local per evaluation requirements.
2. **0-Shot Deterministic AST Smoke Generation vs. Deep Behavioral Tests:**
   - *Status:* When external LLM APIs are offline, Tier 4 deterministic generation synthesizes valid unit tests based on AST function signatures and type bounds. For complex multi-class business logic (e.g. `logistics_engine.py`), killing complex semantic mutants requires targeted behavioral assertions (as demonstrated in the 26-test suite).
3. **CrewAI Upstream Deprecation Warnings:**
   - *Status:* Running `pytest` emits upstream library deprecation warnings from CrewAI 1.15.28 (`function_calling_llm is deprecated`). These originate inside the third-party package and do not impact functionality or test pass rates.
4. **Permanent Streamlit Disablement:**
   - *Status:* Port 8501 is permanently disabled; the application runs exclusively on FastAPI at `http://127.0.0.1:8000/`. Historical Streamlit source files are preserved in the repository for academic evaluation record.

