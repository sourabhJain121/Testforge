# TestForge Stage 2.1: Model Context Protocol (MCP) in Google ADK

**Evaluation Date**: `2026-11-07T14:27:49Z`  
**MCP Server**: FastMCP Stdio Filesystem Server (`testforge/mcp_server.py`)  
**Consumer**: Google ADK Agent Tool Adapter (`testforge/adk_mcp_adapter.py`)  
**Permitted Filesystem Root**: `/Users/sourabh/TestForge`  

---

## 1. Executive Summary

TestForge integrates the official Model Context Protocol (MCP) with Google ADK specialist agents.
ADK agents consume FastMCP tools as native `FunctionTool` objects while enforcing strict path containment,
symlink escape prevention, and credential file redaction.

### Security & Containment Validation Matrix

| Operation | Target Path | Result | Security Policy Enforced |
| :--- | :--- | :---: | :--- |
| **Valid File Read** | `samples/discount.py` | `PASS` | Resolved within permitted root |
| **Directory Listing** | `samples/` | `PASS` | Filtered directory listing |
| **Directory Traversal Attack** | `../../etc/passwd` | **BLOCKED** | Escapes permitted root boundary |
| **Sensitive File Exfiltration** | `.env` | **BLOCKED** | Forbidden pattern policy (.env, credentials) |

---

## 2. Invocation Traces

```json
[
  {
    "timestamp": 1794061669.572499,
    "tool": "read_text_file",
    "arguments": {
      "path": "samples/discount.py"
    },
    "success": true,
    "duration_ms": 336.0,
    "error": null,
    "permitted_root": "/Users/sourabh/TestForge"
  },
  {
    "timestamp": 1794061669.579697,
    "tool": "list_directory",
    "arguments": {
      "path": "samples"
    },
    "success": true,
    "duration_ms": 7.17,
    "error": null,
    "permitted_root": "/Users/sourabh/TestForge"
  },
  {
    "timestamp": 1794061669.580033,
    "tool": "read_text_file",
    "arguments": {
      "path": "../../etc/passwd"
    },
    "success": false,
    "duration_ms": 0.23,
    "error": "Security Violation: Path '../../etc/passwd' escapes permitted project root '/Users/sourabh/TestForge'",
    "permitted_root": "/Users/sourabh/TestForge"
  },
  {
    "timestamp": 1794061669.580145,
    "tool": "read_text_file",
    "arguments": {
      "path": ".env"
    },
    "success": false,
    "duration_ms": 0.11,
    "error": "Security Violation: Access to sensitive file '.env' is strictly forbidden.",
    "permitted_root": "/Users/sourabh/TestForge"
  }
]
```
