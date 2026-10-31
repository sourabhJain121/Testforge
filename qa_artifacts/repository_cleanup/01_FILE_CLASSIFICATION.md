# TESTFORGE — ARTIFACT CLASSIFICATION MATRIX

**Document Version:** 1.0.0  
**Classification Date:** 2026-10-30T16:53:25+05:30  
**Classification Target:** 1,397 files across `/Users/sourabh/TestForge` (excluding `.venv` and `.git`)

---

## 1. CLASSIFICATION CATEGORIES & DISPOSITION RULES

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLASSIFICATION TAXONOMY                         │
├────────────────────────────────┬───────────────────────────────────────┤
│ Cat 1: Essential Project Docs  │ KEEP PERMANENTLY                      │
│ Cat 2: Authoritative Evidence  │ KEEP PERMANENTLY (Current Source)     │
│ Cat 3: Superseded / Duplicates │ CONSOLIDATE & PRUNE REDUNDANT COPIES  │
│ Cat 4: Temporary Audit Scripts │ KEEP REUSABLE / PRUNE ONE-OFF         │
│ Cat 5: Disposable Caches/Logs  │ SAFE TO DELETE IMMEDIATELY            │
│ Cat 6: Uncertain Value         │ PRESERVE PENDING USER APPROVAL        │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. CATEGORY 1: ESSENTIAL PROJECT DOCUMENTATION (KEEP)

These files define the fundamental project architecture, system design, API contracts, and usage:
- `README.md` (Root repository entry point)
- `docs/EVALUATION_PACKAGE/*` (Project Overview, System Architecture, Demonstration Script, Security, Setup, Handover)
- `docs/PHASE_MASTER_TRACKER.md`, `docs/PHASE_ACCEPTANCE_MATRIX.md`, `docs/PROJECT_DEVELOPMENT_ROADMAP.md`
- `docs/TESTFORGE_COMPLETE_TECHNICAL_REPORT.md` (Authoritative technical paper)
- `docs/TESTFORGE_AST_MUTATION_AND_EQUIVALENCE.md` (Formal AST mutation algorithm theory)
- `docs/TESTFORGE_CHECKPOINT_TIMELINE_AND_DIFF_INSPECTOR.md`
- `docker-compose.yml`, `Dockerfile`, `requirements.txt`
- `start_testforge.sh`
- All application source files in `testforge/`, `frontend/`, `server.py`, `app.py`.
- All test suites in `tests/`.
- All benchmark targets in `samples/`.

---

## 3. CATEGORY 2: FINAL AUTHORITATIVE EVALUATION EVIDENCE (KEEP)

The authoritative final evaluation evidence produced during the latest evaluation cycle:
- `qa_artifacts/final_phase2_execution/*`
  - `00_BASELINE_AND_GAP_ANALYSIS.md`
  - `01_TEST_GENERATION_QUALITY.md`
  - `02_AGENTIC_INTEGRATION_VERIFICATION.md`
  - `03_FRONTEND_AND_FAILURE_RECOVERY.md`
  - `04_DEMO_AND_VIVA_FINAL.md`
  - `05_FINAL_REGRESSION_AND_REQUIREMENTS.md`
  - `06_FINAL_EVALUATION_READINESS_REPORT.md`
  - `README.md`
  - `test_frontend_failure_handling.py`
- `qa_artifacts/frontend_backend_browser_audit/*` (Latest browser acceptance audit evidence on port 8000: 72 verified screenshots and structured JSON results)
- `qa_artifacts/testforge_checkpoints.db` (Active SQLite database containing multi-run checkpoints, referenced by `server.py:100`)
- `qa_artifacts/testforge_checkpoints.db-wal` & `testforge_checkpoints.db-shm`
- `benchmark_results.json` & `benchmark_results.md` (Root authoritative benchmark output)

---

## 4. CATEGORY 3: DUPLICATE OR SUPERSEDED HISTORICAL AUDITS

Over 40 intermediate milestone directories in `qa_artifacts/` were generated during historical iterative audit passes (e.g., Oct 22 to Oct 27). Their conclusions have been verified and superseded by `final_phase2_execution` and `frontend_backend_browser_audit`:

