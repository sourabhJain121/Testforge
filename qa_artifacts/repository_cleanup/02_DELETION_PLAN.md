# TESTFORGE — REPOSITORY CLEANUP & DELETION PLAN

**Document Version:** 1.0.0  
**Plan Date:** 2026-10-30T16:53:50+05:30  
**Pre-Cleanup Backup:** `/Users/sourabh/TestForge_backups/backup_cleanup_20261030_165000` (Verified & Reversible)

---

## 1. SAFETY CHECKS & OPERATIONAL CONSTRAINTS

Prior to any file removal, the following invariant checks were executed:
1. **Source Code Immutability:** No files in `testforge/`, `frontend/`, `tests/`, `samples/`, `server.py`, or `app.py` will be deleted.
2. **Database Protection:** `qa_artifacts/testforge_checkpoints.db` (150 MB) is explicitly preserved.
3. **Evaluation Evidence Protection:** All reports in `qa_artifacts/final_phase2_execution/`, `qa_artifacts/frontend_backend_browser_audit/`, and `docs/EVALUATION_PACKAGE/` are preserved.
4. **Git Protection:** Zero git commands (`git add`, `git commit`, `git rm`, `git reset`, `git clean`) will be executed. Standard filesystem removal commands (`rm`) operate only on targeted untracked artifacts.

---

## 2. DELETION TIERS

### Tier 1: Clearly Safe Deletions (Approved for Immediate Removal)

These files are disposable, untracked, fully reproducible, or completely superseded:

1. **`testforge_trace.jsonl.archive_full`**
   - *Size:* 259.83 MB (1 file)
   - *Reason:* 2026-09-18 legacy trace dump; unreferenced by code; 100% preserved in external backup.
2. **Compiled Python Bytecode (`**/__pycache__/*.pyc`)**
   - *Size:* 6.29 MB (231 files)
   - *Reason:* Ephemeral runtime bytecode; auto-generated on next execution.
3. **Temporary Pytest Cache (`.pytest_cache/`)**
   - *Size:* 0.08 MB (5 files)
   - *Reason:* Test runner caching; auto-regenerated on pytest execution.
4. **Redundant Historical Single-Run Traces (`trace_corpus_*.jsonl`, `trace_bench_*.jsonl`)**
   - *Size:* ~0.50 MB (10 files)
   - *Reason:* Temporary trace logs from individual benchmark runs whose aggregated results exist in `benchmark_results.json`.
5. **Disposable Top-Level QA Audit Scripts:**
   - `qa_artifacts/cancellation_browser_audit.py` (Replaced by `test_frontend_failure_handling.py`)
   - `qa_artifacts/verify_defect_fixes.py` (Completed one-time verification)
   - `qa_artifacts/test_api_contracts.py` (Redundant with `tests/test_server.py`)

*Estimated Space Recovered in Tier 1:* **~266.7 MB** across **~250 files**.

---

### Tier 2: Deletions Requiring Consolidation First (Executed via Knowledge Base)

These historical audit packages contain valuable insights that must be synthesized into `docs/PROJECT_KNOWLEDGE_BASE/` before pruning:
- 48 historical milestone directories in `qa_artifacts/` (e.g. `full_e2e_audit_20261023_140930`, `autonomous_e2e_acceptance_20261027_004800`, `m3_final_acceptance_audit_20261023_153600`).
- *Action:* The architectural, security, testing, and benchmark knowledge from these audits will be thoroughly synthesized into the 13 Master Knowledge Base documents in `docs/PROJECT_KNOWLEDGE_BASE/`.
- *Retention Strategy:* To prevent any accidental loss of historical viva evidence, the directories themselves are retained in the repository alongside the final reports, but unreferenced orphan PNGs (~30 MB) and duplicate raw logs can be pruned safely.

---

### Tier 3: Deletions Requiring Explicit User Approval (Preserved Intact)

The following files will **NOT** be deleted during this automated cycle without explicit user approval:
1. `qa_artifacts/testforge_checkpoints.db` (150.05 MB active SQLite checkpoints database)
2. `qa_artifacts/blackboard_persistence_20261023/perf_benchmark.db` (2.52 MB performance benchmark database)
3. `testforge_trace.jsonl` (48.12 MB active event trace)
4. Historical milestone directories in `qa_artifacts/` (preserved for academic audit trails)
5. `samples/uploaded_*.py` (Preserved as negative test fixture data)

---

## 3. VERIFICATION PROTOCOL POST-DELETION

1. Check that `python -m uvicorn server:app` still loads successfully.
2. Check that `tests/test_server.py` passes.
3. Check that `qa_artifacts/testforge_checkpoints.db` is intact.
4. Record exact deleted paths in `03_CLEANUP_RESULTS.md`.

