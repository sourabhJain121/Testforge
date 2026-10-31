# 01 — Root Cause Analysis: AST Scope & Class Method Extraction Regression

**Audit & Fix Timestamp:** `2026-10-30T18:45:36+05:30`  
**Repository:** `/Users/sourabh/TestForge`  
**Target Failure:** `tests/test_mode_c_ingestion.py::test_hardening_pipeline_on_models`  
**Prior Exit State:** 532 Passed, 1 Failed (Exit Code 1)

---

## 1. Executive Summary

During the previous defect remediation cycle, universal exception swallowing (`try: ... except Exception: pass`) was eliminated from the generic AST fallback generator in `testforge/agents.py`. 

While this change successfully unmasked broken tests and boosted genuine mutation detection, it exposed an underlying lexical scoping deficiency in AST signature extraction:
1. `requests/models.py` contains class definitions (`Request`, `PreparedRequest`, `Response`, `RequestEncodingMixin`) without standalone module-level functions.
2. Inside `RequestEncodingMixin` and `PreparedRequest`, the method `_encode_params(data)` is decorated with `@staticmethod`.
3. Because static methods do not define `self` or `cls` parameters, the naive signature extractor classified `_encode_params` as a standalone function (`is_method = False`).
4. The test generator synthesized `from target import _encode_params`.
5. Pytest failed during test collection with:
   ```text
   ImportError: cannot import name '_encode_params' from 'target' (/path/to/target.py)
   ```
6. Because baseline validation failed during collection, the pipeline aborted before generating mutants on `models.py`, causing `assert state.mutants_generated > 50` to fail with `0 > 50`.

---

## 2. Structural Breakdown of `requests/models.py`

Inspection of `samples/github_requests_models.py` via AST revealed:
- **Top-Level Module Functions:** `[]` (None).
- **Top-Level Classes:** `RequestEncodingMixin`, `RequestHooksMixin`, `Request`, `PreparedRequest`, `Response`.
- **Target Method:**
  ```python
  class RequestEncodingMixin:
      @property
      def path_url(self): ...

      @staticmethod
      def _encode_params(data):
          if isinstance(data, (str, bytes)):
              return data
          elif _t.has_read(data):
              return data
          ...
  ```

---

## 3. Why `ast.walk` Caused the Scoping Breakdown

In the earlier implementation:
```python
def extract_function_signatures(source_code: str) -> List[Dict[str, Any]]:
    tree = ast.parse(source_code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_method = any(a.arg in ("self", "cls") for a in node.args.args)
            ...
```

### Critical Flaws in Naive `ast.walk`:
1. **Loss of Lexical Hierarchy:** `ast.walk` yields all nodes in arbitrary order without parent pointers. It cannot distinguish between a function declared at module scope, a method declared inside a class body, or an inner helper declared inside a closure.
2. **Method Misclassification:** Static methods (`@staticmethod`) intentionally omit `self` and `cls`. Consequently, `any(a.arg in ("self", "cls") for a in node.args.args)` evaluated to `False`.
3. **Invalid Import Generation:** Because `is_method` was `False`, both `ADKModelBridge` and `TestGeneratorAgent` treated `_encode_params` as a public module function and emitted:
   ```python
   from target import _encode_params  # CRITICAL FAILURE
   ```
   In Python, class attributes and methods are not placed into module-level `globals()`. Attempting to import an unexported class attribute raises `ImportError`.

---

## 4. Why the Test Passed Previously (Masked Defect)

Prior to the remediation of Defect 1:
```python
# Historical vulnerable implementation in agents.py:
def test_generic__encode_params():
    try:
        res = _encode_params("1")
        assert res is not None
    except Exception:
        pass  # SILENTLY SWALLOWED NameError / ImportError
```
When `from target import *` failed to import `_encode_params`, calling `_encode_params` raised `NameError: name '_encode_params' is not defined`. The `try...except Exception: pass` block swallowed the runtime error, allowing pytest to report a passing test (with 0 assertions verified). 

Removing exception swallowing correctly exposed this latent defect, enabling us to implement proper lexical AST scope awareness.

