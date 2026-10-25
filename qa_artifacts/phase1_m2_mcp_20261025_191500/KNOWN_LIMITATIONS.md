# Known Limitations — Phase 1 Milestone 1.2 (GAP-02)

## 1. GAP-03 Checkpoint Automatic Resumption Deferred
- **Scope Boundary**: In strict accordance with the milestone plan, automatic resumption from SQLite Blackboard checkpoints (GAP-03) is deferred to Milestone 1.3.
- **Current State**: Checkpoints are correctly written to SQLite (`testforge_checkpoints.db`) with full MCP metadata (`mcp_tool_called`, `source_sha`, `line_count`, `target_space`), but autonomous recovery/resumption upon orchestrator reboot will be implemented in Milestone 1.3.

## 2. Remote GitHub MCP Integration Prerequisites
- **Authentication**: When calling remote GitHub MCP operations (e.g. `get_repository_info` against live repositories), GitHub requires a personal access token (`GITHUB_PERSONAL_ACCESS_TOKEN` or `GH_TOKEN`).
- **Unauthenticated Fallback**: Without a token, GitHub's public API limits IP addresses to 60 requests/hour. TestForge gracefully catches this rate limit via `McpError` fault isolation without crashing the agent pipeline or hanging sessions.

## 3. FastMCP Process Cleanup Lifecycle
- **Stdio Child Processes**: FastMCP stdio server runs as a separate Python subprocess. While `MCPClientManager.disconnect()` and `MCPClientManager.disconnect_sync()` ensure prompt process termination, abnormal host SIGKILL could leave an orphaned stdio process until host process garbage collection. All standard orchestrator termination paths invoke clean disconnection in `finally:` blocks.

## 4. Ingestion-Stage Precedence
- **Deterministic Precedence**: MCP tool invocation occurs during the `INGESTING` lifecycle stage. When both an in-memory `source_code` string and a filesystem `file_path` are provided to `TestForgeOrchestrator`, TestForge deterministically prioritizes hashing/verifying the referenced file via `get_file_info`. For tasks that are purely in-memory (no file path or repository URI provided), TestForge skips MCP tool calls cleanly without spurious network or filesystem overhead.
