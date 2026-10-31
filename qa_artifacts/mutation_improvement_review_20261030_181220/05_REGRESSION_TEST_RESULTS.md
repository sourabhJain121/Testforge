# 05 — Full Regression Test Suite Results

**Audit Timestamp:** `2026-10-30T18:12:20+05:30`  
**Execution Environment:** `/Users/sourabh/TestForge/.venv-release/bin/python` (Python 3.13.18)  
**Test Framework:** `pytest-9.1.1` | `pluggy-1.7.0` | `cov-7.1.0`

---

## 1. Full Test Suite Execution Summary

- **Exact Command:**
  ```bash
  .venv-release/bin/python -m pytest tests/ -q
  ```
- **Exit Code:** `1`
- **Total Tests Collected:** `533`
- **Passed Tests:** `532` (99.81%)
- **Failed Tests:** `1` (0.19%)
- **Skipped Tests:** `0`
- **Warnings:** `345` (primarily CrewAI upstream deprecation warnings regarding `function_calling_llm` and Google Cloud Storage compatibility notices)
- **Total Duration:** `173.85s` (2 minutes 53 seconds)

---

## 2. Failing Test Identification & Stack Trace

The single failure in the entire test suite occurred in:
`tests/test_mode_c_ingestion.py::test_hardening_pipeline_on_models`

### Pytest Failure Details:
```text
______________________ test_hardening_pipeline_on_models _______________________

tmp_path = PosixPath('/private/var/folders/7x/5s5hr55523q990nl8mnvy9040000gn/T/pytest-of-sourabh/pytest-27/test_hardening_pipeline_on_mod0')

    def test_hardening_pipeline_on_models(tmp_path):
        """
        Executes the hardening pipeline against models.py and verifies all explicit execution metrics.
        """
        tm = TargetManagerAgent()
        saved_path, analysis = tm.ingest_github(MODELS_URL, output_dir=str(tmp_path))
    
        trace_file = str(tmp_path / "models_trace.jsonl")
        orch = TestForgeOrchestrator(
            target_source_code=analysis.source_code,
            max_iterations=1,
            target_mutation_score=85.0,
            trace_log_path=trace_file,
            target_file_path=str(saved_path),
            engine_mode="local"
        )
    
        state = orch.run()
        assert state is not None
    
        # Verify that the target source under test is genuinely models.py
        assert "class Request" in state.target_source_code
        assert "class PreparedRequest" in state.target_source_code
        assert "class Response" in state.target_source_code
    
        # Verify mutants generated on models.py
>       assert state.mutants_generated > 50, f"Expected >50 mutants on models.py, got {state.mutants_generated}"
E       AssertionError: Expected >50 mutants on models.py, got 0
E       assert 0 > 50
```

### Underlying Cause in Sandbox Execution:
```text
==================================== ERRORS ====================================
_______________________ ERROR collecting test_target.py ________________________
ImportError while importing test module '/private/var/.../test_target.py'.
Traceback:
/opt/homebrew/Cellar/python@3.13/3.13.18/Frameworks/Python.framework/Versions/3.13/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name, package, level)
/private/var/.../test_target.py:2: in <module>
    from target import _encode_params
E   ImportError: cannot import name '_encode_params' from 'target' (/private/var/.../target.py)
=========================== short test summary info ============================
ERROR .../test_target.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

---

## 3. Root Cause Analysis

1. **Target Structure:**
   - The target under test is `requests/models.py`, which is an object-oriented module consisting of classes (`Request`, `PreparedRequest`, `Response`, etc.) without standalone top-level functions.
2. **AST Parsing Flaw in `extract_function_signatures`:**
   - In `testforge/agents.py`, `ast.walk(tree)` visits every AST node regardless of nesting depth.
   - For classes with static methods (such as `@staticmethod def _encode_params(data)` inside `PreparedRequest`), the method parameter list does not include `self` or `cls`.
   - The method detector (`is_method = any(a.arg in ("self", "cls") for a in node.args.args)`) evaluated `is_method` to `False` because there was no `self` parameter.
3. **ADK Generator Ingestion Flaw:**
   - In `testforge/adk_generator.py`, `standalone_sigs = [s for s in signatures if not s.get("is_method")]` erroneously classified `_encode_params` as a standalone function.
   - It selected `target_func = "_encode_params"` and generated:
     ```python
     from target import _encode_params
     ```
   - Because `_encode_params` is a class method inside `PreparedRequest` and not exposed at module scope in `target.py`, pytest collection failed with `ImportError`.
4. **Why It Passed Previously (Historical Context):**
   - In the prior implementation before Defect 1 was remediated, the generic test synthesis fallback wrapped tests in `try: ... except Exception: pass`.
   - When the import or call failed with `NameError` or `ImportError`, the exception was silently swallowed. The tests passed, allowing the pipeline to proceed and generate mutants.
   - Remediating Defect 1 (eliminating exception swallowing) correctly unmasked this underlying defect.

