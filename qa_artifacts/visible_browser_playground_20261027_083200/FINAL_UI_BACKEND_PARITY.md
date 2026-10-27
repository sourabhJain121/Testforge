# Final UI to Backend Parity Report

**Audit Directory**: `qa_artifacts/visible_browser_playground_20261027_083200/`  
**Parity Verification**: 100% Complete across 5 Sample Files + Error Workflows  
**Verdict**: **PASS — VERIFIED FOR TESTED SCOPE**  

---

## 1. Metric Parity Breakdown

All metrics rendered in the visible Google Chrome browser match the authoritative response returned by `/api/harden/status/{job_id}`:

| Sample File | Job ID | Metric Name | Frontend Rendered | Authoritative Backend | Parity Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **discount.py** | `7ece683e` | Mutation Score | `63.2%` | `63.2%` | **MATCH** |
| | | Mutants Killed | `12` | `12` | **MATCH** |
| | | Mutants Survived | `7` | `7` | **MATCH** |
| | | Mutants Generated | `19` | `19` | **MATCH** |
| | | Line Coverage | `100.0%` (10/10) | `100.0%` (10/10) | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (0 failed) | **MATCH** |
| **banking.py** | `c72bfc10` | Mutation Score | `52.2%` | `52.2%` | **MATCH** |
| | | Mutants Killed | `12` | `12` | **MATCH** |
| | | Mutants Survived | `11` | `11` | **MATCH** |
| | | Mutants Generated | `23` | `23` | **MATCH** |
| | | Line Coverage | `90.0%` (9/10) | `90.0%` (9/10) | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (0 failed) | **MATCH** |
| **inventory_pricing.py** | `2d7e1089` | Mutation Score | `46.0%` | `46.0%` | **MATCH** |
| | | Mutants Killed | `17` | `17` | **MATCH** |
| | | Mutants Survived | `20` | `20` | **MATCH** |
| | | Mutants Generated | `37` | `37` | **MATCH** |
| | | Line Coverage | `71.4%` (15/21) | `71.4%` (15/21) | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (0 failed) | **MATCH** |
| **state_machine.py** | `6abda83d` | Mutation Score | `21.1%` | `21.1%` | **MATCH** |
| | | Mutants Killed | `12` | `12` | **MATCH** |
| | | Mutants Survived | `45` | `45` | **MATCH** |
| | | Mutants Generated | `57` | `57` | **MATCH** |
| | | Line Coverage | `64.3%` (9/14) | `64.3%` (9/14) | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (0 failed) | **MATCH** |
| **rate_limiter.py** | `bf3e4392` | Mutation Score | `42.1%` | `42.1%` | **MATCH** |
| | | Mutants Killed | `16` | `16` | **MATCH** |
| | | Mutants Survived | `22` | `22` | **MATCH** |
| | | Mutants Generated | `38` | `38` | **MATCH** |
| | | Line Coverage | `81.8%` (9/11) | `81.8%` (9/11) | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (0 failed) | **MATCH** |

---

## 2. Cancellation and Recovery Parity

- **Cancellation (`1bd95ca1`)**:
  - Frontend Banner: `🛑 Hardening Cancelled`
  - Frontend Status KPI: `CANCELLED`
  - Backend Status: `CANCELLED`
  - Parity: **MATCH**

- **Empty Target Guard**:
  - Frontend: Execution prevented, warning toast shown
  - Backend: No orphaned job created
  - Parity: **MATCH**
