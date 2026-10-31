# TestForge — Phase 2B Implementation Summary: Indirect Prompt-Injection Defense

**Document ID**: TF-SEC-2B-004  
**Phase**: Phase 2B (Indirect Prompt-Injection Defense)  
**Date**: October 30, 2026  
**Implementation Lead**: TestForge Architecture & Security Engineering  

---

## 1. Scope and Implementation Goals

Phase 2B focused on establishing rigorous indirect prompt-injection defenses across TestForge's multi-agent architecture. The implementation addresses how untrusted data (source code, comments, docstrings, documentation, error traces, and inter-agent directives) is ingested, parsed, sanitized, framed, and evaluated by LLMs and downstream tools.

---

## 2. Key Modules Implemented & Modified

### 1. `testforge/prompt_guard.py` (NEW MODULE)
A specialized security module providing indirect prompt-injection mitigation primitives:
- `wrap_untrusted_content(content, content_type, provenance, context_id)`:
  - Encloses untrusted data in `<untrusted_content type='...' provenance='...'>` envelopes.
  - Automatically prepends `# [NOTICE: ...]` comment headers for source code to maintain Python AST parseability while warning LLMs.
  - Escapes delimiter tags (`</untrusted_content>`, `<system>`, `=== system override ===`) to defeat breakout attacks.
- `inspect_source_for_indirect_injections(source_code, guardrail)`:
  - Uses Python's `tokenize` and `ast` parsers to inspect comments, docstrings, and string constants.
  - Scans for 11 distinct prompt-injection patterns.
  - Defuses detected injection payloads in place with `[DEFUSED_PROMPT_INJECTION: <RULE_ID>]` so valid code remains syntactically correct and testable.
- `sanitize_critic_directive(directive, guardrail)`:
  - Validates adversarial directives before writing to the Blackboard or dispatching across A2A channels.
  - Neutralizes high-risk directives and replaces with safe boundary-testing guidance.
- `get_defensive_system_instruction(base_instruction)`:
  - Injects `DEFENSIVE_SYSTEM_PREAMBLE`, establishing immutable instruction precedence.
- `verify_tool_call_safety(tool_name, arguments, allowed_tools)`:
  - Enforces tool whitelists.
  - Blocks dangerous shell execution patterns (`| bash`, `| sh`, `rm -rf /`).
  - Blocks directory traversal sequences (`..`).

### 2. `testforge/security.py` (ENHANCED PATTERNS & AST CHECKS)
- Extended `_PROMPT_INJECTION_PATTERNS` with 4 new comprehensive rules:
  - `INJ_SHELL_EXECUTION`: Matches instructions to execute shell scripts, `curl ... | bash`, `rm -rf /`.
  - `INJ_ENV_LEAK`: Matches instructions to reveal `os.environ`, API keys, or system secrets.
  - `INJ_MARKDOWN_DIRECTIVE`: Detects hidden markdown directives (`<!-- system instruction ... -->`).
  - `INJ_TOOL_HIJACK`: Detects instructions prompting tool misuse.
- Enhanced `INJ_SYSTEM_OVERRIDE` to detect variations like `"ignore all previous safety constraints"`.
- Enhanced `ASTSecurityAnalyzer.visit_Attribute` to block test code attempting to read `os.environ`.

### 3. `testforge/blackboard.py` (TRUST BOUNDARIES & STATE SANITIZATION)
- Added `is_untrusted: bool = True`, `provenance: str = "ingestion"`, and `injection_findings: List[Dict[str, Any]]` to `TargetSpace`.
- Integrated `inspect_source_for_indirect_injections` into `Blackboard.update_partition("target", ...)`. If an injection is found, it logs findings and fires a `LifecycleEvent(EventType.ERROR)`.
- Integrated `sanitize_critic_directive` into `Blackboard.update_partition("critic", ...)`. Defuses any malicious directives before writing to storage.
- Added `get_isolated_target_code(provenance)` to safely wrap and defuse target code when requested by downstream consumers.

### 4. `testforge/agents.py` (`TestGeneratorAgent` & `AdversarialCriticAgent`)
- Updated `TestGeneratorAgent.generate_tests()` to wrap `source_code`, `surviving_diffs`, and `critic_feedback` with `wrap_untrusted_content()`.
- Added `get_defensive_system_instruction()` to system prompts.
- Updated `AdversarialCriticAgent.analyze_surviving_mutants()` to wrap target code and surviving diffs in untrusted content envelopes.

### 5. `testforge/adk_generator.py` (`GoogleADKTestGenerator`)
- Integrated `get_defensive_system_instruction()` into `LlmAgent` instruction and `ADKModelBridge.generate_content_async`.
- In `generate_tests()`: defuses injections in target code, wraps existing test code, diffs, and critic directives in `<untrusted_content>` envelopes.
- Updated deterministic test synthesis (`_synthesize_deterministic_tests`) to cleanly parse code wrapped in untrusted content tags.

### 6. `testforge/crew_critic.py` (`CrewAICriticAgent`)
- Wrapped `CrewAILLMBridge` system instructions with `get_defensive_system_instruction()`.
- In `diagnose_mutants()`: wraps target source code and mutant diffs with `wrap_untrusted_content()`.
- Sanitizes all outgoing `CriticDirectivePayload.directives` and `analysis` via `sanitize_critic_directive()` to prevent downstream poisoning.

### 7. `testforge/adk_engine.py` (`ADKToolRegistry`)
- Integrated `verify_tool_call_safety()` in `execute_tool()`.
- Validates tool names against registered tool definitions and blocks arguments containing directory traversal or shell execution syntax.

### 8. `testforge/orchestrator.py`
- Wrapped `err_msg` from baseline test execution with `wrap_untrusted_content()` when creating `repair_prompt`, preventing malicious exception strings from hijacking the repair loop.

---

## 3. Test Suite: `tests/test_prompt_injection_defense.py`

Implemented a comprehensive 10-scenario adversarial test suite covering all required threat models:
1. Malicious Python comment instructing agent to ignore previous instructions.
2. Malicious docstring requesting environment-variable disclosure.
3. README containing instructions to execute an arbitrary shell command.
4. Retrieved documentation attempting to override system instructions.
5. Prompt injection passed through Blackboard to another agent.
6. Malicious tool output attempting to redirect the agent.
7. Injection attempting to trigger unauthorized tool execution.
8. Injection hidden inside otherwise valid source code.
9. Benign repository instructions that remain usable without false positives.
10. Regression test proving normal repository analysis and test generation still work.

**Result**: 10/10 passed in 9.91s.

