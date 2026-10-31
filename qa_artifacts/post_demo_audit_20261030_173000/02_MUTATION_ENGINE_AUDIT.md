# 02. Mutation Engine Architecture & Execution Audit

**Audit Identifier:** `TF-AUDIT-MUTATION-ENGINE-20261030-173000`  
**Target Code:** `samples/uploaded_logistics_engine.py` (240 lines, 8,277 bytes)  
**Job ID:** `eaaa0e89`  
**Mutants Evaluated:** 258 first-order AST mutants across 8 parallel workers  

---

## 1. Deep Component-by-Component Inspection

### A. AST Mutant Generation (`testforge/mutator.py`)
- **Inspection:** ASTMutator walks the Python AST and systematically generates first-order mutations. Supported operator families include:
  - Comparison operator swapping (`<`, `<=`, `>`, `>=`, `==`, `!=`).
  - Arithmetic operator substitution (`+`, `-`, `*`, `/`, `%`).
  - Condition inversion (`not (...)`).
  - Off-by-one boundary adjustments (`+ 1`, `- 1`).
  - Constant value substitution (floats, integers, strings).
  - Return value replacement (`None`, `0`, `False`).
- **Audit Result: VALID & ROBUST.** On `uploaded_logistics_engine.py`, 258 distinct, syntactically valid AST mutants were generated across lines 13 through 240. Every mutant produces a valid AST and clean unified diff.

---

### B. Mutant Application & Sandbox Isolation (`testforge/sandbox.py`)
- **Question:** Were mutants actually applied to the executable source code, or did tests run against unmodified code?
- **Inspection:** `ParallelSandboxRunner._run_single_test_task` executes inside a dedicated temporary directory created via `tempfile.TemporaryDirectory(prefix="testforge_box_")`:
  ```python
  src_file = os.path.join(tmpdir, "target.py")
  test_file = os.path.join(tmpdir, "test_target.py")

  with open(src_file, "w", encoding="utf-8") as f:
      f.write(target_code)  # Writes m.mutated_code_snippet

  with open(test_file, "w", encoding="utf-8") as f:
      f.write(test_code)
  ```
- **Audit Result: VERIFIED.** The mutated source code snippet (`m.mutated_code_snippet`) is written directly into `target.py` in the temporary directory. The test file imports `from target import *`, ensuring that the mutated module is the exact code imported and executed.

---

### C. Module Caching & Subprocess Isolation
- **Question:** Did Python's `sys.modules` caching cause the unmutated original module to be reused across iterations or workers?
- **Inspection:** The runner invokes pytest via a brand new operating system subprocess:
  ```python
  pytest_cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--disable-warnings", "-p", "no:cacheprovider"]
  subprocess.run(pytest_cmd, cwd=tmpdir, capture_output=True, text=True, timeout=timeout_seconds)
  ```
- **Audit Result: VERIFIED.** Because a new OS subprocess is spawned for each test run, `sys.modules` is initialized completely from scratch in every test execution. Furthermore, `-p no:cacheprovider` disables pytest's `.pytest_cache` directory. There is zero cross-process module caching.

---

### D. Test Execution & Pytest Output Parsing
- **Question:** How does the sandbox determine test failure vs. test pass?
- **Inspection:** In `testforge/sandbox.py`:
  ```python
  if exit_code == 0 and passed > 0:
      status = "PASS"
  elif exit_code == 1 and failed > 0 and not has_exec_error:
      status = "FAIL"
  elif exit_code == -1:
      status = "TIMEOUT"
  else:
      status = "ERROR"
  ```
- **Audit Result: VERIFIED.** Pytest exits with return code `0` when all tests pass, and return code `1` when at least one test fails an assertion. The parsing regular expressions accurately extract `passed` and `failed` test counts from stdout.

---

### E. Killed vs. Survived Classification Logic
- **Question:** Were mutants misclassified by the scoring engine?
- **Inspection:** In `ParallelSandboxRunner.evaluate_mutants_parallel`:
  ```python
  elif result.get("timed_out"):
      mutant.status = "TIMEOUT"
  elif result.get("has_exec_error") or result.get("status") == "ERROR":
      mutant.status = "ERROR"
  elif result.get("status") == "FAIL" and result.get("tests_failed", 0) > 0:
      mutant.status = "KILLED"
  elif result.get("status") == "PASS":
      mutant.status = "SURVIVED"
  ```
  And in `calculate_mutation_scores`:
  $$\text{Raw Mutation Score} = \frac{\text{Killed} + \text{Timeouts}}{\text{Total Valid Mutants}} \times 100\%$$
