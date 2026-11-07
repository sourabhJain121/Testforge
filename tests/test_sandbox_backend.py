"""
test_sandbox_backend.py - Unit and Integration Tests for TestForge Sandbox Backends.

Tests:
  1. is_docker_available returns boolean without hanging.
  2. SubprocessSandboxBackend executes valid pytest commands.
  3. SubprocessSandboxBackend enforces timeouts on infinite loops.
  4. Backend factory selects correct backend class via TESTFORGE_SANDBOX.
  5. DockerSandboxBackend raises RuntimeError when Docker daemon is unreachable.
  6. Subprocess network conftest guard raises PermissionError on non-loopback connection.
  7. Docker backend real network isolation test (conditional on live Docker daemon).
"""

import os
import sys
import tempfile
import urllib.request

import pytest

from testforge.sandbox import (
    DockerSandboxBackend,
    SubprocessSandboxBackend,
    _run_single_test_task,
    get_sandbox_backend,
    is_docker_available,
    write_sandbox_network_guard,
)


def test_is_docker_available_returns_bool():
    """Verify is_docker_available executes quickly and returns a boolean."""
    avail = is_docker_available()
    assert isinstance(avail, bool)


def test_sandbox_backend_factory_selection(monkeypatch):
    """Verify backend factory selects correct subclass based on TESTFORGE_SANDBOX."""
    monkeypatch.delenv("TESTFORGE_SANDBOX", raising=False)
    backend_default = get_sandbox_backend()
    assert isinstance(backend_default, SubprocessSandboxBackend)

    monkeypatch.setenv("TESTFORGE_SANDBOX", "subprocess")
    backend_sub = get_sandbox_backend()
    assert isinstance(backend_sub, SubprocessSandboxBackend)

    monkeypatch.setenv("TESTFORGE_SANDBOX", "docker")
    backend_docker = get_sandbox_backend()
    assert isinstance(backend_docker, DockerSandboxBackend)


def test_subprocess_backend_executes_test():
    """Verify SubprocessSandboxBackend successfully executes passing test assertions."""
    target_code = "def add(a, b):\n    return a + b\n"
    test_code = "from target import add\ndef test_add():\n    assert add(2, 3) == 5\n"
    
    result = _run_single_test_task(test_code, target_code, timeout_seconds=5)
    assert result["status"] == "PASS"
    assert result["tests_passed"] == 1
    assert result["exit_code"] == 0
    assert result["timed_out"] is False


def test_subprocess_backend_timeout_guardrail():
    """Verify SubprocessSandboxBackend catches infinite loops via timeout."""
    target_code = "def loop_forever():\n    while True:\n        pass\n"
    test_code = "from target import loop_forever\ndef test_hang():\n    loop_forever()\n"
    
    result = _run_single_test_task(test_code, target_code, timeout_seconds=1)
    assert result["timed_out"] is True
    assert result["status"] == "TIMEOUT"
    assert result["exit_code"] == -1


def test_docker_backend_unreachable_raises(monkeypatch):
    """Verify DockerSandboxBackend raises RuntimeError when Docker daemon cannot be reached."""
    monkeypatch.setattr("testforge.sandbox.is_docker_available", lambda: False)
    backend = DockerSandboxBackend()
    
    with pytest.raises(RuntimeError) as exc_info:
        backend.run_command(["pytest"], cwd="/tmp", env={}, timeout=5)
    assert "Docker daemon is unreachable" in str(exc_info.value)


def test_subprocess_network_guard_conftest():
    """Verify write_sandbox_network_guard injects conftest that blocks outbound requests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conftest = write_sandbox_network_guard(tmpdir)
        assert os.path.exists(conftest)
        
        target_code = "def query_remote():\n    import urllib.request\n    return urllib.request.urlopen('http://example.com')\n"
        test_code = "import pytest\nfrom target import query_remote\ndef test_net():\n    with pytest.raises(PermissionError):\n        query_remote()\n"
        
        result = _run_single_test_task(test_code, target_code, timeout_seconds=5)
        assert result["status"] == "PASS"
        assert result["tests_passed"] == 1


@pytest.mark.skipif(not is_docker_available(), reason="Docker daemon is not running")
def test_docker_backend_network_isolation(monkeypatch):
    """Verify DockerSandboxBackend blocks network at kernel level (--network none)."""
    monkeypatch.setenv("TESTFORGE_SANDBOX", "docker")
    target_code = "def probe():\n    import urllib.request\n    urllib.request.urlopen('http://1.1.1.1', timeout=2)\n"
    test_code = "from target import probe\ndef test_probe():\n    probe()\n"
    
    result = _run_single_test_task(test_code, target_code, timeout_seconds=5)
    # Under docker --network none, network calls fail with URLError / network unreachable
    assert result["tests_failed"] > 0 or result["exit_code"] != 0
