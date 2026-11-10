# TestForge: Comprehensive Project Discovery & Fact Audit

**Audit Date:** November 10, 2026  
**Auditor:** Principal Discovery Auditor (Read-Only Independent Pass)  
**Branch:** `release/v1.0.0`  
**Evidence Archive Directory:** `docs/AUDIT_EVIDENCE/discovery/`  

---

## D1: Repository State

- **Current Branch:** `release/v1.0.0`
- **HEAD Hash:** `916b843ef6982bb5c0ca1a9baedbb875130bf829`  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:4-6`
- **Git Working Tree Status (`git status --porcelain`):**
  ```text
  ?? docs/AUDIT_EVIDENCE/discovery/
  ?? qa_artifacts/ablation_progression_chart.png
  ?? qa_artifacts/dynamic_model_observability/
  ?? qa_artifacts/final_observability_verification/
  ?? qa_artifacts/release_audit_20261022/
  ?? qa_artifacts/release_audit_20261022_stabilization/
  ```
  *(Note: During test execution, `test_hardened.py` was temporarily modified and `samples/test_hardened_3688a06b.py` was emitted by the test runner; both are test runtime side-effects).*  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:8-28`
- **All Git Tags (15 tags):**
  - `audit-start` (`1d44613e1f6ade392dd3376df6764c50e0eb14c4`)
  - `sealed-eval-freeze` (`9d136110c3066491221db34e8f181d1f32e1b922`)
  - `sealed-v2-freeze` (`8a53c9b24e87292fe957042357f45f8540898e71`)
  - `sealed-v2-measurement-fix` (`68852e5943b53119691c8dc9bf35bca86adcd1db`)
  - `stage-0-done` (`f596d1c0744a3dc0fc52029b4872cdf13bb1e7eb`)
  - `stage-1-done` (`4f1c2d12ee1287249e7842295cd2c010d483516c`)
  - `stage-2-done` (`dcdf1eaed32486d4e525489c7126bc8a8199926f`)
  - `stage-3-done` (`2c1954bf39ca36c654baab0ef20399f6a77ff876`)
  - `stage-4-done` (`8e30bfde47c41185d0e565a7bb3c2d16f71a849a`)
  - `stage-5-done` (`2b98645314429fbaf8b91ccc88f9a4b4be613a46`)
  - `stage-6-done` (`d1cf87d6463e6508c178eaa277f7d07bfd2cc62c`)
  - `stage-7-done` (`1d44613e1f6ade392dd3376df6764c50e0eb14c4`)
  - `v1.0.0-rc1` (`18b33759addd5f92bb773b1a9e9cf32556c008a9`)
  - `v1.0.0-rc2` (`f327d1ecaea2093694a7093dfc20de88394a01e1`)
  - `v1.0.0-rc3` (`8253c9d3a85875c7d12325b2d8b4aff11925b27a`)  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:29-45`
- **All Git Branches with Full Hashes:**
  - `final/ui-verify`: `e9fe6a3ffbc7b01c1553c86f0e3bc0b0152661cd`
  - `main`: `8cec79ad013381f5e52939f2f23152bc38a7c3f4`
  - `release/v1.0.0` (active): `916b843ef6982bb5c0ca1a9baedbb875130bf829`
  - `origin/main`: `8cec79ad013381f5e52939f2f23152bc38a7c3f4`  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:46-51`
- **Total Tracked File Count:** `1532`
- **Git Directory Size (`du -sh .git`):** `237M`  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:53-56`
- **15 Largest Tracked Files in the Repository:**
  1. `docs/WIP_REPORT/TestForge_WIP_Report.pdf` (4,343,127 bytes)
  2. `docs/WIP_REPORT/TestForge_WIP_Report.docx` (1,643,773 bytes)
  3. `qa_artifacts/phase2_test_generation_20261030_190423/benchmark_logistics.json` (1,069,680 bytes)
  4. `docs/AUDIT_EVIDENCE/frontend/pass2_rerun_dashboard.png` (1,040,533 bytes)
  5. `docs/AUDIT_EVIDENCE/frontend/pass1_dashboard.png` (957,980 bytes)
  6. `docs/PROJECT_COVERAGE/TestForge_Project_Coverage.pdf` (777,911 bytes)
  7. `docs/WIP_REPORT/assets/figure3_blackboard_architecture.png` (623,747 bytes)
  8. `docs/WIP_REPORT/assets/figure1_system_architecture.png` (551,972 bytes)
  9. `docs/WIP_REPORT/assets/figure4_mutation_refinement.png` (455,527 bytes)
  10. `docs/WIP_REPORT/assets/figure2_execution_workflow.png` (444,076 bytes)
  11. `docs/screenshots/02_wiretap_topology.png` (435,574 bytes)
  12. `docs/screenshots/09_mode_c_github.png` (432,443 bytes)
  13. `TestForge_GPT_Knowledge_Package.zip` (429,252 bytes)
  14. `docs/screenshots/08_mode_b_synthesis.png` (424,546 bytes)
  15. `docs/screenshots/04_checkpoints_timeline.png` (413,200 bytes)  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:58-74`
- **Tracked File Counts per Top-Level Directory:**
  - `qa_artifacts`: 661
  - `docs`: 329
  - `testforge`: 214
  - `samples`: 154
  - `tests`: 120
  - `root`: 24
  - `scripts`: 17
  - `adk_agents`: 6
  - `frontend`: 3
  - `evals`: 2
  - `.github`: 1
  - `.agents`: 1  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:75-88`
- **Root Files & Scratch/Session File Flagging:**
  - **Tracked Files in Root (24):** `.coverage`, `.dockerignore`, `.env.example`, `.gitignore`, `COVERAGE_IMPROVEMENT_REPORT.md`, `Dockerfile`, `MUTATION_TESTING_REPORT.md`, `README.md`, `TECHNICAL_REPORT.md`, `TESTING_QUALITY_AUDIT.md`, `TestForge_GPT_Knowledge_Package.zip`, `app.py`, `benchmark_results.json`, `benchmark_results.md`, `benchmark_results_fast.json`, `benchmark_results_fast.md`, `docker-compose.yml`, `pyproject.toml`, `requirements.txt`, `run_benchmark.py`, `run_demo.py`, `server.py`, `start_testforge.sh`, `test_hardened.py`.
  - **Untracked Scratch/Agent-Session Files & Directories in Root:**
    * Benchmark job scratch directories: 186 directories named `job_bench_*` and 34 directories named `job_bench_sync_*` (temporary worker scratch spaces).
    * Scratch directory: `scratch/`
    * Untracked runtime traces: `testforge_trace.jsonl`, `testforge_trace.jsonl.old`, `trace_bench_refl_1.jsonl` to `trace_bench_refl_5.jsonl`, `trace_bench_zs_1.jsonl` to `trace_bench_zs_5.jsonl`, `trace_corpus_zs_run_test_offline_zs.jsonl`, `trace_reflected.jsonl`, `trace_zeroshot.jsonl`.
    * SQLite databases: `testforge_checkpoints.db`, `checkpoints.db`.
    * Session report: `PHASE_0_CURRENT_STATE_REPORT.md`.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d1_repo_state.txt:90-145`

---

## D2: People and Provenance

- **Git Commit Authorship (`git shortlog -sne --all`):**
  - Exactly 1 author recorded in git history across all commits and all branches:
    `149  Your Name <your-email@example.com>`
  - Commits per branch:
    * `release/v1.0.0`: 149 (`Your Name <your-email@example.com>`)
    * `final/ui-verify`: 148 (`Your Name <your-email@example.com>`)
    * `main`: 141 (`Your Name <your-email@example.com>`)
    * `origin/main`: 141 (`Your Name <your-email@example.com>`)  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d2_people_provenance.txt:4-16`
- **Team Names, Authors, and Course Mandate in Codebase:**
  - `pyproject.toml:10-13`:
    ```toml
    authors = [
        { name = "Sourabh", email = "sourabh@example.com" },
        { name = "Shreshth", email = "shreshth@example.com" }
    ]
    ```
  - `testforge/__init__.py:9`: `__authors__ = ["Sourabh", "Shreshth"]`
  - Source file headers document division of engineering responsibility:
    * Sourabh (Module 1 & 3: Ingestion, AST Analysis, Orchestrator, LLM Client, UI): `testforge/ingestion.py:4`, `testforge/agents.py:4`, `testforge/llm_client.py:4`, `testforge/orchestrator.py:4`, `frontend/app.js:4`, `frontend/index.html:1632`.
    * Shreshth (Module 2: Mutator, Sandbox, Classifier): `testforge/mutator.py:4`, `testforge/sandbox.py:4`, `tests/test_mutator.py:4`, `tests/test_sandbox.py:4`.
  - Course Mandate references: `README.md:208` ("TestForge implements 6 cutting-edge software engineering capabilities beyond the original coursework mandate").
  - LICENSE: No standalone `LICENSE` or `LICENSE.md` file in root; MIT license declared inside `pyproject.toml:14`.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d2_people_provenance.txt:18-45`
