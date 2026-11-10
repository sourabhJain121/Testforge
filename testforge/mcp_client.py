"""
mcp_client.py - Robust Model Context Protocol (MCP) Client for TestForge.

Features:
  1. Standard MCP Protocol: Uses official mcp SDK (stdio_client, ClientSession).
  2. Lifecycle Callbacks: Dispatches TOOL_START, TOOL_COMPLETE, and ERROR events.
  3. Security Boundaries:
     - Enforces permitted filesystem roots (rejects path traversal, absolute escapes).
     - Blocks sensitive credential files (.env, keys, git configs).
     - Enforces read-only tool whitelists, rejecting destructive operations.
  4. Secret Scrubbing: Redacts credentials from arguments and outputs.
  5. Timeout & Fault Isolation: Clean session cancellation on timeouts or server crashes.
  6. Blackboard Synchronization: Routes safe metadata to Blackboard without dual-state drift.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import select
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    try:
        from mcp.shared.exceptions import McpError
    except ImportError:
        try:
            from mcp.shared.exceptions import MCPError as McpError
        except ImportError:
            class McpError(Exception):  # type: ignore
                pass
except ImportError:
    stdio_client = None  # type: ignore
    StdioServerParameters = None  # type: ignore
    ClientSession = None  # type: ignore
    class McpError(Exception):  # type: ignore
        pass

from testforge.callbacks import (
    CallbackRegistry,
    EventType,
    LifecycleEvent,
)
from testforge.mcp_server import FORBIDDEN_EXTENSIONS, FORBIDDEN_NAME_PATTERNS
from testforge.security import redact_sensitive_data

logger = logging.getLogger("testforge.mcp_client")

# Default read-only tools whitelisted for Phase 3
DEFAULT_ALLOWED_TOOLS = {
    # Filesystem tools
    "read_text_file", "read_file", "list_directory", "get_file_info",
    "directory_tree", "search_files", "list_allowed_directories",
    # GitHub tools
    "get_file_contents", "get_repository_info", "search_repositories",
    "get_repository_tree", "get_issue", "get_pull_request", "list_commits",
    # TestForge Native MCP tools
    "harden_module", "get_report", "list_jobs",
    # FastMCP 4-Tool Protocol Suite
    "mcp_ast_symbol_analyzer", "mcp_mutant_generator",
    "mcp_sandbox_runner", "mcp_equivalence_classifier"
}

# Explicitly blocked destructive tools
BLOCKED_DESTRUCTIVE_TOOLS = {
    "write_file", "edit_file", "create_directory", "move_file",
    "create_or_update_file", "push_files", "create_issue",
    "create_pull_request", "fork_repository", "create_branch"
}


from pydantic import ValidationError


class ReadTextFileInput(BaseModel):
    path: str = Field(..., min_length=1, description="Path to the file to read")


class GetFileInfoInput(BaseModel):
    path: str = Field(..., min_length=1, description="Path to the file to inspect")


class GetFileInfoOutput(BaseModel):
    path: str
    is_file: bool
    is_dir: bool
    size_bytes: int
    line_count: int
    sha256: str


class ListDirectoryInput(BaseModel):
    path: str = Field(default=".", description="Path to directory")


class GetRepositoryInfoInput(BaseModel):
    owner: str = Field(..., min_length=1, description="GitHub repository owner")
    repo: str = Field(..., min_length=1, description="GitHub repository name")


class GetRepositoryInfoOutput(BaseModel):
    full_name: Optional[str] = None
    description: Optional[str] = None
    default_branch: str = "main"
    stargazers_count: int = 0
    open_issues_count: int = 0
    topics: List[str] = Field(default_factory=list)


class GetFileContentsInput(BaseModel):
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    ref: str = "main"


class SearchRepositoriesInput(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


class ToolSelectionDecision(BaseModel):
    required: bool
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    task_file: Optional[str] = None


TOOL_INPUT_MODELS: Dict[str, type[BaseModel]] = {
    "read_text_file": ReadTextFileInput,
    "get_file_info": GetFileInfoInput,
    "list_directory": ListDirectoryInput,
    "get_repository_info": GetRepositoryInfoInput,
    "get_file_contents": GetFileContentsInput,
    "search_repositories": SearchRepositoriesInput,
}


class MCPToolDefinition(BaseModel):
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    server_id: str = "default"


class MCPToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    is_redacted: bool = False


class MCPClientManager:
    """
    Manages connections and tool invocations to an MCP server via stdio transport.
    """

    def __init__(
        self,
        server_params: StdioServerParameters,
        permitted_root: Optional[Union[str, Path]] = None,
        callback_registry: Optional[CallbackRegistry] = None,
        allowed_tools: Optional[Set[str]] = None,
        default_timeout: float = 10.0,
        server_id: str = "mcp-server"
    ):
        self.server_params = server_params
        self.permitted_root = Path(permitted_root).resolve() if permitted_root else None
        self.callbacks = callback_registry
        self.allowed_tools = allowed_tools or DEFAULT_ALLOWED_TOOLS
        self.default_timeout = default_timeout
        self.server_id = server_id

        self._session: Optional[ClientSession] = None
        self._stdio_cm = None
        self._session_cm = None
        self._tools_cache: Dict[str, MCPToolDefinition] = {}
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.RLock()

    @property
    def is_connected(self) -> bool:
        return self._connected and self._session is not None

    async def connect(self) -> None:
        """Establishes stdio connection and initializes the MCP session."""
        with self._lock:
            current_loop = asyncio.get_running_loop()
            if self._connected:
                if self._loop == current_loop:
                    return
                # Clean up session from previous loop
                await self._cleanup()

            try:
                self._stdio_cm = stdio_client(self.server_params)
                read_stream, write_stream = await self._stdio_cm.__aenter__()

                self._session_cm = ClientSession(read_stream, write_stream)
                self._session = await self._session_cm.__aenter__()

                await self._session.initialize()
                self._connected = True
                self._loop = current_loop
                logger.info(f"Connected to MCP server: {self.server_id}")

                # Populate tools cache
                await self._refresh_tools_cache()

            except Exception as exc:
                await self._cleanup()
                safe_err = redact_sensitive_data(str(exc))
                logger.error(f"Failed to connect to MCP server '{self.server_id}': {safe_err}")
                if self.callbacks:
                    self.callbacks.dispatch(LifecycleEvent(
                        event_type=EventType.ERROR,
                        emitter=f"MCPClientManager[{self.server_id}]",
                        payload={"error_type": "ConnectionError", "message": safe_err, "fatal": False}
                    ))
                raise ConnectionError(f"MCP server connection failed: {safe_err}") from exc

    async def _refresh_tools_cache(self) -> None:
        if not self._session:
            return
        tools_resp = await self._session.list_tools()
        self._tools_cache = {}
        for tool in tools_resp.tools:
            self._tools_cache[tool.name] = MCPToolDefinition(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema or {},
                server_id=self.server_id
            )

    async def list_tools(self) -> List[MCPToolDefinition]:
        """Returns the list of discovered tools from the active MCP server."""
        if not self._connected:
            await self.connect()
        return list(self._tools_cache.values())

    def _validate_security_policy(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Validates tool against read-only whitelist, path traversal, and sensitive files."""
        # Check blocked destructive tools
        if tool_name in BLOCKED_DESTRUCTIVE_TOOLS:
            return f"Security Policy Violation: Tool '{tool_name}' is a destructive/write operation and is blocked."

        # Check allowed tools whitelist
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return f"Security Policy Violation: Tool '{tool_name}' is not in the permitted tool whitelist."

        # Check path parameters for filesystem containment and sensitive files
        if self.permitted_root:
            path_keys = [k for k in arguments.keys() if k.lower() in ("path", "filepath", "file_path", "directory", "dir")]
            for key in path_keys:
                raw_path = str(arguments[key])
                candidate = Path(raw_path)
                resolved = candidate.resolve() if candidate.is_absolute() else (self.permitted_root / candidate).resolve()

                # Traversal check
                if resolved != self.permitted_root and self.permitted_root not in resolved.parents:
                    return f"Security Violation: Path '{raw_path}' escapes permitted project root '{self.permitted_root}'"

                # Sensitive files check
                name_lower = resolved.name.lower()
                if name_lower in FORBIDDEN_NAME_PATTERNS or name_lower.startswith(".env"):
                    return f"Security Violation: Access to sensitive file '{resolved.name}' is strictly forbidden."

                if resolved.suffix.lower() in FORBIDDEN_EXTENSIONS:
                    return f"Security Violation: Access to credential file '{resolved.name}' is forbidden."

                parts = [p.lower() for p in resolved.parts]
                if ".git" in parts and ("config" in parts or "credentials" in parts):
                    return "Security Violation: Access to git credentials or config is forbidden."

        return None

    def _validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Validates tool arguments against typed Pydantic models or JSON schema."""
        if tool_name in TOOL_INPUT_MODELS:
            try:
                TOOL_INPUT_MODELS[tool_name].model_validate(arguments)
            except ValidationError as exc:
                return f"SchemaValidationError: Invalid arguments for tool '{tool_name}': {exc}"
            except Exception as exc:
                return f"SchemaValidationError: {exc}"
        elif tool_name in self._tools_cache:
            schema = self._tools_cache[tool_name].input_schema
            required = schema.get("required", [])
            for req in required:
                if req not in arguments:
                    return f"SchemaValidationError: Missing required parameter '{req}' for tool '{tool_name}'"
        return None

    def _validate_response(self, tool_name: str, data: Any, is_error: bool) -> Optional[str]:
        """Validates tool response structure and types against schema contracts."""
        if is_error:
            return None
        if tool_name == "read_text_file":
            if not isinstance(data, str):
                return f"MalformedToolResponse: Expected string content for '{tool_name}', got {type(data).__name__}"
        elif tool_name == "get_file_info":
            if not isinstance(data, dict):
                return f"MalformedToolResponse: Expected dict for '{tool_name}', got {type(data).__name__}"
            try:
                GetFileInfoOutput.model_validate(data)
            except ValidationError as exc:
                return f"MalformedToolResponse: Invalid structure for '{tool_name}': {exc}"
        elif tool_name == "list_directory":
            if not isinstance(data, list):
                return f"MalformedToolResponse: Expected list for '{tool_name}', got {type(data).__name__}"
        elif tool_name == "get_repository_info":
            if not isinstance(data, dict):
                return f"MalformedToolResponse: Expected dict for '{tool_name}', got {type(data).__name__}"
            try:
                GetRepositoryInfoOutput.model_validate(data)
            except ValidationError as exc:
                return f"MalformedToolResponse: Invalid structure for '{tool_name}': {exc}"
        return None

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> MCPToolResult:
        """
        Executes an MCP tool with schema validation, security filtering, and lifecycle telemetry.
        """
        arguments = arguments or {}
        call_timeout = timeout or self.default_timeout
        start_time = time.perf_counter()

        # 1. Dispatch TOOL_START event
        if self.callbacks:
            self.callbacks.dispatch(LifecycleEvent(
                event_type=EventType.TOOL_START,
                emitter=f"MCPClientManager[{self.server_id}]",
                payload={"tool_name": tool_name, "arguments": arguments}
            ))

        # 2. Security Policy Validation
        policy_violation = self._validate_security_policy(tool_name, arguments)
        if policy_violation:
            duration = (time.perf_counter() - start_time) * 1000
            err_msg = redact_sensitive_data(policy_violation)
            logger.warning(f"MCP tool call blocked: {err_msg}")
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.ERROR,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={"error_type": "SecurityPolicyViolation", "message": err_msg, "fatal": False}
                ))
            return MCPToolResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration)

        # 3. Ensure Connected
        if not self._connected:
            try:
                await self.connect()
            except Exception as e:
                duration = (time.perf_counter() - start_time) * 1000
                return MCPToolResult(tool_name=tool_name, success=False, error=str(e), duration_ms=duration)

        # 4. Check tool existence
        if tool_name not in self._tools_cache:
            duration = (time.perf_counter() - start_time) * 1000
            err_msg = f"Unknown or unregistered tool '{tool_name}'. Available: {list(self._tools_cache.keys())}"
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.ERROR,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={"error_type": "ToolNotFoundError", "message": err_msg, "fatal": False}
                ))
            return MCPToolResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration)

        # 5. Schema validation for arguments
        val_error = self._validate_arguments(tool_name, arguments)
        if val_error:
            duration = (time.perf_counter() - start_time) * 1000
            err_msg = redact_sensitive_data(val_error)
            logger.warning(f"MCP tool argument validation failed: {err_msg}")
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.VALIDATION_FAILURE,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={"tool_name": tool_name, "error_type": "SchemaValidationError", "message": err_msg}
                ))
            return MCPToolResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration)

        # 6. Execute with Timeout
        try:
            assert self._session is not None
            call_coro = self._session.call_tool(tool_name, arguments)
            result = await asyncio.wait_for(call_coro, timeout=call_timeout)
            duration = (time.perf_counter() - start_time) * 1000

            # Extract structured content
            extracted_data: Any = None
            if result.content:
                items = []
                for item in result.content:
                    if hasattr(item, "text"):
                        try:
                            import json
                            items.append(json.loads(item.text))
                        except Exception:
                            items.append(item.text)
                    else:
                        items.append(str(item))
                extracted_data = items[0] if len(items) == 1 else items

            tool_res = MCPToolResult(
                tool_name=tool_name,
                success=not result.isError,
                data=extracted_data,
                error=None if not result.isError else str(extracted_data),
                duration_ms=duration
            )

            # Validate response structure
            resp_val_error = self._validate_response(tool_name, extracted_data, result.isError)
            if resp_val_error:
                tool_res.success = False
                tool_res.error = resp_val_error

            # 7. Dispatch TOOL_COMPLETE
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.TOOL_COMPLETE,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={
                        "tool_name": tool_name,
                        "status": "SUCCESS" if tool_res.success else "FAILED",
                        "duration_ms": duration,
                        "output_summary": str(tool_res.data)[:200] if tool_res.data else tool_res.error
                    }
                ))

            return tool_res

        except asyncio.TimeoutError:
            duration = (time.perf_counter() - start_time) * 1000
            err_msg = f"Tool '{tool_name}' timed out after {call_timeout}s"
            logger.error(err_msg)
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.ERROR,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={"error_type": "TimeoutError", "message": err_msg, "fatal": False}
                ))
            return MCPToolResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration)

        except McpError as exc:
            duration = (time.perf_counter() - start_time) * 1000
            err_msg = redact_sensitive_data(str(exc))
            logger.warning(f"MCP server returned error for tool '{tool_name}': {err_msg}")
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.ERROR,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={"error_type": "McpError", "message": err_msg, "fatal": False}
                ))
            return MCPToolResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration)

        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            err_msg = redact_sensitive_data(str(exc))
            logger.error(f"Unexpected error executing MCP tool '{tool_name}': {err_msg}")
            await self._cleanup()
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.ERROR,
                    emitter=f"MCPClientManager[{self.server_id}]",
                    payload={"error_type": type(exc).__name__, "message": err_msg, "fatal": False}
                ))
            return MCPToolResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration)

    def call_tool_sync(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> MCPToolResult:
        """Synchronous helper for calling an MCP tool from non-async code."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    lambda: asyncio.run(self.call_tool(tool_name, arguments, timeout))
                ).result()
        else:
            return loop.run_until_complete(self.call_tool(tool_name, arguments, timeout))

    def list_tools_sync(self) -> List[MCPToolDefinition]:
        """Synchronous helper to list available tools."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(self.list_tools())).result()
        else:
            return loop.run_until_complete(self.list_tools())

    async def disconnect(self) -> None:
        """Closes session and cleans up stdio pipes."""
        with self._lock:
            await self._cleanup()

    def disconnect_sync(self) -> None:
        """Synchronously closes session and cleans up stdio pipes."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(lambda: asyncio.run(self.disconnect())).result()
        else:
            loop.run_until_complete(self.disconnect())

    async def _cleanup(self) -> None:
        if self._session_cm:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None
            self._session = None

        if self._stdio_cm:
            try:
                await self._stdio_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._stdio_cm = None

        self._connected = False
        self._tools_cache.clear()

    async def __aenter__(self) -> "MCPClientManager":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    def sync_to_blackboard(self, tool_result: MCPToolResult, blackboard: Any) -> None:
        """
        Safely bridges tool outputs to the Blackboard TargetSpace without polluting unrelated spaces.
        """
        if not tool_result.success or not blackboard:
            return

        tool = tool_result.tool_name
        data = tool_result.data

        if tool == "read_text_file" and isinstance(data, str):
            import hashlib
            sha = hashlib.sha256(data.encode("utf-8")).hexdigest()
            blackboard.update_target_space(
                target_source_code=data,
                source_sha=sha,
                line_count=data.count("\n") + 1
            )
        elif tool == "get_file_info" and isinstance(data, dict):
            blackboard.update_target_space(
                source_sha=data.get("sha256", ""),
                line_count=data.get("line_count", 0)
            )
        elif tool == "get_file_contents" and isinstance(data, dict):
            content = data.get("content", "")
            if content:
                blackboard.update_target_space(
                    target_source_code=content,
                    source_sha=data.get("sha", ""),
                    line_count=content.count("\n") + 1
                )


