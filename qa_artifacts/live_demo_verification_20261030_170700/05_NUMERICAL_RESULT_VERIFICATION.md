# 05. TestForge Numerical Result Verification & Mathematical Integrity Audit

**Verification Timestamp:** 2026-10-30T17:15:00+05:30  
**Target Ingested:** `samples/uploaded_logistics_engine.py` (Uploaded as `uploaded_uploaded_logistics_engine.py`)  
**Job ID:** `eaaa0e89`  
**Terminal Checkpoint:** `chk_325953cc296f` (Revision 76)  
**Verification Mechanism:** Cross-reconciliation of raw Python AST parsing, SQLite Checkpoint snapshot (`qa_artifacts/testforge_checkpoints.db`), REST API payload (`GET /api/harden/status/eaaa0e89`), and Frontend DOM element renders.

---

## 1. Primary Metrics Reconciliation Matrix

| Metric Description | Raw Source / Disk Reality | Backend Checkpoint (`chk_325953cc296f`) | API Response (`/api/harden/status`) | UI Element Rendered | Variance / Discrepancy | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **File Byte Size** | 8,277 bytes (`wc -c`) | 8,277 bytes (`target_file_metadata.size_bytes`) | 8,277 bytes | Displayed in Ingest badge | 0 bytes | **VERIFIED** |
| **Source Line Count** | 240 lines (`wc -l`) | 240 lines (`line_count`) | 240 lines | Badge: `240 lines` | 0 lines | **VERIFIED** |
| **AST Classes Extracted** | 2 (`ShippingTier`, `WarehouseInventory`) | 2 (`classes` partition) | 2 | Blast Radius Canvas & Ingest Panel | 0 | **VERIFIED** |
| **AST Functions Extracted** | 6 domain functions + 5 class methods | 11 function nodes total | 11 | Call graph nodes & Ingest Panel | 0 | **VERIFIED** |
| **Executable Statements** | 132 statements | 132 statements (`num_statements`) | 132 statements | Internal AST Metric | 0 | **VERIFIED** |
| **Statements Covered** | 43 statements | 43 statements (`lines_covered`) | 43 statements | Line coverage denominator | 0 | **VERIFIED** |
| **Baseline Line Coverage** | 32.57575757575758% | 32.57575757575758% | 32.58% | Coverage Metric Badge: `32.58%` | 0.00% | **VERIFIED** |
| **Baseline Tests Synthesized** | 11 test assertions | 11 (`baseline_tests_generated`) | 11 | Test Studio Suite | 0 | **VERIFIED** |
| **Baseline Tests Executed** | 11 tests in sandbox | 11 (`baseline_tests_executed`) | 11 | Sandbox execution record | 0 | **VERIFIED** |
| **Baseline Tests Passed** | 11 tests passed | 11 (`baseline_tests_passed`) | 11 | Test Suite Status: `11 / 11 Passed` | 0 | **VERIFIED** |
| **Baseline Test Pass Rate** | 100.0% (`11 / 11 * 100`) | 100.0% (`passed: true`) | 100.0% | Pass Rate: `100%` | 0.0% | **VERIFIED** |
| **First-Order Mutants Generated**| 258 AST mutants | 258 (`mutants_generated`) | 258 | Mutants Table Total: `258` | 0 | **VERIFIED** |
| **Mutants Executed** | 258 sandbox runs | 258 (`mutants_executed`) | 258 | Mutants Table Evaluated | 0 | **VERIFIED** |
| **Mutants Killed** | 0 mutants killed | 0 (`mutants_killed`) | 0 | Mutants Table Filter `KILLED`: 0 | 0 | **VERIFIED** |
| **Mutants Survived** | 258 mutants survived | 258 (`mutants_survived`) | 258 | Mutants Table Filter `SURVIVED`: 258| 0 | **VERIFIED** |
| **Raw Mutation Score** | 0.0% (`0 / 258 * 100`) | 0.0% (`raw_mutation_score`) | 0.0% | Score Gauge / Metric: `0.0%` | 0.0% | **VERIFIED** |
| **Reflection Iterations** | 3 completed cycles | 3 (`reflection_iterations_performed`)| 3 | Iteration Indicator: `Cycle 3/3` | 0 | **VERIFIED** |
| **Parallel Worker Concurrency** | 8 sandbox workers | 8 (`recommended_workers`) | 8 | Hardware concurrency setting | 0 | **VERIFIED** |
| **SQLite Checkpoint Count** | 5 checkpoints | 5 checkpoints for job `eaaa0e89` | 5 | Checkpoint Timeline: 5 nodes | 0 | **VERIFIED** |
| **FastMCP Tools Registered** | 4 tools (`analyze_syntax`, etc.)| 4 tools | 4 | MCP Modal Tool Cards: 4 | 0 | **VERIFIED** |
| **A2A Protocol Version** | v0.3.0 | v0.3.0 | v0.3.0 | A2A Card Header: `v0.3.0` | 0 | **VERIFIED** |

