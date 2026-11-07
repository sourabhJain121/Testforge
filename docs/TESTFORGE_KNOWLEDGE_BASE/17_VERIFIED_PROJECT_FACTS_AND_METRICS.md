# TestForge — Authoritative Fact Sheet & Verified Metrics Reference

**Document Version:** 1.0.0 (Authoritative Final)  
**Verification Date:** November 2, 2026  
**Repository Working Directory:** `/Users/sourabh/TestForge`  
**Git HEAD Commit:** `ee8f765c4f7316e87439fab7250103e6da651c02`  
**Runtime Environment:** `.venv-release` (Python 3.13.18, pytest-9.1.1, macOS Darwin arm64)  

---

## 1. Executive Ground Truth Fact Sheet

This document serves as the **single source of truth** for all technical facts, metrics, and configurations across the TestForge project. Every value is verified directly against repository source files, test runners, SQLite tables, or raw telemetry files.

| Metric / Dimension | Authoritative Verified Value | Primary Source Evidence | Verification Method |
| :--- | :--- | :--- | :--- |
| **Project Full Name** | TestForge — Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops | `README.md`, `pyproject.toml` | Verified |
| **Total Test Suite** | **611 passed, 0 failed, 311 warnings** | `tests/` (51 test files) | Executed `.venv-release/bin/python -m pytest tests/ -q` (378.65s) |
| **Statement Coverage** | **81.33% statement coverage** | `testforge/` core engine | `pytest --cov=testforge` / `.coverage` |
| **Discount Mutation (Raw)** | **89.47%** (17/19 mutants killed) | `samples/discount_module.py` | AST Mutator execution in `test_hardened.py` |
| **Discount Mutation (Adj)** | **94.44%** (17/18 non-equivalent killed) | `testforge/equivalence.py` | Excludes 1 verified dead-code mutant |
| **Logistics Mutation (Raw)**| **68.22%** (176/258 mutants killed)| `samples/logistics_module.py` | AST Mutator execution in `test_hardened.py` |
| **Logistics Mutation (Adj)**| **75.21%** (176/234 non-equivalent killed)| `testforge/equivalence.py` | Excludes 24 verified equivalent mutants |
| **Security Guardrails** | **120 trials, 100% defense rate (0 escapes)** | `docs/SECURITY_EVALUATION/` | `testforge/security_evaluation_engine.py` |
| **Performance Benchmark** | **60 empirical runs** (12 cells × 5 reps) | `BENCHMARK_RAW_RESULTS.json` | `testforge/performance_evaluator.py` |
| **Actual LLM Tokens** | **29,476 actual provider tokens** | `testforge_trace.jsonl` | 5 Gemini (29,055) + 1 CodeLlama (250) + 1 Qwen (171) |
| **Actual Prompt Tokens** | **7,132 prompt tokens** | `testforge_trace.jsonl` | 7,050 (Gemini) + 37 (CodeLlama) + 45 (Qwen) |
| **Actual Completion Tokens**| **5,151 completion tokens** | `testforge_trace.jsonl` | 4,812 (Gemini) + 213 (CodeLlama) + 126 (Qwen) |
| **Internal Gemini Tokens** | **17,193 deliberation/reasoning tokens** | Google GenAI SDK usage | $29,476 - (7,132 + 5,151) = 17,193$ tokens |
| **Estimated Tokens** | **27,920 offline heuristic tokens** | `testforge_trace.jsonl` | 61 deterministic AST runs |
| **Deterministic LLM Tokens**| **Strictly 0 tokens** | `testforge_trace.jsonl` | Enforced by `testforge/logger.py` |
| **Telemetry Trace Events**| **305,066 logged events** | `testforge_trace.jsonl` | Line count of append-only JSONL log |
| **SQLite Checkpoints** | **1,310 verified state snapshots** | `qa_artifacts/testforge_checkpoints.db` | `SELECT count(*) FROM checkpoints;` (214.75 MB) |
| **SQLite Integrity** | **`PRAGMA integrity_check` = `ok`** | `qa_artifacts/testforge_checkpoints.db` | Verified via SQLite connection |
| **Actual Billed API Cost** | **$0.00 USD (Zero billed API cost)** | `BENCHMARK_RAW_RESULTS.json` | Automated runs use offline AST synthesis |
| **Core Autonomous Agents** | **5 Core Agents + 2 Gateway Adapters** | `testforge/` source files | Code inspection of classes |
| **Blackboard Partitions** | **5 Partitions** (target, suite, mutant, critic, metrics) | `testforge/blackboard.py` | Pydantic model definitions |
| **FastMCP Tools** | **6 Tools** (3 Filesystem + 3 GitHub) | `testforge/mcp_server.py` | FastMCP tool registration decorators |