# Factory Helpers
def create_filesystem_client(
    permitted_root: Union[str, Path],
    use_node: bool = False,
    callback_registry: Optional[CallbackRegistry] = None
) -> MCPClientManager:
    """
    Creates an MCPClientManager configured for the Filesystem MCP server.
    If use_node is True and npx is available, uses @modelcontextprotocol/server-filesystem.
    Otherwise, uses the native Python FastMCP server.
    """
    root_path = Path(permitted_root).resolve()
    python_bin = sys.executable

    if use_node:
        import shutil
        npx_path = shutil.which("npx") or "/Users/sourabh/.nvm/versions/node/v24.15.0/bin/npx"
        params = StdioServerParameters(
            command=npx_path,
            args=["-y", "@modelcontextprotocol/server-filesystem", str(root_path)]
        )
    else:
        # Native Python FastMCP server
        params = StdioServerParameters(
            command=python_bin,
            args=["-m", "testforge.mcp_server", "filesystem", str(root_path)],
            env={"PYTHONPATH": str(Path(__file__).parent.parent.resolve())}
        )

    return MCPClientManager(
        server_params=params,
        permitted_root=root_path,
        callback_registry=callback_registry,
        server_id="filesystem-mcp"
    )


def create_github_client(
    github_token: Optional[str] = None,
    use_node: bool = False,
    callback_registry: Optional[CallbackRegistry] = None
) -> MCPClientManager:
    """
    Creates an MCPClientManager configured for the GitHub MCP server.
    """
    python_bin = sys.executable
    token = github_token or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    env = {"PYTHONPATH": str(Path(__file__).parent.parent.resolve())}
    if token:
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
        env["GITHUB_TOKEN"] = token

    if use_node:
        import shutil
        npx_path = shutil.which("npx") or "/Users/sourabh/.nvm/versions/node/v24.15.0/bin/npx"
        params = StdioServerParameters(
            command=npx_path,
            args=["-y", "@modelcontextprotocol/server-github"],
            env=env
        )
    else:
        params = StdioServerParameters(
            command=python_bin,
            args=["-m", "testforge.mcp_server", "github"],
            env=env
        )

    return MCPClientManager(
        server_params=params,
        callback_registry=callback_registry,
        server_id="github-mcp"
    )


