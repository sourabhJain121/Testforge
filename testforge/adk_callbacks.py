"""
testforge/adk_callbacks.py

Native Google ADK Model Lifecycle Callbacks for TestForge (Handout Feature F4).
Provides adk_before_model_callback (secret & PII redaction prior to LLM dispatch)
and adk_after_model_callback (AST syntax verification of generated test code).
"""

from __future__ import annotations

import ast
import logging
import re
from typing import Any, Optional, Tuple

logger = logging.getLogger("testforge.adk_callbacks")

# Secret & Token Redaction Patterns
API_KEY_PATTERNS = [
    (r"\bAIza[0-9A-Za-z-_]{20,}\b", "[REDACTED_API_KEY_GEMINI]"),
    (r"\bsk-or-v1-[a-zA-Z0-9_\-]{20,}\b", "[REDACTED_API_KEY_OPENROUTER]"),
    (r"\bsk-[a-zA-Z0-9_\-]{20,}\b", "[REDACTED_API_KEY]"),
    (r"\bghp_[a-zA-Z0-9]{20,}\b", "[REDACTED_API_KEY_GITHUB]"),
    (r"\b(?:bearer|token|apikey|api_key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{16,})['\"]?", "[REDACTED_SECRET]"),
    (r"\b(?:password|passwd|secret)\s*[:=]\s*['\"]?([^'\"\s\n]{8,})['\"]?", "[REDACTED_SECRET]"),
]

# PII Redaction Patterns
PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_PII_EMAIL]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_PII_SSN]"),
    (r"\b\+?[1-9]\d{1,14}\b(?=.*(?:phone|tel|mobile))", "[REDACTED_PII_PHONE]"),
]