- **Samples Provenance (`samples/*.py`, `samples/sealed_eval/*`, `samples/sealed_v2/*`, `jwt_validator.py`):**
  - `samples/sealed_v2/NOTICE`: 0 bytes (empty file).
  - `samples/sealed_v2/*.py` (`bisect_algo.py`, `fractions_algo.py`, `heapq_algo.py`, `shlex_algo.py`, `statistics_algo.py`, `textwrap_algo.py`):
    First & Last Commit: `cf7086e` ("feat(eval): add 6 pure-Python stdlib modules to samples/sealed_v2 for Sealed Set V2 evaluation"). Headers explicitly state adaptation from CPython standard library algorithms (`fractions.py`, `heapq.py`, `shlex.py`, `statistics.py`, `textwrap.py`).
  - `samples/sealed_eval/*.py` (`board_evaluator.py`, `loan_amortization.py`, `markdown_parser.py`, `merkle_tree.py`, `min_heap.py`, `url_router.py`):
    First & Last Commit: `9d13611` ("feat(audit): add 6 diverse domain modules to samples/sealed_eval for sealed generalization test"). Authored during AI agent audit session.
  - `samples/jwt_validator.py`:
    First Commit: `2425db8` ("feat(T3): implement hybrid synthesizer with never-regress guard and FastMCP 4-tool protocol suite"). Last Commit: `e9fe6a3`. Header states: "Production-grade JSON Web Token (JWT) Encoder & Validator. Implements standard RFC 7519 HMAC-SHA256 JWT creation, decoding, expiration verification, tampering defense, and claim boundary assertion in pure Python standard library." Authored during AI agent session.
  - `samples/rate_limiter.py`:
    First Commit: `748d0c6` ("Initial commit"). Enhanced in `2425db8`. Authored during project initial release and T3.
  - `samples/discount.py`, `samples/banking.py`:
    First Commit: `68b5762` ("feat: initial release of TestForge multi-agent test hardening system with Apple Silicon MLX GPU acceleration").
  - `samples/github_pallets_flask*`, `samples/github_requests*`:
    First Commit: `bce442b` ("chore(baseline): record baseline environment, test suite (849 passed), and verification docs"). Adapted directly from open-source GitHub repositories (Pallets Flask, Requests).  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d2_people_provenance.txt:50-130`

---

## D3: Tests

- **Pytest `--collect-only`:**
  **1010 tests collected in 6.60s**  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d3_tests_collect.txt:1-120`
- **Full Suite with xdist (`-n auto`):**
  - Command: `CREWAI_TESTING=true CREWAI_TRACING_ENABLED=false .venv-release/bin/python3 -m pytest -o addopts="" -n auto`
  - Workers: 10 workers (macOS arm64)
  - Real summary line:  
    **`=========== 1009 passed, 1 skipped, 12 warnings in 315.33s (0:05:15) ===========`**
  - CPU utilization: `1370.43s user 281.44s system 523% cpu 5:15.66 total`
  - Skipped count: 1 skipped (`tests/test_sandbox_backend.py:99` `@pytest.mark.skipif(not is_docker_available(), reason="Docker daemon is not running")`)
  - Deselected count: 0 deselected  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d3_tests_xdist.txt:1-40`
- **Full Suite Run Serially (single process):**
  - Command: `CREWAI_TESTING=true CREWAI_TRACING_ENABLED=false .venv-release/bin/python3 -m pytest -o addopts="" -q`
  - Real summary line:  
    **`FAILED tests/test_clean_working_tree_guard.py::test_working_tree_clean_after_pipeline`**  
    **`1 failed, 1008 passed, 1 skipped, 3 warnings in 918.44s (0:15:18)`**
  - Failure root cause: When tests execute, earlier test `tests/test_mode_c_ingestion.py::test_hardening_pipeline_on_models` exports hardened test suites to `test_hardened.py`, causing `test_clean_working_tree_guard.py` to assert that `test_hardened.py` was modified. Under xdist, test workers run isolated in separate temporary files or different execution orders.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d3_tests_serial.txt:1-60`
- **`git status --porcelain` Afterwards:**
  ```text
   M test_hardened.py
  ?? docs/AUDIT_EVIDENCE/discovery/
  ?? qa_artifacts/ablation_progression_chart.png
  ?? qa_artifacts/dynamic_model_observability/
  ?? qa_artifacts/final_observability_verification/
  ?? qa_artifacts/release_audit_20261022/
  ?? qa_artifacts/release_audit_20261022_stabilization/
  ?? samples/test_hardened_3688a06b.py
  ```
  *Changes detected from test run:* `test_hardened.py` was modified by the hardening pipeline test, and `samples/test_hardened_3688a06b.py` was generated.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d3_tests_status.txt:1-25`
- **Count of Test Files and Test Functions per Prefix Group:**
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d3_tests_prefix_groups.txt`

| Prefix Group | Test Files Count | Test Functions Count |
| :--- | :---: | :---: |
| `manual_oracles` | 2 | 11 |
| `test_a2a` | 4 | 26 |
| `test_ablation` | 1 | 3 |
| `test_adk` | 8 | 47 |
| `test_adversarial` | 1 | 9 |
| `test_agent` | 1 | 6 |
| `test_agentic` | 2 | 17 |
| `test_ast` | 2 | 20 |
| `test_benchmark` | 1 | 4 |
| `test_benchmarking` | 2 | 19 |
| `test_blackboard` | 3 | 53 |
| `test_blast` | 1 | 5 |
| `test_boundary` | 1 | 4 |
| `test_bytecode` | 1 | 4 |
| `test_callbacks` | 1 | 12 |
| `test_cancellation` | 1 | 18 |
| `test_checkpoint` | 3 | 36 |
| `test_classifier` | 1 | 2 |
| `test_clean` | 1 | 1 |
| `test_code` | 1 | 9 |
| `test_concurrency` | 1 | 3 |
| `test_coverage` | 1 | 26 |
| `test_crew` | 1 | 9 |
| `test_crewai` | 1 | 11 |
| `test_deployment` | 1 | 11 |
| `test_diff` | 1 | 3 |
| `test_distributed` | 1 | 1 |
| `test_dynamic` | 1 | 13 |
| `test_equivalent` | 1 | 9 |
| `test_evaluation` | 2 | 22 |
| `test_external` | 1 | 2 |
| `test_extra` | 1 | 5 |
| `test_fast` | 1 | 3 |
| `test_feature` | 1 | 9 |
| `test_flaky` | 1 | 8 |
| `test_frontend` | 2 | 20 |
| `test_guardrails` | 1 | 6 |
| `test_hardening` | 1 | 12 |
| `test_held` | 2 | 6 |
| `test_hypothesis` | 1 | 4 |
| `test_ingestion` | 1 | 3 |
| `test_invariants` | 1 | 9 |
| `test_local` | 1 | 2 |
| `test_mcp` | 4 | 27 |
| `test_messaging` | 1 | 5 |
| `test_mode` | 1 | 8 |
| `test_multi` | 1 | 9 |
| `test_multimodal` | 1 | 5 |
| `test_mutation` | 4 | 83 |
| `test_mutator` | 2 | 8 |
| `test_network` | 1 | 29 |
| `test_never` | 1 | 10 |
| `test_observability` | 1 | 11 |
| `test_orchestration` | 1 | 8 |
| `test_parallel` | 1 | 2 |
| `test_performance` | 1 | 10 |
| `test_phase3` | 1 | 2 |
| `test_phase4` | 1 | 3 |
| `test_phase5` | 1 | 4 |
| `test_phase6` | 1 | 4 |
| `test_phase7` | 1 | 6 |
| `test_post` | 1 | 13 |
| `test_privacy` | 1 | 6 |
| `test_production` | 1 | 7 |
| `test_prompt` | 1 | 10 |
| `test_quality` | 1 | 15 |
| `test_reasoning` | 1 | 9 |
| `test_reflection` | 2 | 16 |
| `test_results` | 1 | 5 |
| `test_sandbox` | 3 | 23 |
| `test_sealed` | 1 | 4 |
| `test_security` | 3 | 58 |
| `test_server` | 1 | 6 |
| `test_strategy` | 1 | 13 |
| `test_suite` | 1 | 4 |
| `test_supervisor` | 1 | 13 |
| `test_task` | 1 | 15 |
| `test_teacher` | 1 | 9 |
| `test_test` | 2 | 24 |
| `test_testforge` | 1 | 1 |
| `test_token` | 1 | 7 |
| `test_websocket` | 1 | 8 |
| `test_wiretap` | 1 | 4 |
| **TOTAL** | **117 test files** | **1007 test functions (1010 pytest items)** |

