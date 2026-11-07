"""
tests/test_sandbox_security_isolation.py - Security & OS Resource Isolation Tests for TestForge Sandbox.

Verifies:
  1. Environment scrubbing strips all credentials, API keys, and sensitive tokens.
  2. Sandboxed child subprocesses cannot read caller host secrets from os.environ.
  3. Sandboxed processes have HOME and TMPDIR quarantined to ephemeral sandbox paths.
  4. Graceful handling of infinite loops in measure_coverage without unhandled exceptions.
  5. POSIX preexec resource limit configuration.
"""

import os
import sys
import tempfile
import pytest

from testforge.sandbox import (
    ParallelSandboxRunner,
    build_sanitized_sandbox_env,
    get_sandbox_preexec_fn,
)


class TestSandboxSecurityIsolation:
    """Verifies that the execution sandbox strictly isolates the host environment."""

    def test_build_sanitized_sandbox_env_strips_secrets(self, monkeypatch):
        # Inject simulated sensitive keys into os.environ
        test_secrets = {
            "ANTHROPIC_API_KEY": "sk-ant-api-test-0123456789",
            "OPENAI_API_KEY": "sk-openai-secret-token",
            "GEMINI_API_KEY": "AIzaSyFakeGeminiToken123",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "DATABASE_PASSWORD": "SuperSecretPassword!",
            "GITHUB_TOKEN": "ghp_FakeGitHubPersonalAccessToken123",
            "MY_AUTH_CREDENTIAL": "credential_value",
            "PRIVATE_KEY_PATH": "/etc/ssl/private/key.pem",
        }
        for k, v in test_secrets.items():
            monkeypatch.setenv(k, v)

        with tempfile.TemporaryDirectory(prefix="test_iso_") as tmpdir:
            clean_env = build_sanitized_sandbox_env(tmpdir)

            # Assert all sensitive variables were stripped
            for k in test_secrets.keys():
                assert k not in clean_env, f"Sensitive env var '{k}' was not stripped from sandbox environment!"

            # Assert essential safe runtime keys exist
            assert "PATH" in clean_env
            assert "PYTHONPATH" in clean_env
            assert clean_env["PYTHONDONTWRITEBYTECODE"] == "1"
            assert clean_env["HOME"] == tmpdir
            assert clean_env["TMPDIR"] == tmpdir

    def test_sandboxed_subprocess_cannot_read_host_secret(self, monkeypatch):
        secret_name = "TESTFORGE_SIMULATED_SECRET_TOKEN"
        secret_val = "secret_value_that_must_never_leak_to_sandbox_42"
        monkeypatch.setenv(secret_name, secret_val)

        target_code = "def get_status(): return 'active'\n"
        test_code = f"""
import os
from target import get_status

def test_leak_attempt():
    secret = os.environ.get("{secret_name}")
    assert secret is None, f"Host secret leaked into sandbox subprocess: {{secret}}"
    assert get_status() == 'active'
"""
        runner = ParallelSandboxRunner(timeout_seconds=5)
        res = runner.run_single(test_code, target_code)

        assert res["status"] == "PASS", f"Test failed with: {res.get('stderr')}"
        assert res["tests_passed"] == 1
        assert res["exit_code"] == 0

    def test_sandboxed_subprocess_home_and_tmp_are_isolated(self):
        target_code = "def identity(x): return x\n"
        test_code = """
import os
import tempfile

def test_home_and_tmp_isolation():
    home = os.environ.get("HOME")
    tmp = os.environ.get("TMPDIR")
    # Verify neither HOME nor TMP points to standard user directory root
    assert home is not None
    assert tmp is not None
    assert "testforge_box_" in home or "testforge" in home or "tmp" in home.lower()
"""
        runner = ParallelSandboxRunner(timeout_seconds=5)
        res = runner.run_single(test_code, target_code)

        assert res["status"] == "PASS", f"Test failed with: {res.get('stderr')}"
        assert res["tests_passed"] == 1

    def test_measure_coverage_timeout_handled_gracefully(self):
        # Target code with infinite loop
        target_code = """
def infinite_loop_fn():
    while True:
        pass
"""
        test_code = """
from target import infinite_loop_fn

def test_call_infinite():
    infinite_loop_fn()
"""
        runner = ParallelSandboxRunner(timeout_seconds=1)  # 1s timeout
        pct, cov_info = runner.measure_coverage(test_code, target_code)

        assert pct == 0.0
        assert "timed out" in cov_info.get("raw_output", "").lower()

    def test_get_sandbox_preexec_fn_callable(self):
        preexec = get_sandbox_preexec_fn(timeout_seconds=5)
        if sys.platform != "win32":
            assert callable(preexec)
        else:
            assert preexec is None

    def test_sandboxed_subprocess_network_confinement_blocks_socket_connect(self):
        """Verifies that attempting an outbound socket connection inside the sandbox raises PermissionError (GAP-001)."""
        target_code = "def identity(x): return x\n"
        test_code = """
import socket
import pytest

def test_outbound_socket_blocked():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(PermissionError, match="Outbound network access is strictly prohibited inside the TestForge sandbox."):
        s.connect(("8.8.8.8", 53))
"""
        runner = ParallelSandboxRunner(timeout_seconds=5)
        res = runner.run_single(test_code, target_code, enforce_security=False)

        assert res["status"] == "PASS", f"Test failed with: {res.get('stderr')}"
        assert res["tests_passed"] == 1
        assert res["exit_code"] == 0

    def test_sandboxed_subprocess_network_confinement_blocks_dns_and_urllib(self):
        """Verifies that external DNS lookups and HTTP urlopen raise PermissionError inside the sandbox."""
        target_code = "def identity(x): return x\n"
        test_code = """
import socket
import urllib.request
import pytest

def test_external_dns_blocked():
    with pytest.raises(PermissionError, match="Outbound network access is strictly prohibited inside the TestForge sandbox."):
        socket.getaddrinfo("example.com", 80)

def test_external_urlopen_blocked():
    with pytest.raises(Exception) as exc_info:
        urllib.request.urlopen("http://example.com", timeout=2)
    err = str(exc_info.value)
    if exc_info.value.__cause__:
        err += " " + str(exc_info.value.__cause__)
    assert "Outbound network access is strictly prohibited" in err
"""
        runner = ParallelSandboxRunner(timeout_seconds=5)
        res = runner.run_single(test_code, target_code, enforce_security=False)

        assert res["status"] == "PASS", f"Test failed with: {res.get('stderr')}"
        assert res["tests_passed"] == 2
        assert res["exit_code"] == 0

