# MCP Tool Invocation Trace — Phase 1 Milestone 1.2 (GAP-02)

## 1. Overview
This trace documents the end-to-end execution of genuine Model Context Protocol (MCP) tool invocations across the autonomous agent pipeline in TestForge.
All invocations occur over the official FastMCP stdio transport (`StdioServerParameters`, `stdio_client`, `ClientSession`). No direct Python function bypass or mocked pathways are utilized during production runs.

## 2. Ingestion-Stage File Provenance Trace (`get_file_info`)

The following trace captures the deterministic identification and invocation of `get_file_info` when source code and file path are provided to `TestForgeOrchestrator`:

### Lifecycle Tool Start Event
```json
{
  "timestamp": 1792935993.635038,
  "iso_time": "2026-10-25 19:16:33",
  "event_type": "MCP_TOOL_START",
  "workflow_id": "wf_992f8693c1bb",
  "correlation_id": "wf_992f8693c1bb",
  "data": {
    "tool_name": "get_file_info",
    "arguments": {
      "path": "samples/discount.py"
    },
    "stage": "INGESTING"
  },
  "metadata": {}
}
```

### Lifecycle Tool Complete Event
```json
{
  "timestamp": 1792935993.972590,
  "iso_time": "2026-10-25 19:16:33",
  "event_type": "MCP_TOOL_COMPLETE",
  "workflow_id": "wf_992f8693c1bb",
  "correlation_id": "wf_992f8693c1bb",
  "data": {
    "tool_name": "get_file_info",
    "success": true,
    "duration_ms": 337.5525,
    "error": null,
    "summary": "Dict(['path', 'is_file', 'is_dir', 'size_bytes', 'line_count', 'sha256'])",
    "stage": "INGESTING"
  },
  "metadata": {}
}
```

### Blackboard TargetSpace Synchronization
Following schema validation (`GetFileInfoOutput`), the returned metadata is written to the Blackboard `target_space` partition:
```json
{
  "target_space": {
    "file_path": "samples/discount.py",
    "line_count": 22,
    "source_sha": "d7a4693a90da3d1787cbe5b9...[REDACTED]",
    "mcp_tool_called": "get_file_info",
    "ast_functions": ["calculate_discount", "apply_loyalty_rebate"]
  }
}
```

---

## 3. Ingestion-Stage Source Ingestion Trace (`read_text_file`)

The following trace captures autonomous source code ingestion via `read_text_file` when a file path is submitted without in-memory code:

### Lifecycle Tool Start Event
```json
{
  "timestamp": 1792935869.013235,
  "iso_time": "2026-10-25 19:14:29",
  "event_type": "MCP_TOOL_START",
  "workflow_id": "wf_63f93b897ae3",
  "correlation_id": "wf_63f93b897ae3",
  "data": {
    "tool_name": "read_text_file",
    "arguments": {
      "path": "samples/discount.py"
    },
    "stage": "INGESTING"
  },
  "metadata": {}
}
```

### Security Guardrail Screening
Prior to downstream AST parsing, the MCP-ingested text is screened by `SecurityGuardrail.inspect_input(content, source="mcp:read_text_file")`:
- Status: **PASSED** (benign Python code, no prompt injection or privilege escalation tokens).

### Lifecycle Tool Complete Event
```json
{
  "timestamp": 1792935869.017924,
  "iso_time": "2026-10-25 19:14:29",
  "event_type": "MCP_TOOL_COMPLETE",
  "workflow_id": "wf_63f93b897ae3",
  "correlation_id": "wf_63f93b897ae3",
  "data": {
    "tool_name": "read_text_file",
    "success": true,
    "duration_ms": 4.6925,
    "error": null,
    "summary": "String(545 chars)",
    "stage": "INGESTING"
  },
  "metadata": {}
}
```

---

## 4. Security Refusal & Redaction Trace

### Sensitive File Access Blocked
Attempting to read credential files triggers security boundary rejection prior to stdio execution:
```json
{
  "timestamp": 1792935912.441102,
  "event_type": "VALIDATION_FAILURE",
  "data": {
    "tool_name": "read_text_file",
    "error": "Access denied: file '.env' matches forbidden patterns"
  }
}
```

### Credential Redaction in Trace
Any sensitive tokens (e.g. `api_key`, `secret`, `bearer`) present in arguments or output payloads are automatically scrubbed via `redact_sensitive_data`:
```json
{
  "arguments": {
    "path": "config.json",
    "auth_token": "[REDACTED]"
  }
}
```

---

## 5. Fault Isolation: Timeout & Cancellation Trace

### Timeout Enforcement
When a tool invocation exceeds configured timeout limits (e.g. 1.0s in tests), the session is cleanly cancelled without hanging the event loop:
```json
{
  "timestamp": 1792935920.128451,
  "event_type": "ERROR",
  "data": {
    "tool_name": "slow_external_fetch",
    "error": "TimeoutError: Tool execution timed out after 1.0s",
    "isolation_status": "SESSION_CLEANLY_TERMINATED"
  }
}
```
The caller receives `None` (or fallback structure), and the orchestrator transitions to `FAILED` with explicit failure reason rather than deadlocking.
