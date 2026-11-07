# TestForge Phase-3 Evaluation: Engineering & Evidence Progress

**Branch**: `feat/final-evidence` (branched from `chore/pre-final-verification`)  
**Starting Baseline**: 864 passed, 1 skipped (commit `3db66fc`)  
**Mode**: INTEGRITY FIRST, THEN EVIDENCE, THEN FEATURES, THEN POLISH  
**Last Updated**: 2026-11-07  

---

## Stage-by-Stage Work Queue

### Stage 0: Integrity Reconciliation (Pre-Feature Mandate)
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **0.1** | Score provenance audit & pipeline-only separation | DONE | `de58324` | Documented in `docs/PROVENANCE_AUDIT.md`. Manual oracles separated into `tests/manual_oracles/`. `qa_artifacts/test_hardened_*.py` verified 100% pipeline-generated. |
| **0.2** | Single source of truth (`MULTI_TARGET_BENCHMARK_RESULTS.json`), reconcile stale claims across repo, add sync test | DONE | `e260ea5` | Established JSON as single source of truth, protected server endpoint against overwrite, created `sync_benchmarks.py`, and added `tests/test_benchmark_source_of_truth_sync.py` (4 passed). |
| **0.3** | `order_fsm` survivor loop diagnosis (ToT, ReAct, RAG, convergence stop) | DONE | `bad6cab` | Added float precision candidates and FSM lifecycle synthesis in `IntelligentASTSynthesizer`. `order_fsm.py` kills jumped from 14/106 (13.3%) to 103/106 (97.17% raw, 100% adj; 3 equivalent dead-code fallbacks). `discount.py` kills reached 18/19 (100% adj, 1 equivalent). Single source of truth and docs updated. |
| **0.4** | Baseline competitors: (a) developer, (b) zero-shot, (c) zero-shot+retry, (d) TestForge with 3 seeds | DONE | `e6c09f9` | Evaluated 4 configurations across 4 targets with seeds [42, 43, 44] using `gemini-3.6-flash` (fallback: `qwen2.5-coder:7b`). Saved raw metrics in `qa_artifacts/BASELINE_COMPARISON_RAW.json` and rendered comparison table in `docs/BASELINE_COMPARISON.md`. |
| **0.5** | Fresh benign set (40+ files) & prompt injection attack samples | DONE | `79b98a1` | Generated 30 malicious, 40 fresh benign, 20 held-out benign, and 20 prompt injection files. Evaluated guardrails: 100% TPR (30/30), 0.0% FPR (0/40 fresh, 0/20 held-out), 100% direct injection detection (20/20), 100% indirect injection defusal (20/20). Artifacts in `qa_artifacts/SECURITY_EVALUATION_REPORT.json` and `docs/SECURITY_EVALUATION_REPORT.md`. Added `tests/test_evaluation_corpus_hardening.py` (6 passed). |
| **0.6** | Protocol consolidation (`a2a.py` / `a2a_protocol.py`) & dead code cleanup | DONE | `d9659d0` | Audited and consolidated A2A layers: `testforge/a2a.py` lazy re-exports official A2A protocol components (`build_testforge_agent_card`, `create_testforge_a2a_app`, `TestForgeA2AClient`, `TestForgeA2AExecutor`, `OFFICIAL_A2A_PROTOCOL_VERSION`, etc.) with explicit `__all__` and zero circular dependencies. 36 A2A tests verified passing. Dead code audited. |
| **0.7** | Docker reality check on real Docker daemon | DONE | `0ee4c7f` | Verified live Docker Desktop daemon (v29.4.3, aarch64, Linuxkit 6.12.76). Tagged `testforge:latest` (e4899221a9f1). Executed `tests/test_sandbox_backend.py` (7 passed in 2.95s) with live kernel `--network none` isolation test producing `Errno 101 Network is unreachable`. Evidence captured in `qa_artifacts/DOCKER_VERIFICATION_LOG.md`. |
| **0.8** | ADK production orchestrator path verification | DONE | `3190861` | Pinned `google-adk==1.14.1` in `requirements.txt` and verified in `pyproject.toml`. Verified that all 7 core specialist agents instantiate and bind to `google.adk.runners.Runner` and `google.adk.sessions.BaseSessionService`. Verified `TestForgeOrchestrator` native ADK pipeline binding. Added `tests/test_adk_production_path.py` (3 passed). |
| **0.9** | Test runner speed optimization without dropping tests | DONE | `c0bf98b` | Configured `[tool.pytest.ini_options]` in `pyproject.toml` with `fast`, `slow`, `docker`, `live_llm` markers and warning suppressions. Built `testforge/scripts/run_tests.py` offering `--profile fast` (142 tests in 8.3s via parallel xdist workers) and `--profile full` without dropping any tests. Stage 0 complete. |

