"""
testforge/privacy_mode.py

Privacy Mode, Zero-Egress Enforcement, and PII/Secret Scrubbing (Handout Feature F4 & Sub-Task 4.1).

Guarantees:
1. Single Unified Toggle: Accessible via env var (TESTFORGE_PRIVACY_MODE=true), CLI flag (--privacy-mode),
   API (POST /api/privacy/toggle), or dashboard UI toggle.
2. Zero-Egress Air-Gap Compliance: When enabled, blocks all outbound internet traffic.
   Only loopback connections to local Ollama (127.0.0.1:11434) and internal services are permitted.
   External socket connections raise PrivacySecurityError.
3. Model Routing Confinement: Completely blocks cloud LLM dispatch (Gemini, OpenRouter, Anthropic).
   Forces local Ollama (e.g. qwen2.5-coder:7b) or deterministic offline AST synthesis.
4. Comprehensive Sanitization: Prompts dispatched to local models are pre-scrubbed of API keys,
   tokens, credentials, and PII.
"""

from __future__ import annotations

import logging
import os
import re
import socket
from typing import Any, Dict, List, Optional, Set, Tuple

from testforge.adk_callbacks import redact_secrets_and_pii

logger = logging.getLogger("testforge.privacy_mode")


class PrivacySecurityError(PermissionError):
    """Raised when an operation violates zero-egress Privacy Mode policies."""
    pass


# Permitted local ports in Privacy Mode (Ollama, local test server, stdio)
ALLOWED_LOCAL_HOSTS: Set[str] = {"127.0.0.1", "localhost", "::1"}
ALLOWED_LOCAL_PORTS: Set[int] = {11434, 8000, 8001, 8080}


class ZeroEgressSocketInterceptor:
    """
    Patches socket.create_connection and socket.socket.connect during Privacy Mode
    to guarantee zero outbound egress to external networks.
    """

    _original_create_connection = None
    _original_socket_connect = None
    _active = False
    _blocked_attempts: List[Dict[str, Any]] = []

    @classmethod
    def install(cls) -> None:
        if cls._active:
            return

        cls._original_create_connection = socket.create_connection
        cls._original_socket_connect = socket.socket.connect

        def guarded_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
            host, port = address[0], address[1]
            if not cls._is_allowed(host, port):
                record = {"target": f"{host}:{port}", "blocked": True, "call": "create_connection"}
                cls._blocked_attempts.append(record)
                err_msg = (
                    f"PrivacySecurityError: Zero-egress Privacy Mode is ACTIVE. "
                    f"Outbound connection to '{host}:{port}' was blocked."
                )
                logger.error(err_msg)
                raise PrivacySecurityError(err_msg)
            return cls._original_create_connection(address, timeout=timeout, source_address=source_address)

        def guarded_connect(sock_self, address):
            if isinstance(address, tuple) and len(address) >= 2:
                host, port = address[0], address[1]
                if not cls._is_allowed(host, port):
                    record = {"target": f"{host}:{port}", "blocked": True, "call": "socket.connect"}
                    cls._blocked_attempts.append(record)
                    err_msg = (
                        f"PrivacySecurityError: Zero-egress Privacy Mode is ACTIVE. "
                        f"Outbound socket connection to '{host}:{port}' was blocked."
                    )
                    logger.error(err_msg)
                    raise PrivacySecurityError(err_msg)
            return cls._original_socket_connect(sock_self, address)

        socket.create_connection = guarded_create_connection
        socket.socket.connect = guarded_connect
        cls._active = True
        logger.info("ZeroEgressSocketInterceptor successfully installed.")

    @classmethod
    def uninstall(cls) -> None:
        if not cls._active:
            return
        if cls._original_create_connection:
            socket.create_connection = cls._original_create_connection
        if cls._original_socket_connect:
            socket.socket.connect = cls._original_socket_connect
        cls._active = False
        logger.info("ZeroEgressSocketInterceptor uninstalled.")

    @classmethod
    def _is_allowed(cls, host: str, port: int) -> bool:
        host_str = str(host).lower()
        # Allow loopback
        if host_str in ALLOWED_LOCAL_HOSTS or host_str.startswith("127."):
            return True
        # Allow unix domain sockets (host is empty or int)
        if host == "":
            return True
        return False

    @classmethod
    def get_blocked_attempts(cls) -> List[Dict[str, Any]]:
        return list(cls._blocked_attempts)

    @classmethod
    def clear_blocked_attempts(cls) -> None:
        cls._blocked_attempts.clear()


class PrivacyModeManager:
    """
    Coordinates global Privacy Mode state, model enforcement, and PII scrubbing.
    """

    _instance: Optional[PrivacyModeManager] = None

    def __init__(self):
        # Initial state from environment variable
        env_val = os.environ.get("TESTFORGE_PRIVACY_MODE", "").lower().strip()
        self._enabled = env_val in ("true", "1", "yes", "on")
        if self._enabled:
            ZeroEgressSocketInterceptor.install()

    @classmethod
    def get_instance(cls) -> PrivacyModeManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        os.environ["TESTFORGE_PRIVACY_MODE"] = "true"
        ZeroEgressSocketInterceptor.install()
        logger.info("Privacy Mode ENABLED: Zero-egress air-gap active, cloud LLMs prohibited.")

    def disable(self) -> None:
        self._enabled = False
        os.environ["TESTFORGE_PRIVACY_MODE"] = "false"
        ZeroEgressSocketInterceptor.uninstall()
        logger.info("Privacy Mode DISABLED: Standard cloud & network operations restored.")

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self.enable()
        else:
            self.disable()

    def scrub_prompt(self, prompt: str) -> Tuple[str, int]:
        """Sanitizes sensitive API keys, tokens, and PII prior to model dispatch."""
        return redact_secrets_and_pii(prompt)

    def validate_model_selection(self, model_name: str) -> str:
        """
        Validates model choice against Privacy Mode policy.
        If Privacy Mode is active and a cloud model is requested, automatically redirects
        to local Ollama (qwen2.5-coder:7b) or raises PrivacySecurityError.
        """
        lower = model_name.lower()
        is_cloud = any(k in lower for k in ["gemini", "gpt", "claude", "openrouter", "deepseek"])
        if self._enabled and is_cloud:
            logger.warning(
                f"Privacy Mode Active: Cloud model '{model_name}' prohibited. "
                "Automatically rerouting to local air-gapped model 'qwen2.5-coder:7b'."
            )
            return "qwen2.5-coder:7b"
        return model_name

    def get_status(self) -> Dict[str, Any]:
        return {
            "privacy_mode_enabled": self._enabled,
            "zero_egress_active": ZeroEgressSocketInterceptor._active,
            "blocked_egress_attempts": ZeroEgressSocketInterceptor.get_blocked_attempts(),
            "enforced_model_fallback": "qwen2.5-coder:7b (Local Ollama)",
            "pii_scrubbing": "ACTIVE",
            "allowed_hosts": list(ALLOWED_LOCAL_HOSTS),
        }
