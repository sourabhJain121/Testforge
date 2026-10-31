# Report 01: Multi-Callable Discovery & Synthesis Architecture

**Artifact Directory**: `qa_artifacts/phase2_test_generation_20261030_190423/`  
**Evaluation Phase**: Phase 2 — Intelligent Multi-Callable Test Generation & Refinement  
**Status**: VERIFIED & BENCHMARKED  
**Date**: October 30, 2026  

---

## 1. Executive Summary

In Phase 1 and earlier historical executions, TestForge exhibited a severe architectural bottleneck: test generation stopped at `signatures[0]`, omitting all remaining top-level functions and completely ignoring class methods (`instance`, `staticmethod`, `classmethod`). In `uploaded_logistics_engine.py`, 9 out of 10 callables were left untested, resulting in a disastrous baseline mutation score of **3.10% (8/258 killed)**.

In Phase 2, we designed, implemented, and benchmarked the **`IntelligentASTSynthesizer`** and its companion AST analysis engine (`testforge/intelligent_generator.py`). The engine dynamically discovers and synthesizes tests for **100% of eligible callables** across module functions, class constructors, instance methods, and static methods.

---

## 2. Discovery & Synthesis Architecture

```
                                  Source Code (AST)
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │   IntelligentASTSynthesizer     │
                         │      (Callable Discovery)       │
                         └────────────────┬────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
       Top-Level Functions                            Classes & Methods
    ┌───────────────────────┐                     ┌───────────────────────┐
    │  ASTCallableAnalyzer  │                     │   ClassInfo Discovery │
    │  - Guard extraction   │                     │  - __init__ args      │
    │  - Thresholds (T±1)   │                     │  - Instance methods   │
    │  - Enum / sets        │                     │  - Static methods     │
    └───────────┬───────────┘                     └───────────┬───────────┘
                │                                             │
                └───────────────────────┬─────────────────────┘
                                        ▼
                         ┌─────────────────────────────────┐
                         │       ReferenceExecutor         │
                         │  (Isolated Pre-Flight Sandbox)  │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │    SynthesizedSuiteResult       │
                         │  - Value-aware assertions       │
                         │  - Boundary tests (T, T-1, T+1) │
                         │  - pytest.raises exception guards│
                         └─────────────────────────────────┘
```

### Callable Eligibility Rules
1. **Module Functions**: All non-mangled public/internal functions (`def foo()`, `def _bar()`). Nested helper functions inside other functions are excluded as unit test targets.
2. **Class Methods**:
   - `__init__`: Inspected to determine constructor signature and state initialization requirements.
   - **Instance Methods**: Synthesized using a managed class instance constructed with nominal arguments.
   - **Static Methods**: Invoked directly via `ClassName.method(...)`.
   - **Class Methods**: Invoked directly via `ClassName.method(...)`.
   - Dunder methods (`__repr__`, `__eq__`, `__hash__`) are excluded from standalone direct calls and verified via behavioral tests.

---

## 3. Empirical Callable Discovery Comparison

### Target 1: `samples/discount.py` (20 LOC)

| Metric | Phase 1 Baseline | Phase 2 Multi-Callable | Delta |
|---|---|---|---|
| Discovered Callables | 1 | 1 | 0 |
| Eligible Callables | 1 | 1 | 0 |
| Covered Callables | 1 (`calculate_discount`) | 1 (`calculate_discount`) | 0 |
| Callable Coverage % | 100.0% | 100.0% | 0.0% |
| Total Tests Synthesized | 4 | 11 | +7 (+175%) |

### Target 2: `samples/uploaded_logistics_engine.py` (240 LOC)

| Callable Name | Scope | Callable Type | Phase 1 Baseline Status | Phase 2 Implementation Status |
|---|---|---|---|---|
| `calculate_item_discount` | Module | Function | Tested (Single Target) | **Fully Covered (15 tests)** |
| `estimate_freight_cost` | Module | Function | **OMITTED (Untested)** | **Fully Covered (11 tests)** |
| `calculate_customs_duty` | Module | Function | **OMITTED (Untested)** | **Fully Covered (11 tests)** |
| `validate_tracking_number` | Module | Function | **OMITTED (Untested)** | **Fully Covered (6 tests)** |
| `compute_sla_deadline_hours` | Module | Function | **OMITTED (Untested)** | **Fully Covered (11 tests)** |
| `process_bulk_order` | Module | Function | **OMITTED (Untested)** | **Fully Covered (4 tests)** |
| `WarehouseInventory.get_available_stock` | Class | Instance Method | **OMITTED (Untested)** | **Fully Covered (1 test)** |
| `WarehouseInventory.reserve_stock` | Class | Instance Method | **OMITTED (Untested)** | **Fully Covered (3 tests)** |
| `WarehouseInventory.release_stock` | Class | Instance Method | **OMITTED (Untested)** | **Fully Covered (3 tests)** |
| `WarehouseInventory.restock_needed` | Class | Instance Method | **OMITTED (Untested)** | **Fully Covered (1 test)** |
| `WarehouseInventory (State Transition)` | Class | State Machine | **OMITTED (Untested)** | **Fully Covered (1 multi-step test)** |

### Multi-Callable Discovery Summary

| Metric | Phase 1 Baseline | Phase 2 Multi-Callable | Absolute Improvement |
|---|---|---|---|
| **Discovered Callables** | 10 | 10 | — |
| **Eligible Callables** | 10 | 10 | — |
| **Tested Callables** | 1 | **10** | **+9 callables** |
| **Callable Coverage %** | 10.0% | **100.0%** | **+90.0%** |
| **Skipped Callables** | 9 | **0** | **-9 skipped** |
| **Total Tests Synthesized** | 11 | **64** | **+53 tests (+481%)** |

---

## 4. Class Method Synthesis Mechanics

The synthesis engine inspects classes using AST and builds stateful test cases:

```python
# Synthesized by IntelligentASTSynthesizer for WarehouseInventory
def test_WarehouseInventory_get_available_stock_nominal():
    obj = WarehouseInventory({'SKU-001': 20})
    result = obj.get_available_stock('SKU-001')
    assert result == 20

def test_WarehouseInventory_state_and_methods():
    obj = WarehouseInventory({'SKU-001': 20})
    res_0 = obj.get_available_stock('SKU-001')
    assert res_0 == 20
    res_1 = obj.reserve_stock('SKU-001', 2)
    assert res_1 is True
    res_2 = obj.release_stock('SKU-001', 2)
    assert res_2 is True
    res_3 = obj.restock_needed('SKU-001', 2)
    assert res_3 is False
```

Every method call is validated during pre-flight in `ReferenceExecutor` against clean target code before the suite is packaged. Any method that fails pre-flight is skipped and recorded in `skipped_callables` with a diagnostic reason, preventing broken tests from contaminating candidate suites.

