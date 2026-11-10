# TestForge Release & Viva Submission Checklist (v1.0.0)

This checklist outlines the automated verification baselines and manual human-only steps required for official submission and live oral viva evaluation for **Autonomous Agentic AI Systems (Phase-3 Evaluation)**.

---

## Part 1: Automated Verification Audit (Completed)

All automated verification gates have been audited, executed, and archived under `docs/AUDIT_EVIDENCE/release/`:

| Verification Gate | Task | Evidence File | Verified Status |
| :--- | :--- | :--- | :--- |
| **Clean Baseline** | R0 | `docs/AUDIT_EVIDENCE/release/r0_state_integrity.txt` | ✓ Confirmed zero uncommitted diff vs base |
| **Suite Integrity** | R1 | `docs/AUDIT_EVIDENCE/release/tests_xdist.txt` | ✓ 995 passed in parallel (210s) |
| **Measurement Audit** | R2 | `docs/AUDIT_EVIDENCE/release/rescore_sealed_v2.json` | ✓ Fixed false-kills (`DEF-022`) & coverage doubling (`DEF-023`) |
| **Harness Suite** | R2 | `docs/AUDIT_EVIDENCE/release/tests_xdist_post_r2.txt` | ✓ 999 tests passed (4 new harness regression tests) |
| **mutmut Concordance**| R2 | `docs/AUDIT_EVIDENCE/release/mutmut_cross_check.txt` | ✓ 100% agreement on baseline inadequacy (0 kills) |
| **Dashboard Truthfulness**| R3 | `docs/AUDIT_EVIDENCE/release/r3_dashboard_truthfulness.txt`| ✓ Canonical hash locked, mock badge enforcement active |
| **Repo Hygiene & Secrets**| R4 | `docs/AUDIT_EVIDENCE/release/r4_repo_hygiene.txt` | ✓ 0 secrets leaked, `.mutmut-cache/` gitignored |
| **Claims & Disclosure**| R5 | `docs/AUDIT_EVIDENCE/release/r5_claims_register.txt` | ✓ 31 claims cataloged, AI Disclosure in README |
| **Core-10 Viva Guide** | R6 | `docs/AUDIT_EVIDENCE/release/r6_core10_study_guide.txt` | ✓ All 10 architectural exercises tested & passing |
| **Linter Zero-Defect**| R7 | `docs/AUDIT_EVIDENCE/release/r7_final_close.txt` | ✓ `ruff check testforge/` returned 0 errors |

---

## Part 2: Human-Only Pre-Submission Checklist

Complete the following manual checks prior to packing the final submission archive or presenting to the viva examination board:

### 1. Interactive Headless & Manual Browser Pass
- [ ] **Launch Server:**
  ```bash
  .venv-release/bin/python server.py --host 127.0.0.1 --port 8000
  ```
- [ ] **Open Browser:** Navigate to `http://127.0.0.1:8000` in Google Chrome or Chromium.
- [ ] **Tab Progression Check:**
  - [ ] Target Selection: Select `samples/discount.py` and verify AST parsing visualization.
  - [ ] Configuration: Inspect iteration limit (default: 2), mutation score target (85.0%), and engine selection (`auto`).
  - [ ] Live Monitor: Verify WebSocket connection indicator turns green (`Connected`).
  - [ ] Mutants Table: Check mutation diff view and syntax highlighter.
  - [ ] Benchmarks & Ablation: Confirm multi-target comparison table loads, and check for the `✓ FULL AGENTIC EVALUATION` authenticity badge.
  - [ ] MCP / A2A Tab: Verify FastMCP server status reports `ONLINE` and A2A broker lists registered agent handlers.

### 2. Live Viva Demonstration Script
Ensure your demonstration terminal is prepared with the release virtual environment:
```bash
source .venv-release/bin/activate
```
- [ ] **Exercise 1 (Live Hardening Execution):**
  ```bash
  testforge harden --target samples/discount.py --iterations 2
  ```
  *Demonstration Goal:* Show the CLI terminal output displaying real measured line coverage (100.0%) and mutation score progression across iterations.
- [ ] **Exercise 2 (Blackboard Checkpoint Inspection):**
  ```bash
  python -c "from testforge.blackboard import Blackboard; bb = Blackboard(); print('Partitions:', list(bb.PARTITION_MODELS.keys()))"
  ```
  *Demonstration Goal:* Explain the 8-partition memory isolation architecture and SQLite WAL checkpoint mechanism.
- [ ] **Exercise 3 (False-Kill Guardrail Defense):**
  Explain to the panel how `DEF-022` was discovered and solved:
  - Reference: [`testforge/benchmarking.py:BenchmarkRunner.evaluate_suite`](file:///Users/sourabh/TestForge/testforge/benchmarking.py)
  - Key Invariant: Any candidate test suite failing clean reference code (`pass@1`) is strictly quarantined as `INVALID_SUITE` (0 kills, 0.0% mutation score), preventing false positives.

### 3. Submission Archive Hygiene
If preparing a standalone submission ZIP or tarball:
- [ ] Confirm `.git/` is either retained (for version history evidence) or omitted if only source distribution is required.
- [ ] Ensure virtual environments (`.venv/`, `.venv-release/`) are excluded from archive (`tar --exclude='.venv*' ...`).
- [ ] Ensure temporary caches are purged:
  ```bash
  find . -type d -name "__pycache__" -exec rm -rf {} +
  rm -rf .pytest_cache/ .mutmut-cache/ mutants/
  ```
- [ ] Verify that `NOTICE` (PSF License attribution for Sealed V2) and `LICENSE` (Apache 2.0) are present in the root folder.