---

## 2. Agent Inventory Ground Truth

| Agent Class | Formal Role | Operational Status |
| :--- | :--- | :--- |
| `TestForgeOrchestrator` | Central Supervisor / FSM Coordinator | Active Default |
| `TargetManagerAgent` | Ingestion & Security Threat Scanner | Active Default |
| `TestGeneratorAgent` | Baseline & Reflection Test Synthesizer | Active Default |
| `AdversarialCriticAgent` | Surviving Mutant Diagnostician & Refinement Director | Active Default |
| `GoogleADKTestGenerator` | Google ADK `LlmAgent` Alternative Generator | Active Alternative |
| `CrewAICriticAgent` | CrewAI `Agent` Alternative Adversarial Critic | Active Alternative |
| `TestForgeA2AExecutor` | External Agent-to-Agent (A2A) Protocol Bridge | Active Gateway |

---

## 3. Supported Model Architecture Ground Truth

| Provider | Model Identifier | Execution Type | Verified Live In TestForge |
| :--- | :--- | :---: | :---: |
| **Google GenAI** | `gemini-3.6-flash` | Cloud API | **Yes** (5 calls, 29,055 tokens) |
| **Local Ollama** | `codellama:7b` | Local Metal GPU | **Yes** (1 call, 250 tokens, 8.16s) |
| **Local Ollama** | `qwen2.5-coder:7b` | Local Metal GPU | **Yes** (1 call, 171 tokens, 6.93s) |
| **OpenRouter Cloud** | `deepseek/deepseek-coder` | Cloud API | Supported in code; verified via mock tests |
| **Deterministic AST Synthesizer**| `Deterministic AST Synthesizer` | In-Memory Engine | **Yes** (61 calls, 0 actual tokens, < 0.5s) |

---

## 4. MCP Tools Ground Truth

### 1. Filesystem MCP Server (`create_filesystem_server`)
1. `read_text_file(path: str)`: Path-bounded safe text reading.
2. `list_directory(path: str)`: Path-bounded directory listing (masks credentials).
3. `get_file_info(path: str)`: File metadata and SHA-256 hash inspection.

### 2. GitHub MCP Server (`create_github_server`)
1. `get_file_contents(owner: str, repo: str, path: str, ref: str)`: Remote source file fetching with size limits.
2. `get_repository_info(owner: str, repo: str)`: Repository metadata inspection.
3. `search_repositories(query: str, per_page: int)`: Public repository search.

---

## 5. Security & Threat Model Ground Truth (Criterion 8)

- **Scenarios Evaluated:** 10 attack vectors (S1 Prompt Injection, S2 AST Scope Escape, S3 Directory Traversal, S4 Infinite Deliberation DOS, S5 Mock Poisoning, S6 Privilege Escalation, S7 Dynamic Code Execution, S8 Telemetry Evasion, S9 Blackboard Partition Tampering, S10 Secret Extraction).
- **Trials:** 120 deterministic trials across 3 architectures (Zero-Shot, Few-Shot, ReAct) and 4 personas (Defensive SRE, Aggressive QA, Enterprise Architect, Novice Developer).
- **Defense Rate:** 100% defense rate (0 successful attacks).
- **Automated Tests:** 18 dedicated tests in `tests/test_security_variations.py`.

---

## 6. End-to-End Performance Ground Truth (Criterion 10)

- **Authoritative Dataset:** `docs/PERFORMANCE_EVALUATION/BENCHMARK_RAW_RESULTS.json`.
- **Total Experimental Runs:** Exactly 60 runs (12 matrix cells × 5 repetitions).
- **Key Finding:** ReAct achieved the highest mutation score (89.47% discount, 68.22% logistics); Few-Shot achieved optimal efficiency (54% lower tokens, 48% lower latency).
- **Cost Disclosure:** Estimated cost ($0.000182) is a hypothetical model applying Gemini published rates to offline tokens. Actual billed API cost was **$0.00 USD**.