### Stage 1: Evidence (Viva Package)
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **1.1** | Feature flags for every capability with behavioral tests | TODO | - | Configurable toggles: ref_exec, reflection, self_consistency, tot, react, rag, memory, critic, equivalence |
| **1.2** | Parallel mutant execution (ProcessPoolExecutor) with score parity verification | TODO | - | Report speedup vs serial |
| **1.3** | 4 extra real-world-style targets (50-150 LOC) with permissive licenses | TODO | - | Tokenizer, rate limiter, interval utility, bank/inventory |
| **1.4** | E1 Ablation matrix (7 configurations, 3 seeds, 8 targets, metrics & PNG chart) | TODO | - | Zero-shot -> +ref -> +refl -> +SC -> +ToT/ReAct -> +RAG/memory -> +3-critic |
| **1.5** | E2 Held-out mutants (unseen seeds + 2 unseen operator classes) | TODO | - | Report seen vs held-out score gap per target |
| **1.6** | E3 External mutation judge (`mutmut` / `cosmic-ray`) comparison | TODO | - | Independent mutation score comparison |
| **1.7** | E4 `adk eval` on Planner and Generator | TODO | - | Trajectory & response-match scoring in `evals/` |
| **1.8** | E5 Local vs Cloud model comparison (Gemini, qwen2.5-coder:7b, others) | TODO | - | Score, latency, cost, and tokens |

### Stage 2: Handout Protocols: MCP and A2A for Real
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **2.1** | MCP tool consumption in ADK agent with path containment | TODO | - | Attach FastMCP tools to ADK agent, capture live invocation trace |
| **2.2** | TestForge as MCP server (`harden_module`, `get_report`, `list_jobs`) | TODO | - | FastMCP server, test with official client, Claude Desktop config |
| **2.3** | Distributed cross-process A2A with separate Critic process | TODO | - | Dual-process execution, distinct PIDs in logs, in-process fallback |
| **2.4** | Label accuracy in documentation | TODO | - | Disambiguate official A2A vs FIPA envelopes |

### Stage 3: ADK Depth, Observability & Guardrails
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **3.1** | `DatabaseSessionService` & ADK `MemoryService` cross-job learning | TODO | - | Demonstrate cross-job mutant memory reuse |
| **3.2** | ADK Callbacks (`before_tool_callback`, `before_agent_callback`) | TODO | - | Path policy and iteration/token budget guards |
| **3.3** | Output guardrails & human approval gate for repo writes / PRs | TODO | - | Block forbidden imports/network in tests, API + UI button |
| **3.4** | Observability: OpenTelemetry trace exporter & dashboard integration | TODO | - | Per-job trace id, tokens, cost, latency, supervisor decision log |
| **3.5** | `adk web` compatibility and documentation | TODO | - | Verify and document `adk web` against project agents |

### Stage 4: Privacy & Multimodal
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **4.1** | Privacy mode with zero-egress proof & PII/secret scrubbing | TODO | - | Single toggle (UI/CLI/env), verify zero outbound connections |
| **4.2** | Multimodal (image) requirement derivation for state machines | TODO | - | Upload diagram, derive FSM transition tests (Gemini vision / local) |

