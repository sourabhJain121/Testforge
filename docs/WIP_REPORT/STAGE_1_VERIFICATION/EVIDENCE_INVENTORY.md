# TestForge Stage 1: Evidence Inventory & Asset Catalog

**Document ID:** TF-WIP-EVID-001  
**Inspection Date:** November 2, 2026  
**Commit SHA:** `ee8f765c4f7316e87439fab7250103e6da651c02`  

---

## 1. Overview of Historical Evidence Repositories

TestForge maintains an extensive, immutable historical record of quality assurance audits, empirical benchmark runs, regression test logs, SQLite checkpoint databases, and real browser screenshots under `qa_artifacts/`. All artifacts are preserved in accordance with project safety guidelines.

---

## 2. Key Audit Evidence Directories

| Artifact Directory | Primary Purpose | Key Contents & Verification Artifacts | Date / Timestamp |
| :--- | :--- | :--- | :--- |
| `qa_artifacts/phase3_independent_validation_20261031_142800/` | Independent reproduction of benchmark results | `01_REPRODUCIBILITY_RESULTS.md`, `02_ASSERTION_CORRECTNESS_AUDIT.md`, `03_MUTANT_KILL_VALIDATION.md`, `04_SUITE_PROVENANCE_AUDIT.md`, `07_BASELINE_DISCREPANCY_RECONCILIATION.md`, `discount_isolated.db` (659 KB), `logistics_isolated.db` (48.6 MB), `discount_isolated_trace.jsonl`, `logistics_isolated_trace.jsonl` | 2026-10-31T14:28:00+05:30 |
| `qa_artifacts/phase4_final_readiness_20261031_144500/` | End-to-end live browser workflow & readiness audit | `01_DATABASE_INTEGRITY_AND_IDENTITY.md`, `02_LIVE_WORKFLOW_VERIFICATION.md`, `03_SECURITY_AND_ISOLATION_REVIEW.md`, `04_ACADEMIC_REQUIREMENTS_TRACEABILITY.md`, `05_BENCHMARK_EVIDENCE_CONSISTENCY.md`, `06_FULL_REGRESSION_RESULTS.md`, `screenshots/` (21 genuine browser captures) | 2026-10-31T14:45:00+05:30 |
| `qa_artifacts/phase2_test_generation_20261030_190423/` | Multi-callable generation & boundary synthesis | `01_MULTI_CALLABLE_GENERATION.md`, `02_ASSERTION_QUALITY.md`, `03_BOUNDARY_NEGATIVE_GENERATION.md`, `06_BENCHMARK_COMPARISON.md`, `benchmark_discount.json`, `benchmark_logistics.json`, generated test suites | 2026-10-30T19:04:23+05:30 |
| `qa_artifacts/post_ast_mutation_baseline_20261030_185148/` | Pre-improvement baseline mutation scores | `02_DISCOUNT_BASELINE.md` (5.26%), `03_LOGISTICS_BASELINE.md` (3.10%), `discount_baseline.db` (196 KB), `logistics_baseline.db` (22.6 MB) | 2026-10-30T18:51:48+05:30 |
| `qa_artifacts/ast_scope_regression_fix_20261030_184536/` | AST function scope bugfix audit | `01_ROOT_CAUSE.md`, `02_AST_SCOPE_IMPLEMENTATION.md`, `05_FULL_REGRESSION_RESULTS.md` | 2026-10-30T18:45:36+05:30 |
| `qa_artifacts/final_defect_fixes_20261030_175000/` | Verification of exception swallowing & fallback fixes | Root cause analyses, regression logs, defect verification suite | 2026-10-30T17:50:00+05:30 |

---

## 3. SQLite Persistence & Database Evidence

1. **Active Master Checkpoint Database:**
   - **Path:** `qa_artifacts/testforge_checkpoints.db`
   - **Size:** 208,117,760 bytes (~198.4 MB)
   - **WAL Journal:** `testforge_checkpoints.db-wal` (3.5 MB)
   - **Record Count:** 1,104 snapshots across 210 distinct hardening jobs.
   - **Table Structure:**
     - `blackboard_checkpoints`: Serialized snapshots, stages, timestamps, SHA-256 integrity hashes.
     - `checkpoint_tags`: Partition indexing and metadata tags.
2. **Phase 3 Isolated Benchmark Databases:**
   - `qa_artifacts/phase3_independent_validation_20261031_142800/discount_isolated.db` (659 KB)
   - `qa_artifacts/phase3_independent_validation_20261031_142800/logistics_isolated.db` (48.6 MB)

---

## 4. Real Application Screenshots Inventory

All screenshots were captured during live end-to-end browser audits using automated browser drivers interacting with the live FastAPI backend on `http://127.0.0.1:8000`.

Source directory: `qa_artifacts/phase4_final_readiness_20261031_144500/screenshots/`

| Image Filename | Native Resolution | File Size | UI View / Functionality Proved | Planned Report Role |
| :--- | :---: | :---: | :--- | :--- |
| `01_homepage.png` | 1920 × 1080 | 317 KB | TestForge Unified Cockpit Standby View: System health, navigation tabs, architecture header, and sample selection. | **Figure 3: TestForge Unified Application Dashboard** |
| `07_discount_hardened_kpi.png` | 1920 × 1080 | 353 KB | Terminal Hardening Results for `discount.py`: 11/11 tests passing, 89.47% raw mutation score, 100% line coverage, and iteration breakdown. | **Figure 4: Test Generation & Mutation Results (`discount.py`)** |
| `11_logistics_hardened_kpi.png` | 1920 × 1080 | 261 KB | Multi-Callable Hardening Results for `uploaded_logistics_engine.py`: 64/64 tests passing, 68.22% raw mutation score, 90.15% line coverage, and 176 killed mutants. | **Figure 5: Enterprise Multi-Callable Mutation Hardening Results** |
| `08_checkpoints_timeline.png` | 1920 × 1080 | 315 KB | SQLite Checkpoints Tab: Interactive revision timeline showing atomic snapshots, stage tags, and diff inspection controls. | **Figure 6: Blackboard State Checkpoint Timeline & Differential Audit** |
| `02_a2a_modal.png` | 1920 × 1080 | 127 KB | A2A Protocol v0.3.0 Diagnostic Modal: Displays JSON-LD AgentCard schema, skills list, and endpoint status. | Supporting Appendix Evidence |
| `03_mcp_modal.png` | 1920 × 1080 | 125 KB | FastMCP Tool Diagnostic Modal: Displays active tool registrations (`read_text_file`, `list_directory`, `get_repository_info`). | Supporting Appendix Evidence |
| `09_checkpoints_diff_view.png`| 1920 × 1080 | 164 KB | Checkpoint Diff Inspector Modal: Side-by-side semantic diff between adjacent Blackboard revisions. | Supporting Appendix Evidence |

---

## 5. Verification Integrity

- **Zero Artificial / Fabricated Mockups:** All screenshots originate from authentic browser DOM snapshots captured during Phase 4 live execution.
- **Trace Consistency:** Every screenshot corresponds to an exact microsecond timestamp in `testforge_trace.jsonl` and `qa_artifacts/phase4_final_readiness_20261031_144500/02_LIVE_WORKFLOW_VERIFICATION.md`.
- **Readiness for Stage 2:** Selected figures will be copied into `docs/WIP_REPORT/assets/` during Stage 2 document generation.

