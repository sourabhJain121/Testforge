# TestForge — Phase 2B Prompt Data Flow Security Audit

**Document ID**: TF-SEC-2B-002  
**Phase**: Phase 2B (Indirect Prompt-Injection Defense)  
**Date**: October 30, 2026  
**Auditor**: TestForge Security & QA Engineering  

---

## 1. Audit Scope & Objectives

The objective of this audit was to trace every path where external or untrusted data enters the agent context, prompt assembly pipelines, or tool dispatch mechanisms within TestForge. 

Untrusted data includes:
- Python source code from user workspaces or remote repositories.
- Code comments (`# ...`) and docstrings (`"""..."""`).
- Repository documentation (`README.md`, specs, markdown files).
- Configuration files (`pyproject.toml`, `.env`, yaml files).
- AST mutant unified diffs.
- Subprocess sandbox stdout/stderr and error messages.
- Inter-agent messages and directives stored in the shared Blackboard.
- Tool invocation parameters and tool results.

---

## 2. Ingestion & Extraction Flows

### Flow 1: External Source Code Ingestion (`testforge/ingestion.py` & `testforge/github_service.py`)
- **Data Origin**: Remote GitHub API / raw download or local directory upload.
- **Handling**: Fetched via bounded HTTP reader (`fetch_bounded_content`) with SSRF validation (`SafeGitHubRedirectHandler`).
- **Storage**: Ingested content is loaded into `Blackboard.update_partition("target", ...)`.
- **Pre-2B Vulnerability**: Target source code was treated as trusted text without untrusted provenance metadata or injection scanning.
- **Remediation**:
  - `TargetSpace.is_untrusted` defaults to `True`.
  - Ingestion updates trigger `inspect_source_for_indirect_injections()`.
  - Identified injection patterns are logged, stored in `TargetSpace.injection_findings`, and dispatched via `LifecycleEvent(EventType.ERROR)`.

### Flow 2: File Documentation & Markdown (`README.md`, docs)
- **Data Origin**: Repository README, markdown documentation, or issue tickets.
- **Handling**: Read and supplied as agent context during repository analysis.
- **Pre-2B Vulnerability**: Direct insertion into system prompt or user query without framing.
- **Remediation**:
  - Wrapped using `wrap_untrusted_content(content, content_type="readme", provenance="repository_docs")`.
  - Escapes delimiter tags (`</untrusted_content>`) to prevent envelope breakout.

---

## 3. Agent Prompt Assembly Flows

### Flow 3: Autonomous Test Generator (`testforge/agents.py` - `TestGeneratorAgent`)
- **Prompts Generated**:
  - Initial suite generation (`generate_tests`).
  - Self-repair and mutation-guided hardening.
- **Inputs Interpolated**:
  - `source_code`: Target Python function under test.
  - `surviving_diffs`: AST mutation diffs.
  - `critic_feedback` / `critic_directive`: Feedback from Critic.
- **Pre-2B Vulnerability**: Placed directly into template strings without data framing; comments could issue instructions like `"ignore previous instructions"`.
- **Remediation**:
  - `wrap_untrusted_content()` wraps `source_code`, `surviving_diffs`, and `critic_feedback`.
  - `inspect_source_for_indirect_injections()` defuses malicious comments and docstrings.
  - Prompt preamble prepends `DEFENSIVE_SYSTEM_PREAMBLE`.

### Flow 4: Google ADK Autonomous Generator (`testforge/adk_generator.py` - `GoogleADKTestGenerator`)
- **Prompts Generated**: `ADKModelBridge.generate_content_async`, `Runner.run_async`.
- **Inputs Interpolated**: `target_source_code`, `existing_test_code`, `surviving_diffs`, `critic_directive`.
- **Pre-2B Vulnerability**: Raw formatting in markdown blocks without instruction precedence enforcement.
- **Remediation**:
  - `LlmAgent` instruction wrapped with `get_defensive_system_instruction()`.
  - Target source code defused and wrapped in untrusted data delimiters.
  - Critic directives sanitized prior to prompt assembly.

