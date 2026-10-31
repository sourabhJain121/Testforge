# TestForge — Phase 2B Indirect Prompt-Injection Threat Model

**Document ID**: TF-SEC-2B-001  
**Phase**: Phase 2B (Indirect Prompt-Injection Defense)  
**Classification**: Internal Engineering Security Specification  
**Status**: ACTIVE / AUDITED  
**Date**: October 30, 2026  

---

## 1. Executive Summary

TestForge integrates multi-agent AI deliberation (Google ADK, CrewAI, Gemini / Claude / OpenAI via `HybridLLMClient`, and local deterministic models) to inspect Python source code, generate unit test suites, run mutation testing, and validate code resilience.

In an automated testing and code hardening platform, untrusted content from ingested source repositories, pull requests, issue trackers, or documentation flows directly into prompts supplied to LLM agents. Without defense-in-depth boundaries, attackers can embed malicious instructions inside source code comments, docstrings, README files, or AST mutant diffs to hijack agent personas, exfiltrate API keys, execute arbitrary shell commands, or disable security guardrails.

This threat model identifies all attack surfaces, threat actors, attack vectors, trust boundaries, and remediation controls implemented during Phase 2B.

---

## 2. Threat Actors and Capabilities

| Threat Actor | Motivation | Access Level | Attack Vectors |
| :--- | :--- | :--- | :--- |
| **Malicious Repository Author** | Compromise the testing pipeline; steal API keys; execute code on server. | Full control over repository files (Python source, comments, docstrings, `README.md`, config files). | Indirect prompt injection hidden in docstrings, comments, test names, and doc files. |
| **Malicious Dependency / Upstream Contributor** | Supply-chain attack via transitive repository dependency. | Commit access to an ingested repo or library. | Injected instructions into third-party library files ingested by TestForge. |
| **Compromised Tool / Subprocess** | Corrupt agent decisions via manipulated error messages or tool outputs. | Subprocess sandbox stdout/stderr or MCP tool response. | Delimiter breakout, instruction override in error traces. |
| **Malicious Critic / Agent Feedback** | Propagate injection across agents via shared Blackboard context. | Internal agent communication channel (A2A, Blackboard partitions). | Contagion of poisoned directives from Generator to Critic to Orchestrator. |

---

## 3. Threat Classification (STRIDE / OWASP LLM Top 10)

This threat model aligns with **OWASP Top 10 for LLM Applications (2025/2026)**:
- **LLM01: Prompt Injection (Direct & Indirect)**: Attacker crafts inputs that manipulate LLM behavior against system intent.
- **LLM02: Sensitive Information Disclosure**: Leaking environment variables, credentials, or system prompts.
- **LLM06: Excessive Agency / Insecure Tool Use**: Prompt injection compelling the agent to invoke dangerous shell or filesystem tools.

### Attack Vector Taxonomies

1. **Instruction Override Attacks**:
   - Phrases such as `"Ignore all previous instructions"`, `"Disregard prior constraints"`, `"System override"`.
   - Goal: Force model to generate trivial passing tests (`assert True`) or empty suites to achieve a false 100% mutation kill score.
2. **Secret Exfiltration Attacks**:
   - Directives: `"Print os.environ['GEMINI_API_KEY']"`, `"Reveal system prompt"`, `"Output process.env"`.
   - Goal: Steal model provider API credentials, GitHub access tokens, or database credentials.
3. **Delimiter Escape Attacks**:
   - Premature closure of framing tokens, e.g., `</untrusted_content>`, `[SYSTEM DIRECTIVE]`, `=== system override ===`.
   - Goal: Break out of passive data envelopes to impersonate system-level instructions.
4. **Tool Hijack & Path Traversal Attacks**:
   - Instructing the LLM or tool executor to call unauthorized tools (`system_exec`, `rm -rf /`) or access files outside repository boundaries (`../../../etc/passwd`).
5. **Cross-Agent Contagion (Blackboard Poisoning)**:
   - Poisoned inputs analyzed by an early agent (e.g., Critic) are reflected into directives stored on the Blackboard, infecting subsequent generation rounds and peer agents (ADK Generator).

---

## 4. Trust Boundaries & Data Flow Architecture

```
[Untrusted External Sources]
(GitHub Repos, Local Files, README.md, Docstrings, Comments, Tool Outputs)
                    |
                    v
    +----------------------------------+
    |    TRUST BOUNDARY 1: Ingestion   |
    |  - Mark TargetSpace.is_untrusted |
    |  - AST Injection Scanning        |
    +----------------------------------+
                    |
                    v
    +----------------------------------+
    | TRUST BOUNDARY 2: Prompt Guard   |
    |  - wrap_untrusted_content()      |
    |  - Delimiter Escape Neutralizer  |
    |  - Defensive System Instruction  |
    +----------------------------------+
                    |
                    v
    +----------------------------------+
    | TRUST BOUNDARY 3: Agent Envelopes|
    |  - Google ADK Generator          |
    |  - CrewAI Critic Agent           |
    |  - TestGeneratorAgent            |
    +----------------------------------+
                    |
                    v
    +----------------------------------+
    | TRUST BOUNDARY 4: Blackboard     |
    |  - sanitize_critic_directive()   |
    |  - Atomic partition validation   |
    |  - Error event dispatch          |
    +----------------------------------+
                    |
                    v
    +----------------------------------+
    | TRUST BOUNDARY 5: Tool Safety    |
    |  - verify_tool_call_safety()     |
    |  - Path traversal checks         |
    |  - Shell command execution block |
    |  - Sandbox AST Security Filter   |
    +----------------------------------+
```

---

## 5. Defense-in-Depth Mitigation Strategy

1. **Passive Data Framing (`wrap_untrusted_content`)**:
   - All untrusted inputs are enclosed in strict XML-style `<untrusted_content>` tags.
   - Any attempt to close the tag prematurely is escaped (`&lt;/untrusted_content&gt;`).
   - Clear warning banners (`# [NOTICE: ...]`) instruct both humans and LLMs that the content is untrusted data.
2. **Defensive System Preambles (`get_defensive_system_instruction`)**:
   - Immutable preamble gives developer instructions absolute priority over all passive data blocks.
   - Explicit instructions forbid agents from following role changes, secret leaks, or command execution requests.
3. **AST-Level Injection Defusing (`inspect_source_for_indirect_injections`)**:
   - Comments and docstrings are tokenized and parsed via Python's `tokenize` and `ast` modules.
   - Identified prompt injection payloads are replaced with neutral tokens `[DEFUSED_PROMPT_INJECTION: <RULE_ID>]`.
   - The code remains syntactically valid Python so valid test suites can still be generated.
4. **State Sanitation & Contagion Prevention (`sanitize_critic_directive`)**:
   - All reflection directives and critic messages are inspected prior to writing to the Blackboard.
   - Malicious directives are defused to prevent cross-agent infection.
5. **Tool Execution Verification (`verify_tool_call_safety`)**:
   - Tool requests are checked against strict tool whitelists.
   - Arguments are screened for shell piping (`| bash`, `| sh`), dangerous commands (`rm -rf`), and directory traversal (`..`).
6. **Code AST Security Guardrail (`SecurityGuardrail.inspect_code_ast`)**:
   - Generated test suites are verified prior to sandbox execution.
   - Disallows `os.environ`, `eval`, `exec`, `subprocess`, socket operations, and dangerous reflection.

