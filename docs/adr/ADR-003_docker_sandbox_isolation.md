# ADR-003: Subprocess & Real Docker Sandbox Isolation

## Status
Accepted

## Context
Evaluating untrusted LLM-generated test code and executing hundreds of mutated Python targets introduces serious security and stability hazards:
1. Infinite loops or recursive hangs caused by mutated loop conditions.
2. Accidental or malicious filesystem tampering (`os.remove`, overwriting repository files).
3. Network egress or data exfiltration during test execution.
4. Process exhaustion (fork bombs).

## Decision
We implemented a **Multi-Tier Sandboxing Architecture**:
1. **Tier 1: ProcessPool Subprocess Isolation**:
   - Each mutant evaluation runs in an isolated subprocess (`subprocess.Popen`) using temporary execution directories.
   - A strict 5.0-second execution timeout kills hung processes via SIGKILL.
   - Resource limits (`resource.setrlimit`) constrain maximum heap memory and CPU time.
2. **Tier 2: Real Docker Daemon Isolation (`testforge/docker_sandbox.py`)**:
   - When a Docker daemon is available, execution occurs inside an ephemeral container (`testforge:latest`).
   - The container is configured with `--network none` (disabling network egress), read-only root filesystems, and unprivileged user execution.
   - Real kernel verification confirmed that outbound socket creation raises `Errno 101 Network is unreachable`.
3. **Tier 3: Zero-Egress Privacy Mode (`testforge/privacy_mode.py`)**:
   - Enforces air-gapped isolation at the host OS level by intercepting `socket.socket.connect` and blocking non-loopback destinations while permitting local Ollama connections (`127.0.0.1:11434`).

## Consequences

### Positive
- Complete protection against runaway mutants and infinite loops.
- Deterministic test execution timing without cross-test state leakage.
- Flexible deployment: runs seamlessly on developer laptops via fast subprocesses while supporting hardened enterprise CI environments via Docker.

### Negative / Trade-offs
- Docker container spawning incurs slight process initialization latency (~100-200ms per batch), mitigated by executing tests in parallel worker batches.

