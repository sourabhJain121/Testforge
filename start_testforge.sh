#!/usr/bin/env bash
# ==============================================================================
# TestForge: Official Single-Command Application Launcher (FastAPI Only)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON="${SCRIPT_DIR}/.venv-release/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "[ERROR] Release virtual environment not found at ${VENV_PYTHON}."
    echo "Please ensure .venv-release is properly configured."
    exit 1
fi

echo "================================================================================"
echo "⚡ Starting TestForge Autonomous Agentic Test Hardening Cockpit"
echo "URL: http://127.0.0.1:8000/"
echo "Stack: HTML5 / CSS3 / Vanilla JS + FastAPI REST & WebSockets"
echo "Architecture: arm64 Apple Silicon Optimized"
echo "================================================================================"

exec "$VENV_PYTHON" -m uvicorn server:app --host 127.0.0.1 --port 8000