---

## D4: Agents and Frameworks (Code Truth)

- **The 8 Canonical Agents as Defined in Code:**
  1. `SupervisorAgent` ([`testforge/supervisor_agent.py:277`](file:///Users/sourabh/TestForge/testforge/supervisor_agent.py#L277))  
     *Base Class:* Plain Python `class SupervisorAgent:`. Wraps `google.adk.agents.llm_agent.LlmAgent`, `google.adk.runners.Runner`, and `google.adk.sessions.in_memory_session_service.InMemorySessionService`.
  2. `CodeIntelligenceAgent` ([`testforge/code_intelligence_agent.py:336`](file:///Users/sourabh/TestForge/testforge/code_intelligence_agent.py#L336))  
     *Base Class:* Plain Python `class CodeIntelligenceAgent:`. Wraps AST visitor and Google ADK `LlmAgent`.
  3. `TestPlanningAgent` ([`testforge/planning_agent.py:187`](file:///Users/sourabh/TestForge/testforge/planning_agent.py#L187))  
     *Base Class:* Plain Python `class TestPlanningAgent:`. Wraps Google ADK `LlmAgent` and `Runner`.
  4. `GoogleADKTestGenerator` ([`testforge/adk_generator.py:465`](file:///Users/sourabh/TestForge/testforge/adk_generator.py#L465))  
     *Base Class:* Plain Python `class GoogleADKTestGenerator:`. Wraps Google ADK `LlmAgent` and `Runner`. Registered under A2A as `agent:google-adk:generator` (labelled `TestGeneratorAgent` in UI/docs).
  5. `TestExecutionAgent` ([`testforge/execution_agent.py:226`](file:///Users/sourabh/TestForge/testforge/execution_agent.py#L226))  
     *Base Class:* Plain Python `class TestExecutionAgent:`. Wraps sandbox runner, Google ADK `LlmAgent`, and `Runner`.
  6. `MutationQualityCriticAgent` ([`testforge/crew_critic.py:966`](file:///Users/sourabh/TestForge/testforge/crew_critic.py#L966))  
     *Base Class:* Plain Python `class MutationQualityCriticAgent:`. Wraps CrewAI `CriticCrew`, `MutantAnalystAgent`, `TestQualityReviewerAgent`, `RepairStrategistAgent` (which instantiate `crewai.Agent`, `crewai.Task`, and `crewai.Crew`).
  7. `SecurityAgent` ([`testforge/security_agent.py:201`](file:///Users/sourabh/TestForge/testforge/security_agent.py#L201))  
     *Base Class:* Plain Python `class SecurityAgent:`. Wraps deterministic `SecurityGuardrail` and Google ADK `LlmAgent`.
  8. `ReflectionRepairAgent` ([`testforge/reflection_agent.py:346`](file:///Users/sourabh/TestForge/testforge/reflection_agent.py#L346))  
     *Base Class:* Plain Python `class ReflectionRepairAgent:`. Wraps Google ADK `LlmAgent` and `Runner`.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt:30-80`
- **Documentation & Frontend Mismatch Analysis:**
  - `README.md:68-80` does not list the 8 individual canonical agents in a table; it cites `testforge/agents.py` and `testforge/orchestrator.py` and shows `TargetManagerAgent` in an ASCII diagram.
  - `docs/architecture.md:50-60` and `frontend/app.js:4624-4632` list the 8 canonical agents with uniform URIs:
    `agent:google-adk:supervisor`, `agent:google-adk:code-intel`, `agent:google-adk:planner`, `agent:google-adk:generator`, `agent:google-adk:execution`, `agent:crewai:critic`, `agent:google-adk:security`, `agent:google-adk:repair`.
  - Class Name Divergence: In code, Agent #4 is named `GoogleADKTestGenerator` (`testforge/adk_generator.py:465`), while documentation and frontend refer to it as `TestGeneratorAgent` or `TestGenerationAgent`.
- **Google ADK Feature Usage: Production Path vs. Test-Only:**
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt:85-180`
  - `google.adk.runners.Runner`: **PRODUCTION PATH** (`testforge/supervisor_agent.py:326`, `testforge/adk_generator.py:513`, `testforge/reflection_agent.py:415`).
  - `SessionService`: **PRODUCTION PATH** (Uses `google.adk.sessions.in_memory_session_service.InMemorySessionService` in `supervisor_agent.py:323` and `adk_generator.py:511`). `DatabaseSessionService` exists only in `testforge/scripts/run_adk_cross_job_learning.py` (TEST/SCRIPT ONLY).
  - `MemoryService`: **TEST/SCRIPT ONLY** (`InMemoryMemoryService` used in `testforge/scripts/run_adk_cross_job_learning.py:28`; 0 occurrences in `orchestrator.py` or `server.py`).
  - `LlmAgent with tools`: **PARTIAL** (`LlmAgent` is instantiated across all ADK agents in the production path, but **0 tools are passed to `LlmAgent(tools=...)`** in production; tools are invoked via direct Python calls or FastMCP client).
  - `ParallelAgent`: **TEST-ONLY** (`ADKParallelAnalysisAgent(ParallelAgent)` defined in `testforge/adk_workflow_agents.py:175`, tested in `tests/test_adk_workflow_agents.py`; NOT imported or used in `orchestrator.py`).
  - `LoopAgent`: **TEST-ONLY** (`ADKLoopReflectionAgent(LoopAgent)` defined in `testforge/adk_workflow_agents.py:427`, tested in `tests/test_adk_workflow_agents.py`; NOT imported or used in `orchestrator.py`).
  - `SequentialAgent`: **MISSING** (0 occurrences in entire codebase).
  - `sub_agents / AgentTool delegation`: **MISSING** (0 occurrences in entire codebase).
  - `ADK callbacks`: **TEST-ONLY** (`testforge/adk_callbacks.py:40-315` tested in `tests/test_adk_callbacks.py`; production pipeline uses custom `testforge/callbacks.py:CallbackRegistry`).
  - `ADK events streamed to UI`: **NOT USED** (UI receives events from `testforge/websocket_hub.py` broadcasting Python dictionaries from `CallbackRegistry`, not official ADK `Event` objects).
- **CrewAI Deep Dive:**
  - `Crew`, `Task`, `Agent`: Used in `testforge/crew_critic.py` lines 741, 766, 791, 865, 878, 889, 902, 1014, 1283, 1291.
  - `Flow`: `TestHardeningFlow(Flow[HardeningFlowState])` defined in `testforge/flows/hardening_flow.py:52` with `@start`, `@listen`, and `router`. **TEST-ONLY** (used in `tests/test_crewai_depth.py:188-226`; NOT used in `server.py -> orchestrator.py`).
  - Production LLM: `CrewAILLMBridge` (`testforge/crew_critic.py:513-600`) calls `gemini-3.6-flash` via `HybridLLMClient` if live LLM is enabled and API key is present; otherwise falls back to `_synthesize_deterministic_critique()`.
  - Memory: `CriticCrew` sets `memory=True` (line 1010), but memory is internally disabled by CrewAI when `CREWAI_TESTING="true"`.
  - Custom `@tool`: 5 tools defined in `testforge/crew_critic.py:660-720`: `inspect_mutant_diff`, `inspect_unreached_arcs`, `analyze_assertion_density`, `audit_tautological_assertions`, `synthesize_repair_directives`.
  - Gated / Mocked: `os.environ["CREWAI_TESTING"] = "true"` set at `testforge/crew_critic.py:38`. `CrewAILLMBridge.set_mock_response()` allows deterministic test overrides.
- **Installed Library Versions:**
  - `google-adk==1.14.1`
  - `google-genai==1.75.0`
  - `crewai==1.15.28`
  - `crewai-core==1.15.28`
  - `mcp==1.28.1`
  - `a2a-sdk==0.3.26`
  - `fastapi==0.159.1`
  - `pytest==9.1.1`
  - `mutmut==3.8.1`
  - `hypothesis==6.170.15`
  - `opentelemetry-api==1.45.1`, `opentelemetry-sdk==1.45.1`  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt:4-28`

---

## D5: Protocols

- **Model Context Protocol (MCP):**
  - Tool inventory in code (`testforge/mcp_server.py`):
    * Standard server (`create_testforge_server()`): 7 tools: `mcp_ast_symbol_analyzer`, `mcp_mutant_generator`, `mcp_sandbox_runner`, `mcp_equivalence_classifier`, `harden_module`, `get_report`, `list_jobs`.
    * Protocol Suite server (`create_protocol_suite_server()`): 4 core tools: `mcp_ast_symbol_analyzer`, `mcp_mutant_generator`, `mcp_sandbox_runner`, `mcp_equivalence_classifier`.
    * Filesystem server (`create_filesystem_server()`): 4 tools: `read_text_file`, `write_text_file`, `list_directory`, `get_file_info`.
    * GitHub server (`create_github_server()`): 3 tools: `fetch_file_contents`, `search_repositories`, `get_repository_tree`.
  - Transports: FastMCP `server.run(transport="stdio")`.
  - Consumption by ADK Agents in Production Path: **NONE**. `orchestrator.py:110` initializes `self.mcp_client = create_filesystem_client(...)`, but no ADK agent (`supervisor_agent.py`, `adk_generator.py`, etc.) consumes MCP tools directly. In `hybrid_synthesizer.py`, MCP tools are imported and invoked as direct Python functions.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d5_protocols.txt:1-85`
- **Agent2Agent (A2A) Protocol:**
  - Official `a2a-sdk` import: **YES**, imported in `testforge/a2a_protocol.py:43-49` (`A2ACardResolver`, `ClientFactory`, `AgentExecutor`, `AgentCard`) and `server.py:609`.
  - Endpoints exposed in `server.py`:
    * `/.well-known/agent-card.json` (lines 570-585)
    * `/.well-known/agent.json` (lines 571-585)
    * `/api/a2a/test` (lines 590-640)
  - Agent Card file path: Built dynamically via `testforge/a2a_protocol.py:build_testforge_agent_card()`.
  - Cross-Process Runner & Test: `testforge/a2a_distributed.py:30-80` implements `A2ACriticProcessManager` which spawns `python -m testforge.scripts.run_critic_service --host 127.0.0.1 --port 8011` as an out-of-process A2A worker. Verified by `tests/test_distributed_cross_process_a2a.py:20`.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d5_protocols.txt:90-160`

---

## D6: RAG, Multimodal, Privacy, Deployment

- **Agentic RAG:**
  - Vector & Embedding Method: Normalized TF-IDF / bi-gram token frequency vector (`_tokenize_and_vectorize`) + cosine similarity (`_cosine_similarity`) implemented in `testforge/rag/vector_store.py:28-60`. Optional ChromaDB persistence if `chromadb` is installed.
  - Store Persistence: `DEFAULT_PERSIST_DIR` (`.testforge/kb` or `~/.testforge/kb`), stored as JSON files (`{collection_name}.json`).
  - Production Path & Flags: **TEST-ONLY**. `AgenticKnowledgeRetriever` and `TestForgeVectorStore` are tested in `tests/test_agentic_rag.py` (4 tests), but are NOT imported or called in `orchestrator.py` or `server.py`. There is NO on/off flag in production, and no benchmark measurement artifact comparing RAG on/off.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt:1-55`
- **Multimodal (Vision/Audio/Video/PDF):**
  - Inputs Implemented: **Image only (PNG/JPG)**. Audio, video, and PDF are **NOT implemented**.
  - Vision Model: `gemini-3.6-flash` via `google.genai` client in `testforge/multimodal_fsm.py:198`.
  - Test Diagram Origin: Generated programmatically using `matplotlib` via `generate_fsm_diagram()` in `testforge/multimodal_fsm.py:73` and saved to `tests/fixtures/fsm_diagram.png`.
  - Independent Fixtures: None. The only image fixture is `tests/fixtures/fsm_diagram.png` (generated by the script).  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt:60-95`
- **Zero-Egress Privacy:**
  - Enforcement Mechanism:
    1. Socket Interceptor: `ZeroEgressSocketInterceptor` in `testforge/privacy_mode.py:40-120` monkey-patches `socket.socket.connect` and `socket.create_connection`, throwing `PrivacySecurityError` for any non-loopback address.
    2. AST Safety Guardrail: `SecurityGuardrail` in `testforge/security.py:601-616` inspects candidate test code AST and blocks direct socket and HTTP client creation with rule `SEC_AST_NETWORK_SOCKET`.
    3. Docker isolation: `testforge/sandbox_backend.py:35` passes `--network none`.
  - Test File: `tests/test_privacy_mode.py` and `tests/test_network_security.py`. Evidence: `docs/AUDIT_EVIDENCE/T2/` and `docs/SECURITY_EVALUATION_REPORT.md`.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt:100-145`
- **Deployment & Docker Status:**
  - `Dockerfile`: Multi-stage Python 3.13-slim image, non-root user `testforge`, exposes ports 8000 (FastAPI) and 8501 (Streamlit), healthcheck on `/healthz`.
  - `docker-compose.yml`: 3 services (`backend` on port 8000, `ollama` on port 11434, `dashboard` on port 8501 under `legacy-streamlit` profile).
  - GitHub Workflows: `.github/workflows/testforge_pr_check.yml` (runs on PRs to main/master, checks changed files, runs CLI hardening, executes pytest suite, uploads SARIF report).
  - Docker Availability: Docker CLI available at `/Applications/Docker.app/Contents/Resources/bin/docker`; Docker Desktop daemon v29.4.3 is running and operational.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt:150-230`

---

## D7: Results Truth

- **Mutation Score JSON Inventory in `qa_artifacts/`:**
  - Total JSON files with mutation scores: 45 files.
  - Fix commit/tag: `sealed-v2-measurement-fix` (`68852e5943b53119691c8dc9bf35bca86adcd1db`, timestamp `2026-11-08 13:24:20 +0530`, epoch `1794124460`).
  - Pre-fix vs Post-fix breakdown: All files produced prior to epoch 1794124460 (such as `milestone2_ast_mutation_20261023_140500/m2_benchmark_results.json`, `phase2_m1_evaluation_corpus_20261025_211500/benchmark_corpus_results.json`) contained the DEF-022 defect (failing candidate tests credited with false kills). Files produced after epoch 1794124460 (such as `docs/AUDIT_EVIDENCE/T2/rescore_verified_summary.json` and `docs/AUDIT_EVIDENCE/T3/t3_evaluation_results.json`) enforce strict DEF-022 clean-code validation.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d7_results_truth.txt:1-60`
- **Canonical & Post-Rescore Results Table (Target x Condition):**
  *Evidence path:* `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`, `docs/AUDIT_EVIDENCE/T2/rescore_verified_summary.json`, `docs/AUDIT_EVIDENCE/T3/t3_evaluation_results.json`

| Target | Condition | Killed / Total | Raw MS (%) | Adj MS (%) | Pass@1 Status | INVALID_SUITE | Model / Engine |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `samples/discount.py` (19 mutants) | Developer Baseline | 1 / 19 | 5.26% | 5.56% | PASS | 0 | Deterministic Minimal Baseline |
| | Single-Pass Zero-Shot | 12 / 19 | 63.16% | 66.67% | PASS | 0 | Cloud LLM (`gemini-3.6-flash`) |
| | Agentic Reflection | 18 / 19 | 94.74% | 100.0% | PASS | 0 | Google ADK + CrewAI |
| `samples/order_fsm.py` (106 mutants) | Developer Baseline | 7 / 106 | 6.60% | 6.67% | PASS | 0 | Deterministic Minimal Baseline |
| | Single-Pass Zero-Shot | 14 / 106 | 13.21% | 13.33% | PASS | 0 | Cloud LLM (`gemini-3.6-flash`) |
| | Agentic Reflection | 103 / 106 | 97.17% | 100.0% | PASS | 0 | Google ADK + CrewAI |
| `samples/lru_cache.py` (42 mutants) | Developer Baseline | 3 / 42 | 7.14% | 7.89% | PASS | 0 | Deterministic Minimal Baseline |
| | Single-Pass Zero-Shot | 10 / 42 | 23.81% | 26.32% | PASS | 0 | Cloud LLM (`gemini-3.6-flash`) |
| | Agentic Reflection | 13 / 42 | 30.95% | 34.21% | PASS | 0 | Google ADK + CrewAI |
| `samples/stats_calculator.py` (73 mutants)| Developer Baseline | 5 / 73 | 6.85% | 7.04% | PASS | 0 | Deterministic Minimal Baseline |
| | Single-Pass Zero-Shot | 22 / 73 | 30.14% | 30.99% | PASS | 0 | Cloud LLM (`gemini-3.6-flash`) |
| | Agentic Reflection | 33 / 73 | 45.21% | 46.48% | PASS | 0 | Google ADK + CrewAI |
| **Macro Average (Canonical 4 Targets)** | **Developer Baseline** | **16 / 240** | **6.46%** | **6.79%** | **PASS** | **0** | **Deterministic AST** |
| | **Single-Pass Zero-Shot** | **58 / 240** | **32.58%** | **34.33%** | **PASS** | **0** | **gemini-3.6-flash** |
| | **Agentic Reflection** | **167 / 240**| **67.02%** | **70.17%** | **PASS** | **0** | **ADK + CrewAI** |
| `samples/jwt_validator.py` (147 mutants)| Developer Baseline | 72 / 147 | 48.98% | 50.35% | PASS | 0 | Developer Starter Suite |
| | Pure Deterministic AST | 0 / 147 | 0.00% | 0.00% | **FAIL** | **1** | Intelligent AST Synthesizer |
| | Hybrid Synthesizer | 80 / 147 | 54.42% | 55.94% | PASS | 0 | Hybrid Engine (AST + Reflection) |
| `samples/rate_limiter.py` (147 mutants)| Developer Baseline | 32 / 147 | 21.77% | 24.24% | PASS | 0 | Developer Starter Suite |
| | Pure Deterministic AST | 83 / 147 | 56.46% | 62.88% | PASS | 0 | Intelligent AST Synthesizer |
| | Hybrid Synthesizer | 87 / 147 | 59.18% | 65.91% | PASS | 0 | Hybrid Engine (AST + Reflection) |

- **Mutant Count Verification (`jwt_validator.py` vs `rate_limiter.py`):**
  - `jwt_validator.py`: `147` mutants
  - `rate_limiter.py`: `147` mutants
  - Direct Verification: Both files literally produce exactly 147 AST mutants when `ASTMutator().generate_mutants()` is executed. Mutants are counted by AST traversal applying 7 mutation operator categories across every AST statement node. By mathematical coincidence of their AST node types, both modules yielded 147 mutants.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d7_results_truth.txt:85-115`
- **Hybrid Synthesizer Evaluation Provenance:**
  - Number of runs: $n=1$, random seed: `42`.
  - Model: `gemini-3.6-flash` (with AST invariant seeding and FastMCP reflection).
  - Target familiarity: Both `jwt_validator.py` and `rate_limiter.py` were created/enhanced during T3 evaluation.
- **Search for Historic / Inflated Numbers and Retraction Status:**
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d7_results_truth.txt:120-220`

| Number | File:Line | Surrounding Context | Labelled Retracted? |
| :--- | :--- | :--- | :---: |
| `91.5` | `docs/CLAIMS_REGISTER.md:48` | `Local Qwen Zero-Shot: 91.5% ± 25.7%` | **YES** (Retracted in CLM-028) |
| `91.5` | `docs/SEALED_V2_EVALUATION.md:50` | `~~91.5% ± 25.7%~~` | **YES** (Struck-through & Retracted) |
| `97.8` | `docs/CLAIMS_REGISTER.md:49` | `Local Qwen ZS + 1 Retry: 97.8% ± 8.2%` | **YES** (Retracted in CLM-028) |
| `97.8` | `docs/SEALED_V2_EVALUATION.md:51` | `~~97.8% ± 8.2%~~` | **YES** (Struck-through & Retracted) |
| `62.8` | `docs/CLAIMS_REGISTER.md:50` | `Deterministic AST (Sealed V2): 62.8% ± 29.6%` | **YES** (Retracted in CLM-028) |
| `62.8` | `docs/SEALED_V2_EVALUATION.md:52` | `~~62.8% ± 29.6%~~` | **YES** (Struck-through & Retracted) |
| `62.8` | `docs/PROVENANCE_AUDIT.md:37` | `Arithmetic Mean Adj Mutation Score: 62.8%` | **NO** (Historical audit log) |
| `31.5` | `docs/CLAIMS_REGISTER.md:51` | `Full Agentic (Sealed V2): 31.5% ± 26.2%` | **YES** (Retracted in CLM-028) |
| `31.5` | `docs/SEALED_V2_EVALUATION.md:53` | `~~31.5% ± 26.2%~~` | **YES** (Struck-through & Retracted) |
| `36.19` | `docs/CLAIMS_REGISTER.md:53` | `Sealed Evaluation V1 Lift: +36.19% / 45.51%` | **YES** (Noted as pre-DEF-022) |
| `36.19` | `docs/SEALED_EVALUATION.md:41` | `Arithmetic Mean Raw Mutation Score: +36.19%` | **NO** (Unretracted historical text) |
| `45.51` | `docs/CLAIMS_REGISTER.md:53` | `Sealed Evaluation V1: 45.51%` | **YES** (Noted as pre-DEF-022) |
| `45.51` | `docs/SEALED_EVALUATION.md:41` | `Arithmetic Mean Raw Mutation Score: 45.51%` | **NO** (Unretracted historical text) |
| `80.5` | `docs/CLAIMS_REGISTER.md:52` | `Cloud Gemini Paired Subset: 80.5% ± 39.1%` | **YES** (Retracted in CLM-028) |
| `79.1` | `README.md:221` | `134 tests reduced to 28 tests (79.1% reduction)` | **NO** (Active claim: Minimizer) |
| `79.1` | `docs/CLAIMS_REGISTER.md:59` | `Suite Minimization Reduction: 79.1%` | **YES** (Verified in CLM-013) |
| `8.5` | `docs/CLAIMS_REGISTER.md:60` | `External mutmut correlation: r = 0.9988, p = 0.0012` | **YES** (Active claim) |
| `5.39` | `README.md:283` | `240 down to 28, 5.39x speedup` | **NO** (Active claim: Diff mode) |
| `0.9988` | `docs/CLAIMS_REGISTER.md:23`| `Pearson r = 0.9988` | **YES** (Active claim with caveat) |
| `5.26` | `README.md:126` | `samples/discount.py baseline: 5.26%` | **NO** (Active benchmark number) |
| `67.02` | `README.md:118` | `Macro Average raw mutation score: 67.02%` | **NO** (Active benchmark number) |
| `70.17` | `README.md:118` | `Macro Average adj mutation score: 70.17%` | **NO** (Active benchmark number) |

---

## D8: Frontend Honesty

- **Literal Display Values Search in `frontend/` and `server.py`:**
  - `11.99`: **None found** (0 matches)
  - `42.8`: **None found** (0 matches)
  - `650.7`: **None found** (0 matches)
  - `128.4`: **None found** (0 matches)
  - `chk_fa468f59ba29`: **None found** (0 matches)
  - `VALID (100%)`: Found only in `frontend/app.js:4898` as a conditional ternary expression:  
    `<td><span class="badge ${isAstValid ? 'badge-green' : 'badge-red'}">${isAstValid ? 'VALID (100%)' : 'INVALID (0%)'}</span></td>`
- **Hidden / `display:none` Search in `frontend/`:**
  - Standard modal backdrops: `#settings-modal-backdrop`, `#a2a-modal-backdrop`, `#mcp-modal-backdrop`, `#restore-modal-backdrop`.
  - Ingestion subviews: `.ingestion-subview.hidden` toggled when switching between Mode A, Mode B, and Mode C.
  - Alert banners, tooltips, dropdowns, and loading/empty placeholders.
  - Test aliases: Legacy alias elements (`data-alias`) were sanitized during T1; no synthetic test-dummy buttons remain.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d8_frontend_honesty.txt:1-120`
- **Cockpit HTML Tab Views (7 Primary Tabs):**
  1. `Target Ingestion` (`#tab-btn-ingestion` -> `#view-ingestion`)
  2. `Blast Radius & Call Graph` (`#tab-btn-blast` -> `#view-blast`)
  3. `Hardening Lab & Results` (`#tab-btn-lab` -> `#view-lab`)
  4. `Multi-Agent Wiretap` (`#tab-btn-wiretap` -> `#view-wiretap`)
  5. `Observability Trace` (`#tab-btn-observability` -> `#view-observability`)
  6. `Benchmarks & Ablation` (`#tab-btn-benchmarks` -> `#view-benchmarks`)
  7. `Checkpoint Timeline & Diff` (`#tab-btn-checkpoints` -> `#view-checkpoints`)
- **Frontend vs. Backend API Route Mismatch Analysis:**
  - Total frontend fetch routes: 40
  - Total `server.py` registered routes: 56
  - Mismatches: **0 genuine mismatches**. The 6 detected non-literal endpoints (`/api/approval/requests/`, `/api/benchmark/job/`, `/api/checkpoints/`, `/api/harden/cancel/`, `/api/harden/resume/`, `/api/harden/status/`) are parameterized route templates where the frontend appends an ID dynamically.  
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d8_frontend_honesty.txt:130-175`
- **Live Server Probe Results:**
  *Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d8_frontend_honesty.txt:180-220`
  - `GET /healthz`:
    `{"status":"healthy","service":"testforge-backend","version":"2.0.0","timestamp":1794307210.75}`
  - `GET /readyz`:
    `{"status":"ready","service":"testforge-backend","db_accessible":true,"subsystems":{"ast_mutator":"operational","blackboard":"operational","sandbox_storage":"operational","sqlite_persistence":"operational"}}`
  - `GET /api/benchmark/multi-target/summary` (Provenance Fields):
    * `commit`: `"bad6cab"`
    * `model_name`: `"gemini-3.6-flash"`
    * `fast_mode`: `false`
    * `engine_mode`: Embedded per scenario (`"Deterministic Minimal Baseline"`, `"Single-Pass Zero-Shot Generator"`, `"Autonomous Multi-Agent Reflection Loop (Pipeline-Only)"`)
    * `is_mocked`: `false`

---

## D9: Handout Coverage Matrix

*Evidence paths cited in column 5.*

| # | Topic | File:Line Implementing It | Used in Production Path? | Demo Command | Evidence Path | Status |
| :---: | :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | ReAct / CoT / ToT / Self-consistency | `testforge/reflection_agent.py:635` (ReAct), `800` (ToT), `testforge/planning_agent.py:457` (CoT), `testforge/adk_generator.py:327` (Self-consistency) | Y | `.venv-release/bin/python3 -m pytest tests/test_reasoning_strategies.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **WORKING** |
| 2 | Agentic RAG | `testforge/rag/vector_store.py:60`, `testforge/rag/knowledge_retriever.py:36` | Test-Only | `.venv-release/bin/python3 -m pytest tests/test_agentic_rag.py -v` | `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt` | **TEST-ONLY** |
| 3 | CrewAI agents / tools / memory / tasks / crews | `testforge/crew_critic.py:660` (@tool), `741` (Agent), `865` (Task), `902` (Crew, memory) | Y | `.venv-release/bin/python3 -m pytest tests/test_crewai_critic.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **WORKING** |
| 4 | CrewAI Flows | `testforge/flows/hardening_flow.py:52` (`TestHardeningFlow`) | Test-Only | `.venv-release/bin/python3 -m pytest tests/test_crewai_depth.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **TEST-ONLY** |
| 5 | ADK LlmAgent | `testforge/supervisor_agent.py:324`, `testforge/adk_generator.py:494`, `testforge/planning_agent.py:219`, `testforge/execution_agent.py:266`, `testforge/security_agent.py:235` | Y | `.venv-release/bin/python3 -m pytest tests/test_adk_production_path.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **WORKING** |
| 6 | ADK tools / function calling | `testforge/supervisor_agent.py:324` | N | NOT RUN | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **MISSING** (ADK `tools=` parameter not used) |
| 7 | ADK state / sessions / memory | `testforge/supervisor_agent.py:323` (`InMemorySessionService`), `testforge/scripts/run_adk_cross_job_learning.py:25` (`DatabaseSessionService`, `InMemoryMemoryService`) | Partial | `.venv-release/bin/python3 -m pytest tests/test_adk_cross_job_learning.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **PARTIAL** (MemoryService is test-only) |
| 8 | ADK events / async | `testforge/adk_workflow_agents.py:30` (`Event`, `EventActions`), `testforge/adk_callbacks.py:210` | Test-Only | `.venv-release/bin/python3 -m pytest tests/test_adk_workflow_agents.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **TEST-ONLY** |
| 9 | ADK orchestration (coordinator / sub-agents) | `testforge/supervisor_agent.py:277`, `testforge/orchestrator.py:120` | Partial | `.venv-release/bin/python3 -m pytest tests/test_supervisor_agent.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **PARTIAL** (Coordinator operational; ADK `sub_agents=` parameter unused) |
| 10 | ADK multi-agent workflows (graph/dynamic/collaborative) | `testforge/adk_workflow_agents.py:175` (`ParallelAgent`), `427` (`LoopAgent`) | Test-Only | `.venv-release/bin/python3 -m pytest tests/test_adk_workflow_agents.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **TEST-ONLY** |
| 11 | ADK callbacks | `testforge/adk_callbacks.py:40-315` | Test-Only | `.venv-release/bin/python3 -m pytest tests/test_adk_callbacks.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **TEST-ONLY** |
| 12 | Guardrails / safety | `testforge/security.py:239-760` (`SecurityGuardrail`) | Y | `.venv-release/bin/python3 -m pytest tests/test_security.py -v` | `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt` | **WORKING** |
| 13 | Agent evaluation (official `adk eval`) | `testforge/scripts/run_adk_eval.py:1-220`, `evals/planner_eval.evalset.json`, `evals/generator_eval.evalset.json` | Test-Only | `.venv-release/bin/python3 -m pytest tests/test_adk_eval_suite.py -v` | `docs/AUDIT_EVIDENCE/discovery/d4_agents_frameworks.txt` | **WORKING** (Offline evaluation harness) |
| 14 | Monitoring / observability | `testforge/logger.py:28` (`TraceLogger`), `testforge/callbacks.py:20` (`CallbackRegistry`), `testforge/opentelemetry_instrumentation.py:45` | Y | `.venv-release/bin/python3 -m pytest tests/test_token_observability_audit.py -v` | `docs/AUDIT_EVIDENCE/discovery/d8_frontend_honesty.txt` | **WORKING** |
| 15 | Deployment | `Dockerfile:1-48`, `docker-compose.yml:1-55`, `.github/workflows/testforge_pr_check.yml:1-75` | Y | `docker --version && docker compose config` | `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt` | **WORKING** |
| 16 | Model Context Protocol (MCP) | `testforge/mcp_server.py:1-430`, `testforge/mcp_client.py:1-260` | Partial | `.venv-release/bin/python3 -m pytest tests/test_mcp_four_tools.py -v` | `docs/AUDIT_EVIDENCE/discovery/d5_protocols.txt` | **WORKING** (FastMCP stdio server and direct protocol tools) |
| 17 | Agent2Agent (A2A) | `testforge/a2a.py:1-1400`, `testforge/a2a_protocol.py:1-350`, `testforge/a2a_distributed.py:1-120` | Y | `.venv-release/bin/python3 -m pytest tests/test_a2a_protocol.py -v` | `docs/AUDIT_EVIDENCE/discovery/d5_protocols.txt` | **WORKING** |
| 18 | Local LLMs / privacy | `testforge/privacy_mode.py:1-250`, `testforge/llm_client.py:480-550` | Y | `.venv-release/bin/python3 -m pytest tests/test_privacy_mode.py -v` | `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt` | **WORKING** |
| 19 | Multimodal (text/audio/image/video) | `testforge/multimodal_fsm.py:1-320` | Partial | `.venv-release/bin/python3 -m pytest tests/test_multimodal_fsm.py -v` | `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt` | **PARTIAL** (Image only; Audio/Video/PDF missing) |
| 20 | Industry use cases (debugging/execution) | `testforge/diff_incremental.py:1-160`, `testforge/flaky_detector.py:1-180`, `testforge/minimizer.py:1-210` | Y | `.venv-release/bin/python3 -m pytest tests/test_diff_incremental.py tests/test_flaky_test_detector.py tests/test_minimizer.py -v` | `docs/AUDIT_EVIDENCE/discovery/d6_rag_multimodal_privacy.txt` | **WORKING** |

---

## D10: Docs Inventory

*Full inventory of all 77 markdown files in `docs/*.md` and `docs/viva/*.md`.*  
*Evidence path:* `docs/AUDIT_EVIDENCE/discovery/d10_docs_inventory.txt`

| File Path | Lines | Last Commit Date | Last Commit Hash & Subject |
| :--- | :---: | :---: | :--- |
| `docs/A2A_PROTOCOL_SPECIFICATION.md` | 115 | 2026-11-07 | `1d44613` chore: complete Stage 7 final hygiene check, ruff clean, and pass DONE GATE |
| `docs/ABLATION_STUDY.md` | 133 | 2026-11-07 | `a4c8e77` feat(eval): complete E1 ablation matrix across 7 configs, 8 targets, and 3 seeds |
| `docs/ADK_CROSS_JOB_LEARNING.md` | 86 | 2026-11-07 | `27c87f3` feat(adk): implement ADK DatabaseSessionService and InMemoryMemoryService cross-job learning |
| `docs/ADK_EVAL_REPORT.md` | 45 | 2026-11-07 | `0ea03bb` feat(eval): execute E4 adk eval on Planner and Generator in evals/ |
| `docs/ADK_WEB_GUIDE.md` | 83 | 2026-11-07 | `1d44613` chore: complete Stage 7 final hygiene check, ruff clean, and pass DONE GATE |
| `docs/AGENTIC_REGRESSION_DIAGNOSIS.md` | 127 | 2026-11-08 | `9d7703b` feat(orch): implement never-regress guard and diagnose agentic regression |
| `docs/AGENTIC_UPGRADE_AUDIT.md` | 383 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/AUDIT_PROGRESS.md` | 36 | 2026-11-08 | `ad0c685` docs(audit): finalize audit progress ledger with commit hash for Sub-Task A9 |
| `docs/AUTONOMOUS_EXECUTION_LOG.md` | 172 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/BASELINES_AUDIT.md` | 54 | 2026-11-08 | `97e0817` fix(security): resolve DEF-021 adversarial evasions and complete Sub-Task A5 security audit |
| `docs/BASELINE_COMPARISON.md` | 62 | 2026-11-07 | `e6c09f9` feat(benchmark): add baseline competitor multi-seed evaluation and report |
| `docs/CLAIMS_REGISTER.md` | 64 | 2026-11-10 | `2b558c8` audit(T2): rescore benchmarks with fixed DEF-022 harness and synchronize claims register |
| `docs/CLOSE_PROGRESS.md` | 79 | 2026-11-08 | `0391ef3` docs: complete claims audit, update paired benchmarks, and finalize CLOSE_PROGRESS |
| `docs/DEFECT_LEDGER.md` | 28 | 2026-11-08 | `857f7bc` fix(frontend): resolve DEF-024 execution engine column shift, retitle panel |
| `docs/DEMO_SCRIPT.md` | 116 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/DEPENDENCY_COMPATIBILITY_REPORT.md` | 220 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/DEPLOYMENT_GUIDE.md` | 177 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/DIFF_INCREMENTAL_MODE.md` | 31 | 2026-11-07 | `fec40f9` feat(diff-mode): implement diff-incremental PR-aware mutation hardening |
| `docs/ENVIRONMENT.md` | 52 | 2026-11-07 | `82be443` chore(env): measure and record real environment, fix pyproject.toml dependencies |
| `docs/EQUIVALENCE_DETECTION_REPORT.md` | 30 | 2026-11-07 | `f564f3a` feat(equivalence): implement bytecode dis comparison and advanced semantic equivalence |
| `docs/EXTERNAL_MUTATION_JUDGE.md` | 47 | 2026-11-08 | `dd4b3b9` fix(audit): DEF-020 add statistical caveat to mutmut Pearson correlation claim on N=4 |
| `docs/FEATURE_AUDIT.md` | 46 | 2026-11-08 | `d172100` feat(audit): complete Sub-Task A7 real Chrome frontend audit across all controls |
| `docs/FINAL_FIX_PROGRESS.md` | 23 | 2026-11-08 | `28879a6` docs: finalize FINAL_FIX_PROGRESS.md marking all F0-F6 tasks 100% DONE |
| `docs/FLAKY_TEST_DETECTION.md` | 33 | 2026-11-07 | `d0ac81a` feat(flaky): implement multi-seed randomized flaky-test detection and quarantine |
| `docs/FRONTEND_TEST_MATRIX.md` | 152 | 2026-11-07 | `13f2a4f` docs(frontend): update FRONTEND_TEST_MATRIX with privacy, approval gate, minimizer |
| `docs/HELD_OUT_MUTANTS.md` | 47 | 2026-11-07 | `4fa1a54` feat(eval): evaluate E2 held-out mutants across unseen seeds and 2 new operators |
| `docs/HYPOTHESIS_PROPERTY_TESTING.md` | 32 | 2026-11-07 | `7f2e05e` feat(property-testing): implement hypothesis property-based test generation |
| `docs/LOCAL_VS_CLOUD_EVALUATION.md` | 47 | 2026-11-07 | `eda2a31` feat(eval): complete E5 Local vs Cloud model comparison |
| `docs/MCP_ADK_INTEGRATION.md` | 76 | 2026-11-07 | `fc270a1` feat(mcp): implement MCP tool consumption in Google ADK with path containment |
| `docs/MULTIMODAL_FSM_DERIVATION.md` | 101 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/OPENTELEMETRY_OBSERVABILITY.md` | 58 | 2026-11-07 | `191f5e5` feat(observability): implement OpenTelemetry distributed tracing spans |
| `docs/PERFORMANCE_EVALUATION_REPORT.md` | 327 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/PHASE_ACCEPTANCE_MATRIX.md` | 277 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/PRIVACY_MODE.md` | 32 | 2026-11-07 | `6e03310` feat(privacy): implement zero-egress network air-gap, socket block, and PII scrubber |
| `docs/PROGRESS.md` | 114 | 2026-11-07 | `1d44613` chore: complete Stage 7 final hygiene check, ruff clean, and pass DONE GATE |
| `docs/PROGRESS_FINAL.md` | 27 | 2026-11-10 | `916b843` docs: mark T4 as DONE on release/v1.0.0 branch |
| `docs/PROJECT_REPRESENTATION_STATEMENT.md` | 148 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/PROMPT_GUARD.md` | 56 | 2026-11-07 | `1d44613` chore: complete Stage 7 final hygiene check, ruff clean, and pass DONE GATE |
| `docs/PROVENANCE_AUDIT.md` | 59 | 2026-11-08 | `68852e5` fix(eval): resolve sealed v2 measurement defects, classify as dev set (R2) |
| `docs/README_EXPANSION_PLAN.md` | 115 | 2026-11-08 | `a3d5b84` docs(claims): expand CLAIMS_REGISTER to CLM-027, lead README with negative results |
| `docs/RELEASE_CHECKLIST.md` | 134 | 2026-11-08 | `5d15841` chore(release): finalize release checklist, clean linter, and 999 verified tests |
| `docs/RELEASE_NOTES_v1.0.0.md` | 91 | 2026-11-08 | `5d15841` chore(release): finalize release checklist, clean linter, and 999 verified tests |
| `docs/RELEASE_PROGRESS.md` | 26 | 2026-11-08 | `5d15841` chore(release): finalize release checklist, clean linter, and 999 verified tests |
| `docs/RELEASE_READINESS_AUDIT.md` | 242 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/REPRODUCIBILITY_AUDIT.md` | 77 | 2026-11-08 | `37c8a77` feat(audit): complete Sub-Task A9 documentation sync, 27 viva Q&As |
| `docs/RUBRIC_ALIGNMENT.md` | 82 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/SEALED_EVALUATION.md` | 53 | 2026-11-08 | `f44916d` docs(audit): complete A3 sealed generalization evaluation across 6 diverse modules |
| `docs/SEALED_V2_EVALUATION.md` | 72 | 2026-11-10 | `2b558c8` audit(T2): rescore benchmarks with fixed DEF-022 harness and synchronize claims register |
| `docs/SEALED_V2_MEASUREMENT_AUDIT.md` | 104 | 2026-11-08 | `68852e5` fix(eval): resolve sealed v2 measurement defects, classify as dev set (R2) |
| `docs/SECURITY_AUDIT.md` | 103 | 2026-11-08 | `8c94045` feat(security): complete F3 security holdout with 150 site-packages files (0% FPR) |
| `docs/SECURITY_EVALUATION_REPORT.md` | 108 | 2026-11-07 | `7e7af78` feat(security): expand evaluation corpus to 30 malicious, 40 fresh benign |
| `docs/SECURITY_HOLDOUT.md` | 33 | 2026-11-08 | `8c94045` feat(security): complete F3 security holdout with 150 site-packages files (0% FPR) |
| `docs/SUITE_MINIMIZATION_REPORT.md` | 32 | 2026-11-07 | `c8d0bd4` feat(minimizer): implement kill-matrix greedy set cover test minimization |
| `docs/SURVIVING_MUTANTS.md` | 151 | 2026-11-07 | `bad6cab` feat(generator): add FSM lifecycle and float precision synthesis |
| `docs/TESTFORGE_11_REQUIREMENTS_DEEP_AUDIT.md` | 162 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/TESTFORGE_AST_MUTATION_AND_EQUIVALENCE.md` | 302 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/TESTFORGE_BLACKBOARD_PERSISTENCE.md` | 217 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/TESTFORGE_CHECKPOINT_TIMELINE_AND_DIFF_INSPECTOR.md` | 368 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/TESTFORGE_COMPLETE_TECHNICAL_REPORT.md` | 457 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/TESTFORGE_DEPENDENCY_REPRODUCIBILITY.md` | 161 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/TESTFORGE_DEVELOPMENT_AND_RELEASE_STATUS.md` | 202 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/TESTFORGE_FINAL_RELEASE_GATE.md` | 293 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/TESTFORGE_NEXT_PHASE_ROADMAP.md` | 137 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/TESTFORGE_TECHNICAL_REPORT_EVIDENCE.md` | 69 | 2026-10-25 | `854b4c6` feat: complete final major milestones, teacher requirements, full browser acceptance audit |
| `docs/TEST_DIFF_REVIEW.md` | 76 | 2026-11-08 | `a3d5b84` docs(claims): expand CLAIMS_REGISTER to CLM-027, lead README with negative results |
| `docs/UNIVERSITY_REQUIREMENTS_ACCEPTANCE_MATRIX.md` | 270 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/VERIFICATION_REPORT.md` | 412 | 2026-11-08 | `37c8a77` feat(audit): complete Sub-Task A9 documentation sync, 27 viva Q&As |
| `docs/architecture.md` | 151 | 2026-11-07 | `1d44613` chore: complete Stage 7 final hygiene check, ruff clean, and pass DONE GATE |
| `docs/viva/COMPONENT_BREAKDOWN.md` | 93 | 2026-11-07 | `1d44613` chore: complete Stage 7 final hygiene check, ruff clean, and pass DONE GATE |
| `docs/viva/CORE10_STUDY_GUIDE.md` | 387 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |
| `docs/viva/EXAMINER_QA.md` | 304 | 2026-11-10 | `8cec79a` feat(release): finalize production cockpit UI, telemetry hydration, sandbox safety |

- **Course Final Reports, Presentations & Contribution Matrices Existing in Repository:**
  - **Slide Decks & PPTX Files:**
    * `docs/PROJECT_COVERAGE/TestForge_Project_Coverage.pptx`
    * `docs/VIVA.PRESENTATION/TestForge_Final_Defense_Presentation.pptx`
    * `docs/VIVA.PRESENTATION/TestForge_Requirements_Coverage_Matrix.pptx`
  - **Comprehensive Final Reports:**
    * `docs/WIP_REPORT/TestForge_WIP_Report.pdf` (and `TestForge_WIP_Report.docx`, 4.3 MB / 1.6 MB)
    * `docs/TESTFORGE_COMPLETE_TECHNICAL_REPORT.md` (457 lines)
    * `TECHNICAL_REPORT.md` (root directory, 67 lines)
    * `qa_artifacts/phase2_finalization_20261026_141500/final_report/FINAL_PROJECT_REPORT.md`
  - **Contribution & Requirement Matrices:**
    * `docs/UNIVERSITY_REQUIREMENTS_ACCEPTANCE_MATRIX.md` (270 lines)
    * `docs/RUBRIC_ALIGNMENT.md` (82 lines)
    * `docs/VIVA.PRESENTATION/TESTFORGE_REQUIREMENTS_COVERAGE_MATRIX.md`
    * `qa_artifacts/phase2_finalization_20261026_141500/final_report/TEACHER_REQUIREMENTS_MATRIX.md`
    * `qa_artifacts/autonomous_repair_20261027_112700/ELEVEN_REQUIREMENTS_EVIDENCE_MATRIX.csv`

---

## Contradictions Found

1. **Git Author Identity vs. Project Documentation Authors:**
   `git shortlog -sne --all` records exactly 1 author (`Your Name <your-email@example.com>`, 149 commits), whereas `pyproject.toml:10-13`, `testforge/__init__.py:9`, `run_benchmark.py:5`, `run_demo.py:5`, and source headers name two co-authors: `Sourabh` and `Shreshth`.
2. **ADK Workflow Primitives (Claims vs. Code):**
   `docs/architecture.md` and `docs/8_AGENT_UPGRADE/FINAL_EIGHT_AGENT_ARCHITECTURE.md` claim `ParallelAgent` and `LoopAgent` coordinate the multi-agent workflow. In actual code, `ADKParallelAnalysisAgent` and `ADKLoopReflectionAgent` are defined in `testforge/adk_workflow_agents.py` and tested in `tests/test_adk_workflow_agents.py`, but are **NOT imported or used** in the production orchestrator (`testforge/orchestrator.py` or `testforge/supervisor_agent.py`), which uses a procedural Python loop.
3. **ADK Tool Calling:**
   Documentation states ADK agents use tool calling. In code, **no tools are passed to any `LlmAgent(tools=...)`** in the production path (`testforge/supervisor_agent.py`, `testforge/adk_generator.py`). Tools are executed via direct Python functions or FastMCP client calls.
4. **Agent Naming Inconsistency:**
   Agent 4 is defined in code as `GoogleADKTestGenerator` (`testforge/adk_generator.py:465`), but documentation and frontend refer to it as `TestGeneratorAgent` or `TestGenerationAgent`.
5. **Agentic RAG Integration:**
   `docs/PROJECT_CONTINUATION/PROJECT_CURRENT_STATE.md` references `TestForgeVectorStore` and `AgenticKnowledgeRetriever`, but RAG is not integrated into `orchestrator.py` or `server.py` and has no active production flag.
6. **Multimodal Scope:**
   Handout topics cite multimodal inputs (text, audio, image, video). The codebase only implements image input for FSM state diagrams in `testforge/multimodal_fsm.py`; audio, video, and PDF inputs are not implemented.
7. **Test Cleanliness Regression in Serial Run:**
   Running pytest serially yields 1 failure (`tests/test_clean_working_tree_guard.py`) because `tests/test_mode_c_ingestion.py` writes to tracked `test_hardened.py`, modifying the working tree mid-suite. Under pytest-xdist (`-n auto`), worker isolation allows all 1009 tests to pass cleanly.
8. **Historic Benchmarks Retraction Status:**
   Inflated figures from pre-DEF-022 evaluations (such as `91.5%`, `97.8%`, `62.8%`, `31.5%`, `80.5%`) are formally retracted in `docs/CLAIMS_REGISTER.md` and `docs/SEALED_V2_EVALUATION.md`, but historical unretracted mentions remain in older narrative documents like `docs/SEALED_EVALUATION.md:41-42` (`+36.19% / 45.51%`) and `docs/viva/EXAMINER_QA.md:113-114`.

---

## UNKNOWN / Needs a Human

1. **Course Name and University Affiliation:**
   The exact course code, course title, semester, and university department are not specified in `pyproject.toml` or `README.md` (only general phrases like "coursework mandate" and "teacher review"). A human author must confirm the official course name and university details.
2. **Git Author Configuration Provenance:**
   The git repository was committed under `Your Name <your-email@example.com>`. A human must provide the official Git identity configuration (`git config user.name` / `user.email`) if required for final submission attribution.
3. **Submission Deadlines & Specific Submission Portal Requirements:**
   Whether submission requires uploading `TestForge_WIP_Report.pdf`, the `.pptx` defense presentation, or a GitHub repository link cannot be determined from code alone.

