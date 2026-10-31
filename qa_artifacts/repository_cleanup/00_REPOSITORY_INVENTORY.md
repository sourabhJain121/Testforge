# TESTFORGE — REPOSITORY INVENTORY AND AUDIT ASSESSMENT

**Execution Date:** 2026-10-30T16:53:00+05:30  
**Repository Directory:** `/Users/sourabh/TestForge`  
**Git Baseline Commit:** `dc040f027d191d25225d4eb09a5885eef6233f79` (`main`)  
**Pre-Cleanup External Backup:** `/Users/sourabh/TestForge_backups/backup_cleanup_20261030_165000` (Verified)

---

## 1. REPOSITORY OVERVIEW & COMPONENT SIZING

Total non-virtualenv, non-git files across the workspace: **1,397 files**, totaling **642.87 MB**.

```
Workspace Root Breakdown:
├── .venv-release/                  1.3 GB   (Active Python 3.13 production runtime - PROTECTED)
├── .venv/                          604 MB   (Alternative environment - PROTECTED)
├── qa_artifacts/                   339 MB   (Audit history, checkpoints, screenshots, test logs)
│   ├── testforge_checkpoints.db    150 MB   (Active SQLite checkpoints database - PROTECTED)
│   ├── historical audits (48 pkgs) 189 MB   (Audit screenshots, reports, jsonl, scripts)
├── testforge_trace.jsonl.archive_full 260 MB (Obsolete trace archive from 2026-09-18 - DISPOSABLE)
├── testforge_trace.jsonl            49 MB   (Active pipeline event trace - PRESERVE)
├── tests/                          4.6 MB   (Pytest test suite & cached bytecode)
├── testforge/                      2.8 MB   (Core multi-agent application package)
├── docs/                           580 KB   (Architecture, academic specs, evaluation package)
├── samples/                        324 KB   (Benchmark target Python files)
├── frontend/                       320 KB   (HTML5, CSS3, Vanilla JS single-page app)
└── Configuration & Root Files      300 KB   (server.py, app.py, Dockerfile, requirements.txt)
```

---

## 2. FILE INVENTORY BY EXTENSION & CATEGORY

| Extension / Category | File Count | Size (MB) | Purpose / Description | Recommendation |
| :--- | :---: | :---: | :--- | :--- |
| `.archive_full` | 1 | 259.83 MB | Historical snapshot of execution traces from Sep 2026. Not referenced by any code or test. | **Safe to Delete** (Preserved in external backup) |
| `.png` (Screenshots) | 394 | 166.90 MB | Browser automation and UI audit screenshots across 48 QA directories. 76 are completely unreferenced. | **Consolidate & Selectively Prune** (Keep authoritative set) |
| `.db` / `.db-wal` / `.db-shm` | 6 | 154.00 MB | `qa_artifacts/testforge_checkpoints.db` (150 MB active SQLite DB referenced in `server.py:100`), plus benchmark DB. | **PRESERVE Active DB** |
| `.jsonl` (Trace Logs) | 62 | 48.95 MB | Pipeline telemetry traces (`testforge_trace.jsonl`, `trace_reflected.jsonl`, etc.). | **Keep Active Trace**, prune old test fragments |
| `.pyc` (Python Bytecode) | 231 | 6.29 MB | Python cache directories (`__pycache__`). Auto-generated on runtime execution. | **Safe to Delete** (Regenerable) |
| `.md` (Markdown Reports) | 353 | 2.26 MB | Architectural specs, academic checklists, audit deliverables. High overlap across 48 historical milestones. | **Consolidate into Master Knowledge Base** |
| `.py` (Source & Scripts) | 179 | 2.11 MB | Core modules (34), Pytest suites (43), sample targets (31), and one-off QA audit scripts (71). | **Protect Core & Tests**; classify temporary scripts |
| `.json` (Structured Data) | 43 | 1.32 MB | Benchmark outputs, coverage summaries, A2A card schemas. | **Keep Authoritative Benchmarks** |
| `.log` (Execution Logs) | 36 | 0.45 MB | Pytest terminal captures, server stderr/stdout logs. | **Prune redundant terminal dumps** |
| `.csv` (Data exports) | 58 | 0.26 MB | Metric spreadsheets and mutation breakdown logs. | **Consolidate** |
| Frontend Assets (`.js`, `.html`, `.css`) | 3 | 0.30 MB | Production single-page web interface (`frontend/index.html`, `app.js`, `style.css`). | **STRICTLY PROTECTED** |
| Configuration (`Dockerfile`, `requirements.txt`, etc.) | 8 | 0.05 MB | Root project manifests, environment configs. | **STRICTLY PROTECTED** |

