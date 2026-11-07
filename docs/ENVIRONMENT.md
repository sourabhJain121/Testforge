# TestForge Verification Environment Specification

## System & Host Details
- **Operating System:** macOS (Darwin arm64)
- **Kernel Version:** `Darwin Sourabhs-MacBook-Pro.local 27.2.0 Darwin Kernel Version 27.2.0 arm64`
- **Architecture:** Apple Silicon (arm64, M-series)
- **System Python (`/opt/homebrew/bin/python3`):** Python 3.15.2
- **Development & Verification Python (`/opt/homebrew/bin/python3.13` / `.venv-release/bin/python3`):** Python 3.13.18
- **Container Runtime:** Docker Desktop 29.4.3 (build `055a478`)

## Engine & Model Backends
- **Local Engine Backend:** Ollama (`qwen2.5-coder:7b`) serving on `http://127.0.0.1:11434`
- **Cloud Engine Backend:** Google Gemini API (`gemini-2.5-flash`) via `google-genai` SDK and direct REST fallback
- **ADK Agent Engine:** Google ADK `1.14.1` with native `ParallelAgent` and `LoopAgent` runners
- **Critic Agent Engine:** CrewAI `1.15.28` multi-agent deliberation framework

## Primary Python Environment (`.venv-release`)
Measured via `.venv-release/bin/pip list` on November 7, 2026:

| Package | Version | Role in TestForge |
|---|---|---|
| `python` | 3.13.18 | Target execution runtime |
| `google-adk` | 1.14.1 | Google ADK multi-agent primitives (`LlmAgent`, `ParallelAgent`, `LoopAgent`) |
| `google-genai` | 1.75.0 | Google Gemini official Python SDK |
| `crewai` | 1.15.28 | Multi-agent collaborative critic crews |
| `crewai-core` | 1.15.28 | Core abstractions for CrewAI |
| `fastapi` | 0.159.1 | REST, SSE, and WebSocket backend server |
| `uvicorn` | 0.54.0 | ASGI web server |
| `pytest` | 9.1.1 | Subprocess and test execution driver |
| `pytest-cov` | 7.1.0 | Coverage measurement pytest plugin |
| `coverage` | 7.16.2 | Deterministic line and branch coverage collector |
| `pydantic` | 2.12.5 | Schema modeling and contract validation |
| `pydantic-settings` | 2.16.1 | Settings and environment variable loader |
| `mcp` | 1.28.1 | Model Context Protocol v1 stdio server/client |
| `a2a-sdk` | 0.3.26 | Agent-to-Agent protocol communication SDK |
| `psutil` | 7.2.2 | Hardware acceleration and process monitoring |
| `httpx` | 0.28.1 | Async HTTP client for external APIs |
| `rich` | 14.3.4 | Terminal visualizer and table formatter |
| `playwright` | 1.64.1 | Headless browser QA automation |
| `ruff` | 0.8.0 | High-performance linter and code formatter |

## Packaging & Virtualenv Reproduction
- Package specification is declared in `pyproject.toml` (`[project]`).
- Minimum Python requirement: `requires-python = ">=3.11"`.
- Editable installation verified via:
  ```bash
  python3.13 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -e .
  testforge --help
  ```
