# Live UI to Authoritative Backend Cross-Check & Parity Analysis

**Audit Run**: `qa_artifacts/visible_browser_playground_20261027_083200/`  
**Execution Timestamp**: 2026-10-27T08:52:00+05:30 to 2026-10-27T08:55:00+05:30  
**Status**: 100% PARITY ACHIEVED ACROSS ALL 5 SAMPLES  

---

## 1. Summary of Cross-Check Findings

Every sample source file executed through the visible browser interface was tracked through the complete chain:
`UI Button Click` → `POST /api/harden/start` → `TaskLifecycleFSM` → `Parallel Sandbox` → `Critic & Reflections` → `GET /api/harden/status/{id}` → `Frontend DOM KPI Cards`

### Comprehensive Parity Verification Table:

| Target File | Job ID | Metric Field | Frontend DOM Value | Backend Authoritative Value | Parity Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **discount.py** | `7ece683e` | Mutation Score | `63.2%` | `63.2%` (63.1578%) | **MATCH** |
| | | Mutants Killed | `12` | `12` | **MATCH** |
| | | Mutants Survived | `7` | `7` | **MATCH** |
| | | Mutants Generated | `19` | `19` | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (`tests_failed == 0`) | **MATCH** |
| | | Final Status | `TARGET_SCORE_UNREACHED` | `TARGET_SCORE_UNREACHED` | **MATCH** |
| **banking.py** | `c72bfc10` | Mutation Score | `52.2%` | `52.2%` (52.1739%) | **MATCH** |
| | | Mutants Killed | `12` | `12` | **MATCH** |
| | | Mutants Survived | `11` | `11` | **MATCH** |
| | | Mutants Generated | `23` | `23` | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (`tests_failed == 0`) | **MATCH** |
| | | Final Status | `TARGET_SCORE_UNREACHED` | `TARGET_SCORE_UNREACHED` | **MATCH** |
| **inventory_pricing.py** | `2d7e1089` | Mutation Score | `46.0%` | `46.0%` (45.9459%) | **MATCH** |
| | | Mutants Killed | `17` | `17` | **MATCH** |
| | | Mutants Survived | `20` | `20` | **MATCH** |
| | | Mutants Generated | `37` | `37` | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (`tests_failed == 0`) | **MATCH** |
| | | Final Status | `TARGET_SCORE_UNREACHED` | `TARGET_SCORE_UNREACHED` | **MATCH** |
| **state_machine.py** | `6abda83d` | Mutation Score | `21.1%` | `21.1%` (21.0526%) | **MATCH** |
| | | Mutants Killed | `12` | `12` | **MATCH** |
| | | Mutants Survived | `45` | `45` | **MATCH** |
| | | Mutants Generated | `57` | `57` | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (`tests_failed == 0`) | **MATCH** |
| | | Final Status | `TARGET_SCORE_UNREACHED` | `TARGET_SCORE_UNREACHED` | **MATCH** |
| **rate_limiter.py** | `bf3e4392` | Mutation Score | `42.1%` | `42.1%` (42.1052%) | **MATCH** |
| | | Mutants Killed | `16` | `16` | **MATCH** |
| | | Mutants Survived | `22` | `22` | **MATCH** |
| | | Mutants Generated | `38` | `38` | **MATCH** |
| | | Clean Code Verdict | `🟢 ALL PASSED` | `True` (`tests_failed == 0`) | **MATCH** |
| | | Final Status | `TARGET_SCORE_UNREACHED` | `TARGET_SCORE_UNREACHED` | **MATCH** |

---

## 2. Independent Formula Recomputation

The mutation score formula:
$$\text{Score} = \frac{\text{Mutants Killed}}{\text{Mutants Generated}} \times 100$$
was independently validated against the returned counts:
- `discount.py`: $\frac{12}{19} \times 100 = 63.1578\% \rightarrow \mathbf{63.2\%}$ (Exact match)
- `banking.py`: $\frac{12}{23} \times 100 = 52.1739\% \rightarrow \mathbf{52.2\%}$ (Exact match)
- `inventory_pricing.py`: $\frac{17}{37} \times 100 = 45.9459\% \rightarrow \mathbf{46.0\%}$ (Exact match)
- `state_machine.py`: $\frac{12}{57} \times 100 = 21.0526\% \rightarrow \mathbf{21.1\%}$ (Exact match)
- `rate_limiter.py`: $\frac{16}{38} \times 100 = 42.1052\% \rightarrow \mathbf{42.1\%}$ (Exact match)

No fake metrics, simulated numbers, or hardcoded values were present. The rendered UI reflects genuine execution telemetry in real time.