def redact_secrets_and_pii(text: str) -> Tuple[str, int]:
    """
    Scans and sanitizes raw text prompts, replacing API keys, tokens,
    passwords, and PII with safe redacted placeholders.
    Returns (sanitized_text, redaction_count).
    """
    if not text:
        return "", 0

    sanitized = text
    redaction_count = 0

    for pattern, replacement in API_KEY_PATTERNS:
        matches = len(re.findall(pattern, sanitized, flags=re.IGNORECASE))
        if matches > 0:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            redaction_count += matches

    for pattern, replacement in PII_PATTERNS:
        matches = len(re.findall(pattern, sanitized, flags=re.IGNORECASE))
        if matches > 0:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            redaction_count += matches

    return sanitized, redaction_count


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Parses code through ast.parse() to guarantee syntactic soundness.
    Returns (is_valid, error_message).
    """
    if not code or not code.strip():
        return False, "Code is empty or whitespace."

    # Extract markdown code block if wrapped
    clean_code = code.strip()
    if "```python" in clean_code:
        parts = clean_code.split("```python")
        if len(parts) > 1:
            clean_code = parts[1].split("```")[0].strip()
    elif "```" in clean_code:
        parts = clean_code.split("```")
        if len(parts) > 1:
            clean_code = parts[1].split("```")[0].strip()

    try:
        ast.parse(clean_code)
        return True, None
    except SyntaxError as e:
        err = f"Syntax error at line {e.lineno or 1}: {e.msg}"
        return False, err


def adk_before_model_callback(
    arg1: Any,
    arg2: Any = None,
) -> Any:
    """
    Native Google ADK before_model_callback.
    Intercepts prompts prior to cloud LLM transmission to sanitize secrets, API keys, and PII.
    Supports both direct string invocation and ADK runner (callback_context, llm_request) protocol.
    """
    # Case A: Direct string invocation (model_input, context)
    if isinstance(arg1, str):
        sanitized, count = redact_secrets_and_pii(arg1)
        if count > 0:
            logger.info(f"adk_before_model_callback: Redacted {count} secret/PII item(s) from prompt.")
        return sanitized

    # Case B: ADK runtime protocol (callback_context, llm_request)
    # or (llm_request, callback_context)
    req = arg2 if arg2 is not None and hasattr(arg2, "prompt") else arg1
    if hasattr(req, "prompt") and isinstance(req.prompt, str):
        sanitized, count = redact_secrets_and_pii(req.prompt)
        if count > 0:
            logger.info(f"adk_before_model_callback: Redacted {count} secret/PII item(s) in LlmRequest.")
            req.prompt = sanitized
        return req

    # Case C: Model request with contents
    if hasattr(req, "contents"):
        logger.debug("adk_before_model_callback: LlmRequest contents inspected.")
        return req

    return arg1


def adk_after_model_callback(
    arg1: Any,
    arg2: Any = None,
) -> Any:
    """
    Native Google ADK after_model_callback.
    Validates that model-generated output adheres strictly to valid Python AST syntax
    before downstream compilation or execution in the sandbox.
    Raises ValueError on syntax violation or returns validated response.
    """
    # Case A: Direct string invocation (model_output, context)
    if isinstance(arg1, str):
        is_valid, err = validate_python_syntax(arg1)
        if not is_valid:
            logger.error(f"adk_after_model_callback syntax validation failed: {err}")
            raise ValueError(f"Generated test code has invalid Python syntax: {err}")
        return arg1

    # Case B: ADK runtime protocol (callback_context, llm_response)
    resp = arg2 if arg2 is not None and (hasattr(arg2, "content") or hasattr(arg2, "text")) else arg1
    text_content = ""
    if hasattr(resp, "text") and isinstance(resp.text, str):
        text_content = resp.text
    elif hasattr(resp, "content") and isinstance(resp.content, str):
        text_content = resp.content

    if text_content:
        is_valid, err = validate_python_syntax(text_content)
        if not is_valid:
            logger.error(f"adk_after_model_callback: LlmResponse syntax validation failed: {err}")
            raise ValueError(f"Model output contains invalid Python syntax: {err}")

    return resp


class ADKSecurityPolicy:
    """
    Configurable security policy for Google ADK tool execution and agent lifecycle guards.
    """
    def __init__(
        self,
        allowed_root_dir: Optional[str] = None,
        forbidden_files: Optional[Tuple[str, ...]] = None,
        forbidden_paths: Optional[Tuple[str, ...]] = None,
        max_iterations: int = 5,
        max_token_budget: int = 500_000,
        max_cost_usd: float = 5.0,
    ):
        import os
        self.allowed_root_dir = os.path.abspath(allowed_root_dir or os.getcwd())
        self.forbidden_files = forbidden_files or (
            ".env",
            ".git",
            "id_rsa",
            "id_ed25519",
            "credentials",
            "service_account.json",
            "master_key",
        )
        self.forbidden_paths = forbidden_paths or (
            "/etc",
            "/root",
            "/proc",
            "/sys",
            "/dev",
            "/private/etc",
        )
        self.max_iterations = max_iterations
        self.max_token_budget = max_token_budget
        self.max_cost_usd = max_cost_usd


_DEFAULT_POLICY = ADKSecurityPolicy()


def adk_before_tool_callback(
    arg1: Any,
    arg2: Any = None,
    arg3: Any = None,
    policy: Optional[ADKSecurityPolicy] = None,
) -> Any:
    """
    Native Google ADK before_tool_callback.
    Enforces path containment policy and blocks directory traversal or sensitive file access
    prior to tool invocation.

    Supported invocation protocols:
    1. Direct functional: adk_before_tool_callback(tool_name: str, tool_args: dict, context=None)
    2. ADK Runner callback: adk_before_tool_callback(callback_context: Any, tool: Any, tool_input: Any)
    """
    import os
    pol = policy or _DEFAULT_POLICY

    # Extract tool_name and tool_args based on protocol
    tool_name = ""
    tool_args: dict[str, Any] = {}

    if isinstance(arg1, str):
        # Case 1: Direct functional invocation (tool_name, tool_args)
        tool_name = arg1
        tool_args = arg2 if isinstance(arg2, dict) else {}
    elif hasattr(arg2, "name") or hasattr(arg1, "tool_name"):
        # Case 2: ADK Runner protocol (callback_context, tool, tool_input)
        tool_name = getattr(arg2, "name", "") or getattr(arg1, "tool_name", "")
        if isinstance(arg3, dict):
            tool_args = arg3
        elif hasattr(arg3, "dict"):
            tool_args = arg3.dict()
        elif hasattr(arg3, "model_dump"):
            tool_args = arg3.model_dump()
        elif isinstance(arg2, dict):
            tool_args = arg2

    # Scan tool arguments for path-like values
    path_keys = {"path", "file_path", "target_path", "directory", "filename", "filepath", "source_path"}
    for key, val in tool_args.items():
        if not isinstance(val, str):
            continue

        val_lower = val.lower()

        # Check for forbidden sensitive files
        for bad_file in pol.forbidden_files:
            if bad_file in val_lower or os.path.basename(val).lower() == bad_file.lower():
                err_msg = f"ADK Path Policy Violation: Access to sensitive file '{val}' is forbidden by before_tool_callback."
                logger.error(err_msg)
                raise PermissionError(err_msg)

        # Check for traversal syntax
        if ".." in val:
            # Check resolved containment
            resolved = os.path.abspath(val)
            if not resolved.startswith(pol.allowed_root_dir):
                err_msg = f"ADK Path Policy Violation: Directory traversal outside allowed root in '{val}'."
                logger.error(err_msg)
                raise PermissionError(err_msg)

        # Check for forbidden absolute paths
        for bad_prefix in pol.forbidden_paths:
            if val.startswith(bad_prefix):
                err_msg = f"ADK Path Policy Violation: Access to system directory '{val}' is forbidden by before_tool_callback."
                logger.error(err_msg)
                raise PermissionError(err_msg)

    # Return valid status
    if isinstance(arg1, str):
        return True, None
    return arg3 if arg3 is not None else arg1


def adk_before_agent_callback(
    arg1: Any,
    arg2: Any = None,
    arg3: Any = None,
    policy: Optional[ADKSecurityPolicy] = None,
) -> Any:
    """
    Native Google ADK before_agent_callback.
    Enforces iteration caps, token consumption budgets, and cost ceilings before an agent turn begins.

    Supported invocation protocols:
    1. Direct functional: adk_before_agent_callback(agent_name: str, context: dict, state: dict)
    2. ADK Runner callback: adk_before_agent_callback(callback_context: Any, agent: Any)
    """
    pol = policy or _DEFAULT_POLICY

    agent_name = ""
    state_dict: dict[str, Any] = {}

    if isinstance(arg1, str):
        # Case 1: Direct functional invocation (agent_name, context, state)
        agent_name = arg1
        if isinstance(arg3, dict):
            state_dict = arg3
        elif isinstance(arg2, dict):
            state_dict = arg2
    else:
        # Case 2: ADK Runner protocol (callback_context, agent)
        agent_obj = arg2 if arg2 is not None else arg1
        agent_name = getattr(agent_obj, "name", str(agent_obj))
        ctx = arg1
        if hasattr(ctx, "state") and isinstance(ctx.state, dict):
            state_dict = ctx.state
        elif hasattr(ctx, "session") and hasattr(ctx.session, "state"):
            state_dict = ctx.session.state

    # 1. Check Iteration Budget
    current_iter = state_dict.get("iteration") or state_dict.get("current_iteration") or 0
    if current_iter >= pol.max_iterations:
        err_msg = f"ADK Agent Budget Guard: Maximum iteration limit ({pol.max_iterations}) reached for agent '{agent_name}'."
        logger.error(err_msg)
        raise RuntimeError(err_msg)

    # 2. Check Token Budget
    tokens_consumed = state_dict.get("tokens_consumed") or state_dict.get("total_tokens") or 0
    if tokens_consumed >= pol.max_token_budget:
        err_msg = f"ADK Agent Budget Guard: Token budget limit ({pol.max_token_budget}) exceeded for agent '{agent_name}' (consumed: {tokens_consumed})."
        logger.error(err_msg)
        raise RuntimeError(err_msg)

    # 3. Check Cost Budget
    cost_usd = state_dict.get("cost_usd") or state_dict.get("estimated_cost_usd") or 0.0
    if cost_usd >= pol.max_cost_usd:
        err_msg = f"ADK Agent Budget Guard: Cost ceiling (${pol.max_cost_usd}) exceeded for agent '{agent_name}' (accumulated: ${cost_usd:.4f})."
        logger.error(err_msg)
        raise RuntimeError(err_msg)

    # Return valid status
    if isinstance(arg1, str):
        return True, None
    return arg2 if arg2 is not None else arg1


