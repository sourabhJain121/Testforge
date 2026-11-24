"""
sandbox.py - Multiprocess Sandboxed Test Execution Runtime.

Author: Shreshth (Module 2)
System: Autonomous Multi-Agent Hardening Engine

Features:
  - Subprocess isolation in ephemeral temporary directories
  - Strict timeout enforcement (5s default) to guard against mutation infinite loops
  - Parallel batch execution across CPU cores via ProcessPoolExecutor
  - Hardware tuned for Apple Silicon M2 Pro (10 cores)
  - Pytest & pytest-cov execution with JSON coverage extraction
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import types
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from testforge.accel import hw_profile
from testforge.equivalence import EquivalenceClassification, EquivalentMutantAnalyzer
from testforge.state import MutantRecord


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """
    Parses pytest console output to distinguish real test assertion failures from
    infrastructure/import/syntax errors.
    """
    collected_m = re.search(r"collected\s+(\d+)\s+item", stdout)
    collected = int(collected_m.group(1)) if collected_m else 0

    passed_m = re.search(r"(\d+)\s+passed", stdout)
    passed = int(passed_m.group(1)) if passed_m else 0

    failed_m = re.search(r"(\d+)\s+failed", stdout)
    failed = int(failed_m.group(1)) if failed_m else 0

    errors_m = re.search(r"(\d+)\s+error", stdout)
    errors = int(errors_m.group(1)) if errors_m else 0

    # Distinguish execution/infrastructure errors (ImportError, ModuleNotFoundError, SyntaxError, collection error)
    combined = f"{stdout}\n{stderr}"
    has_exec_error = (
        (exit_code != 0 and collected == 0)
        or "ImportError" in combined
        or "ModuleNotFoundError" in combined
        or "SyntaxError" in combined
        or "IndentationError" in combined
        or exit_code in (2, 3, 4)
    )

    failure_type = "NONE"
    if exit_code == 0 and passed > 0:
        status = "PASS"
        failure_type = "SURVIVED"
    elif exit_code == 1 and failed > 0 and not has_exec_error:
        status = "FAIL"
        if "AssertionError" in combined or "assert " in combined:
            failure_type = "ASSERTION_FAIL"
        else:
            failure_type = "EXCEPTION_FAIL"
    elif exit_code == -1:
        status = "TIMEOUT"
        failure_type = "TIMEOUT"
    else:
        status = "ERROR"
        failure_type = "IMPORT_OR_SYNTAX_ERROR"

    return {
        "collected": collected,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "status": status,
        "has_exec_error": has_exec_error,
        "failure_type": failure_type,
    }


_SENSITIVE_ENV_SUBSTRINGS = (
    "KEY", "SECRET", "TOKEN", "PASSW", "CRED", "AUTH", "PRIVATE",
    "DATABASE", "AWS", "GENAI", "ANTHROPIC", "OPENAI", "GOOGLE", "AZURE"
)


def build_sanitized_sandbox_env(tmpdir: str, target_file_path: Optional[str] = None) -> Dict[str, str]:
    """
    Constructs a least-privilege, scrubbed environment dictionary for sandboxed test execution.
    Strips caller credentials, API keys, and sensitive tokens while preserving essential paths.
    """
    pythonpath_entries = [tmpdir]
    if target_file_path:
        target_abs = os.path.abspath(target_file_path)
        target_dir = os.path.dirname(target_abs)
        if os.path.isdir(target_dir):
            pythonpath_entries.append(target_dir)
    pythonpath_entries.append(os.getcwd())

    # Existing virtualenv and system paths
    base_path = os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
    virtual_env = os.path.dirname(os.path.dirname(sys.executable))

    sub_env: Dict[str, str] = {
        "PATH": base_path,
        "PYTHONPATH": os.pathsep.join(pythonpath_entries),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "VIRTUAL_ENV": virtual_env,
        "TMPDIR": tmpdir,
        "TEMP": tmpdir,
        "TMP": tmpdir,
        "HOME": tmpdir,
    }

    # Whitelisted safe OS environment variables to preserve platform stability
    safe_keys = {
        "SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR",
        "LANG", "LC_ALL", "LC_CTYPE", "TERM",
        "USER", "LOGNAME"
    }
    for k in safe_keys:
        if k in os.environ:
            sub_env[k] = os.environ[k]

    # Copy any existing non-sensitive env variables, rejecting anything matching sensitive keywords
    for k, v in os.environ.items():
        k_upper = k.upper()
        if any(substr in k_upper for substr in _SENSITIVE_ENV_SUBSTRINGS):
            continue  # Strictly scrub secrets, keys, and tokens
        if k not in sub_env and not k_upper.startswith("SSH_"):
            sub_env[k] = v

    # Final enforce: ensure HOME and TMPDIR remain isolated
    sub_env["HOME"] = tmpdir
    sub_env["TMPDIR"] = tmpdir
    return sub_env


def get_sandbox_preexec_fn(timeout_seconds: Optional[int] = None):
    """
    Returns a POSIX preexec callable that places the child process in a new process group
    and applies OS-level CPU and memory resource limits via the resource module.
    """
    if sys.platform == "win32":
        return None

    def _preexec():
        try:
            os.setsid()
        except Exception:
            pass
        try:
            import resource
            if timeout_seconds and hasattr(resource, "RLIMIT_CPU"):
                soft_cpu = max(int(timeout_seconds) + 4, 1)
                hard_cpu = max(int(timeout_seconds) + 6, 2)
                resource.setrlimit(resource.RLIMIT_CPU, (soft_cpu, hard_cpu))
            if hasattr(resource, "RLIMIT_AS"):
                max_as = 1536 * 1024 * 1024  # 1.5 GB memory cap
                resource.setrlimit(resource.RLIMIT_AS, (max_as, max_as))
        except Exception:
            pass

    return _preexec


_NETWORK_GUARD_CONFTEST = '''# TestForge Execution-Time Sandbox Network Confinement Guard (GAP-001)
import socket

_orig_socket_connect = socket.socket.connect
_orig_socket_connect_ex = socket.socket.connect_ex
_orig_create_connection = getattr(socket, "create_connection", None)
_orig_getaddrinfo = getattr(socket, "getaddrinfo", None)

def _is_loopback(address):
    if isinstance(address, (tuple, list)) and len(address) > 0:
        h = str(address[0]).lower().strip()
    elif isinstance(address, str):
        h = address.lower().strip()
    else:
        return False
    return h in ("127.0.0.1", "localhost", "::1", "0.0.0.0", "")

def _guarded_connect(self, address):
    if getattr(self, "family", None) == getattr(socket, "AF_UNIX", -999):
        return _orig_socket_connect(self, address)
    if not _is_loopback(address):
        raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")
    return _orig_socket_connect(self, address)

def _guarded_connect_ex(self, address):
    if getattr(self, "family", None) == getattr(socket, "AF_UNIX", -999):
        return _orig_socket_connect_ex(self, address)
    if not _is_loopback(address):
        raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")
    return _orig_socket_connect_ex(self, address)

def _guarded_create_connection(address, *args, **kwargs):
    if not _is_loopback(address):
        raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")
    if _orig_create_connection:
        return _orig_create_connection(address, *args, **kwargs)
    raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")

def _guarded_getaddrinfo(host, port, *args, **kwargs):
    if host and not _is_loopback(host):
        raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")
    if _orig_getaddrinfo:
        return _orig_getaddrinfo(host, port, *args, **kwargs)
    return []

socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
if _orig_create_connection:
    socket.create_connection = _guarded_create_connection
if _orig_getaddrinfo:
    socket.getaddrinfo = _guarded_getaddrinfo

try:
    import urllib.request
    _orig_urlopen = urllib.request.urlopen
    def _guarded_urlopen(url, *args, **kwargs):
        raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")
    urllib.request.urlopen = _guarded_urlopen
except Exception:
    pass

try:
    import http.client
    _orig_http_connect = http.client.HTTPConnection.connect
    def _guarded_http_connect(self):
        if not _is_loopback(self.host):
            raise PermissionError("Outbound network access is strictly prohibited inside the TestForge sandbox.")
        return _orig_http_connect(self)
    http.client.HTTPConnection.connect = _guarded_http_connect
except Exception:
    pass

# Prevent C-extension shadowing of pure Python target modules under test
try:
    import sys
    sys.modules["_bisect"] = None
except Exception:
    pass
'''


def write_sandbox_network_guard(tmpdir: str) -> str:
    """
    Injects an execution-time network confinement guard into the sandbox directory.
    Intercepts socket, urllib, and http connections so any outbound network connection
    attempt immediately raises PermissionError while preserving local loopback and UNIX sockets.
    """
    conftest_path = os.path.join(tmpdir, "conftest.py")
    mode = "a" if os.path.exists(conftest_path) else "w"
    with open(conftest_path, mode, encoding="utf-8") as f:
        f.write(_NETWORK_GUARD_CONFTEST)
    return conftest_path


def _populate_target_aliases(
    tmpdir: str,
    code: str,
    target_file_path: Optional[str] = None,
    companion_files: Optional[Dict[str, str]] = None
) -> None:
    """Writes target code to target.py, module name aliases, and materializes companion dependencies."""
    with open(os.path.join(tmpdir, "target.py"), "w", encoding="utf-8") as f:
        f.write(code)
    if target_file_path:
        base_name = os.path.basename(target_file_path)
        mod_name = os.path.splitext(base_name)[0]
        if mod_name != "target":
            with open(os.path.join(tmpdir, f"{mod_name}.py"), "w", encoding="utf-8") as f:
                f.write(code)
        parent_dir = os.path.dirname(target_file_path)
        if parent_dir and not os.path.isabs(parent_dir):
            clean_parent = os.path.normpath(parent_dir)
            if not clean_parent.startswith("..") and not os.path.isabs(clean_parent):
                target_sub = os.path.join(tmpdir, clean_parent)
                try:
                    os.makedirs(target_sub, exist_ok=True)
                    with open(os.path.join(target_sub, "__init__.py"), "w", encoding="utf-8") as f:
                        pass
                    with open(os.path.join(target_sub, base_name), "w", encoding="utf-8") as f:
                        f.write(code)
                except Exception:
                    pass

    # Materialize companion modules for multi-file dependency resolution in isolated sandbox
    if companion_files:
        abs_tmp = os.path.abspath(tmpdir)
        for rel_path, comp_code in companion_files.items():
            dest_file = os.path.normpath(os.path.join(tmpdir, rel_path))
            if not dest_file.startswith(abs_tmp):
                continue
            parent = os.path.dirname(dest_file)
            if parent:
                os.makedirs(parent, exist_ok=True)
                init_file = os.path.join(parent, "__init__.py")
                if not os.path.exists(init_file):
                    try:
                        with open(init_file, "w", encoding="utf-8") as init_f:
                            pass
                    except Exception:
                        pass
            try:
                with open(dest_file, "w", encoding="utf-8") as f:
                    f.write(comp_code)
            except Exception:
                pass


def is_docker_available() -> bool:
    """
    Returns True if Docker CLI is installed and the Docker daemon is responding.
    Enforces a strict 1.5s non-blocking timeout.
    """
    try:
        proc = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5
        )
        return proc.returncode == 0
    except Exception:
        return False


class SandboxBackend(ABC):
    """
    Abstract base class for sandboxed test execution backends.
    """
    @abstractmethod
    def run_command(
        self,
        cmd: List[str],
        cwd: str,
        env: Dict[str, str],
        timeout: float,
        preexec_fn: Optional[Any] = None
    ) -> Tuple[int, str, str, bool]:
        """
        Executes sandboxed test command.
        Returns: (exit_code, stdout, stderr, timed_out)
        """
        pass


class SubprocessSandboxBackend(SandboxBackend):
    """
    Local process-isolated sandbox backend (default).
    Enforces subprocess timeout, detached process group termination,
    least-privilege environment variable scrubbing, and python-level network monkeypatching.
    
    Known limitations:
      - Best-effort isolation (defense in depth), not a kernel-level hardware sandbox.
      - On macOS arm64, RLIMIT_AS (virtual memory limit) is not enforced by the Darwin kernel.
      - Network confinement via Python conftest.py prevents Python socket/urllib/http requests,
        but non-Python child binaries (e.g. spawned curl) are unconstrained without cgroups/Docker.
    """
    def run_command(
        self,
        cmd: List[str],
        cwd: str,
        env: Dict[str, str],
        timeout: float,
        preexec_fn: Optional[Any] = None
    ) -> Tuple[int, str, str, bool]:
        effective_timeout = min(timeout, 10.0) if timeout > 0 else 10.0
        run_kwargs: Dict[str, Any] = {
            "cwd": cwd,
            "env": env,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        if preexec_fn is not None:
            run_kwargs["preexec_fn"] = preexec_fn

        proc = None
        try:
            proc = subprocess.Popen(cmd, **run_kwargs)
            stdout, stderr = proc.communicate(timeout=effective_timeout)
            return proc.returncode, stdout, stderr, False
        except subprocess.TimeoutExpired:
            if proc:
                try:
                    if os.name == "posix":
                        try:
                            pgid = os.getpgid(proc.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        except (ProcessLookupError, PermissionError):
                            proc.kill()
                    else:
                        proc.kill()
                except Exception:
                    pass
                try:
                    proc.communicate(timeout=1.0)
                except Exception:
                    pass
            return -1, "", f"Subprocess timed out after {effective_timeout}s (Safety Guardrail: Infinite loop caught)", True
        except Exception as exc:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            return -2, "", str(exc), False


class DockerSandboxBackend(SandboxBackend):
    """
    Hardware-isolated Docker container sandbox backend.
    Enforces true Linux kernel namespaces, cgroups v2 limits (--memory 512m --cpus 1.0 --pids-limit 128),
    read-only root filesystem, dropped capabilities (--cap-drop ALL), and complete network isolation (--network none).
    """
    def __init__(self, image: Optional[str] = None):
        self.image = image or os.environ.get("TESTFORGE_DOCKER_IMAGE", "testforge:latest")

    def run_command(
        self,
        cmd: List[str],
        cwd: str,
        env: Dict[str, str],
        timeout: float,
        preexec_fn: Optional[Any] = None
    ) -> Tuple[int, str, str, bool]:
        if not is_docker_available():
            raise RuntimeError(
                "DockerSandboxBackend requested (TESTFORGE_SANDBOX=docker) but Docker daemon is unreachable. "
                "Ensure Docker Desktop or dockerd is running, or unset TESTFORGE_SANDBOX to use subprocess isolation."
            )

        abs_cwd = os.path.abspath(cwd)
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--read-only",
            "--memory", "512m",
            "--cpus", "1.0",
            "--pids-limit", "128",
            "--cap-drop", "ALL",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "-v", f"{abs_cwd}:/app:ro",
            "-w", "/app",
        ]

        for k in ("PYTHONPATH", "HOME", "TMPDIR"):
            if k in env:
                docker_cmd.extend(["-e", f"{k}={env[k]}"])

        # Translate host python executable to container python
        container_cmd = ["python" if c == sys.executable else c for c in cmd]
        full_cmd = docker_cmd + [self.image] + container_cmd

        try:
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return res.returncode, res.stdout, res.stderr, False
        except subprocess.TimeoutExpired:
            return -1, "", f"Docker container timed out after {timeout}s (Safety Guardrail: Infinite loop caught)", True
        except Exception as exc:
            return -2, "", str(exc), False


def get_sandbox_backend() -> SandboxBackend:
    """
    Factory creating the configured sandbox execution backend.
    Selectable via TESTFORGE_SANDBOX: 'subprocess' (default) or 'docker'.
    """
    backend_mode = os.environ.get("TESTFORGE_SANDBOX", "subprocess").lower().strip()
    if backend_mode == "docker":
        return DockerSandboxBackend()
    return SubprocessSandboxBackend()


def _evaluate_single_mutant_in_memory(
    test_code: str,
    mutated_code: str,
    target_file_path: Optional[str] = None,
    companion_files: Optional[Dict[str, str]] = None,
    timeout_seconds: float = 2.0
) -> Optional[Dict[str, Any]]:
    """
    Ultra-fast in-memory mutant evaluation avoiding cold subprocess/pytest startup overhead.
    Evaluates mutated module and executes test assertions directly in memory with infinite loop guards.
    Returns standard parsed result dict or None if fallback to subprocess sandbox is required.
    """
    if not test_code or not test_code.strip() or not mutated_code:
        return None

    # AST Syntax validation for mutated code: SyntaxError in mutant is an automatic kill
    try:
        mutant_ast = ast.parse(mutated_code)
    except (SyntaxError, IndentationError) as syn_err:
        return {
            "exit_code": 1,
            "stdout": "",
            "stderr": f"Mutant failed Python syntax compilation: {syn_err}",
            "status": "FAIL",
            "failure_type": "EXCEPTION_FAIL",
            "timed_out": False,
            "duration_ms": 0.2,
            "tests_collected": 1,
            "tests_passed": 0,
            "tests_failed": 1,
            "tests_errors": 0,
            "has_exec_error": False,
        }

    # If test code has syntax error, defer to standard runner
    try:
        test_ast = ast.parse(test_code)
    except (SyntaxError, IndentationError):
        return None

    # Determine module alias names
    mod_aliases = ["target"]
    if target_file_path:
        base_name = os.path.basename(target_file_path)
        stem = os.path.splitext(base_name)[0]
        if stem and stem != "target":
            mod_aliases.append(stem)

    all_keys = list(mod_aliases)
    if companion_files:
        for rel_p in companion_files:
            c_stem = os.path.splitext(os.path.basename(rel_p))[0]
            if c_stem:
                all_keys.append(c_stem)

    saved_modules = {k: sys.modules.get(k) for k in all_keys}
    start_time = time.perf_counter()

    try:
        # 1. Mount and compile mutated target module
        target_mod = types.ModuleType("target")
        target_mod.__file__ = target_file_path or "target.py"
        for alias in mod_aliases:
            sys.modules[alias] = target_mod

        # Mount companion modules if provided
        if companion_files:
            for rel_p, comp_code in companion_files.items():
                c_stem = os.path.splitext(os.path.basename(rel_p))[0]
                if c_stem:
                    c_mod = types.ModuleType(c_stem)
                    c_mod.__file__ = rel_p
                    sys.modules[c_stem] = c_mod
                    try:
                        exec(compile(comp_code, rel_p, "exec"), c_mod.__dict__)
                    except Exception:
                        pass

        try:
            exec(compile(mutant_ast, target_mod.__file__, "exec"), target_mod.__dict__)
        except Exception as exc:
            dur_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Mutant top-level evaluation raised {type(exc).__name__}: {exc}",
                "status": "FAIL",
                "failure_type": "EXCEPTION_FAIL",
                "timed_out": False,
                "duration_ms": max(0.1, dur_ms),
                "tests_collected": 1,
                "tests_passed": 0,
                "tests_failed": 1,
                "tests_errors": 0,
                "has_exec_error": False,
            }

        # 2. Compile and execute test suite module
        test_mod = types.ModuleType("test_target")
        test_mod.__file__ = "test_target.py"
        try:
            exec(compile(test_ast, "test_target.py", "exec"), test_mod.__dict__)
        except Exception as exc:
            dur_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Test suite import with mutant raised {type(exc).__name__}: {exc}",
                "status": "FAIL",
                "failure_type": "EXCEPTION_FAIL",
                "timed_out": False,
                "duration_ms": max(0.1, dur_ms),
                "tests_collected": 1,
                "tests_passed": 0,
                "tests_failed": 1,
                "tests_errors": 0,
                "has_exec_error": False,
            }

        # 3. Discover test callables
        test_callables = []
        for name, obj in test_mod.__dict__.items():
            if name.startswith("test_") and callable(obj):
                test_callables.append((name, obj))
            elif isinstance(obj, type) and name.startswith("Test"):
                try:
                    inst = obj()
                    for m_name in dir(inst):
                        if m_name.startswith("test_"):
                            m_val = getattr(inst, m_name)
                            if callable(m_val):
                                test_callables.append((f"{name}.{m_name}", m_val))
                except Exception:
                    return None

        if not test_callables:
            return None

        tests_passed = 0
        tests_failed = 0
        failure_type = "NONE"
        err_msg = ""

        # Step count infinite loop guard
        step_count = 0
        max_steps = int(timeout_seconds * 300_000)

        def _step_trace(frame, event, arg):
            nonlocal step_count
            step_count += 1
            if step_count > max_steps:
                raise TimeoutError("Execution step limit exceeded (Safety Guardrail: Infinite loop caught)")
            return _step_trace

        orig_trace = sys.gettrace()
        sys.settrace(_step_trace)
        try:
            for t_name, t_func in test_callables:
                try:
                    sig = inspect.signature(t_func)
                    if len(sig.parameters) > 0:
                        return None  # Parameterized or fixture test requires pytest runner
                    t_func()
                    tests_passed += 1
                except AssertionError as ae:
                    tests_failed += 1
                    failure_type = "ASSERTION_FAIL"
                    err_msg = f"AssertionError in {t_name}: {ae}"
                    break
                except TimeoutError as te:
                    dur_ms = (time.perf_counter() - start_time) * 1000.0
                    return {
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": str(te),
                        "status": "TIMEOUT",
                        "failure_type": "TIMEOUT",
                        "timed_out": True,
                        "duration_ms": max(0.1, dur_ms),
                        "tests_collected": len(test_callables),
                        "tests_passed": tests_passed,
                        "tests_failed": 0,
                        "tests_errors": 1,
                        "has_exec_error": False,
                    }
                except Exception as exc:
                    tests_failed += 1
                    failure_type = "EXCEPTION_FAIL"
                    err_msg = f"{type(exc).__name__} in {t_name}: {exc}"
                    break
        finally:
            sys.settrace(orig_trace)

        dur_ms = (time.perf_counter() - start_time) * 1000.0
        if tests_failed > 0:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": err_msg,
                "status": "FAIL",
                "failure_type": failure_type,
                "timed_out": False,
                "duration_ms": max(0.1, dur_ms),
                "tests_collected": len(test_callables),
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_errors": 0,
                "has_exec_error": False,
            }
        else:
            return {
                "exit_code": 0,
                "stdout": f"{tests_passed} passed",
                "stderr": "",
                "status": "PASS",
                "failure_type": "NONE",
                "timed_out": False,
                "duration_ms": max(0.1, dur_ms),
                "tests_collected": len(test_callables),
                "tests_passed": tests_passed,
                "tests_failed": 0,
                "tests_errors": 0,
                "has_exec_error": False,
            }
    except Exception:
        return None
    finally:
        for k, v in saved_modules.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def _apply_mutant_evaluation_result(
    mutant: MutantRecord,
    result: Dict[str, Any],
    baseline_passed: bool = True,
    covered_lines: Optional[Set[int]] = None
) -> None:
    """Applies the structured execution result dict to a MutantRecord instance."""
    mutant.is_executed = True
    mutant.stdout = result.get("stdout", "")
    mutant.stderr = result.get("stderr", "")
    mutant.execution_time_ms = result.get("duration_ms", 0.0)

    if not baseline_passed:
        mutant.status = "ERROR"
        mutant.kill_classification = "IMPORT_OR_SYNTAX_ERROR"
        mutant.equivalence_status = "UNKNOWN"
        mutant.equivalence_reason = "Baseline test suite failed; cannot evaluate mutant."
    elif result.get("timed_out") or result.get("status") in ("TIMEOUT", "TIMED_OUT"):
        mutant.status = "TIMEOUT"
        mutant.kill_classification = "TIMEOUT"
        mutant.equivalence_status = "NOT_EQUIVALENT"
        mutant.equivalence_confidence = "HIGH"
        mutant.equivalence_reason = "Execution timed out in sandbox (infinite loop or hang)."
    elif result.get("has_exec_error") or result.get("status") == "ERROR":
        mutant.status = "ERROR"
        mutant.kill_classification = "IMPORT_OR_SYNTAX_ERROR"
        mutant.equivalence_status = "NOT_EQUIVALENT"
        mutant.equivalence_confidence = "HIGH"
        mutant.equivalence_reason = "Subprocess suffered execution or environment error."
    elif result.get("status") == "FAIL" and result.get("tests_failed", 0) > 0:
        if covered_lines is not None and getattr(mutant, "line_number", None) not in covered_lines:
            mutant.status = "SURVIVED"
            mutant.kill_classification = "UNCOVERED"
            mutant.equivalence_status = "NOT_EQUIVALENT"
            mutant.equivalence_confidence = "HIGH"
            mutant.equivalence_reason = f"Mutant on line {mutant.line_number} was not in executed statements (uncovered line); kill rejected."
        else:
            mutant.status = "KILLED"
            fail_type = result.get("failure_type", "ASSERTION_FAIL")
            if fail_type == "EXCEPTION_FAIL":
                mutant.kill_classification = "EXCEPTION_FAIL"
                mutant.equivalence_reason = "Detected and killed by unhandled target exception."
            else:
                mutant.kill_classification = "ASSERTION_FAIL"
                mutant.equivalence_reason = "Detected and killed by failing test assertion."
            mutant.equivalence_status = "NOT_EQUIVALENT"
            mutant.equivalence_confidence = "HIGH"
    elif result.get("status") == "PASS":
        mutant.kill_classification = "SURVIVED"
        eq_res = EquivalentMutantAnalyzer.analyze_mutant(mutant)
        if eq_res.status == EquivalenceClassification.EQUIVALENT:
            mutant.status = "EQUIVALENT"
            mutant.equivalence_status = eq_res.status.value
            mutant.equivalence_method = eq_res.method.value
            mutant.equivalence_reason = eq_res.reason
            mutant.equivalence_confidence = eq_res.confidence.value
        elif eq_res.status == EquivalenceClassification.POTENTIALLY_EQUIVALENT:
            mutant.status = "POTENTIALLY_EQUIVALENT"
            mutant.equivalence_status = eq_res.status.value
            mutant.equivalence_method = eq_res.method.value
            mutant.equivalence_reason = eq_res.reason
            mutant.equivalence_confidence = eq_res.confidence.value
        else:
            mutant.status = "SURVIVED"
            mutant.equivalence_status = "UNKNOWN"
            mutant.equivalence_method = "NONE"
            mutant.equivalence_reason = eq_res.reason
            mutant.equivalence_confidence = "NONE"
    else:
        mutant.status = "ERROR"


def _run_single_test_task(
    test_code: str,
    target_code: str,
    timeout_seconds: int,
    enforce_security: bool = True,
    target_file_path: Optional[str] = None,
    companion_files: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Isolated worker function designed for ProcessPoolExecutor execution.
    Inspects test code against AST security policies before executing pytest in a sandbox directory.
    """
    start_time = time.perf_counter()
    eff_timeout = min(timeout_seconds, 10) if timeout_seconds > 0 else 10

    if enforce_security:
        from testforge.security import SecurityGuardrail
        sec_res = SecurityGuardrail().inspect_code_ast(test_code, enforce_policy=True)
        if not sec_res.allowed:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            violation_summary = "; ".join(f"[{v.rule_id}] {v.message}" for v in sec_res.violations)
            return {
                "exit_code": -3,
                "stdout": "",
                "stderr": f"Security Guardrail Blocked: {violation_summary}",
                "status": "SECURITY_BLOCKED",
                "timed_out": False,
                "duration_ms": elapsed_ms,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 1,
                "has_exec_error": True
            }

    # Fast in-memory evaluation path before allocating temporary filesystem directories
    fast_res = _evaluate_single_mutant_in_memory(
        test_code=test_code,
        mutated_code=target_code,
        target_file_path=target_file_path,
        companion_files=companion_files,
        timeout_seconds=eff_timeout
    )
    if fast_res is not None:
        return fast_res

    with tempfile.TemporaryDirectory(prefix="testforge_box_") as tmpdir:
        src_file = os.path.join(tmpdir, "target.py")
        test_file = os.path.join(tmpdir, "test_target.py")

        _populate_target_aliases(tmpdir, target_code, target_file_path, companion_files=companion_files)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        # Inject execution-time network confinement guard (GAP-001)
        write_sandbox_network_guard(tmpdir)

        # Build clean sanitized environment inheriting virtualenv and setting isolated PYTHONPATH
        sub_env = build_sanitized_sandbox_env(tmpdir, target_file_path=target_file_path)
        preexec = get_sandbox_preexec_fn(eff_timeout)

        # Use the virtualenv's python executable
        pytest_cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--disable-warnings", "-p", "no:cacheprovider"]

        backend = get_sandbox_backend()
        res_code, res_stdout, res_stderr, timed_out = backend.run_command(
            pytest_cmd,
            cwd=tmpdir,
            env=sub_env,
            timeout=eff_timeout,
            preexec_fn=preexec
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if timed_out:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Subprocess timed out after {eff_timeout}s (Safety Guardrail: Infinite loop caught)",
                "status": "TIMEOUT",
                "failure_type": "TIMEOUT",
                "timed_out": True,
                "duration_ms": elapsed_ms,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 1,
                "has_exec_error": False
            }

        parsed = parse_pytest_output(res_stdout, res_stderr, res_code)
        return {
            "exit_code": res_code,
            "stdout": res_stdout,
            "stderr": res_stderr,
            "status": parsed["status"],
            "failure_type": parsed.get("failure_type", "NONE"),
            "timed_out": False,
            "duration_ms": elapsed_ms,
            "tests_collected": parsed["collected"],
            "tests_passed": parsed["passed"],
            "tests_failed": parsed["failed"],
            "tests_errors": parsed["errors"],
            "has_exec_error": parsed["has_exec_error"]
        }