### Flow 5: CrewAI Adversarial Critic Agent (`testforge/crew_critic.py` - `CrewAICriticAgent`)
- **Prompts Generated**: CrewAI `Task` description and `Agent` goal/backstory.
- **Inputs Interpolated**: `target_source_code`, `surviving_diffs`.
- **Pre-2B Vulnerability**: Malicious source code comments could trick Critic into returning directives that tell Generator to erase tests or leak environment variables.
- **Remediation**:
  - `target_source_code` and `surviving_diffs` wrapped with `wrap_untrusted_content()`.
  - `CrewAI` agent instructed to treat code as passive data.
  - Output directives sanitized with `sanitize_critic_directive()` before returning or storing.

---

## 4. Shared State & Tool Execution Flows

### Flow 6: Blackboard Partition Communication (`testforge/blackboard.py`)
- **Shared Partitions**: `target`, `mutant`, `critic`, `suite`, `metrics`.
- **Pre-2B Vulnerability**: A corrupted directive from Critic would be stored in `CriticSpace` and read by `TestGeneratorAgent` or `GoogleADKTestGenerator`, causing cross-agent infection.
- **Remediation**:
  - `Blackboard.update_partition("critic", ...)` automatically runs `sanitize_critic_directive()`.
  - Neutralizes high-risk directives and replaces with safe fallbacks (`[DEFUSED_DIRECTIVE: ...]`).
  - Added `get_isolated_target_code()` method for secure retrieval of target code.

### Flow 7: ADK Tool Registry & Subprocess Execution (`testforge/adk_engine.py`)
- **Tools**: `tool_compute_blast_radius`, `tool_inspect_git_diff`, `tool_execute_sandbox`, `tool_ast_audit`.
- **Pre-2B Vulnerability**: Prompt-injected LLM could pass shell commands (e.g. `| bash`) or path traversal arguments (`../../..`).
- **Remediation**:
  - `ADKToolRegistry.execute_tool()` invokes `verify_tool_call_safety()`.
  - Rejects unknown tool names, path traversal (`..`), and shell piping syntax (`| bash`, `| sh`, `rm -rf`).

### Flow 8: Orchestrator Self-Repair Loop (`testforge/orchestrator.py`)
- **Prompt Generated**: `repair_prompt` on baseline validation failure.
- **Inputs Interpolated**: Sandbox `stdout`/`stderr` error output.
- **Pre-2B Vulnerability**: If code exception contained malicious injection strings, it was directly placed into prompt.
- **Remediation**: Wrapped with `wrap_untrusted_content(err_msg, content_type="test_error", provenance="sandbox")`.

---

## 5. Summary Matrix of Data Flows & Applied Controls

| Flow ID | Source | Sink | Risk Level | Defense Mechanism Applied |
| :--- | :--- | :--- | :--- | :--- |
| **DF-01** | Ingestion Source Code | `TargetSpace` | CRITICAL | `inspect_source_for_indirect_injections`, AST defusing |
| **DF-02** | Target Source Code | `TestGeneratorAgent` | CRITICAL | `wrap_untrusted_content`, system preamble |
| **DF-03** | Target Source Code | `GoogleADKTestGenerator` | CRITICAL | `wrap_untrusted_content`, ADK system instruction |
| **DF-04** | Target Source Code & Diffs | `CrewAICriticAgent` | HIGH | `wrap_untrusted_content`, directive sanitization |
| **DF-05** | Critic Directive | `Blackboard[CriticSpace]` | HIGH | `sanitize_critic_directive` at partition boundary |
| **DF-06** | Sandbox Stderr / Stdout | `Orchestrator.repair_prompt`| MEDIUM | `wrap_untrusted_content` as passive test error |
| **DF-07** | LLM Tool Call Arguments | `ADKToolRegistry` | CRITICAL | `verify_tool_call_safety` (whitelist, path, shell) |
| **DF-08** | Generated Test Code | Subprocess Sandbox | HIGH | `CodeSanitizer`, `ASTSecurityAnalyzer` |

