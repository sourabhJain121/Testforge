# TestForge — Phase 2B Residual Risk Assessment

**Document ID**: TF-SEC-2B-006  
**Phase**: Phase 2B (Indirect Prompt-Injection Defense)  
**Date**: October 30, 2026  
**Auditor**: TestForge Security Assessment Group  

---

## 1. Executive Summary

Phase 2B implemented comprehensive indirect prompt-injection defenses:
- Untrusted content envelopes with delimiter breakout neutralization (`wrap_untrusted_content`).
- Authoritative defensive system instructions (`DEFENSIVE_SYSTEM_PREAMBLE`).
- AST-level comment and docstring inspection and defusing (`inspect_source_for_indirect_injections`).
- State-partition trust boundaries and directive sanitization (`sanitize_critic_directive`).
- Tool execution argument and whitelist validation (`verify_tool_call_safety`).
- Code AST security analysis blocking `os.environ` attribute access.

This document assesses the residual risks following these remediations and identifies operational recommendations for subsequent development phases (Phase 2C: Safe Subprocess Execution).

---

## 2. Residual Risk Analysis Matrix

| Threat Category | Pre-Mitigation Risk | Post-Mitigation Risk | Implemented Safeguards | Residual Risk / Monitoring Plan |
| :--- | :--- | :--- | :--- | :--- |
| **Comment/Docstring Prompt Injection** | **CRITICAL** | **LOW** | AST tokenization and regex defusing. Replaces payloads with inert tokens. | Extremely obfuscated homoglyph or unicode zero-width attacks. *Phase 2C/3 can add unicode normalization.* |
| **Instruction Precedence Override** | **HIGH** | **LOW** | Immutable `DEFENSIVE_SYSTEM_PREAMBLE` gives developer instructions strict precedence. | Future LLMs with weak instruction following. Mitigated by using frontier models (Gemini 2.5 Flash / Claude 3.5 Sonnet). |
| **Delimiter Breakout Attacks** | **HIGH** | **VERY LOW** | Sanitization and HTML-entity escaping of `</untrusted_content>`, `<system>`, `===`. | Regex patterns cover all known variations. Automated tests verify escaping. |
| **Blackboard State Poisoning** | **HIGH** | **LOW** | Sanitization at partition boundary (`update_partition("critic")`). Ingestion tagged untrusted. | Cross-partition sync remains strictly validated via Pydantic models. |
| **Tool Execution Hijacking** | **CRITICAL** | **VERY LOW** | Strict tool whitelist in `ADKToolRegistry`, path traversal rejection, shell pipe checks. | Verified in `test_scenario_7`. Any new tool registration must adhere to Pydantic schemas. |
| **Subprocess Execution of Unsafe Code** | **CRITICAL** | **MEDIUM-LOW** | `SecurityGuardrail.inspect_code_ast` blocks dangerous imports, calls, and `os.environ`. | Addressed fully in **Phase 2C (Safe Subprocess Execution & Resource Limits)**. |

---

## 3. Boundary Assumptions and Prerequisites

1. **Non-Execution of Untrusted Files**: Untrusted repository source code is only parsed via `ast.parse` and `tokenize.tokenize` during analysis, and never directly `exec()`ed or imported in the main process.
2. **Subprocess Isolation**: Candidate tests run in `SubprocessSandbox`, which is governed by timeouts and AST pre-execution filters.
3. **Pydantic Validation**: All partitions in Blackboard require Pydantic model validation. Unsanitized raw dictionaries cannot bypass validation.

---

## 4. Recommendations for Phase 2C (Safe Subprocess Execution)

1. Enforce operating-system level resource limits (`rlimit_cpu`, `rlimit_as`, `rlimit_fsize`) on subprocess execution.
2. Maintain ephemeral temporary directories for sandbox test runs, destroying them immediately after execution.
3. Ensure no network sockets can be opened from within child test execution processes.

