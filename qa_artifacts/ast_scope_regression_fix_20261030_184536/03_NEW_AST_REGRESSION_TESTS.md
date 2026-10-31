# 03 — Targeted AST Scope Regression Test Suite

**Audit & Fix Timestamp:** `2026-10-30T18:45:36+05:30`  
**Test Module:** `tests/test_ast_scope_extraction.py`  
**Execution Environment:** `/Users/sourabh/TestForge/.venv-release/bin/python`

---

## 1. Test Suite Architecture

The newly created test module `tests/test_ast_scope_extraction.py` provides comprehensive verification across 9 targeted areas:

| Test Identifier | Verified Capability | Key Assertion |
| :--- | :--- | :--- |
| `test_top_level_function_extraction` | Top-level module function parsing | `scope == "module"`, `is_method is False`, `from target import {fn}` |
| `test_instance_method_extraction` | Instance method extraction & self stripping | `method_type == "instance"`, `pos_args` excludes `self`, no invalid direct import |
| `test_static_method_extraction` | `@staticmethod` decorator & class binding | `method_type == "staticmethod"`, access via `{Class}.{method}` |
| `test_class_method_extraction` | `@classmethod` decorator & cls stripping | `method_type == "classmethod"`, `pos_args` excludes `cls` |
| `test_nested_function_handling` | Closures & inner functions | `scope == "nested"`, `qualified_name == "outer.<locals>.inner"`, omitted from import |
| `test_decorated_methods_and_properties` | Properties (`@property`) & decorators | Decorator list preserved, `build_nominal_arguments` returns `None` for getters |
| `test_multi_argument_function_signatures` | Functions with $\ge 3$ required arguments | `required_pos` accurate, nominal string generated |
| `test_keyword_only_argument_handling` | `*, key: str` keyword-only arguments | `required_kwonly` accurate, nominal string includes `key="..."` |
| `test_prepared_request_encode_params_regression` | Specific `PreparedRequest._encode_params` regression | Static method imported via class, sandbox execution succeeds with 0 errors |

---

## 2. Execution Log & Verification

### Pytest Command:
```bash
.venv-release/bin/python -m pytest tests/test_ast_scope_extraction.py -v
```

### Output:
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.18, pytest-9.1.1, pluggy-1.7.0 -- /Users/sourabh/TestForge/.venv-release/bin/python
cachedir: .pytest_cache
rootdir: /Users/sourabh/TestForge
plugins: cov-7.1.0, anyio-4.15.1, platformdirs-4.13.5
collected 9 items

tests/test_ast_scope_extraction.py::test_top_level_function_extraction PASSED [ 11%]
tests/test_ast_scope_extraction.py::test_instance_method_extraction PASSED [ 22%]
tests/test_ast_scope_extraction.py::test_static_method_extraction PASSED [ 33%]
tests/test_ast_scope_extraction.py::test_class_method_extraction PASSED  [ 44%]
tests/test_ast_scope_extraction.py::test_nested_function_handling PASSED [ 55%]
tests/test_ast_scope_extraction.py::test_decorated_methods_and_properties PASSED [ 66%]
tests/test_ast_scope_extraction.py::test_multi_argument_function_signatures PASSED [ 77%]
tests/test_ast_scope_extraction.py::test_keyword_only_argument_handling PASSED [ 88%]
tests/test_ast_scope_extraction.py::test_prepared_request_encode_params_regression PASSED [100%]

======================== 9 passed, 2 warnings in 2.33s =========================
```

**Status:** **9/9 PASSED (100%)**. Exit Code: `0`.

