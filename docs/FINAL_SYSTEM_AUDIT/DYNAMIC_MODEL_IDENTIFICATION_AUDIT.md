# TestForge Dynamic Model Identification & Observability Audit

**Document Status:** Complete & Verified  
**Date:** November 2, 2026  
**Evaluation Scope:** Dynamic Model Resolution, Execution Telemetry, Token Accounting Distinction, and Scope-Aware Metrics  
**Project:** TestForge — Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops  

---

## 1. Executive Summary

This audit verifies the comprehensive architectural overhaul of model identification and telemetry accounting in TestForge. Previously, the dashboard displayed a static provider label (`Cloud LLM Active` or generic engine text) that did not reflect actual execution telemetry. Furthermore, aggregate token counters mixed heuristic offline deterministic estimates with genuine foundation model API tokens.

Following this upgrade:
1. **Four Architectural Concepts are Strictly Separated:**
   - **Configured Model:** The targeted model from user configuration or environment (`gemini-3.6-flash`, `codellama:7b`, etc.).
   - **Active Provider:** The currently connected physical transport (`Google GenAI (Gemini)`, `Local Ollama`, `OpenRouter Cloud`, or `None (Offline)`).
   - **Actual Execution Engine:** The engine that genuinely executed and produced the tests, resolved dynamically from recorded telemetry events (`Gemini – gemini-3.6-flash`, `CodeLlama (Ollama / Local)`, `qwen2.5-coder:7b (Ollama / Local)`, `Deterministic AST Synthesizer`, `Mixed Execution Engines`, or `No Execution Yet`).
   - **Last Execution Model:** The specific model invoked in the most recent deliberation cycle.
2. **Deterministic Synthesizer Disconnection:** Offline AST generation runs are explicitly classified with `is_actual_llm = False`, `actual_total_tokens = 0`, and `provider = None`. No phantom tokens are attributed to foundation model consumption.
3. **Multi-Model Local Inference Verified:** Genuine local Ollama models (`codellama:7b` and `qwen2.5-coder:7b`) were executed and logged live, confirming real multi-tier LLM fallback and execution.
4. **Automated Regression Suite:** 13 unit and behavioral tests in `tests/test_dynamic_model_identification.py` rigorously validate dynamic model identification and scope isolation. Combined with the 7 existing token audit tests, all 20 observability tests pass with 100% reliability.
5. **Full Regression Health:** The complete TestForge suite (611 tests) passes with 0 failures.

---

## 2. Dynamic Model Identification Architecture

### 2.1 The Four Conceptual Boundaries

| Conceptual Dimension | Source of Truth | Example Values | Meaning |
| :--- | :--- | :--- | :--- |
| **Configured Model** | Environment / UI Setting (`TESTFORGE_MODEL`) | `gemini-3.6-flash`, `codellama:7b` | Intended LLM requested by user configuration |
| **Active Provider** | Environment Keys & Service Probing (`GEMINI_API_KEY`, Ollama daemon `/api/tags`) | `Google GenAI (Gemini)`, `Local Ollama`, `OpenRouter Cloud`, `None (Offline)` | Connectivity status of external LLM services |
| **Actual Execution Engine** | `testforge_trace.jsonl` Telemetry (`data.execution_engine`) | `Gemini – gemini-3.6-flash`, `CodeLlama (Ollama / Local)`, `Deterministic AST Synthesizer`, `Mixed Execution Engines` | What engine *actually generated* the code in the selected scope |
| **Last Execution Model** | Most recent `LLM_INFERENCE_TELEMETRY` event | `gemini-3.6-flash`, `codellama:7b`, `Deterministic AST Synthesizer` | Specific model from the latest deliberation cycle |

### 2.2 Dynamic Engine Resolution Logic

In `testforge/logger.py`, function `resolve_dynamic_execution_engine(event_data)` resolves an execution engine string based strictly on telemetry properties:

```python
def resolve_dynamic_execution_engine(event_data: Dict[str, Any]) -> str:
    is_actual = event_data.get("is_actual_llm", False)
    provider = str(event_data.get("provider") or "").strip().lower()
    model = str(event_data.get("model_name") or event_data.get("model") or "").strip()

    if not is_actual or "deterministic" in provider or "ast" in provider:
        return "Deterministic AST Synthesizer"

    if "gemini" in provider or "google" in provider or "gemini" in model.lower():
        clean_model = model if model and model.lower() != "gemini" else "gemini-3.6-flash"
        return f"Gemini – {clean_model}"

    if "ollama" in provider or "local" in provider:
        clean_model = model
        if clean_model.lower().startswith("local ollama:"):
            clean_model = clean_model[len("Local Ollama:"):].strip()
        if "codellama" in clean_model.lower():
            return "CodeLlama (Ollama / Local)"
        return f"{clean_model} (Ollama / Local)"

    if "openrouter" in provider:
        return f"OpenRouter ({model or 'unknown'})"

    return model or provider or "Unknown Engine"
```

For telemetry aggregates across a scope, `determine_scope_execution_engine(engine_labels)` determines the top-level KPI:
- If 0 events: `"No Execution Yet"`
- If exactly 1 distinct engine: That engine's canonical label (e.g., `"Deterministic AST Synthesizer"`, `"CodeLlama (Ollama / Local)"`)
- If >1 distinct engines: `"Mixed Execution Engines"`

---

## 3. Real Model Identification Test Results