- **Audit Result: VERIFIED.** The classification logic is strictly sound. A mutant is classified as `KILLED` if and only if the test suite failed an assertion (`status == "FAIL"`). If all tests passed (`status == "PASS"`), the mutant is classified as `SURVIVED`.

---

## 2. Why Did All 258 Mutants Survive in the Live Demo?

### The Forensic Evidence
In raw checkpoint `chk_3921cdba2556` (Job `eaaa0e89`, Iteration 1), examining mutant `MUT_CONST_VAL_001` (Line 13: `STANDARD = "STANDARD"` mutated to `STANDARD = "MUTATED"`):
- Pytest was invoked on `test_target.py` containing the 11 tests from Revision 25.
- The raw stdout recorded in the database is:
  ```
  collecting ... collected 11 items
  test_target.py::test_generic_calculate_item_discount PASSED [  9%]
  test_target.py::test_generic_estimate_freight_cost PASSED [ 18%]
  test_target.py::test_generic_calculate_customs_duty PASSED [ 27%]
  test_target.py::test_generic_validate_tracking_number PASSED [ 36%]
  test_target.py::test_generic_compute_sla_deadline_hours PASSED [ 45%]
  test_target.py::test_generic_process_bulk_order PASSED [ 54%]
  test_target.py::test_generic___init__ PASSED [ 63%]
  test_target.py::test_generic_get_available_stock PASSED [ 72%]
  test_target.py::test_generic_reserve_stock PASSED [ 81%]
  test_target.py::test_generic_release_stock PASSED [ 90%]
  test_target.py::test_generic_restock_needed PASSED [100%]
  ============================== 11 passed in 0.03s ==============================
  ```
- Pytest exited with return code `0`.
- All 11 tests passed.
- Therefore, the mutant was classified as `SURVIVED`.

### The Fundamental Flaw: Universal Exception Swallowing
Every single one of the 11 tests executed had this exact structure:
```python
def test_generic_calculate_item_discount():
    try:
        res = calculate_item_discount(1, 1, 1)
        assert res is not None
    except Exception:
        pass
```
Because of `except Exception: pass`:
1. If the mutant causes an `AssertionError`, it is caught by `except Exception: pass`.
2. If the mutant causes a `ZeroDivisionError`, it is caught by `except Exception: pass`.
3. If the mutant causes a `ValueError` (such as invalid tier or negative price), it is caught by `except Exception: pass`.
4. If the mutant causes a `TypeError` (e.g. wrong argument types), it is caught by `except Exception: pass`.
5. If the unmutated code raises an exception because dummy argument `1` is invalid, it is caught by `except Exception: pass`.

**Under this structure, it is mathematically impossible for pytest to fail on any mutant.**  
The tests did not test any behavior; they merely called the function and silently discarded any error. Thus, all 258 mutants produced return code `0` and were classified as `SURVIVED`.

---

## 3. Checklist of Audit Questions

| Audit Question | Investigation Finding | Conclusion |
| :--- | :--- | :---: |
| Mutants applied to executable source? | Yes, written to `target.py` in sandbox temp directory. | **NO DEFECT** |
| Correct mutated file imported? | Yes, `from target import *` imports local sandbox module. | **NO DEFECT** |
| Module caching caused original module to run? | No, separate OS subprocess created with fresh interpreter. | **NO DEFECT** |
| Test execution used intended target path? | Yes, `cwd=tmpdir` ensures correct module resolution. | **NO DEFECT** |
| Generated tests exercised mutated code? | Partially executed, but assertions/exceptions were suppressed. | **ROOT DEFECT** |
| Mutant results incorrectly classified? | No, `result["status"] == "PASS"` correctly maps to `SURVIVED`. | **NO DEFECT** |
| Exceptions/timeouts treated as survivors? | Timeouts are killed; errors are flagged as `ERROR`. | **NO DEFECT** |
| Equivalent mutants in denominator incorrectly? | No, equivalent mutants are excluded when detected. | **NO DEFECT** |
| Result table matches raw execution records? | Exactly matches 258 records in SQLite database. | **NO DEFECT** |

