# TestForge Surviving Mutant Empirical Analysis

> **Scope**: Exhaustive AST mutant analysis across all 4 canonical benchmark targets.
> **Analysis Timestamp**: 2026-11-07
> **Methodology**: Deterministic AST mutant injection, parallel subprocess sandbox execution, and semantic equivalence classification.

## 1. Executive Summary Table

| Target Module | Total Mutants | Killed | Survived | Equivalent | Raw Kill Score | Adjusted Kill Score | Primary Findings |
|---|---|---|---|---|---|---|---|
| `samples/discount.py` | 19 | 18 | 0 | 1 | 94.7% | 100.0% | 1 Equivalent, 0 Killable/Unknown |
| `samples/order_fsm.py` | 106 | 103 | 0 | 3 | 97.2% | 100.0% | 3 Equivalent (dead-code fallbacks), 0 Killable/Unknown |
| `samples/lru_cache.py` | 42 | 13 | 25 | 4 | 31.0% | 34.2% | 4 Equivalent, 25 Killable/Unknown |
| `samples/stats_calculator.py` | 73 | 33 | 38 | 2 | 45.2% | 46.5% | 2 Equivalent, 38 Killable/Unknown |

---

## Target Analysis: `samples/discount.py`
- **Source File**: `samples/discount.py`
- **Test Suite Used**: `qa_artifacts/test_hardened_discount.py`
- **Total Mutants Injected**: 19
- **Killed**: 18
- **Survived**: 0
- **Equivalent**: 1
- **Raw Mutation Score**: 94.74%
- **Adjusted Mutation Score**: 100.00%

### Surviving & Equivalent Mutants Ledger

| Mutant ID | Operator | Line | Status | Classification | Diff Summary | Root Cause & Killability Rationale |
|---|---|---|---|---|---|---|
| `MUT_BOUNDARY_SWAP_003` | `BOUNDARY_SWAP` | L9 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_3) @@ -6,15 +...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |

## Target Analysis: `samples/order_fsm.py`
- **Source File**: `samples/order_fsm.py`
- **Test Suite Used**: `qa_artifacts/test_hardened_order_fsm.py` (100% Autonomous Pipeline-Generated)
- **Total Mutants Injected**: 106
- **Killed**: 103
- **Survived**: 0 (killable)
- **Equivalent**: 3
- **Raw Mutation Score**: 97.17%
- **Adjusted Mutation Score**: 100.00%

### Surviving & Equivalent Mutants Ledger

| Mutant ID | Operator | Line | Status | Classification | Diff Summary | Root Cause & Killability Rationale |
|---|---|---|---|---|---|---|
| `MUT_CONST_VAL_079` | `CONST_VAL` | L71 | `EQUIVALENT` | **EQUIVALENT** | `return False, reason or "TRANSITION_REJECTED"` -> `reason or ""` | In `transition_order_state`, `validate_transition` returns `(False, <error_string>)` whenever invalid. Since `<error_string>` is non-empty for every invalid transition, the right-hand operand `"TRANSITION_REJECTED"` is unreachable dead-code. Mutating it to `""` produces identical observable output. |
| `MUT_CONST_VAL_083` | `CONST_VAL` | L83 | `EQUIVALENT` | **EQUIVALENT** | `initial_state: str = ""` (mutated from `"CREATED"`) | In `OrderFSM.__init__`, `self.state = initial_state if initial_state in ALLOWED_TRANSITIONS else "CREATED"`. If mutated to `""`, `"" not in ALLOWED_TRANSITIONS`, falling back to `"CREATED"`. Calling `OrderFSM()` with default arguments results in the exact same state `"CREATED"`. |
| `MUT_CONST_VAL_097` | `CONST_VAL` | L97 | `EQUIVALENT` | **EQUIVALENT** | `return False, reason or "REJECTED"` -> `reason or ""` | In `OrderFSM.transition`, `self.can_transition` calls `validate_transition`, which always returns a non-empty string when False. The fallback `"REJECTED"` is mathematically unreachable. |


## Target Analysis: `samples/lru_cache.py`
- **Source File**: `samples/lru_cache.py`
- **Test Suite Used**: `IntelligentASTSynthesizer generated`
- **Total Mutants Injected**: 42
- **Killed**: 13
- **Survived**: 25
- **Equivalent**: 4
- **Raw Mutation Score**: 30.95%
- **Adjusted Mutation Score**: 34.21%

### Surviving & Equivalent Mutants Ledger