# Canonical alias for single mutant test execution
_run_single_mutant_test = _run_single_test_task


class ParallelSandboxRunner:
    """
    High-throughput sandboxed runner designed to maximize multi-core CPU throughput.
    """
    def __init__(
        self,
        timeout_seconds: int = 5,
        max_workers: Optional[int] = None,
        cancel_event: Optional[Any] = None,
        target_file_path: Optional[str] = None,
        companion_files: Optional[Dict[str, str]] = None
    ):
        self.timeout = timeout_seconds
        self.max_workers = max_workers or hw_profile.recommended_workers
        self.cancel_event = cancel_event
        self.target_file_path = target_file_path
        self.companion_files: Dict[str, str] = dict(companion_files or {})
        self.active_pids: Set[int] = set()
        self._executor: Optional[Any] = None

    def set_companion_files(self, companion_files: Dict[str, str]) -> None:
        """Dynamically registers or updates companion files to materialize in isolated sandbox."""
        self.companion_files = dict(companion_files or {})

    @property
    def active_processes(self) -> List[Any]:
        """Returns active worker process objects known to the executor pool."""
        if hasattr(self, "_executor") and self._executor is not None:
            procs = getattr(self._executor, "_processes", {})
            return list(procs.values())
        return []

    def terminate_all_workers(self) -> None:
        """
        Send SIGKILL to all active child PIDs.
        Clear the worker queue and shut down the executor pool without waiting.
        """
        current_pid = os.getpid()
        current_pgid = os.getpgrp() if os.name == "posix" else None

        if hasattr(self, "_executor") and self._executor is not None:
            procs = getattr(self._executor, "_processes", {})
            for pid, p in list(procs.items()):
                if pid == current_pid:
                    continue
                self.active_pids.add(pid)
                try:
                    if os.name == "posix":
                        try:
                            pgid = os.getpgid(pid)
                            if pgid != current_pgid:
                                os.killpg(pgid, signal.SIGKILL)
                            else:
                                os.kill(pid, signal.SIGKILL)
                        except (ProcessLookupError, PermissionError):
                            os.kill(pid, signal.SIGKILL)
                    else:
                        p.kill()
                except Exception:
                    pass
            try:
                self._executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
            self._executor = None

        for pid in list(self.active_pids):
            if pid == current_pid:
                self.active_pids.discard(pid)
                continue
            try:
                if os.name == "posix":
                    try:
                        pgid = os.getpgid(pid)
                        if pgid != current_pgid:
                            os.killpg(pgid, signal.SIGKILL)
                        else:
                            os.kill(pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        os.kill(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
            finally:
                self.active_pids.discard(pid)

    def run_single(
        self,
        test_code: str,
        target_code: str,
        target_file_path: Optional[str] = None,
        enforce_security: bool = True
    ) -> Dict[str, Any]:
        """Runs a single test synchronously (e.g. for baseline suite validation)."""
        if self.cancel_event and self.cancel_event.is_set():
            return {
                "exit_code": -4,
                "stdout": "",
                "stderr": "Execution cancelled before single test execution",
                "status": "CANCELLED",
                "cancelled": True,
                "timed_out": False,
                "duration_ms": 0.0,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 0,
                "has_exec_error": True
            }
        target_path = target_file_path or self.target_file_path
        return _run_single_test_task(
            test_code,
            target_code,
            self.timeout,
            enforce_security=enforce_security,
            target_file_path=target_path,
            companion_files=self.companion_files
        )

    def evaluate_mutants_parallel(
        self,
        test_code: str,
        mutants: List[MutantRecord],
        baseline_passed: bool = True,
        covered_lines: Optional[List[int]] = None
    ) -> List[MutantRecord]:
        """
        Runs the test suite against every mutant concurrently across CPU cores.
        Strict mutation testing contract: A mutant is ONLY marked KILLED if:
        1. Baseline clean tests passed
        2. Test suite actually executed against the mutant and failed an assertion or timed out.
        """
        if not mutants:
            return []

        if self.cancel_event and self.cancel_event.is_set():
            return mutants

        # Normalize any dict representations into MutantRecord instances
        coerced_mutants: List[MutantRecord] = []
        for item in mutants:
            if isinstance(item, MutantRecord):
                coerced_mutants.append(item)
            elif isinstance(item, dict):
                try:
                    coerced_mutants.append(MutantRecord(**item))
                except Exception:
                    coerced_mutants.append(MutantRecord(
                        mutant_id=item.get("mutant_id", "MUT"),
                        mutation_type=item.get("mutation_type", "AOR"),
                        line_number=item.get("line_number", 1),
                        original_code_snippet=item.get("original_code_snippet", ""),
                        mutated_code_snippet=item.get("mutated_code_snippet", ""),
                        unified_diff=item.get("unified_diff", item.get("diff", "")),
                        status=item.get("status", "PENDING"),
                        is_valid_syntax=item.get("is_valid_syntax", True),
                    ))
            else:
                coerced_mutants.append(item)
        mutants = coerced_mutants

        executable_mutants: List[MutantRecord] = []
        for m in mutants:
            is_valid = m.get("is_valid_syntax", True) if isinstance(m, dict) else getattr(m, "is_valid_syntax", True)
            m_status = m.get("status", "PENDING") if isinstance(m, dict) else getattr(m, "status", "PENDING")
            if not is_valid or m_status == "INVALID":
                if isinstance(m, dict):
                    m["status"] = "INVALID"
                    m["is_executed"] = False
                    m["equivalence_status"] = "NOT_EQUIVALENT"
                    m["equivalence_method"] = "NONE"
                    m["equivalence_confidence"] = "HIGH"
                    m["equivalence_reason"] = "Mutant rejected prior to execution: invalid Python AST syntax."
                else:
                    m.status = "INVALID"
                    m.is_executed = False
                    m.equivalence_status = "NOT_EQUIVALENT"
                    m.equivalence_method = "NONE"
                    m.equivalence_confidence = "HIGH"
                    m.equivalence_reason = "Mutant rejected prior to execution: invalid Python AST syntax."
            elif covered_lines is not None and getattr(m, "line_number", None) not in covered_lines:
                # Consistency check: mutant line was never executed by test suite
                if isinstance(m, dict):
                    m["status"] = "SURVIVED"
                    m["is_executed"] = False
                    m["kill_classification"] = "UNCOVERED"
                    m["equivalence_status"] = "NOT_EQUIVALENT"
                    m["equivalence_confidence"] = "HIGH"
                    m["equivalence_reason"] = f"Mutant on line {m.get('line_number')} was not in executed statements (uncovered line); survives without execution."
                else:
                    m.status = "SURVIVED"
                    m.is_executed = False
                    m.kill_classification = "UNCOVERED"
                    m.equivalence_status = "NOT_EQUIVALENT"
                    m.equivalence_confidence = "HIGH"
                    m.equivalence_reason = f"Mutant on line {m.line_number} was not in executed statements (uncovered line); survives without execution."
            else:
                executable_mutants.append(m)

        if not executable_mutants:
            return mutants

        # Strict evaluation contract: If baseline tests failed on clean reference code,
        # mutants CANNOT be evaluated or killed.
        if not baseline_passed:
            for m in executable_mutants:
                m.status = "ERROR"
                m.is_executed = False
                m.equivalence_status = "UNKNOWN"
                m.equivalence_method = "NONE"
                m.equivalence_confidence = "NONE"
                m.equivalence_reason = "Baseline clean test suite failed; cannot evaluate or kill mutants."
            return mutants

        # If no test code is provided, mutants survive by default
        if not test_code or not test_code.strip():
            for m in executable_mutants:
                m.status = "SURVIVED"
                m.is_executed = False
                m.equivalence_status = "UNKNOWN"
                m.equivalence_method = "NONE"
                m.equivalence_confidence = "NONE"
                m.equivalence_reason = "No test assertions provided; mutant survives by default."
            return mutants

        # Enforce unyielding hard timeout per mutant (max 10s)
        mutant_timeout = min(self.timeout, 10.0) if self.timeout > 0 else 10.0

        # High-performance in-memory batch pre-pass: evaluates mutants without subprocess spawning overhead
        remaining_mutants: List[MutantRecord] = []
        completed_count = 0
        total_count = len(executable_mutants)

        for m in executable_mutants:
            if self.cancel_event and self.cancel_event.is_set():
                break
            fast_res = _evaluate_single_mutant_in_memory(
                test_code=test_code,
                mutated_code=m.mutated_code_snippet,
                target_file_path=self.target_file_path,
                companion_files=self.companion_files,
                timeout_seconds=mutant_timeout
            )
            if fast_res is not None:
                _apply_mutant_evaluation_result(m, fast_res, baseline_passed, covered_lines)
                completed_count += 1
                try:
                    from testforge.websocket_hub import global_websocket_hub
                    global_websocket_hub.broadcast_event({
                        "event_type": "PIPELINE_TELEMETRY",
                        "phase": "EXECUTING",
                        "stage": "MUTANT_EVALUATION",
                        "detail": f"Evaluating mutant {completed_count}/{total_count} (fast memory sandbox)...",
                        "current": completed_count,
                        "total": total_count,
                        "percent": round((completed_count / total_count) * 100) if total_count > 0 else 0,
                        "mutant": {
                            "mutant_id": m.mutant_id,
                            "status": m.status,
                            "mutation_type": m.mutation_type,
                            "line_number": m.line_number,
                            "exec_duration_ms": m.execution_time_ms,
                            "diff": getattr(m, "diff", "") or getattr(m, "unified_diff", "")
                        }
                    })
                except Exception:
                    pass
            else:
                remaining_mutants.append(m)

        if not remaining_mutants or (self.cancel_event and self.cancel_event.is_set()):
            return mutants

        # Bounded batch wait to protect orchestrator loop from indefinite deadlocks
        batch_timeout = max(20.0, (len(remaining_mutants) * mutant_timeout) / max(1, self.max_workers) + 15.0)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            self._executor = executor
            for pid in getattr(executor, "_processes", {}):
                self.active_pids.add(pid)

            future_to_mutant = {
                executor.submit(
                    _run_single_test_task,
                    test_code,
                    m.mutated_code_snippet,
                    int(mutant_timeout),
                    True,
                    self.target_file_path,
                    self.companion_files
                ): m for m in remaining_mutants
            }

            for pid in getattr(executor, "_processes", {}):
                self.active_pids.add(pid)

            try:
                for future in as_completed(future_to_mutant, timeout=batch_timeout):
                    if self.cancel_event and self.cancel_event.is_set():
                        # Hard process-level cancellation and executor termination
                        self.terminate_all_workers()
                        for f in future_to_mutant:
                            if not f.done():
                                f.cancel()
                        break
                    mutant = future_to_mutant[future]
                    completed_count += 1
                    try:
                        result = future.result(timeout=mutant_timeout + 2.0)
                        _apply_mutant_evaluation_result(mutant, result, baseline_passed, covered_lines)
                    except (TimeoutError, subprocess.TimeoutExpired):
                        mutant.is_executed = True
                        mutant.status = "TIMEOUT"
                        mutant.kill_classification = "TIMEOUT"
                        mutant.equivalence_status = "NOT_EQUIVALENT"
                        mutant.equivalence_confidence = "HIGH"
                        mutant.equivalence_reason = "Mutant evaluation timed out (caught by per-mutant timeout guard)."
                    except Exception as exc:
                        mutant.status = "ERROR"
                        mutant.stderr = str(exc)

                    # Real-time sub-step telemetry broadcast per evaluated mutant
                    try:
                        from testforge.websocket_hub import global_websocket_hub
                        global_websocket_hub.broadcast_event({
                            "event_type": "PIPELINE_TELEMETRY",
                            "phase": "EXECUTING",
                            "stage": "MUTANT_EVALUATION",
                            "detail": f"Evaluating mutant {completed_count}/{total_count} in isolated sandbox...",
                            "current": completed_count,
                            "total": total_count,
                            "percent": round((completed_count / total_count) * 100) if total_count > 0 else 0,
                            "mutant": {
                                "mutant_id": mutant.mutant_id,
                                "status": mutant.status,
                                "mutation_type": mutant.mutation_type,
                                "line_number": mutant.line_number,
                                "exec_duration_ms": mutant.execution_time_ms,
                                "diff": getattr(mutant, "diff", "") or getattr(mutant, "unified_diff", "")
                            }
                        })
                    except Exception:
                        pass
            except TimeoutError:
                for f, m in future_to_mutant.items():
                    if not f.done():
                        f.cancel()
                        m.is_executed = True
                        m.status = "TIMEOUT"
                        m.kill_classification = "TIMEOUT"
                        m.equivalence_status = "NOT_EQUIVALENT"
                        m.equivalence_confidence = "HIGH"
                        m.equivalence_reason = "Mutant batch execution timed out (deadlock guardrail)."
            finally:
                self._executor = None

        return mutants

    def measure_coverage(self, test_code: str, target_code: str, target_file_path: Optional[str] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Executes pytest-cov inside the sandbox and parses coverage percentage and statement counts.
        """
        target_path = target_file_path or self.target_file_path
        with tempfile.TemporaryDirectory(prefix="testforge_cov_") as tmpdir:
            src_file = os.path.join(tmpdir, "target.py")
            test_file = os.path.join(tmpdir, "test_target.py")
            cov_json_path = os.path.join(tmpdir, "cov.json")

            _populate_target_aliases(tmpdir, target_code, target_path, companion_files=self.companion_files)

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)

            # Inject execution-time network confinement guard (GAP-001)
            write_sandbox_network_guard(tmpdir)

            sub_env = build_sanitized_sandbox_env(tmpdir, target_file_path=target_path)
            preexec = get_sandbox_preexec_fn(self.timeout)

            mod_name = os.path.splitext(os.path.basename(target_path))[0] if target_path else "target"
            cov_module = mod_name if mod_name != "target" else "target"
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=target",
                "--cov=samples",
                f"--cov={cov_module}",
                "--cov-branch",
                f"--cov-report=json:{cov_json_path}",
                test_file,
                "-p", "no:cacheprovider"
            ]

            backend = get_sandbox_backend()
            res_code, res_stdout, res_stderr, timed_out = backend.run_command(
                cmd,
                cwd=tmpdir,
                env=sub_env,
                timeout=self.timeout,
                preexec_fn=preexec
            )

            if timed_out:
                cov_info = {
                    "percent_covered": 0.0,
                    "line_coverage_pct": 0.0,
                    "covered_lines": 0,
                    "num_statements": 0,
                    "missing_lines": 0,
                    "branch_coverage_percent": 0.0,
                    "branch_coverage": 0.0,
                    "total_branches": 0,
                    "covered_branches": 0,
                    "missing_branches_count": 0,
                    "missing_branches": [],
                    "executed_branches": [],
                    "executed_lines": [],
                    "baseline_passed": False,
                    "exit_code": -1,
                    "raw_output": f"Coverage measurement timed out after {self.timeout}s (Safety Guardrail)"
                }
                return 0.0, cov_info

            baseline_passed = (res_code == 0) and not timed_out
            cov_info = {
                "percent_covered": 0.0,
                "line_coverage_pct": 0.0,
                "covered_lines": 0,
                "num_statements": 0,
                "missing_lines": 0,
                "branch_coverage_percent": 0.0,
                "branch_coverage": 0.0,
                "total_branches": 0,
                "covered_branches": 0,
                "missing_branches_count": 0,
                "missing_branches": [],
                "executed_branches": [],
                "executed_lines": [],
                "baseline_passed": baseline_passed,
                "exit_code": res_code,
                "raw_output": res_stdout or res_stderr
            }

            if os.path.exists(cov_json_path):
                try:
                    with open(cov_json_path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        files = data.get("files", {})

                        # Target File Disambiguation:
                        # Avoid aggregating alias files created in tmpdir (e.g. target.py and samples/target.py).
                        target_base = os.path.basename(target_path) if target_path else "target.py"
                        selected_file_meta = None

                        # Find candidates excluding __init__.py
                        non_init_files = [
                            (fname, fmeta) for fname, fmeta in files.items()
                            if not fname.endswith("__init__.py")
                        ]

                        # Preference 1: Non-init candidate that was executed (covered_lines > 0)
                        executed_candidates = [
                            (fname, fmeta) for fname, fmeta in non_init_files
                            if fmeta.get("summary", {}).get("covered_lines", 0) > 0
                        ]

                        if executed_candidates:
                            # Prefer target.py or basename match if multiple
                            matched = [
                                (fn, fm) for fn, fm in executed_candidates
                                if fn == "target.py" or os.path.basename(fn) == target_base
                            ]
                            selected_file_meta = matched[0][1] if matched else executed_candidates[0][1]
                        elif non_init_files:
                            # Preference 2: Non-init candidate matching target.py or basename
                            matched = [
                                (fn, fm) for fn, fm in non_init_files
                                if fn == "target.py" or os.path.basename(fn) == target_base
                            ]
                            selected_file_meta = matched[0][1] if matched else non_init_files[0][1]

                        if selected_file_meta:
                            f_summary = selected_file_meta.get("summary", {})
                            pct = float(f_summary.get("percent_statements_covered", f_summary.get("percent_covered", 0.0)))
                            cov_info["percent_covered"] = pct
                            cov_info["line_coverage_pct"] = pct
                            cov_info["covered_lines"] = int(f_summary.get("covered_lines", 0))
                            cov_info["num_statements"] = int(f_summary.get("num_statements", 0))
                            cov_info["missing_lines"] = int(f_summary.get("missing_lines", 0))
                            cov_info["executed_lines"] = selected_file_meta.get("executed_lines", [])

                            num_branches = int(f_summary.get("num_branches", 0))
                            covered_branches = int(f_summary.get("covered_branches", 0))
                            missing_branches_count = int(f_summary.get("missing_branches", 0))
                            branch_pct = float(f_summary.get("percent_branches_covered", round((covered_branches / num_branches * 100.0) if num_branches > 0 else 100.0, 2)))

                            cov_info["branch_coverage_percent"] = branch_pct
                            cov_info["branch_coverage"] = branch_pct
                            cov_info["total_branches"] = num_branches
                            cov_info["covered_branches"] = covered_branches
                            cov_info["missing_branches_count"] = missing_branches_count
                            cov_info["missing_branches"] = selected_file_meta.get("missing_branches", [])
                            cov_info["executed_branches"] = selected_file_meta.get("executed_branches", [])
                            return pct, cov_info
                        else:
                            # Fallback to totals if no non-init files entry
                            totals = data.get("totals", {})
                            pct = float(totals.get("percent_statements_covered", totals.get("percent_covered", 0.0)))
                            cov_info["percent_covered"] = pct
                            cov_info["line_coverage_pct"] = pct
                            cov_info["covered_lines"] = int(totals.get("covered_lines", 0))
                            cov_info["num_statements"] = int(totals.get("num_statements", 0))
                            cov_info["missing_lines"] = int(totals.get("missing_lines", 0))
                            cov_info["executed_lines"] = []

                            num_branches = int(totals.get("num_branches", 0))
                            covered_branches = int(totals.get("covered_branches", 0))
                            missing_branches_count = int(totals.get("missing_branches", 0))
                            branch_pct = round((covered_branches / num_branches * 100.0) if num_branches > 0 else 100.0, 2)

                            cov_info["branch_coverage_percent"] = branch_pct
                            cov_info["branch_coverage"] = branch_pct
                            cov_info["total_branches"] = num_branches
                            cov_info["covered_branches"] = covered_branches
                            cov_info["missing_branches_count"] = missing_branches_count
                            return pct, cov_info
                except Exception:
                    pass

            return 0.0, cov_info

    def validate_and_filter_candidate_suite(
        self,
        candidate_test_code: str,
        target_code: str,
        existing_test_code: Optional[str] = None,
        surviving_mutants: Optional[List[Any]] = None
    ) -> CandidateSuiteValidationResult:
        """
        Validates candidate test functions individually against clean target code so that
        one broken test does not force the entire candidate suite to be discarded.
        """
        validator = GranularTestValidator()
        return validator.validate_candidate_suite(
            candidate_test_code=candidate_test_code,
            target_code=target_code,
            sandbox_runner=self,
            timeout_seconds=self.timeout,
            existing_test_code=existing_test_code,
            surviving_mutants=surviving_mutants
        )


class TestValidationStatus:
    VALID = "VALID"
    FAILING = "FAILING"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    TRIVIAL_NO_ASSERTIONS = "TRIVIAL_NO_ASSERTIONS"
    REQUIRES_SUITE_CONTEXT = "REQUIRES_SUITE_CONTEXT"


@dataclass
class TestFunctionRecord:
    name: str
    code: str
    status: str
    reason: str = ""
    has_meaningful_assertions: bool = True
    duration_ms: float = 0.0
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    mutants_killed: List[str] = field(default_factory=list)


@dataclass
class CandidateSuiteValidationResult:
    overall_status: str
    total_candidates: int
    valid_tests: List[TestFunctionRecord] = field(default_factory=list)
    failing_tests: List[TestFunctionRecord] = field(default_factory=list)
    inconclusive_tests: List[TestFunctionRecord] = field(default_factory=list)
    trivial_tests: List[TestFunctionRecord] = field(default_factory=list)
    retained_test_code: str = ""
    retained_count: int = 0
    rejected_count: int = 0
    quarantined_count: int = 0
    error_message: Optional[str] = None
    summary: str = ""
    mutants_killed: List[str] = field(default_factory=list)


class GranularTestValidator:
    """
    AST-aware granular validator that inspects, extracts, and validates candidate
    test functions individually against unchanged original code so that one broken
    test does not force the entire candidate suite to be discarded.
    """

    @staticmethod
    def is_meaningful_assertion(node: ast.AST) -> bool:
        if isinstance(node, ast.Assert):
            test = node.test
            # Constant booleans / literals are trivial (e.g. assert True, assert 1, assert "ok")
            if isinstance(test, ast.Constant):
                return False
            # Negated constants (e.g. assert not False)
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                if isinstance(test.operand, ast.Constant):
                    return False
            return True
        return False

    @classmethod
    def has_meaningful_assertions(
        cls,
        func_node: ast.AST,
        helper_defs: Optional[Dict[str, ast.AST]] = None,
        visited_helpers: Optional[Set[str]] = None
    ) -> bool:
        """
        Validates that a test function contains substantive assertions, exception
        checks (pytest.raises / warns / self.assert*), or delegates verification to a
        custom assertion helper (e.g. assert_valid_order, verify_account).
        Preserves rejection of trivial tests and calls to ordinary non-assertion helpers.
        """
        if visited_helpers is None:
            visited_helpers = set()

        for n in ast.walk(func_node):
            if cls.is_meaningful_assertion(n):
                return True
            # Exception / warning checks via context manager: with pytest.raises(...):
            if isinstance(n, ast.With):
                for item in n.items:
                    ctx = item.context_expr
                    if isinstance(ctx, ast.Call):
                        func = ctx.func
                        if isinstance(func, ast.Attribute) and func.attr in ("raises", "warns"):
                            return True
                        elif isinstance(func, ast.Name) and func.id in ("raises", "warns"):
                            return True
            # unittest-style or object assertions: self.assertEqual, tester.assert_valid, etc.
            if isinstance(n, ast.Call):
                func = n.func
                if isinstance(func, ast.Attribute) and func.attr.startswith(("assert", "verify")):
                    return True
                # Standalone custom assertion helpers (addresses M-01)
                if isinstance(func, ast.Name):
                    fn_name = func.id
                    if fn_name.startswith(("assert_", "verify_")) or fn_name == "assert_never":
                        return True
                    # If helper is defined in module context, inspect helper body for assertions
                    if helper_defs and fn_name in helper_defs and fn_name not in visited_helpers:
                        visited_helpers.add(fn_name)
                        if cls.has_meaningful_assertions(
                            helper_defs[fn_name],
                            helper_defs=helper_defs,
                            visited_helpers=visited_helpers
                        ):
                            return True
        return False

    @staticmethod
    def split_test_module(test_code: str) -> Tuple[str, List[ast.AST], List[str]]:
        """
        Parses test module using AST, separating module context (imports, constants,
        fixtures, helpers, setup) from candidate test functions/classes.
        """
        warnings: List[str] = []
        tree = ast.parse(test_code)
        preamble_nodes: List[ast.AST] = []
        test_nodes: List[ast.AST] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Detect @pytest.fixture decorators
                is_fixture = any(
                    (isinstance(dec, ast.Name) and dec.id == "fixture") or
                    (isinstance(dec, ast.Attribute) and dec.attr == "fixture") or
                    (isinstance(dec, ast.Call) and isinstance(dec.func, (ast.Name, ast.Attribute)) and
                     getattr(dec.func, "id", getattr(dec.func, "attr", "")) == "fixture")
                    for dec in node.decorator_list
                )
                is_test_name = node.name.startswith("test_") or node.name.endswith("_test")
                if is_test_name and not is_fixture:
                    test_nodes.append(node)
                else:
                    preamble_nodes.append(node)
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    test_nodes.append(node)
                else:
                    preamble_nodes.append(node)
            else:
                preamble_nodes.append(node)

        preamble_mod = ast.Module(body=preamble_nodes, type_ignores=[])
        preamble_code = ast.unparse(preamble_mod).strip()
        return preamble_code, test_nodes, warnings

    @staticmethod
    def extract_pytest_test_statuses(stdout: str) -> Dict[str, str]:
        """
        Extracts individual test statuses from pytest console output.
        """
        statuses: Dict[str, str] = {}
        pattern = re.compile(
            r"(?:^|[\r\n])\S*?(?:test_\w+\.py|\w+\.py)::(?:(?P<class>\w+)::)?(?P<test>\w+)(?:\[.*?\])?\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED)"
        )
        for match in pattern.finditer(stdout):
            test_name = match.group("test")
            status = match.group("status")
            if test_name not in statuses or status in ("FAILED", "ERROR"):
                statuses[test_name] = status
        return statuses

    @classmethod
    def merge_test_suites(
        cls,
        existing_test_code: str,
        new_valid_test_code: str,
        target_code: str,
        sandbox_runner: Optional[ParallelSandboxRunner] = None
    ) -> str:
        """
        Safely merges existing accepted test suite with newly validated test functions.
        Ensures existing tests are preserved and merged suite passes against target code.
        """
        if not existing_test_code or not existing_test_code.strip():
            return new_valid_test_code
        if not new_valid_test_code or not new_valid_test_code.strip():
            return existing_test_code

        try:
            exist_tree = ast.parse(existing_test_code)
            cand_tree = ast.parse(new_valid_test_code)
        except Exception:
            return existing_test_code

        exist_tests: Dict[str, ast.AST] = {}
        exist_preamble: List[ast.AST] = []
        for n in exist_tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
                n.name.startswith("test_") or n.name.endswith("_test") or n.name.startswith("Test")
            ):
                exist_tests[n.name] = n
            else:
                exist_preamble.append(n)

        cand_tests: Dict[str, ast.AST] = {}
        cand_preamble: List[ast.AST] = []
        for n in cand_tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
                n.name.startswith("test_") or n.name.endswith("_test") or n.name.startswith("Test")
            ):
                cand_tests[n.name] = n
            else:
                cand_preamble.append(n)

        # Merge preambles avoiding duplicate imports/constants
        combined_preamble: List[ast.AST] = list(exist_preamble)
        existing_unparsed = {ast.unparse(n).strip() for n in exist_preamble}
        for n in cand_preamble:
            unparsed = ast.unparse(n).strip()
            if unparsed not in existing_unparsed:
                combined_preamble.append(n)
                existing_unparsed.add(unparsed)

        # Merge test functions (candidate tests augment/update existing suite)
        merged_tests = dict(exist_tests)
        for name, node in cand_tests.items():
            merged_tests[name] = node

        final_body = combined_preamble + list(merged_tests.values())
        merged_code = ast.unparse(ast.Module(body=final_body, type_ignores=[]))

        # Validate merged suite if sandbox is available
        if sandbox_runner:
            check = sandbox_runner.run_single(merged_code, target_code)
            if check["status"] == "PASS" and check.get("tests_passed", 0) > 0:
                return merged_code
            else:
                return existing_test_code

        return merged_code

    def validate_candidate_suite(
        self,
        candidate_test_code: str,
        target_code: str,
        sandbox_runner: Optional[ParallelSandboxRunner] = None,
        timeout_seconds: int = 5,
        existing_test_code: Optional[str] = None,
        surviving_mutants: Optional[List[Any]] = None
    ) -> CandidateSuiteValidationResult:
        """
        Executes granular validation on candidate test suite:
        1. Safely parses module via AST.
        2. Separates module context from candidate test functions.
        3. Identifies meaningful assertions and custom assertion helpers.
        4. Evaluates suite & individual tests against unchanged clean target code.
        5. Separates valid tests from failing/timeout/infrastructure errors.
        6. Retains valid tests while quarantining failing candidates.
        7. Optionally re-evaluates retained candidates against surviving mutants.
        """
        if not candidate_test_code or not candidate_test_code.strip():
            return CandidateSuiteValidationResult(
                overall_status="EMPTY_CANDIDATE",
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                summary="Candidate test code was empty. Existing suite retained."
            )

        # 1. AST Syntax Check
        try:
            preamble_code, test_nodes, _ = self.split_test_module(candidate_test_code)
        except SyntaxError as exc:
            return CandidateSuiteValidationResult(
                overall_status=TestValidationStatus.SYNTAX_ERROR,
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                quarantined_count=1,
                error_message=f"SyntaxError at line {exc.lineno}: {exc.msg}",
                summary=f"Candidate suite rejected due to SyntaxError at line {exc.lineno}."
            )
        except Exception as exc:
            return CandidateSuiteValidationResult(
                overall_status=TestValidationStatus.SYNTAX_ERROR,
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                quarantined_count=1,
                error_message=f"AST Parse Error: {str(exc)}",
                summary="Candidate suite rejected due to AST parse error."
            )

        total_candidates = len(test_nodes)
        if total_candidates == 0:
            return CandidateSuiteValidationResult(
                overall_status="NO_TESTS_FOUND",
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                summary="No candidate test functions found in module."
            )

        runner = sandbox_runner or ParallelSandboxRunner(timeout_seconds=timeout_seconds)

        # Extract helper function definitions from preamble and existing suite context
        helper_defs: Dict[str, ast.AST] = {}
        try:
            if preamble_code:
                p_tree = ast.parse(preamble_code)
                for n in p_tree.body:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        helper_defs[n.name] = n
        except Exception:
            pass
        try:
            if existing_test_code:
                e_tree = ast.parse(existing_test_code)
                for n in e_tree.body:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if n.name not in helper_defs:
                            helper_defs[n.name] = n
        except Exception:
            pass

        # 2. Fast Path: Run full candidate suite against clean target
        full_run = runner.run_single(candidate_test_code, target_code)

        # Infrastructure / Collection error check (e.g. missing import, module not found)
        if full_run.get("has_exec_error") and full_run.get("tests_collected", 0) == 0:
            inconclusive = [
                TestFunctionRecord(
                    name=getattr(node, "name", "unknown"),
                    code=ast.unparse(node),
                    status=TestValidationStatus.INFRASTRUCTURE_ERROR,
                    reason=full_run.get("stderr") or full_run.get("stdout") or "Collection error in candidate module"
                )
                for node in test_nodes
            ]
            return CandidateSuiteValidationResult(
                overall_status=TestValidationStatus.INFRASTRUCTURE_ERROR,
                total_candidates=total_candidates,
                inconclusive_tests=inconclusive,
                retained_test_code=existing_test_code or "",
                retained_count=0,
                rejected_count=0,
                quarantined_count=total_candidates,
                error_message=full_run.get("stderr") or "Infrastructure error during test collection",
                summary=f"Candidate suite collection failed due to infrastructure error ({full_run.get('stderr', '').strip()[:80]}). Existing suite preserved."
            )

        # Parse per-test results from stdout if available
        suite_statuses = self.extract_pytest_test_statuses(full_run.get("stdout", ""))

        valid_records: List[TestFunctionRecord] = []
        failing_records: List[TestFunctionRecord] = []
        inconclusive_records: List[TestFunctionRecord] = []
        trivial_records: List[TestFunctionRecord] = []
        valid_nodes: List[ast.AST] = []

        # 3. Granular Inspection & Validation of Candidate Tests
        for node in test_nodes:
            test_name = getattr(node, "name", "unknown")
            is_async = isinstance(node, ast.AsyncFunctionDef)
            node_code = ast.unparse(node)
            decorators = [ast.unparse(d) for d in getattr(node, "decorator_list", [])]

            # Assertion quality screening (including custom assertion helper resolution)
            if not self.has_meaningful_assertions(node, helper_defs=helper_defs):
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.TRIVIAL_NO_ASSERTIONS,
                    reason="Test contains no substantive assertions or exception checks.",
                    has_meaningful_assertions=False,
                    is_async=is_async,
                    decorators=decorators
                )
                trivial_records.append(rec)
                continue

            # Check if full suite already passed completely
            if full_run["status"] == "PASS" and full_run.get("tests_failed", 0) == 0:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.VALID,
                    reason="Verified in clean candidate suite execution.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                valid_records.append(rec)
                valid_nodes.append(node)
                continue

            # Check if this test passed in the full suite run
            if suite_statuses.get(test_name) == "PASSED":
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.VALID,
                    reason="Passed in module context during suite run.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                valid_records.append(rec)
                valid_nodes.append(node)
                continue

            # Otherwise, evaluate test individually in isolated context
            isolated_module = f"{preamble_code}\n\n{node_code}" if preamble_code else node_code
            iso_res = runner.run_single(isolated_module, target_code)

            if iso_res.get("timed_out"):
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.TIMEOUT,
                    reason=f"Isolated execution timed out after {timeout_seconds}s.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                inconclusive_records.append(rec)
            elif iso_res.get("has_exec_error") or iso_res.get("status") == "ERROR":
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.INFRASTRUCTURE_ERROR,
                    reason=iso_res.get("stderr") or "Execution/import error in isolated test.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                inconclusive_records.append(rec)
            elif iso_res.get("status") == "FAIL" and iso_res.get("tests_failed", 0) > 0:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.FAILING,
                    reason=iso_res.get("stderr") or iso_res.get("stdout") or "Failed assertion against clean code.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                failing_records.append(rec)
            elif iso_res.get("status") == "PASS" and iso_res.get("tests_passed", 0) > 0:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.VALID,
                    reason="Passed clean target check in isolated execution.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                valid_records.append(rec)
                valid_nodes.append(node)
            else:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.FAILING,
                    reason=iso_res.get("stderr") or "Unverified test outcome.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                failing_records.append(rec)

        # 4. Reassemble Retained Valid Tests
        retained_code = ""
        if valid_nodes:
            candidate_retained_mod = f"{preamble_code}\n\n" + "\n\n".join(ast.unparse(n) for n in valid_nodes)
            reassemble_check = runner.run_single(candidate_retained_mod, target_code)
            if reassemble_check.get("status") == "PASS" and reassemble_check.get("tests_passed", 0) > 0:
                retained_code = candidate_retained_mod
            else:
                retained_code = existing_test_code or ""

        # Merge with existing suite if existing code is provided
        if existing_test_code and existing_test_code.strip():
            if retained_code:
                merged = self.merge_test_suites(
                    existing_test_code=existing_test_code,
                    new_valid_test_code=retained_code,
                    target_code=target_code,
                    sandbox_runner=runner
                )
                retained_code = merged
            else:
                retained_code = existing_test_code

        # 5. Re-evaluate retained tests against surviving mutants to verify differentiation/killing
        killed_mutant_ids: List[str] = []
        if surviving_mutants and retained_code:
            for m in surviving_mutants:
                mut_code = m.get("mutated_code_snippet") if isinstance(m, dict) else getattr(m, "mutated_code_snippet", None)
                mut_id = m.get("mutant_id", "unknown") if isinstance(m, dict) else getattr(m, "mutant_id", "unknown")
                if mut_code:
                    mut_run = runner.run_single(retained_code, mut_code)
                    if mut_run.get("status") == "FAIL" or mut_run.get("tests_failed", 0) > 0:
                        killed_mutant_ids.append(mut_id)

        retained_count = len(valid_records)
        quarantined_count = len(failing_records) + len(trivial_records) + len(inconclusive_records)

        if retained_count == total_candidates:
            overall_status = "ALL_VALID"
        elif retained_count > 0:
            overall_status = "PARTIALLY_VALID"
        else:
            overall_status = "ALL_FAILED"

        summary = (
            f"Validated {total_candidates} candidate test(s): {retained_count} valid, "
            f"{len(failing_records)} failing, {len(trivial_records)} trivial, "
            f"{len(inconclusive_records)} inconclusive."
        )
        if killed_mutant_ids:
            summary += f" Distinguished/killed {len(killed_mutant_ids)} surviving mutant(s)."

        return CandidateSuiteValidationResult(
            overall_status=overall_status,
            total_candidates=total_candidates,
            valid_tests=valid_records,
            failing_tests=failing_records,
            inconclusive_tests=inconclusive_records,
            trivial_tests=trivial_records,
            retained_test_code=retained_code,
            retained_count=retained_count,
            rejected_count=len(failing_records),
            quarantined_count=quarantined_count,
            summary=summary,
            mutants_killed=killed_mutant_ids
        )


# Alias for ADK and single-process usage
SubprocessSandbox = ParallelSandboxRunner
