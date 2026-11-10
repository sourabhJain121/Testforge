"""
adk_engine.py - Agent Development Kit (ADK) Tool-Use & Deliberation Architecture.

Author: Sourabh & Shreshth
System: Autonomous Multi-Agent Hardening Engine

Features:
  - Standard Pydantic ADK Contracts:
      * ToolDefinition: Schema declaration (name, description, parameters schema)
      * ToolCallResult: Execution outcome (tool_name, success, output, error, latency)
      * ADKContext: Per-iteration deliberation context (memory, active tool, history)
  - Registered Core Executable Tools:
      1. tool_execute_sandbox: Sandboxed subprocess execution against target/mutant
      2. tool_compute_blast_radius: Static AST call-graph dependency and risk analysis
      3. tool_inspect_git_diff: Extraction of modified lines from working tree git diff
      4. tool_ast_audit: Surviving mutant failure diagnosis and diff inspection
  - Automatic Telemetry: Every tool invocation logs structured JSONL records
    into `testforge_trace.jsonl` under `event_type: "ADK_TOOL_CALL"`.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from testforge.blast_analyzer import BlastRadiusAnalyzer
from testforge.git_diff import GitDiffInspector
from testforge.logger import TraceLogger
from testforge.prompt_guard import verify_tool_call_safety
from testforge.sandbox import SubprocessSandbox


class ToolDefinition(BaseModel):
    """
    Standard ADK tool contract schema declaration.
    """
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolCallResult(BaseModel):
    """
    Standard outcome contract of an executed ADK tool.
    """
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    latency_sec: float = 0.0


class ADKContext(BaseModel):
    """
    Stateful deliberation context maintained across agent reflection steps.
    """
    iteration: int = 1
    active_tool: Optional[str] = None
    memory: Dict[str, Any] = Field(default_factory=dict)
    reflection_history: List[Dict[str, Any]] = Field(default_factory=list)


class ADKToolRegistry:
    """
    Central registry and dispatcher for ADK tools.
    Manages execution, argument validation, timing, and structured trace logging.
    """
    def __init__(self, logger: Optional[TraceLogger] = None):
        self.logger = logger
        self.tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._register_core_tools()

    def register_tool(self, definition: ToolDefinition, handler: Callable[..., Any]):
        """Registers a new tool contract and its executable handler."""
        self.tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        return self.tools.get(tool_name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self.tools.values())

    def _register_core_tools(self):
        # 1. tool_compute_blast_radius
        self.register_tool(
            ToolDefinition(
                name="tool_compute_blast_radius",
                description="Runs BlastRadiusAnalyzer to compute upstream callers, downstream callees, impacted ratio, and risk category.",
                parameters={
                    "type": "object",
                    "properties": {
                        "source_code": {"type": "string", "description": "Target Python source code"},
                        "target_function": {"type": "string", "description": "Specific function to inspect"}
                    },
                    "required": ["source_code"]
                }
            ),
            self._handle_compute_blast_radius
        )

        # 2. tool_inspect_git_diff
        self.register_tool(
            ToolDefinition(
                name="tool_inspect_git_diff",
                description="Retrieves modified and added line numbers from git diff using GitDiffInspector.",
                parameters={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "default": "."},
                        "target_file": {"type": "string", "description": "File path to inspect"}
                    }
                }
            ),
            self._handle_inspect_git_diff
        )

        # 3. tool_execute_sandbox
        self.register_tool(
            ToolDefinition(
                name="tool_execute_sandbox",
                description="Executes candidate test suite against code in an isolated subprocess sandbox with strict timeout guardrail.",
                parameters={
                    "type": "object",
                    "properties": {
                        "test_code": {"type": "string"},
                        "target_code": {"type": "string"},
                        "timeout_sec": {"type": "number", "default": 5.0}
                    },
                    "required": ["test_code", "target_code"]
                }
            ),
            self._handle_execute_sandbox
        )

        # 4. tool_ast_audit
        self.register_tool(
            ToolDefinition(
                name="tool_ast_audit",
                description="Audits surviving mutant diffs, diagnoses assertion gaps, and returns actionable feedback.",
                parameters={
                    "type": "object",
                    "properties": {
                        "surviving_diffs": {"type": "array", "items": {"type": "string"}},
                        "target_code": {"type": "string"}
                    },
                    "required": ["surviving_diffs"]
                }
            ),
            self._handle_ast_audit
        )

    def _handle_compute_blast_radius(self, source_code: str, target_function: str = "") -> Dict[str, Any]:
        return BlastRadiusAnalyzer.analyze_impact(target_function=target_function, source_code=source_code)

    def _handle_inspect_git_diff(self, repo_path: str = ".", target_file: Optional[str] = None) -> List[int]:
        return GitDiffInspector.get_modified_lines(repo_path=repo_path, target_file=target_file)

    def _handle_execute_sandbox(self, test_code: str, target_code: str, timeout_sec: float = 5.0) -> Dict[str, Any]:
        sandbox = SubprocessSandbox(timeout_seconds=timeout_sec)
        result = sandbox.run_single(test_code=test_code, target_code=target_code)
        return {
            "passed": result.passed,
            "exit_code": result.exit_code,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500],
            "timed_out": result.timed_out,
            "duration_ms": round(result.duration_seconds * 1000.0, 1)
        }

    def _handle_ast_audit(self, surviving_diffs: List[str], target_code: str = "") -> Dict[str, Any]:
        return {
            "surviving_count": len(surviving_diffs),
            "surviving_diffs_sample": surviving_diffs[:5],
            "summary": f"{len(surviving_diffs)} mutants survived previous test assertions."
        }

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[ADKContext] = None
    ) -> ToolCallResult:
        """
        Executes a registered tool by name with arguments, measures latency,
        updates ADKContext, and logs the execution under event_type: 'ADK_TOOL_CALL'.
        """
        start_time = time.perf_counter()
        if tool_name not in self._handlers:
            err = f"Unknown tool: '{tool_name}'. Available: {list(self.tools.keys())}"
            res = ToolCallResult(tool_name=tool_name, success=False, output=None, error=err, latency_sec=0.0)
            self._log_tool_call(tool_name, arguments, res, context)
            return res

        # Validate tool call safety against prompt injection attacks
        is_safe, sec_err = verify_tool_call_safety(tool_name, arguments, set(self.tools.keys()))
        if not is_safe:
            res = ToolCallResult(tool_name=tool_name, success=False, output=None, error=sec_err, latency_sec=0.0)
            self._log_tool_call(tool_name, arguments, res, context)
            return res

        handler = self._handlers[tool_name]
        try:
            output = handler(**arguments)
            latency = time.perf_counter() - start_time
            res = ToolCallResult(
                tool_name=tool_name,
                success=True,
                output=output,
                latency_sec=round(latency, 4)
            )
        except Exception as exc:
            latency = time.perf_counter() - start_time
            res = ToolCallResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=str(exc),
                latency_sec=round(latency, 4)
            )

        if context:
            context.active_tool = tool_name
            context.reflection_history.append({
                "tool": tool_name,
                "success": res.success,
                "latency_sec": res.latency_sec,
                "timestamp": time.time()
            })

        self._log_tool_call(tool_name, arguments, res, context)
        return res

    def _log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: ToolCallResult,
        context: Optional[ADKContext]
    ):
        if self.logger:
            # Truncate large string parameters in logs
            sanitized_args = {}
            for k, v in arguments.items():
                if isinstance(v, str) and len(v) > 300:
                    sanitized_args[k] = v[:300] + "..."
                elif isinstance(v, list) and len(v) > 10:
                    sanitized_args[k] = f"[{len(v)} items]"
                else:
                    sanitized_args[k] = v

            output_summary = result.output
            if isinstance(output_summary, dict) and "call_graph" in output_summary:
                output_summary = {k: v for k, v in output_summary.items() if k != "call_graph"}

            payload = {
                "tool_name": tool_name,
                "arguments": sanitized_args,
                "success": result.success,
                "error": result.error,
                "latency_seconds": result.latency_sec,
                "iteration": context.iteration if context else 1,
                "output_preview": str(output_summary)[:300] if output_summary is not None else None
            }
            self.logger.log_event(event_type="ADK_TOOL_CALL", data=payload)
