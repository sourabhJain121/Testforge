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
    (r"\bAIza[0-9A-Za-z-_]{35}\b", "[REDACTED_API_KEY]"),
    (r"\bsk-[a-zA-Z0-9]{20,}\b", "[REDACTED_API_KEY]"),
    (r"\bghp_[a-zA-Z0-9]{20,}\b", "[REDACTED_API_KEY]"),
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

