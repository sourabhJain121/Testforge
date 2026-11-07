# MCP & Tool Integration Audit

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** FACTUAL AUDIT COMPLETED  

---

## 1. Overview of Tool Architecture

TestForge utilizes tools across two distinct layers:
1. **Model Context Protocol (MCP) Standard Layer:** Implemented using the official `mcp` SDK (`mcp>=1.28.0`, specifically `FastMCP` and `stdio_client`) in [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py) and [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py).
2. **Internal ADK Deliberation Tool Layer:** Implemented in [`testforge/adk_engine.py`](file:///Users/sourabh/TestForge/testforge/adk_engine.py) to provide structured function calling and audit records during agent reflection cycles.

> [!NOTE]
> **Third-Party vs. Local MCP Implementation Status:**  
> TestForge does **not** rely on external third-party cloud-hosted MCP servers. Instead, TestForge implements two **in-process/local FastMCP servers** (`Filesystem MCP Server` and `GitHub MCP Server`) conforming strictly to the official MCP protocol specification over `stdio` transport. This design eliminates external network dependencies while strictly adhering to the MCP standard.

---

## 2. MCP Tool Inventory ([`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py))

### 2.1 Filesystem MCP Server (`TestForge Filesystem MCP`)

| Tool Name | Server & Source File | Purpose | Input Schema | Output Schema | Consuming Agent | Live Invoked? | Logged? |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **`read_text_file`** | `FastMCP`<br>[`mcp_server.py:88`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L88) | Reads contents of a UTF-8 file strictly within the permitted project root. Blocks path traversal (`../`) and sensitive files (`.env`, keys). | `path: str` | `str` (file contents) | Supervisor / Ingestion / Code Intelligence | Yes (during MCP target file ingestion) | Yes (`TOOL_START`, `TOOL_COMPLETE` in `testforge_trace.jsonl`) |
| **`list_directory`** | `FastMCP`<br>[`mcp_server.py:106`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L106) | Lists files and subdirectories within a permitted directory. | `path: str = "."` | `List[Dict[str, Any]]` (`name`, `is_dir`, `size_bytes`) | Code Intelligence / Ingestion | Yes (in directory discovery tests) | Yes |
| **`get_file_info`** | `FastMCP`<br>[`mcp_server.py:138`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L138) | Returns line count, size in bytes, and SHA-256 hash without loading full content into memory. | `path: str` | `Dict[str, Any]` (`path`, `size_bytes`, `line_count`, `sha256`) | Supervisor / Code Intelligence | Yes (during metadata inspection) | Yes |

### 2.2 GitHub MCP Server (`TestForge GitHub MCP`)

| Tool Name | Server & Source File | Purpose | Input Schema | Output Schema | Consuming Agent | Live Invoked? | Logged? |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **`get_file_contents`** | `FastMCP`<br>[`mcp_server.py:238`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L238) | Retrieves file content from GitHub repository with SSRF prevention and size limits. | `owner: str`, `repo: str`, `path: str`, `ref: str = "main"` | `Dict[str, Any]` (`path`, `size_bytes`, `sha`, `content`) | Supervisor / GitHub Ingestion Service | Yes (during GitHub ingestion tests) | Yes |
| **`get_repository_info`**| `FastMCP`<br>[`mcp_server.py:222`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L222) | Retrieves repository metadata (name, default branch, stars, description). | `owner: str`, `repo: str` | `Dict[str, Any]` | Supervisor / GitHub Ingestion Service | Yes | Yes |
| **`search_repositories`**| `FastMCP`<br>[`mcp_server.py:267`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L267) | Searches GitHub repositories by query string with bounded result limits. | `query: str`, `limit: int = 5` | `List[Dict[str, Any]]` | Supervisor / GitHub Ingestion Service | Yes | Yes |
| **`get_repository_tree`**| `FastMCP`<br>[`mcp_server.py:285`](file:///Users/sourabh/TestForge/testforge/mcp_server.py#L285) | Fetches recursive git tree for a repo/branch to discover testable modules. | `owner: str`, `repo: str`, `ref: str = "main"`, `recursive: bool = True` | `Dict[str, Any]` (`items: List`, `truncated: bool`) | Supervisor / Code Intelligence | Yes | Yes |

---

## 3. Internal ADK Tool Inventory ([`testforge/adk_engine.py`](file:///Users/sourabh/TestForge/testforge/adk_engine.py))

TestForge provides an internal tool deliberation registry used during reflection cycles:

| Tool Identifier | Source File & Class | Purpose | Parameters Schema | Consuming Agent | Live Invoked? | Logged Event |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`tool_execute_sandbox`** | [`adk_engine.py:155`](file:///Users/sourabh/TestForge/testforge/adk_engine.py#L155)<br>Calls `ParallelSandboxRunner` | Executes candidate unit tests against target code in ephemeral subprocess. | `test_code: str`, `target_code: str`, `timeout_sec: float = 5.0` | Test Execution Agent / Adversarial Critic | Yes | `event_type: "ADK_TOOL_CALL"` |
| **`tool_compute_blast_radius`** | [`adk_engine.py:175`](file:///Users/sourabh/TestForge/testforge/adk_engine.py#L175)<br>Calls `BlastRadiusAnalyzer` | Builds AST call graph and evaluates risk category (`LOW`, `MEDIUM`, `HIGH`). | `source_code: str`, `target_function: str = ""` | Code Intelligence / Ingestion | Yes | `event_type: "ADK_TOOL_CALL"` |
| **`tool_inspect_git_diff`** | [`adk_engine.py:195`](file:///Users/sourabh/TestForge/testforge/adk_engine.py#L195)<br>Calls `GitDiffInspector` | Inspects working tree git diff to identify modified lines for targeted mutation. | `repo_root: Optional[str] = None` | Code Intelligence / Planning | Yes | `event_type: "ADK_TOOL_CALL"` |
| **`tool_ast_audit`** | [`adk_engine.py:215`](file:///Users/sourabh/TestForge/testforge/adk_engine.py#L215) | Analyzes surviving mutant unified diffs and diagnoses syntactic gaps. | `surviving_diffs: List[str]`, `target_code: str` | Mutation & Quality Critic Agent | Yes | `event_type: "ADK_TOOL_CALL"` |

---

## 4. Tool Governance & Security Safeguards

1. **Permitted Root Jail:** The Filesystem MCP Server strictly resolves paths against `root_dir.resolve()` and rejects directory traversal (`../`) or absolute path escapes.
2. **Blocked Sensitive Files:** FastMCP rejects requests for `.env`, `.env.*`, `id_rsa`, `*.pem`, `*.key`, and git credentials.
3. **SSRF Guardrail:** The GitHub MCP Server verifies hosts via `validate_url_hostname` against `ALLOWED_GITHUB_HOSTS` (`api.github.com`, `raw.githubusercontent.com`) and rejects private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`).
4. **Destructive Tool Whitelist:** Destructive MCP tools (`write_file`, `edit_file`, `create_directory`, `push_files`) are permanently blocked in `DEFAULT_ALLOWED_TOOLS` ([`mcp_client.py:47`](file:///Users/sourabh/TestForge/testforge/mcp_client.py#L47)).
5. **Telemetry Logging:** Every tool invocation emits structured `TOOL_START` and `TOOL_COMPLETE` (or `ERROR`) events through `CallbackRegistry` directly to `testforge_trace.jsonl`.