### Stage 5: Beyond the Handout
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **5.1** | Kill-matrix minimization (greedy set cover, dashboard heatmap) | TODO | - | Tests x mutants matrix, minimal suite reduction |
| **5.2** | Diff-incremental mode (mutate only changed lines in PR) | TODO | - | Integrate into CI, measure time saved |
| **5.3** | Flaky-test detection (randomized execution order re-runs) | TODO | - | Flag nondeterministic test executions |
| **5.4** | Stronger equivalence detection (bytecode `dis` comparison + LLM judge) | TODO | - | Measure precision on labeled sample |
| **5.5** | Hypothesis property testing generation (`@given`) | TODO | - | Emit property tests, identify property-only kills |
| **5.6** | Extended mutation operators (statement deletion, exception swap) | TODO | - | Broaden AST operator diversity |

### Stage 6: Frontend: Real Browser Verification
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **6.1** | UI components for all new features (ablation, privacy, heatmap, traces) | TODO | - | Vanilla JS, zero npm dependencies |
| **6.2** | Rebuild `docs/FRONTEND_TEST_MATRIX.md` from live DOM | TODO | - | Reconcile element IDs and routes against live server |
| **6.3** | Live browser exercise of every control with screenshots | TODO | - | Real Chrome execution, 0 console errors, 0 broken requests |
| **6.4** | Self-repair loop on any non-PASS controls | TODO | - | Root-cause fix in correct layer |
| **6.5** | Full second-pass regression verification of frontend matrix | TODO | - | Capture view screenshots in `docs/screenshots/` |

### Stage 7: Documentation, Demo & Viva Pack
| Sub-Task ID | Description | Status | Last Commit | Next Step / Notes |
| :--- | :--- | :---: | :---: | :--- |
| **7.1** | README update (Mermaid architecture, coverage matrix, real versions) | TODO | - | Map handout topics to files, one-command demo |
| **7.2** | `docs/architecture.md` and 4+ ADRs | TODO | - | Blackboard, ADK+CrewAI, Docker sandbox, ref execution |
| **7.3** | `docs/viva/` component breakdown and examiner Q&A | TODO | - | Technical deep dives and documented limitations |
| **7.4** | `docs/DEMO_SCRIPT.md` (10-minute demo script with fallback plan) | TODO | - | Timed walkthrough from weak tests to live hardening |
| **7.5** | Final report Phase 2 reconciliation | TODO | - | Comprehensive final report in `docs/VERIFICATION_REPORT.md` |
| **7.6** | Phase-3 mapping table (rubric C11-C15) | TODO | - | Rubric alignment table with concrete evidence |
| **7.7** | Final hygiene check, tags, and PR summary | TODO | - | Clean git status, ruff check 0 errors, branch ready |

---

## DONE GATE Criteria Checklist
- [ ] Full pytest passes (zero failures), count >= 864, plus all new tests.
- [ ] Every reported score is regenerated by the pipeline end-to-end, comes from the single JSON source of truth, and README/frontend/docs match it. MANUAL results labeled separately.
- [ ] Baselines (developer, zero-shot, zero-shot+retry) and ablation table exist with seeds, mean ± std, and models recorded.
- [ ] Held-out mutant results and an external mutation judge (`mutmut`/`cosmic-ray`) are reported.
- [ ] MCP consumption, TestForge-as-MCP-server, and cross-process A2A demonstrated with automated tests and logs.
- [ ] ADK sessions, memory, tool/agent callbacks, and OTel traces working and tested.
- [ ] Privacy mode with zero-egress proof; image-input path implemented and tested.
- [ ] Docker sandbox backend verified on real Docker daemon (or BLOCKED with reason).
- [ ] Every control in `FRONTEND_TEST_MATRIX.md` is PASS in real browser with zero console errors.
- [ ] `DEFECT_LEDGER.md` has zero OPEN items; `PROGRESS.md` shows all items DONE or BLOCKED-with-evidence.
- [ ] README, architecture docs, ADRs, viva pack, demo script, and final report complete; ruff clean; git clean.