def create_testforge_client(
    permitted_root: Optional[Path] = None,
    callback_registry: Optional[CallbackRegistry] = None
) -> MCPClientManager:
    """
    Creates an MCPClientManager configured for the native TestForge MCP server.
    """
    root_path = (permitted_root or Path(__file__).parent.parent).resolve()
    python_bin = sys.executable
    params = StdioServerParameters(
        command=python_bin,
        args=["-m", "testforge.mcp_server", "testforge", str(root_path)],
        env={"PYTHONPATH": str(root_path)}
    )
    return MCPClientManager(
        server_params=params,
        permitted_root=root_path,
        callback_registry=callback_registry,
        server_id="testforge-mcp"
    )


class ToolResultDict(dict):
    """
    Subclass of dict providing attribute access (.success, .data, .error, .duration_ms, .tool_name)
    in addition to dict keys (['data'], ['success'], etc.).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def tool_name(self) -> str:
        return self.get("tool_name", "")

    @property
    def success(self) -> bool:
        return bool(self.get("success", False))

    @property
    def data(self) -> Any:
        return self.get("data")

    @property
    def error(self) -> Optional[str]:
        return self.get("error")

    @property
    def duration_ms(self) -> float:
        return float(self.get("duration_ms", 0.0))

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ToolResultDict' object has no attribute '{name}'")


class FastMCPStdioClient:
    """
    Standard MCP JSON-RPC stdio transport client managing an isolated child process
    running `testforge.mcp_server`.

    Features:
    - Launches isolated child process with sys.executable -m testforge.mcp_server protocol.
    - JSON-RPC 2.0 handshake (initialize, notifications/initialized).
    - stdio tools/list and tools/call dispatch.
    - select() timeout protection on stdio read.
    - Resilient fallback: on timeout, EOF, or broken pipe, falls back to direct
      in-process execution and logs `MCP_STDIO_FALLBACK_TRIGGERED`.
    - Emits OpenTelemetry trace_event spans for tool execution telemetry.
    - Clean process teardown (terminate -> wait -> kill) with zero zombie processes.
    """
    def __init__(
        self,
        command: Optional[List[str]] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
    ):
        self.repo_root = Path(__file__).parent.parent.resolve()
        self.command = command or [sys.executable, "-m", "testforge.mcp_server", "protocol"]
        self.cwd = cwd or str(self.repo_root)
        base_env = os.environ.copy()
        base_env["PYTHONPATH"] = str(self.repo_root)
        if env:
            base_env.update(env)
        self.env = base_env
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._started = False
        self._closed = False

    def is_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def pid(self) -> Optional[int]:
        return self.process.pid if self.process else None

    def start(self) -> None:
        with self._lock:
            if self.is_alive():
                return
            self._closed = False
            try:
                self.process = subprocess.Popen(
                    self.command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    env=self.env,
                    text=True,
                    bufsize=1,
                )
                self._started = True
                self._handshake()
            except Exception as e:
                logger.error(f"Failed to start FastMCP stdio subprocess: {e}")
                self.close()

    def _handshake(self) -> None:
        init_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "testforge-agent", "version": "1.0.0"},
            },
        }
        res = self._send_request_raw(init_req, timeout=5.0)
        if not res or "result" not in res:
            logger.warning(f"FastMCP stdio handshake failed: {res}")
            return
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        self._send_notification_raw(notif)

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _send_notification_raw(self, payload: Dict[str, Any]) -> None:
        if not self.is_alive() or not self.process or not self.process.stdin:
            return
        line = json.dumps(payload) + "\n"
        try:
            self.process.stdin.write(line)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def _send_request_raw(self, payload: Dict[str, Any], timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if not self.is_alive() or not self.process or not self.process.stdin or not self.process.stdout:
            return None
        t_out = timeout or self.timeout
        line = json.dumps(payload) + "\n"
        try:
            self.process.stdin.write(line)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            logger.warning(f"Failed to write to FastMCP stdio: {e}")
            return None

        # Wait for response using select
        try:
            rlist, _, _ = select.select([self.process.stdout], [], [], t_out)
        except (ValueError, OSError) as e:
            logger.warning(f"Select error on FastMCP stdio: {e}")
            return None

        if not rlist:
            logger.warning(f"FastMCP stdio read timed out after {t_out}s")
            return None

        try:
            resp_line = self.process.stdout.readline()
        except (BrokenPipeError, OSError) as e:
            logger.warning(f"Read error on FastMCP stdio: {e}")
            return None

        if not resp_line:
            logger.warning("FastMCP stdio received EOF from server")
            return None

        try:
            return json.loads(resp_line.strip())
        except Exception as e:
            logger.warning(f"FastMCP stdio invalid JSON response: {e}")
            return None

    def list_tools(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        with self._lock:
            if not self.is_alive() and not self._closed:
                self.start()
            req = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/list",
                "params": {},
            }
            res = self._send_request_raw(req, timeout=timeout)
            if res and "result" in res and "tools" in res["result"]:
                return res["result"]["tools"]
            # Fallback tool definitions
            return [
                {"name": "mcp_ast_symbol_analyzer", "description": "AST Symbol Analysis"},
                {"name": "mcp_mutant_generator", "description": "Mutant Generation Engine"},
                {"name": "mcp_sandbox_runner", "description": "Isolated Sandbox Runner"},
                {"name": "mcp_equivalence_classifier", "description": "Equivalence Classifier"},
            ]

    def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> ToolResultDict:
        start_time = time.time()
        args = arguments or {}

        with self._lock:
            if not self.is_alive() and not self._started and not self._closed:
                self.start()

            res: Optional[Dict[str, Any]] = None
            if self.is_alive() and not self._closed:
                req = {
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/call",
                    "params": {"name": name, "arguments": args},
                }
                res = self._send_request_raw(req, timeout=timeout)

        duration_ms = (time.time() - start_time) * 1000.0

        if res is not None and "result" in res:
            result_obj = res["result"]
            data = None
            if "content" in result_obj and isinstance(result_obj["content"], list):
                content_list = result_obj["content"]
                if len(content_list) == 1:
                    raw_text = content_list[0].get("text", "") if isinstance(content_list[0], dict) else str(content_list[0])
                    try:
                        data = json.loads(raw_text)
                    except Exception:
                        data = raw_text
                elif len(content_list) > 1:
                    data = []
                    for item in content_list:
                        raw = item.get("text", "") if isinstance(item, dict) else str(item)
                        try:
                            data.append(json.loads(raw))
                        except Exception:
                            data.append(raw)
                else:
                    data = []
            else:
                data = result_obj

            if name == "mcp_mutant_generator" and isinstance(data, dict):
                data = [data]

            try:
                from testforge.observability import trace_event
                trace_event("mcp.tool_call", {
                    "tool": name,
                    "transport": "stdio",
                    "duration_ms": duration_ms,
                    "status": "success",
                })
            except Exception:
                pass

            return ToolResultDict(tool_name=name, success=True, data=data, error=None, duration_ms=duration_ms)

        # Fallback triggered
        logger.warning(f"MCP_STDIO_FALLBACK_TRIGGERED: FastMCP stdio call failed for '{name}'. Falling back to in-process execution.")
        try:
            from testforge.observability import trace_event
            trace_event("MCP_STDIO_FALLBACK_TRIGGERED", {
                "tool": name,
                "transport": "in_process_fallback",
                "reason": "stdio_timeout_or_pipe_error",
            })
        except Exception:
            pass

        fallback_result = self._execute_in_process(name, args)
        fallback_duration_ms = (time.time() - start_time) * 1000.0
        fallback_result["duration_ms"] = fallback_duration_ms

        try:
            from testforge.observability import trace_event
            trace_event("mcp.tool_call", {
                "tool": name,
                "transport": "in_process_fallback",
                "duration_ms": fallback_duration_ms,
                "status": "success" if fallback_result.success else "error",
                "fallback": True,
            })
        except Exception:
            pass

        return fallback_result

    def call_tool_sync(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> ToolResultDict:
        return self.call_tool(name=tool_name, arguments=arguments, timeout=timeout)

    def _execute_in_process(self, name: str, arguments: Dict[str, Any]) -> ToolResultDict:
        from testforge.mcp_server import (
            mcp_ast_symbol_analyzer,
            mcp_mutant_generator,
            mcp_sandbox_runner,
            mcp_equivalence_classifier,
        )
        try:
            if name == "mcp_ast_symbol_analyzer":
                source = arguments.get("source_code") or arguments.get("code") or ""
                out = mcp_ast_symbol_analyzer(source_code=source)
                return ToolResultDict(tool_name=name, success=True, data=out, error=None)
            elif name == "mcp_mutant_generator":
                source = arguments.get("source_code") or arguments.get("code") or ""
                max_mutants = int(arguments.get("max_mutants", 30))
                out = mcp_mutant_generator(source_code=source, max_mutants=max_mutants)
                return ToolResultDict(tool_name=name, success=True, data=out, error=None)
            elif name == "mcp_sandbox_runner":
                test_suite = arguments.get("test_suite_code", "")
                target_src = arguments.get("target_source", "")
                timeout_sec = float(arguments.get("timeout_seconds", 3.0))
                out = mcp_sandbox_runner(
                    test_suite_code=test_suite,
                    target_source=target_src,
                    timeout_seconds=timeout_sec,
                )
                return ToolResultDict(tool_name=name, success=True, data=out, error=None)
            elif name == "mcp_equivalence_classifier":
                orig = arguments.get("original_source", "")
                mut = arguments.get("mutant_source", "")
                out = mcp_equivalence_classifier(original_source=orig, mutant_source=mut)
                return ToolResultDict(tool_name=name, success=True, data=out, error=None)
            else:
                return ToolResultDict(tool_name=name, success=False, data=None, error=f"Unknown tool: {name}")
        except Exception as e:
            return ToolResultDict(tool_name=name, success=False, data=None, error=str(e))

    def close(self) -> None:
        with self._lock:
            if self.process is not None:
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                except Exception:
                    pass
                try:
                    if self.process.stdout:
                        self.process.stdout.close()
                except Exception:
                    pass
                try:
                    if self.process.stderr:
                        self.process.stderr.close()
                except Exception:
                    pass
                try:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=1.0)
                except Exception:
                    pass
                finally:
                    self.process = None

    def disconnect_sync(self) -> None:
        self.close()

    def sync_to_blackboard(self, tool_result: Any, blackboard: Any) -> None:
        if not getattr(tool_result, "success", False) or not blackboard:
            return

    def __enter__(self) -> "FastMCPStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


def create_fastmcp_stdio_client(
    timeout: float = 10.0,
) -> FastMCPStdioClient:
    """
    Creates and returns a FastMCPStdioClient instance targeting the 4-tool protocol suite.
    """
    return FastMCPStdioClient(timeout=timeout)