---

## 3. TOP 20 LARGEST FILES IN WORKSPACE

1. `testforge_trace.jsonl.archive_full` — **259.83 MB** (Obsolete root trace dump)
2. `qa_artifacts/testforge_checkpoints.db` — **150.05 MB** (Active checkpoints database)
3. `testforge_trace.jsonl` — **48.12 MB** (Active pipeline event log)
4. `qa_artifacts/blackboard_persistence_20261023/perf_benchmark.db` — **2.52 MB** (Temporary benchmark DB)
5. `qa_artifacts/frontend_backend_browser_audit/screenshots/32_redoc_initial.png` — **2.10 MB** (ReDoc API render)
6. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/05_ast_diff_equivalence_inspector.png` — **1.38 MB**
7. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/04d_mutants_table_equiv.png` — **1.38 MB**
8. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/03_hardening_completed.png` — **1.37 MB**
9. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/04a_mutants_table_all.png` — **1.37 MB**
10. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/04c_mutants_table_survived.png` — **1.37 MB**
11. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/04b_mutants_table_killed.png` — **1.37 MB**
12. `qa_artifacts/m3_final_acceptance_audit_20261023_153600/screenshots/10_mutant_diff_inspected.png` — **1.29 MB**
13. `qa_artifacts/m3_final_acceptance_audit_20261023_153600/screenshots/09_hardening_completed.png` — **1.29 MB**
14. `qa_artifacts/phase2_master_acceptance_20261023_162200/screenshots/10_hardening_completed.png` — **1.22 MB**
15. `qa_artifacts/phase2_master_acceptance_20261023_162200/screenshots/11_mutant_diff_inspected.png` — **1.22 MB**
16. `qa_artifacts/testforge_checkpoints.db-wal` — **1.21 MB** (SQLite write-ahead log)
17. `qa_artifacts/milestone_3_evidence_20261023_150000/screenshots/m3_01_wiretap_live_connected.png` — **1.15 MB**
18. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/02d_mode_c_github.png` — **1.10 MB**
19. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/07_checkpoint_diff_viewer.png` — **1.06 MB**
20. `qa_artifacts/full_e2e_audit_20261023_140930/screenshots/02c_mode_b_synthesis.png` — **1.06 MB**

---

## 4. TEMPORARY QA AUDIT SCRIPTS

The following Python scripts in `qa_artifacts/` were generated for one-time audits or specialized browser checks:
- `qa_artifacts/run_full_browser_audit.py` (32 KB)
- `qa_artifacts/run_extended_controls_and_edge_cases.py` (16 KB)
- `qa_artifacts/checkpoint_ui_browser_audit.py` (12 KB)
- `qa_artifacts/cancellation_browser_audit.py` (12 KB)
- `qa_artifacts/verify_defect_fixes.py` (8 KB)
- `qa_artifacts/test_api_contracts.py` (8 KB)
- `qa_artifacts/final_phase2_execution/test_frontend_failure_handling.py` (8 KB - reusable verification tool)

---

## 5. REPOSITORY HEALTH & ASSESSMENT

1. **Working Code & Tests Integrity:** Application source code (`testforge/`), frontend files (`frontend/`), server (`server.py`), and test suite (`tests/`) are clean, fully tested, and passing 523/523 tests.
2. **Artifact Bloat Factor:** Over 60% of repository disk usage (outside `.venv`) consists of obsolete root trace dumps (`testforge_trace.jsonl.archive_full`, 260 MB), historical screenshots (167 MB), and Python cache files (6.3 MB).
3. **Documentation Dispersion:** Valuable project architectural and evaluation data is currently fragmented across 353 markdown files in 48 milestone directories. Consolidating this into a clean `docs/PROJECT_KNOWLEDGE_BASE/` is essential for knowledge transfer.

