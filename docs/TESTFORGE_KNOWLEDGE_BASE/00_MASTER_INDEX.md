# TestForge Master Knowledge Base — Document Index & Navigation Guide

**Project Title:** TestForge — Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops  
**Document Collection:** ChatGPT Technical Knowledge Base & Viva Study Repository  
**Location:** `docs/TESTFORGE_KNOWLEDGE_BASE/`  
**Repository Working Directory:** `/Users/sourabh/TestForge`  
**Current Engine Baseline:** 611 Tests Passing (0 Failed, 0 Skipped, 311 Warnings), 81.33% Statement Coverage  
**Last Verified Date:** November 2, 2026  

---

## 1. Document Map & Recommended Study Flow

This knowledge base is designed as an exhaustive, self-contained study and retrieval archive. Every file is rooted in the actual source code, SQLite checkpoint database, telemetry traces, and verified test suites.

```
                              [00_MASTER_INDEX.md]
                                       |
           +---------------------------+---------------------------+
           |                                                       |
[01_PROJECT_OVERVIEW]                                    [02_SYSTEM_ARCHITECTURE]
           |                                                       |
[03_AGENT_INVENTORY]                                    [04_TEST_GENERATION_ENGINE]
           |                                                       |
[05_LLM_MODELS_PROVIDERS]                               [06_BLACKBOARD_STATE_PERSISTENCE]
           |                                                       |
[07_MCP_A2A_INTEGRATIONS]                               [08_EVALUATION_METHODOLOGY]
           |                                                       |
[09_SECURITY_GUARDRAILS]                                [10_PERFORMANCE_BENCHMARKS]
           |                                                       |
[11_OBSERVABILITY_TELEMETRY]                            [12_API_FRONTEND_BACKEND]
           |                                                       |
[13_EXECUTION_SETUP]                                    [14_COMPLETE_CODEBASE_REFERENCE]
           |                                                       |
[15_DESIGN_DECISIONS]                                   [16_END_TO_END_WALKTHROUGH]
           |                                                       |
[17_VERIFIED_FACTS_METRICS]                             [18_LIMITATIONS_UNRESOLVED]
           |                                                       |
[19_VIVA_QUESTIONS_ANSWERS] <==========================> [20_QUICK_REVISION_NOTES]
```

### Table of Contents & File Manifest