| Directory / Artifact Set | Size | Files | Reason for Deprecation |
| :--- | :---: | :---: | :--- |
| `qa_artifacts/full_e2e_audit_20261023_140930/` | 23.78 MB | 37 (26 pngs) | Audited legacy Streamlit frontend (Port 8501). Superseded by FastAPI browser audit. |
| `qa_artifacts/m3_final_acceptance_audit_20261023_153600/` | 14.64 MB | 31 (18 pngs) | Milestone 3 intermediate audit on legacy UI. Superseded. |
| `qa_artifacts/phase2_master_acceptance_20261023_162200/` | 14.22 MB | 35 (19 pngs) | Intermediate Phase 2 audit on legacy UI. Superseded. |
| `qa_artifacts/visible_browser_playground_20261027_083200/` | 11.18 MB | 38 (15 pngs) | Early browser playground test prior to single-frontend consolidation. Superseded. |
| `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/` | 18.64 MB | 114 (53 pngs)| Automated bot run on legacy layout. Superseded. |
| `qa_artifacts/autonomous_repair_20261027_112700/` | 9.20 MB | 28 (12 pngs) | Intermediate self-repair test run. Superseded. |
| `qa_artifacts/complete_frontend_acceptance_audit/` | 8.34 MB | 100 (56 pngs)| Dual-frontend transition audit. Superseded by final FastAPI audit. |
| `qa_artifacts/teacher_review_implementation_20261027_105100/` | 7.22 MB | 16 (9 pngs) | Pre-teacher review milestone. |
| `qa_artifacts/teacher_release_acceptance_20261027_111000/` | 6.96 MB | 14 (7 pngs) | Intermediate release audit. |
| `qa_artifacts/final_acceptance_20261025_214800/` | 5.48 MB | 34 (17 pngs) | Legacy milestone acceptance. |
| `qa_artifacts/demo_rehearsal_20261025_220900/` | 5.29 MB | 22 (17 pngs) | Historical demo run. |
| `qa_artifacts/browser_audit/` | 5.08 MB | 15 (12 pngs) | Early browser snapshot. |
| `qa_artifacts/baseline_verdict_consistency_20261027_095000/` | 3.89 MB | 11 (5 pngs) | Intermediate verdict check. |
| `qa_artifacts/pre_phase2_readiness/` | 2.73 MB | 37 (18 pngs) | Pre-Phase-2 audit superseded by `final_phase2_execution`. |
| Unreferenced historical PNGs | ~30 MB | 76 pngs | Loose screenshots unreferenced in any report. |

*Disposition:* All information from these reports has been incorporated into the master technical documentation and final evaluation deliverables. All raw files are preserved in the pre-cleanup external backup `/Users/sourabh/TestForge_backups/backup_cleanup_20261030_165000`.

---

## 5. CATEGORY 4: TEMPORARY GENERATED SCRIPTS

| Script Path | Size | Classification | Action | Reason |
| :--- | :---: | :---: | :---: | :--- |
| `qa_artifacts/final_phase2_execution/test_frontend_failure_handling.py` | 8 KB | **Reusable Test Utility** | **KEEP** | Exercises real frontend error scenarios and active cancellation against live API. |
| `qa_artifacts/run_full_browser_audit.py` | 32 KB | **One-Off Audit Runner** | **Consolidate / Prune** | Automated script used to drive one specific historical browser run. Output is captured. |
| `qa_artifacts/run_extended_controls_and_edge_cases.py` | 16 KB | **One-Off Audit Runner** | **Consolidate / Prune** | Automated script for edge-case DOM probing. Output is captured. |
| `qa_artifacts/checkpoint_ui_browser_audit.py` | 12 KB | **One-Off Audit Runner** | **Consolidate / Prune** | Single-use UI inspector script. Output is captured. |
| `qa_artifacts/cancellation_browser_audit.py` | 12 KB | **One-Off Audit Runner** | **Consolidate / Prune** | Single-use cancellation inspector script. Replaced by `test_frontend_failure_handling.py`. |
| `qa_artifacts/verify_defect_fixes.py` | 8 KB | **One-Off Verification** | **Consolidate / Prune** | Tested intermediate defect patches. Verified. |
| `qa_artifacts/test_api_contracts.py` | 8 KB | **Duplicate API Test** | **Consolidate / Prune** | Duplicates tests in `tests/test_server.py`. |

---

## 6. CATEGORY 5: DISPOSABLE LOGS AND CACHES (SAFE TO DELETE)

| Path / Pattern | Size | Items | Description |
| :--- | :---: | :---: | :--- |
| `testforge_trace.jsonl.archive_full` | 259.83 MB | 1 file | Untracked raw trace log snapshot from September 2026. Zero references across codebase. |
| `**/__pycache__/*.pyc` | 6.29 MB | 231 files | Compiled Python bytecode across `tests/`, `testforge/`, `samples/`. Automatically regenerated on run. |
| `.pytest_cache/` | 0.08 MB | Cache files | Pytest step cache from previous runs. Rebuilt on test execution. |
| Redundant trace logs (`trace_corpus_*.jsonl`, `trace_bench_*.jsonl`) | ~0.50 MB | 10 files | Temporary individual run traces whose metrics are merged into `benchmark_results.json`. |

---

## 7. CATEGORY 6: UNCERTAIN FILES (PRESERVED PENDING USER APPROVAL)

- `qa_artifacts/blackboard_persistence_20261023/perf_benchmark.db` (2.52 MB): Historical SQLite benchmark DB. Kept intact because it contains performance timing data.
- Sample targets with edge-case names (`samples/uploaded_bad.py`, `samples/uploaded_08_syntax_error.py`, etc.): Kept intact because they serve as negative test inputs for ingestion tests.

