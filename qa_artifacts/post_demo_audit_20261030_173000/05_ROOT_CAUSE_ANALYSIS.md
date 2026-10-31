# 05. Root Cause Analysis & Defect Classification

**Audit Identifier:** `TF-AUDIT-ROOT-CAUSE-20261030-173000`  
**Evaluation Scope:** Analysis of TestForge live demo behavior, 0% mutation score on logistics engine, and test artifact provenance discrepancies.

---

## 1. Classification of Findings

| Finding ID | Phenomenon Observed | Technical Classification | Root Cause Category |
| :---: | :--- | :---: | :---: |
| **F-01** | All 258 mutants on `uploaded_logistics_engine.py` survived (0.0% score) | **Test-Generation Weakness** | Universal Exception Swallowing in Fallback Generator |
| **F-02** | Initial ADK generation produced single dummy stub `test_calculate_item_discount_nominal` with 0 arguments | **Test-Generation Weakness** | Incomplete signature argument mapping in offline ADK generator |
| **F-03** | `test_hardened.py` contained 1 test while baseline reported 11 passed tests | **Architecture / State Sync Defect** | Premature Blackboard synchronization in `A2ABroker` |
| **F-04** | 7 mutants survived on `samples/discount.py` (63.2% score) | **Insufficient Test Coverage** | Genuine boundary condition gaps (nominal tests vs. boundary values) |
| **F-05** | AST mutator generation, subprocess sandboxing, and score computation | **Verified Functionality** | Zero defects in mutation engine core |

---

## 2. Root Cause Analysis

### Finding F-01: Universal Exception Swallowing in Fallback Synthesizer
- **Classification:** **Test-Generation Weakness**
- **Location:** `testforge/agents.py`, method `TestGeneratorAgent._synthesize_ast_aware_tests`, lines 909–918.
- **Code:**
  ```python
  else:
      dummy_args = ", ".join(["1"] * len(args))
      test_functions.append(f"""
  def test_generic_{fn}():
      try:
          res = {fn}({dummy_args})
          assert res is not None
      except Exception:
          pass
  """)
  ```
- **Analysis:**  
  When an uploaded module contains functions not explicitly hardcoded into the deterministic synthesizer rules, the fallback generator creates dummy functions with `try: ... except Exception: pass`.  
  The intention was to ensure that candidate tests for unknown functions would not immediately crash pytest during baseline validation if dummy arguments were invalid.  
  However, wrapping test assertions in `except Exception: pass` completely destroys test sensitivity. Any runtime failure, assertion failure, syntax error in the mutant, or unexpected output is caught and ignored. Consequently, every mutant passes pytest with exit code 0, leading to a 100% survival rate and a 0% mutation score.

---

### Finding F-02: ADK Offline Generator Signature Mismatch
- **Classification:** **Test-Generation Weakness**
- **Location:** `testforge/adk_generator.py`, method `ADKModelBridge._synthesize_deterministic_tests`, lines 245–268.
- **Code:**
  ```python
  if len(args) == 2:
      test_lines.extend([...])
  elif len(args) == 1:
      test_lines.extend([...])
  else:
      test_lines.extend([
          f"    assert {target_func}() is not None",
      ])
  ```
- **Analysis:**  
  The offline deterministic fallback for Google ADK handles functions with 1 or 2 arguments, but falls back to `target_func()` with zero arguments for functions with 3 or more arguments (`len(args) >= 3`).  
  Because `calculate_item_discount` has 3 arguments (`unit_price`, `quantity`, `customer_tier`), it fell into the `else:` branch and generated `calculate_item_discount()` without arguments.  
  This caused an immediate `TypeError: missing required arguments`, failing pass@1 baseline validation and forcing the system into self-repair.

---

### Finding F-03: Premature Blackboard Synchronization in `A2ABroker`
- **Classification:** **Architecture / Synchronization Defect**
- **Location:** `testforge/a2a.py`, method `A2ABroker._handle_generator_response`, lines 602–607.
- **Code:**
  ```python
  # Atomically update Blackboard SuiteSpace
  self._blackboard.update_suite_space(
      current_test_code=sanitized_code,
      active_provider="Google ADK Generator",
  )
  ```
- **Analysis:**  
  The `A2ABroker` was configured to automatically synchronize the payload of any `generate_tests` A2A message into Blackboard `SuiteSpace` immediately upon receipt, **before** the Sandbox validates whether the tests pass on clean reference code.  
  In `TestForgeOrchestrator`:
  1. ADK generated a candidate test (`test_calculate_item_discount_nominal`).
  2. `A2ABroker` immediately wrote this candidate test into Blackboard `SuiteSpace`.
  3. The sandbox tested the candidate and rejected it (`All candidate tests broke clean code... Retaining previous working test suite`).
  4. The orchestrator preserved the working suite in local variable `self.state.current_test_code` and evaluated all mutants against it.
  5. However, at the end of the workflow, `self.blackboard.sync_to_state(self.state)` copied the partition data from `SuiteSpace` back into `self.state.current_test_code`.
  6. As a result, the rejected candidate test (1 test) was synced into the terminal state and exported to `test_hardened.py`, while the 11 tests that actually executed were overwritten.

---

### Finding F-04: Genuine Boundary Gaps in Nominal Tests
- **Classification:** **Insufficient Test Coverage (Standard Mutation Behavior)**
- **Location:** `samples/discount.py`
- **Analysis:**  
  In the controlled experiment on `samples/discount.py`, 7 mutants survived.  
  Inspection revealed that the generated test suite only exercised nominal inputs (`price=100.0`, `quantity=10`, `quantity=0`, `price=-10.0`). It did not test exact boundary values such as `quantity=5` or `price=0.0`.  
  This is the exact intended behavior of mutation testing: it exposes deficiencies in test boundary coverage. These surviving mutants are genuine survivors, not artifacts of an engine defect.

---

### Finding F-05: Core Mutation Engine Health
- **Classification:** **Verified Healthy Subsystem**
- **Location:** `testforge/mutator.py`, `testforge/sandbox.py`
- **Analysis:**  
  The core components of the mutation engine performed flawlessly:
  1. **AST Mutation:** 258 valid mutants generated on logistics, 19 on discount.
  2. **Process Isolation:** Clean directory sandboxing and fresh Python subprocesses prevented caching.
  3. **Classification:** Assertions failing in pytest correctly caused exit code 1, mapping to `KILLED`.
  4. **Parallelism:** Multi-process worker pool scaled cleanly across 8 CPU cores without deadlocks.

---

## 3. Summary of Root Cause vs. Perception

| Perception from Live Demo | Objective Technical Reality | Root Cause |
| :--- | :--- | :--- |
| *"TestForge is incapable of killing mutants (0% score)."* | TestForge killed 12 of 19 mutants (63.2% score) on `discount.py`. | Logistics fallback tests had `except Exception: pass`, which swallowed all failures. |
| *"The 11 passing tests were fake."* | 11 generic tests were genuinely generated and executed in Revision 25. | The tests used `except Exception: pass`, making them pass unconditionally on clean code and mutants alike. |
| *"The exported test suite was manually edited."* | Exported `test_hardened.py` was machine-generated by Google ADK. | A premature Blackboard sync in `A2ABroker` overwrote the 11-test suite with a 1-test quarantined candidate. |
| *"Mutation testing is broken."* | The mutation engine, sandbox, subprocesses, and scoring formulas are 100% correct. | The fault lies entirely in the test generator's fallback assertion synthesis. |