| Mutant ID | Operator | Line | Status | Classification | Diff Summary | Root Cause & Killability Rationale |
|---|---|---|---|---|---|---|
| `MUT_BOUNDARY_SWAP_003` | `BOUNDARY_SWAP` | L25 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_3) @@ -2,36 +...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |
| `MUT_RETURN_VAL_019` | `RETURN_VAL` | L63 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_19) @@ -2,36 ...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |
| `MUT_RETURN_VAL_022` | `RETURN_VAL` | L76 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_22) @@ -2,36 ...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |
| `MUT_BOUNDARY_SWAP_025` | `BOUNDARY_SWAP` | L78 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_25) @@ -2,36 ...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |
| `MUT_OFF_BY_ONE_004` | `OFF_BY_ONE` | L25 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_4) @@ -2,36 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_OFF_BY_ONE_005` | `OFF_BY_ONE` | L25 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_5) @@ -2,36 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_006` | `CONST_VAL` | L26 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_6) @@ -2,36 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_008` | `CONST_VAL` | L30 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_8) @@ -2,36 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_009` | `CONST_VAL` | L33 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_9) @@ -2,36 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_010` | `CONST_VAL` | L34 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_10) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_COND_INV_011` | `COND_INV` | L42 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_11) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_LOGICAL_CONN_012` | `LOGICAL_CONN` | L42 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_12) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_COND_INV_013` | `COND_INV` | L50 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_13) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_016` | `CONST_VAL` | L60 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_16) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_RETURN_VAL_017` | `RETURN_VAL` | L61 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_17) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_018` | `CONST_VAL` | L62 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_18) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_COND_INV_023` | `COND_INV` | L78 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_23) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_COMP_OP_024` | `COMP_OP` | L78 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_24) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_COND_INV_026` | `COND_INV` | L81 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_26) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_LOGICAL_CONN_027` | `LOGICAL_CONN` | L81 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_27) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_COMP_OP_028` | `COMP_OP` | L81 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_28) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_RETURN_VAL_029` | `RETURN_VAL` | L89 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_29) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_031` | `CONST_VAL` | L100 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_31) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_032` | `CONST_VAL` | L101 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_32) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_ARITH_OP_033` | `ARITH_OP` | L105 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_33) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_RETURN_VAL_039` | `RETURN_VAL` | L108 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_39) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_MATH_FUNC_040` | `MATH_FUNC` | L108 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_40) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_ARITH_OP_041` | `ARITH_OP` | L108 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_41) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_042` | `CONST_VAL` | L108 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_42) @@ -2,36 ...` | Killed if tests assert exact state transition or precision requirement. |

## Target Analysis: `samples/stats_calculator.py`
- **Source File**: `samples/stats_calculator.py`
- **Test Suite Used**: `IntelligentASTSynthesizer generated`
- **Total Mutants Injected**: 73
- **Killed**: 33
- **Survived**: 38
- **Equivalent**: 2
- **Raw Mutation Score**: 45.21%
- **Adjusted Mutation Score**: 46.48%

### Surviving & Equivalent Mutants Ledger

| Mutant ID | Operator | Line | Status | Classification | Diff Summary | Root Cause & Killability Rationale |
|---|---|---|---|---|---|---|
| `MUT_BOUNDARY_SWAP_013` | `BOUNDARY_SWAP` | L26 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_13) @@ -2,45 ...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |
| `MUT_BOUNDARY_SWAP_042` | `BOUNDARY_SWAP` | L57 | `EQUIVALENT` | **EQUIVALENT** | `--- target.py (original) +++ target.py (mutant_42) @@ -2,45 ...` | Mathematically proven equivalent by boundary equivalence analyzer. Cannot be killed by any valid test. |
| `MUT_CONST_VAL_002` | `CONST_VAL` | L14 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_2) @@ -2,45 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_005` | `CONST_VAL` | L18 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_5) @@ -2,45 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_OFF_BY_ONE_008` | `OFF_BY_ONE` | L24 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_8) @@ -2,45 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_OFF_BY_ONE_009` | `OFF_BY_ONE` | L24 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_9) @@ -2,45 +...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_010` | `CONST_VAL` | L25 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_10) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_014` | `CONST_VAL` | L27 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_14) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_ARITH_OP_015` | `ARITH_OP` | L27 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_15) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_016` | `CONST_VAL` | L27 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_16) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_023` | `CONST_VAL` | L34 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_23) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_026` | `CONST_VAL` | L43 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_26) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_028` | `CONST_VAL` | L46 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_28) @@ -2,52 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_RETURN_VAL_035` | `RETURN_VAL` | L49 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_35) @@ -2,52 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_ARITH_OP_036` | `ARITH_OP` | L49 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_36) @@ -2,52 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_ARITH_OP_037` | `ARITH_OP` | L49 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_37) @@ -2,52 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_ARITH_OP_038` | `ARITH_OP` | L49 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_38) @@ -2,52 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_039` | `CONST_VAL` | L49 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_39) @@ -2,52 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_OFF_BY_ONE_043` | `OFF_BY_ONE` | L57 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_43) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_OFF_BY_ONE_044` | `OFF_BY_ONE` | L57 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_44) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_045` | `CONST_VAL` | L58 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_45) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_046` | `CONST_VAL` | L60 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_46) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_RETURN_VAL_048` | `RETURN_VAL` | L62 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_48) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_MATH_FUNC_050` | `MATH_FUNC` | L63 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_50) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_053` | `CONST_VAL` | L63 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_53) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_055` | `CONST_VAL` | L69 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_55) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_OFF_BY_ONE_058` | `OFF_BY_ONE` | L71 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_58) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_060` | `CONST_VAL` | L71 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_60) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_062` | `CONST_VAL` | L73 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_62) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_063` | `CONST_VAL` | L74 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_63) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_064` | `CONST_VAL` | L75 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_64) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_065` | `CONST_VAL` | L76 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_65) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_066` | `CONST_VAL` | L77 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_66) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_067` | `CONST_VAL` | L78 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_67) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_MATH_FUNC_068` | `MATH_FUNC` | L74 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_68) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_069` | `CONST_VAL` | L74 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_69) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_MATH_FUNC_070` | `MATH_FUNC` | L75 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_70) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_071` | `CONST_VAL` | L75 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_71) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_MATH_FUNC_072` | `MATH_FUNC` | L78 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_72) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |
| `MUT_CONST_VAL_073` | `CONST_VAL` | L78 | `SURVIVED` | **KILLABLE** | `--- target.py (original) +++ target.py (mutant_73) @@ -2,45 ...` | Killed if tests assert exact state transition or precision requirement. |