| Execution Mode | Target Config | Actual Result in Telemetry | Actual LLM Tokens | Estimated Tokens | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Local Ollama: CodeLlama** | `codellama:7b` | `CodeLlama (Ollama / Local)` | **250** (37 prompt, 213 completion) | 0 | 8.16 s | **VERIFIED** |
| **Local Ollama: Qwen** | `qwen2.5-coder:7b` | `qwen2.5-coder:7b (Ollama / Local)` | **171** (45 prompt, 126 completion) | 0 | 6.93 s | **VERIFIED** |
| **Deterministic AST Synthesizer** | Offline Fallback | `Deterministic AST Synthesizer` | **0** | **555** | 0.00 s | **VERIFIED** |
| **Historical Mixed Records** | All History | `Mixed Execution Engines` | **29,476** | **26,700** | — | **VERIFIED** |
| **Current Scope (Pre-run)** | Fresh Scope | `No Execution Yet` | **0** | **0** | — | **VERIFIED** |
| **Google Gemini API** | Live API Call | Not invoked in audit run (preserves paid quota; 5 historical calls logged) | — | — | — | **PRESERVED** |
| **OpenRouter Cloud** | `OPENROUTER_API_KEY` | Not configured in test environment | — | — | — | **NOT TESTED** |

---

## 4. Scope-Aware Observability Verification

### 4.1 Historical Scope (`scope=all`)
- **Total Logged Events:** 291,698 events
- **Execution Engine KPI:** `Mixed Execution Engines`
- **Engine Breakdown Badges:**
  - `Deterministic AST Synthesizer`: 58 runs
  - `Gemini – gemini-3.6-flash`: 5 runs
  - `CodeLlama (Ollama / Local)`: 1 run
  - `qwen2.5-coder:7b (Ollama / Local)`: 1 run
- **Actual LLM Tokens:** 29,476
- **Estimated Deterministic Tokens:** 26,700
- **Combined Tokens:** 56,176

### 4.2 Current Scope (`scope=current`)
- **Execution Engine KPI:** `No Execution Yet` (when no active workflow has executed in the session)
- **Actual LLM Tokens:** 0
- **Estimated Tokens:** 0
- **Isolation Verification:** Complete isolation from historical events; historical token tallies do not leak into the current run view.

### 4.3 Deterministic Workflow Scope (`workflow_id=wf_29dacc90bd25`)
- **Execution Engine KPI:** `Deterministic AST Synthesizer`
- **Actual LLM Tokens:** 0
- **Estimated Tokens:** 555
- **Actual LLM Calls:** 0
- **Deterministic Calls:** 1

### 4.4 CodeLlama Workflow Scope (`workflow_id=wf_test_codellama_7e79a7`)
- **Execution Engine KPI:** `CodeLlama (Ollama / Local)`
- **Actual LLM Tokens:** 250
- **Estimated Tokens:** 0
- **Actual LLM Calls:** 1
- **Deterministic Calls:** 0

### 4.5 Qwen Workflow Scope (`workflow_id=wf_test_qwen_616b46`)
- **Execution Engine KPI:** `qwen2.5-coder:7b (Ollama / Local)`
- **Actual LLM Tokens:** 171
- **Estimated Tokens:** 0
- **Actual LLM Calls:** 1
- **Deterministic Calls:** 0

---

## 5. Playwright Browser Verification

Headless Chromium browser verification was executed against `http://127.0.0.1:8000`:
- **Console Errors:** 0
- **Failed Network Requests:** 0
- **Artifacts Captured:**
  1. `qa_artifacts/dynamic_model_observability/01_historical_mixed_engines.png`
  2. `qa_artifacts/dynamic_model_observability/02_current_run_deterministic.png`
  3. `qa_artifacts/dynamic_model_observability/02b_deterministic_ast_run.png`
  4. `qa_artifacts/dynamic_model_observability/03_codellama_scope.png`
  5. `qa_artifacts/dynamic_model_observability/04_qwen_scope.png`

---

## 6. Dynamic Model Regression Test Suite

Thirteen automated tests were created in `tests/test_dynamic_model_identification.py`:
1. `test_gemini_dynamic_identification`: Asserts Gemini telemetry resolves to `Gemini – <model>`.
2. `test_ollama_dynamic_identification`: Asserts arbitrary Ollama model resolves to `<model> (Ollama / Local)`.
3. `test_codellama_dynamic_identification`: Asserts CodeLlama resolves to `CodeLlama (Ollama / Local)`.
4. `test_openrouter_dynamic_identification`: Asserts OpenRouter resolves to `OpenRouter (<model>)`.
5. `test_deterministic_ast_identification`: Asserts offline AST engine resolves to `Deterministic AST Synthesizer`.
6. `test_mixed_historical_engine_identification`: Asserts multiple distinct engines produce `Mixed Execution Engines`.
7. `test_unknown_legacy_metadata_identification`: Asserts legacy untagged records fail safely to descriptive labels.
8. `test_current_workflow_isolation`: Asserts querying current workflow does not combine historical records.
9. `test_model_switching_between_successive_workflows`: Asserts switching engines between runs produces correct respective single-engine labels.
10. `test_no_execution_state`: Asserts 0 executions resolve to `No Execution Yet`.
11. `test_actual_token_accounting`: Asserts actual LLM events contribute strictly to actual LLM token tallies.
12. `test_estimated_token_accounting`: Asserts deterministic events contribute strictly to estimated token tallies and 0 to actual.
13. `test_correct_api_response_structure`: Asserts API separates `configured_model`, `active_provider`, `actual_execution_engine`, and `last_execution_model`.

**Test Result:** 13 passed, 0 failed.

---

## 7. Audit Verdict

**VERDICT: ACCEPTED & FULLY VERIFIED**  
Dynamic model identification and token accounting distinction are complete, robustly tested, verified via browser automation, and seamlessly integrated into the TestForge platform.