| File | Title | Primary Focus & Viva Coverage |
| :--- | :--- | :--- |
| [`00_MASTER_INDEX.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/00_MASTER_INDEX.md) | **Master Index & Navigation** | Knowledge base catalog, topic indexing, study paths, discrepancy register. |
| [`01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md) | **Project Overview & Problem Statement** | Motivation, research problem, formal objectives, coverage vs mutation testing gap. |
| [`02_COMPLETE_SYSTEM_ARCHITECTURE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/02_COMPLETE_SYSTEM_ARCHITECTURE.md) | **System Architecture** | Multi-agent topology, component diagram, request lifecycle, data flow. |
| [`03_AGENT_INVENTORY_AND_HIERARCHICAL_ARCHITECTURE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/03_AGENT_INVENTORY_AND_HIERARCHICAL_ARCHITECTURE.md) | **Agent Inventory & Hierarchy** | 5 active agents + 2 adapters, supervisor-worker vs reflection models, state sharing. |
| [`04_TEST_GENERATION_ENGINE_DEEP_DIVE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/04_TEST_GENERATION_ENGINE_DEEP_DIVE.md) | **Test Generation Engine** | AST parsing, callable discovery, pre-flight reference execution, boundary tests. |
| [`05_LLM_MODELS_PROVIDERS_AND_FALLBACKS.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/05_LLM_MODELS_PROVIDERS_AND_FALLBACKS.md) | **LLM Architecture & Fallbacks** | 4-tier fallback (Gemini, OpenRouter, Ollama CodeLlama/Qwen, AST Deterministic). |
| [`06_BLACKBOARD_STATE_AND_PERSISTENCE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/06_BLACKBOARD_STATE_AND_PERSISTENCE.md) | **Blackboard & State Management** | 5 partitions, thread-safe RLock, snapshots, time-travel, SQLite schema (1,310 CPs). |
| [`07_MCP_A2A_ADK_CREWAI_INTEGRATIONS.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/07_MCP_A2A_ADK_CREWAI_INTEGRATIONS.md) | **Protocols & Frameworks** | FastMCP filesystem/GitHub servers, FIPA-ACL A2A broker, Google ADK & CrewAI. |
| [`08_EVALUATION_METHODOLOGY_AND_METRICS.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/08_EVALUATION_METHODOLOGY_AND_METRICS.md) | **Evaluation Methodology & Formulas** | Statement coverage (81.33%), mutation scores (Discount 89.47%, Logistics 68.22%). |
| [`09_SECURITY_GUARDRAILS_AND_THREAT_MODEL.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/09_SECURITY_GUARDRAILS_AND_THREAT_MODEL.md) | **Security & Guardrails** | 10 attack scenarios, multi-layer AST sanitization, 120 trials, 18 security tests. |
| [`10_PERFORMANCE_BENCHMARKS_AND_MODEL_COMPARISON.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/10_PERFORMANCE_BENCHMARKS_AND_MODEL_COMPARISON.md) | **Performance Benchmarks** | Authoritative 60-run empirical matrix (Zero-Shot, Few-Shot, ReAct × 4 personas). |
| [`11_OBSERVABILITY_TELEMETRY_AND_LOGGING.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/11_OBSERVABILITY_TELEMETRY_AND_LOGGING.md) | **Observability & Telemetry** | `TraceLogger`, 305k events, actual vs estimated tokens, dynamic KPI engine badges. |
| [`12_API_FRONTEND_AND_BACKEND_REFERENCE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/12_API_FRONTEND_AND_BACKEND_REFERENCE.md) | **API & Frontend Architecture** | FastAPI endpoints, WebSocket hub, SSE wiretap, vanilla JS SPA, responsive UI. |
| [`13_EXECUTION_SETUP_AND_TROUBLESHOOTING.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/13_EXECUTION_SETUP_AND_TROUBLESHOOTING.md) | **Setup & Execution Guide** | macOS installation, `.venv-release`, Ollama setup, curl/CLI runs, troubleshooting. |
| [`14_COMPLETE_CODEBASE_REFERENCE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/14_COMPLETE_CODEBASE_REFERENCE.md) | **Codebase File & Class Map** | Exhaustive reference of all 32 `testforge/` modules, classes, and interactions. |
| [`15_DESIGN_DECISIONS_TRADEOFFS_AND_FUTURE_SCOPE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/15_DESIGN_DECISIONS_TRADEOFFS_AND_FUTURE_SCOPE.md) | **Design Decisions & Trade-offs** | Why Blackboard? Why Mutation Testing? Why AST? Trade-offs and future scope. |
| [`16_END_TO_END_PROJECT_WALKTHROUGH.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/16_END_TO_END_PROJECT_WALKTHROUGH.md) | **End-to-End Walkthrough** | Step-by-step trace of `discount.py` from upload to mutation hardening and diff modal. |
| [`17_VERIFIED_PROJECT_FACTS_AND_METRICS.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/17_VERIFIED_PROJECT_FACTS_AND_METRICS.md) | **Authoritative Fact Sheet** | Single source of truth for all metrics, hashes, counts, and test results. |
| [`18_LIMITATIONS_AND_UNRESOLVED_ISSUES.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/18_LIMITATIONS_AND_UNRESOLVED_ISSUES.md) | **Limitations & Disclosures** | Frank academic disclosure of surviving mutants, simulated tests, and offline runs. |
| [`19_VIVA_QUESTIONS_AND_DETAILED_ANSWERS.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/19_VIVA_QUESTIONS_AND_DETAILED_ANSWERS.md) | **Viva Question Bank (150+ Q&A)** | Structured questions across all 11 evaluation dimensions with code references. |
| [`20_QUICK_REVISION_AND_DEFENSE_NOTES.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/20_QUICK_REVISION_AND_DEFENSE_NOTES.md) | **Quick Revision & Defense Pitch** | 2-min, 5-min, 10-min defense scripts, cheat sheets, trap questions to avoid. |

---

## 2. Verified Core Metrics (Ground Truth)

All metrics below are verified directly from repository artifacts, SQLite queries, and test runners as of November 2, 2026:

- **Total Regression Suite:** **611 tests passed, 0 failed, 311 warnings** in 378.65 seconds.
- **Statement Coverage:** **81.33%** across `testforge/` engine modules.
- **Discount Module Mutation Score:**
  - Baseline: 5.26% (1/19 killed)
  - Final Raw: **89.47%** (17/19 killed, 2 survived)
  - Final Adjusted: **94.44%** (17/18 non-equivalent mutants killed; 1 verified equivalent excluded)
- **Logistics Module Mutation Score:**
  - Baseline: 3.10% (8/258 killed)
  - Final Raw: **68.22%** (176/258 killed, 82 survived)
  - Final Adjusted: **75.21%** (176/234 non-equivalent mutants killed; 24 verified equivalent excluded)
- **Security Guardrails (Criterion 8):** **120 trials** (10 attack scenarios × 3 architectures × 4 personas), 100% defense rate, 18 regression tests.
- **Performance Evaluation (Criterion 10):** **60 benchmark runs** in `BENCHMARK_RAW_RESULTS.json` across 12 matrix cells.
- **Telemetry Storage (`testforge_trace.jsonl`):** **305,066 events**.
- **LLM Token Accounting:**
  - Actual LLM Tokens: **29,476 tokens** (7,132 prompt + 5,151 completion + 17,193 Gemini internal reasoning tokens).
  - Estimated Deterministic Tokens: **27,920 tokens** across 61 deterministic runs.
  - Deterministic Actual Tokens: **Strictly 0**.
- **Persistence Store (`qa_artifacts/testforge_checkpoints.db`):** **1,310 checkpoints**, `PRAGMA integrity_check` = `ok`.

---

## 3. Discrepancy Register & Resolution Notes

| Item | Apparent Discrepancy | Ground Truth & Resolution |
| :--- | :--- | :--- |
| **Test Count** | 598 vs 611 | The baseline was 598 tests. In Task 4, exactly 13 tests were added in `tests/test_dynamic_model_identification.py` to cover dynamic model identification, Ollama parsing, and engine switching ($598 + 13 = 611$). |
| **Token Math** | $7,132 + 5,151 \neq 29,476$ | 7,132 is prompt tokens and 5,151 is completion tokens ($12,283$). Google Gemini API's official `total_token_count` bills internal deliberation/reasoning tokens ($17,193$). $12,283 + 17,193 = 29,476$. CodeLlama (250) and Qwen (171) have 0 internal tokens. |
| **Checkpoints** | 1,733 vs 1,300 vs 1,310 | Active DB has **1,310 checkpoints**. 1,733 was an isolated byte pattern in historical test DBs, never a valid row count in `testforge_checkpoints.db`. |
| **Benchmarks** | 24 runs vs 60 runs | 24 runs represented an early unrepeated 12-cell matrix across 2 modules. The authoritative statistical dataset is `BENCHMARK_RAW_RESULTS.json` with **60 runs** (12 cells × 5 repetitions). |
| **Actual API Cost**| $0.000182 vs $0.00 | $0.000182 is a hypothetical estimate applying Gemini 1.5 Flash rates to offline tokens. The actual billed API cost was **$0.00 USD**. |

---

## 4. Recommended Study Paths

1. **For University Viva / Oral Defense (30 Minutes to 2 Hours):**
   - Start with [`20_QUICK_REVISION_AND_DEFENSE_NOTES.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/20_QUICK_REVISION_AND_DEFENSE_NOTES.md) for the high-level elevator pitch and common examiner traps.
   - Read [`03_AGENT_INVENTORY_AND_HIERARCHICAL_ARCHITECTURE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/03_AGENT_INVENTORY_AND_HIERARCHICAL_ARCHITECTURE.md) and [`04_TEST_GENERATION_ENGINE_DEEP_DIVE.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/04_TEST_GENERATION_ENGINE_DEEP_DIVE.md).
   - Review [`19_VIVA_QUESTIONS_AND_DETAILED_ANSWERS.md`](file:///Users/sourabh/TestForge/docs/TESTFORGE_KNOWLEDGE_BASE/19_VIVA_QUESTIONS_AND_DETAILED_ANSWERS.md) for detailed question-and-answer drills.
2. **For Full Technical Understanding (Complete Architectural Review):**
   - Read in numerical sequence: `01` $\rightarrow$ `16`.
3. **For ChatGPT Ingestion & Retrieval:**
   - Upload all files in `docs/TESTFORGE_KNOWLEDGE_BASE/` to a ChatGPT Project or Custom GPT.
   - Use `00_MASTER_INDEX.md` as the system instruction anchor.

