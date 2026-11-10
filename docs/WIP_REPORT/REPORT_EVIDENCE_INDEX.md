# TestForge Work in Progress Report: Evidence Index

**Document ID:** TF-WIP-EVID-INDEX-001  
**Report Title:** TestForge — Autonomous Agentic Unit Test Hardening via Multi-Callable Synthesis and AST Mutation Analysis  
**Course:** Autonomous Agentic AI  
**Author:** Sourabh Jain  
**Verified Commit SHA:** `ee8f765c4f7316e87439fab7250103e6da651c02`  
**GitHub Remote:** `https://github.com/sourabhJain121/Testforge`  
**Inspection Date:** November 2, 2026  

---

## 1. Primary Empirical Evidence Directory Map

This index catalogs every piece of empirical data, verification run, database snapshot, and screenshot used to substantiate the claims in the TestForge Work in Progress Report.

| Report Chapter / Claim | Primary Evidence Directory / Artifact | Key Recorded Metrics | Verification Hash / Integrity Proof |
| :--- | :--- | :--- | :--- |
| **Chapter 2: Requirements Verification** | `qa_artifacts/phase4_final_readiness_20261031_144500/04_ACADEMIC_REQUIREMENTS_TRACEABILITY.md` | 11/12 requirements verified; 1 partially verified (cloud deployment) | 542 passed, 0 failed in 277s |
| **Chapter 3: System Architecture & Workflow** | `testforge/blackboard.py`, `testforge/orchestrator.py`, `docs/VIVA_PREPARATION/02_SYSTEM_ARCHITECTURE.md` | RLock thread safety, 5 Blackboard partitions, closed-loop reflection | Code AST verified at commit `ee8f765c4f7316` |
| **Chapter 4: Implementation Details** | `testforge/intelligent_generator.py`, `testforge/mutator.py`, `server.py` | 1,261 lines in generator, 9 mutation families, 42 REST endpoints | Code AST verified at commit `ee8f765c4f7316` |
| **Chapter 5: Security Guardrails** | `tests/test_network_security.py`, `tests/test_mcp_network_security.py`, `tests/test_prompt_injection_defense.py` | 98 dedicated security tests (100% passing); SSRF, AST, PromptGuard | 0 security bypasses in adversarial suite |
| **Chapter 6: Full Regression Suite** | `qa_artifacts/phase4_final_readiness_20261031_144500/06_FULL_REGRESSION_RESULTS.md` | 542 passed, 0 failed in 277.12s; 305 upstream deprecation warnings | `pytest tests/` exit code 0 |
| **Chapter 7: Discount Benchmark (Offline)** | `qa_artifacts/phase3_independent_validation_20261031_142800/reproduction_discount.json` | 11 tests, 10/10 stmts (100%), 17/19 killed (89.47% raw, 94.44% adjusted) | Suite SHA: `eaa41e0b1e28e872...` |
| **Chapter 7: Discount Benchmark (Live UI)** | `qa_artifacts/phase4_final_readiness_20261031_144500/05_BENCHMARK_EVIDENCE_CONSISTENCY.md` | 18/19 killed (94.74% live UI); fractional input $99.99 killing mutant 18 | Real browser capture (2026-10-31 & 2026-11-02) |
| **Chapter 7: Logistics Benchmark** | `qa_artifacts/phase3_independent_validation_20261031_142800/reproduction_logistics.json` | 64 tests, 119/132 stmts (90.15%), 176/258 killed (68.22% raw, 75.21% adj) | Suite SHA: `c3e17c4d66308ced...` |
| **Chapter 7: Initial Mutation Baseline** | `qa_artifacts/post_ast_mutation_baseline_20261030_185148/02_DISCOUNT_BASELINE.md`, `03_LOGISTICS_BASELINE.md` | Discount: 1/19 killed (5.26%); Logistics: 8/258 killed (3.10%) | Pre-improvement baseline logs |
| **Chapter 8: Live Application Status** | Live FastAPI server on `http://127.0.0.1:8000/` | `/healthz`: healthy; `/readyz`: operational; A2A card active | Browser inspection on 2026-11-02 02:30 |
| **Chapter 8: Persistent SQLite Database** | `qa_artifacts/testforge_checkpoints.db` | 197.3 MB, 1,104 snapshots across 210 hardening jobs | SQLite schema `blackboard_checkpoints` |

---

## 2. Visual Figures & Screenshots Attribution

| Figure Number | Image File Path | Date Captured | Generation Method / Tool | Figure Description & Caption |
| :--- | :--- | :---: | :--- | :--- |
| **Figure 1** | `docs/WIP_REPORT/assets/figure1_system_architecture.png` | 2026-11-02 | Python Matplotlib (Vector 300 DPI) | Overall TestForge System Architecture showing UI, FastAPI, Orchestrator, Multi-Agent Tier, Blackboard, and Sandbox. |
| **Figure 2** | `docs/WIP_REPORT/assets/figure2_execution_workflow.png` | 2026-11-02 | Python Matplotlib (Vector 300 DPI) | Multi-Agent Test Hardening Execution Workflow showing the 8-step closed-loop reflection cycle. |
| **Figure 3** | `docs/WIP_REPORT/assets/fresh_01_homepage.png` | 2026-11-02 02:29 | `agent-browser` (Headless Chromium) | TestForge Unified Application Dashboard and System Health Overview. |
| **Figure 4** | `docs/WIP_REPORT/assets/fresh_02_discount_hardened.png` | 2026-11-02 02:30 | `agent-browser` (Headless Chromium) | Automated Test Generation and Mutation Testing Terminal KPI Results for `discount.py` (89.5% score, 17 killed, 2 survived). |
| **Figure 5** | `docs/WIP_REPORT/assets/figure5_logistics_hardened_kpi.png` | 2026-10-31 14:55 | Playwright (Historical Phase 4 Audit) | Enterprise Multi-Callable Mutation Hardening Terminal Results for `uploaded_logistics_engine.py` (64 Tests, 176 Mutants Killed, 68.22% Score). |
| **Figure 6** | `docs/WIP_REPORT/assets/fresh_03_checkpoints_timeline.png` | 2026-11-02 02:30 | `agent-browser` (Headless Chromium) | Persistent Blackboard Checkpoint Timeline in SQLite showing Atomic Revisions and Semantic Diff Controls. |
| **Figure 7** | `docs/WIP_REPORT/assets/figure7_benchmark_comparison.png` | 2026-11-02 | Python Matplotlib (Vector 300 DPI) | Mutation Score Comparison: Baseline Raw vs. Hardened Raw vs. Hardened Adjusted across Discount and Logistics Benchmarks. |