---

## 2. Mathematical Integrity Proofs

### A. Line Coverage Calculation
$$\text{Coverage Rate} = \frac{\text{Statements Covered}}{\text{Total Executable Statements}} \times 100\%$$
$$\text{Coverage Rate} = \frac{43}{132} \times 100\% = 32.575757...\% \approx 32.58\%$$
- **Reconciliation:** Exactly matches the checkpoint field `baseline_line_coverage = 32.57575757575758` and UI display `32.58%`.

### B. Baseline Test Pass Rate
$$\text{Pass Rate} = \frac{\text{Baseline Tests Passed}}{\text{Baseline Tests Executed}} \times 100\%$$
$$\text{Pass Rate} = \frac{11}{11} \times 100\% = 100.0\%$$
- **Reconciliation:** All 11 synthesized tests executed in the isolated sandbox runner and exited with zero failures and zero assertion errors.

### C. Mutation Score Calculation
$$\text{Mutation Score} = \frac{\text{Mutants Killed}}{\text{Total Mutants Generated} - \text{Equivalent Mutants}} \times 100\%$$
$$\text{Mutation Score} = \frac{0}{258 - 0} \times 100\% = 0.0\%$$
- **Reconciliation:** The baseline test assertions generated under the strict non-LLM provider synthesizes nominal presence checks (`assert calculate_item_discount() is not None`), which validates unmutated execution but does not constrain return boundary values or arithmetic mutations. Consequently, all 258 first-order mutants survived, giving an exact mutation score of 0.0%.

---

## 3. Reflection Iteration Progression

| Iteration | Stage Durations | Mutants Evaluated | Killed | Survived | Cumulative Score | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Iteration 1** | 11.88s | 258 | 0 | 258 | 0.0% | `IN_PROGRESS` |
| **Iteration 2** | 74.28s | 258 | 0 | 258 | 0.0% | `IN_PROGRESS` |
| **Iteration 3** | 69.18s | 258 | 0 | 258 | 0.0% | `TARGET_SCORE_UNREACHED` |
| **Total / Final** | **155.34s** | **258** | **0** | **258** | **0.0%** | **`COMPLETED`** |

---

## 4. Checkpoint Revision & Storage Integrity

| Checkpoint ID | Revision | Stage Name | Size (Bytes) | Hash / Status |
| :--- | :---: | :--- | :---: | :--- |
| `chk_91f73e114939` | 25 | `BASELINE_VALIDATED` | 12,951 B | `IN_PROGRESS` |
| `chk_3921cdba2556` | 34 | `REFLECTION_ITERATION_1` | 11,653,214 B | `INITIALIZING` |
| `chk_c79af66a72cc` | 53 | `REFLECTION_ITERATION_2` | 11,814,605 B | `INITIALIZING` |
| `chk_460bb1a04fb6` | 72 | `REFLECTION_ITERATION_3` | 11,816,347 B | `INITIALIZING` |
| `chk_325953cc296f` | 76 | `FINALIZED` | 11,816,422 B | `TARGET_SCORE_UNREACHED` |

- **Storage Verification:** All 5 checkpoints exist in `qa_artifacts/testforge_checkpoints.db` and are verifiable via SHA-256 and JSON schema deserialization.
- **Snapshot Integrity:** The full Blackboard state, AST structures, mutant diffs, execution logs, and metric histories are preserved in SQLite across all 76 revisions without data loss.

