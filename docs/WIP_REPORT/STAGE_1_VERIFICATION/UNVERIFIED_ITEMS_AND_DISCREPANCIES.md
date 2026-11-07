# TestForge Stage 1: Unverified Items, Discrepancies & Audit Log

**Document ID:** TF-WIP-DISC-001  
**Inspection Date:** November 2, 2026  
**Commit SHA:** `ee8f765c4f7316e87439fab7250103e6da651c02`  

---

## 1. Overview of Audit Findings

In strict compliance with the Stage 1 verification objective, this document catalogs all technical discrepancies discovered across historical documentation, distinguishes verified local implementations from unverified external cloud services, and details the exact resolutions applied to ensure complete factual integrity in the upcoming Work in Progress Report.

---

## 2. Unverified and Partially Verified Items

### 2.1 Public Cloud Hyperscaler Deployment
- **Verification Status:** **Implemented but Partially Verified**.
- **Verified Aspects:** Multi-stage production `Dockerfile`, `docker-compose.yml`, non-root user permissions, internal port bindings (8000), and automated container deployment tests (`tests/test_deployment.py`: 10/10 passed).
- **Unverified Aspects:** Live deployment to managed public cloud platforms (e.g. AWS ECS/Fargate, Google Cloud Run, Azure App Services) has not been executed, as the academic evaluation rubric is scoped to local and offline execution.
- **Report Handling:** The WIP Report will explicitly describe deployment readiness as *local containerized and native reproducibility*, clarifying that public cloud deployment is planned for future production phases.

### 2.2 Live External GitHub API Integration
- **Verification Status:** **Implemented and Verified with Offline Test Doubles**.
- **Verified Aspects:** `testforge/mcp_server.py:create_github_server` and `testforge/github_service.py` implement full repository inspection, safe redirect handling (`SafeGitHubRedirectHandler`), and SSRF defenses tested across 62 automated network security tests.
- **Unverified Aspects:** When executed without a user-provided `GITHUB_TOKEN`, external GitHub API calls route through deterministic offline fixtures to prevent rate-limit failures and paid network requests during academic evaluation.
- **Report Handling:** The report will state that FastMCP GitHub tooling is fully integrated with safe fallbacks and bounded streaming, with live external API calls gated by optional credentials.

### 2.3 Upstream Library Deprecation Notices
- **Verification Status:** **Audited and Confirmed Non-Blocking**.
- **Audit Findings:**
  1. *CrewAI Notice:* `PydanticDeprecatedSince20` and `function_calling_llm` warnings in `crewai==0.11.0`.
  2. *Google Cloud Notice:* `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version of google-cloud-aiplatform`.
- **Impact:** Neither warning impacts application runtime, test execution, or pipeline stability.
- **Report Handling:** Mentioned transparently in Section 2.7–2.8 as known upstream library version notices.

---

## 3. Historical Discrepancies & Exact Resolutions

### Discrepancy 1: Baseline Test Count for `discount.py` (2 Tests vs. 4 Tests)
- **The Discrepancy:**
  - `qa_artifacts/post_ast_mutation_baseline_20261030_185148/02_DISCOUNT_BASELINE.md` reported **2 tests** generated for `discount.py` killing 1/19 mutants (5.26%).
  - `qa_artifacts/phase2_test_generation_20261030_190423/06_BENCHMARK_COMPARISON.md` reported **4 tests** for baseline `discount.py` killing 1/19 mutants (5.26%).
- **Root Cause:**
  - The pre-Phase-2 codebase contained two independent legacy heuristic generators:
    1. `ADKModelBridge._synthesize_deterministic_tests` in `testforge/adk_generator.py` synthesized 2 tests.
    2. `TestGeneratorAgent._synthesize_ast_aware_tests` in `testforge/agents.py` synthesized 4 tests.
  - Because both legacy generators only asserted `assert res is not None`, both suites caught only the condition inversion mutant `MUT_COND_INV_001` and failed on all other 18 mutants, achieving the identical **5.26%** score.
- **Resolution in WIP Report:**
  - Documented in Chapter 7. Both legacy generators achieved identical 5.26% mutation outcomes. Both routines have been unified and superseded by `IntelligentASTSynthesizer`, which deterministically produces **11 tests** achieving **89.47% raw / 94.44% adjusted score**.

---

### Discrepancy 2: Browser Dashboard UI Metric (94.7%) vs. Offline Benchmark (89.47% / 94.44%)
- **The Discrepancy:**
  - The live browser demonstration recorded a terminal mutation score of **94.7%** on `discount.py`.
  - The offline reproducible benchmark report records **89.47% raw** and **94.44% adjusted**.
- **Root Cause:**
  - In offline deterministic test execution, TestForge uses whole-number test inputs (e.g. `price=100.0, quantity=1`). Under these inputs, Mutant 18 (`round(x, 1)`) yields `90.0`, identical to clean code (`90.0`), allowing it to survive (17/19 killed = 89.47% raw, or 17/18 = 94.44% adjusted for 1 equivalent mutant).
  - During the live browser demonstration with dynamic LLM generation enabled, the model synthesized an unrounded fractional price (`price=99.99`). Under this input, $99.99 \times 0.9 = 89.991 \implies \text{round}(..., 2) = 89.99$, whereas Mutant 18 produced $90.0$. The assertion failed, killing Mutant 18!
  - With 18 of 19 mutants killed:
    $$\frac{18}{19} = 94.7368\% \implies \mathbf{94.7\%}$$
- **Resolution in WIP Report:**
  - Fully reconciled in Chapter 7. Both numbers are genuine and reflect distinct execution modes: 89.47% is the offline reproducible static baseline; 94.7% is the live dynamic LLM runtime result.

---

### Discrepancy 3: Active SQLite Checkpoint Database Location
- **The Discrepancy:**
  - Two database files existed: `checkpoints.db` (0 bytes, root directory) and `qa_artifacts/testforge_checkpoints.db` (197.3 MB).
- **Root Cause:**
  - Early prototype runs initialized an empty placeholder at the project root. The production persistent store was centralized into `qa_artifacts/testforge_checkpoints.db`.
- **Resolution in WIP Report:**
  - `qa_artifacts/testforge_checkpoints.db` is confirmed as the authoritative persistent database containing 1,104 atomic snapshots across 210 jobs. Root `checkpoints.db` is ignored and omitted.

---

## 4. User Alignments for Stage 2

The following items are flagged for supervisor and user alignment during Stage 2:
1. **Target Report Length:** Budgeted at ~12–13 pages excluding appendices to ensure high academic density without filler.
2. **Visual Style:** Strictly black-and-white vector diagrams for Figures 1 and 2, consistent with the NEXUS reference PDF.
3. **Primary Benchmark Numbers:** Reporting **89.47% raw / 94.44% adjusted** on Discount, and **68.22% raw / 75.21% adjusted** on Logistics, with a dedicated reconciliation sidebar explaining the live UI 94.7% metric.

