# TestForge — Security Architecture & Reliability

**Course:** CSE3101 - Agentic AI  
**Document ID:** TF-SEC-EVAL-001  
**Date:** October 30, 2026  
**Status:** Evaluation Baseline  

---

## 1. Security Architecture Overview

TestForge incorporates multi-layered security engineering covering network boundaries, prompt isolation, state partitions, and sandbox code execution.

```
+-----------------------------------------------------------------------+
| LAYER 1: Network Boundary & SSRF Protection                           |
|  - ALLOWED_GITHUB_HOSTS whitelist (HTTPS only)                        |
|  - SafeGitHubRedirectHandler (rejects private IPs, loopback, metadata)|
|  - Cross-domain credential stripping on redirects                      |
|  - Bounded download streaming (500 KB limit, atomic disk writes)      |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| LAYER 2: Indirect Prompt-Injection Defense                           |
|  - Untrusted Content Envelopes (<untrusted_content type="..." ...>)   |
|  - Delimiter breakout escaping (&lt;/untrusted_content&gt;)           |
|  - Python AST comment & docstring defusing ([DEFUSED_PROMPT_INJ:...]) |
|  - DEFENSIVE_SYSTEM_PREAMBLE (strict instruction precedence)          |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| LAYER 3: Shared State & Tool Execution Boundaries                     |
|  - Blackboard partition isolation (TargetSpace.is_untrusted = True)   |
|  - sanitize_critic_directive() at partition boundaries                |
|  - verify_tool_call_safety() (whitelists, shell pipe rejection)       |
|  - Path traversal checks (confinement to permitted roots)            |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| LAYER 4: Subprocess Execution Sandbox                                 |
|  - CodeSanitizer & ASTSecurityAnalyzer                                |
|  - Blocking os.system, subprocess, eval, exec, socket, os.environ     |
|  - Strict execution timeouts (5.0s default)                           |
|  - Ephemeral sandbox directory cleanup                                |
+-----------------------------------------------------------------------+
```

---

## 2. Implemented Defense Capabilities

### 2.1 SSRF Protection & Safe Redirects (`testforge/network_security.py`)
- **Strict Hostname Whitelist**: Requests allowed only to `api.github.com`, `raw.githubusercontent.com`, `github.com`, `codeload.github.com`, `objects.githubusercontent.com`.
- **Redirect Interception**: Intercepts HTTP 301, 302, 303, 307, 308 redirects. Fails closed if the destination resolves to loopback (`127.0.0.1`, `::1`), private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), or cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
- **Credential Stripping**: Automatically strips `Authorization`, `X-Access-Token`, and `Cookie` headers if a redirect navigates across different hostnames.

### 2.2 Bounded Source Downloads (`bounded_read`)
- **Pre-allocation Check**: Verifies `Content-Length` header is non-negative and $\le 500$ KB.
- **Chunk-by-Chunk Enforcement**: Streams in 8 KB chunks, immediately terminating the connection if total bytes exceed 500 KB, preventing memory exhaustion.
- **Atomic Persistence**: Writes to a temporary `.tmp` file and replaces the destination only upon full stream completion; zero partial files remain on disk upon failure.

### 2.3 MCP Network Security (`testforge/mcp_server.py`)
- FastMCP tools (`get_file_contents`, `get_repository_tree`) route requests through `SafeGitHubRedirectHandler` and enforce bounded reading on GitHub API responses (10 MB cap for JSON API responses, 500 KB cap for decoded file source).

### 2.4 Indirect Prompt-Injection Safeguards (`testforge/prompt_guard.py`)
- **Untrusted Content Framing**: External source files, docstrings, and diffs are wrapped in `<untrusted_content>` tags with provenance metadata.
- **AST Comment & Docstring Defusing**: Parses Python AST and token streams to detect 11 injection rules. Payloads are replaced with inert tokens `[DEFUSED_PROMPT_INJECTION: <RULE_ID>]` so valid code remains syntactically valid and testable.
- **Instruction Precedence**: Prepend `DEFENSIVE_SYSTEM_PREAMBLE`, mandating that system directives strictly supersede all passive data blocks.
- **Inter-Agent Directive Sanitization**: Defuses adversarial directives before saving to the shared Blackboard, preventing cross-agent contagion.

### 2.5 Tool Call Whitelisting & Path Traversal Prevention
- `verify_tool_call_safety()` validates requested tools against allowed sets, rejects arguments with shell execution syntax (`| bash`, `| sh`, `rm -rf /`), and blocks directory traversal (`..`).

### 2.6 Subprocess Sandbox Isolation (`testforge/sandbox.py`)
- Candidate test suites are executed in an isolated child process via `pytest` with a 5.0-second timeout.
- `SecurityGuardrail.inspect_code_ast` inspects the AST prior to execution, rejecting dangerous imports (`subprocess`, `socket`, `shutil`, `ctypes`) and direct attribute access to `os.environ`.

---

## 3. Dedicated Security Test Suites

The security architecture is verified by **84 dedicated automated tests**:
1. `tests/test_network_security.py` — 62 tests covering URL validation, private IP blocking, redirect limits, credential purging, and chunk limits.
2. `tests/test_mcp_network_security.py` — 12 tests covering real `urllib` FastMCP integration with zero mocking.
3. `tests/test_prompt_injection_defense.py` — 10 tests covering all 10 adversarial prompt injection scenarios.

---

## 4. Known Security Limitations & Residual Risks

1. **Host OS Isolation**: The sandbox relies on Python subprocess isolation and timeouts rather than hardware-level containers (Docker/gVisor). In Phase 2C/Phase 5, OS-level cgroups / rlimits (`rlimit_cpu`, `rlimit_as`) can provide additional isolation.
2. **Obfuscated / Homoglyph Injections**: Sophisticated unicode homoglyphs or multi-step linguistic steganography could potentially bypass current regex patterns.
3. **Live GitHub Rate Limiting**: Anonymous requests to the GitHub API are limited to 60 requests/hour by GitHub. Supplying a `GITHUB_TOKEN` increases limits to 5,000 requests/hour.

