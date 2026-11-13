#!/usr/bin/env bash
# ==============================================================================
# TestForge: Final Evaluation Submission Packaging Script
# Creates TestForge_Submission.zip excluding cache, venv, and binary artifacts
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ZIP_NAME="TestForge_Submission.zip"
OUTPUT_ZIP="${ROOT_DIR}/${ZIP_NAME}"

echo "📦 Preparing TestForge Final Submission Package..."
cd "${ROOT_DIR}"

# 1. Verify required evaluation deliverables
REQUIRED_FILES=(
  "docs/DELIVERABLES/FINAL_15_SLIDE_DECK.md"
  "Dockerfile"
  "render.yaml"
  "deploy/cloudrun.sh"
  "server.py"
  "requirements.txt"
  "pyproject.toml"
  "testforge/crewai_agents.py"
  "testforge/orchestrator.py"
  "testforge/symbolic_solver.py"
  "testforge/dependency_resolver.py"
  "testforge/sandbox.py"
  "frontend/index.html"
  "frontend/app.js"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "❌ Error: Required file missing: $f"
    exit 1
  fi
done

echo "✅ All required evaluation deliverables verified."

# 2. Remove existing archive if present
rm -f "${OUTPUT_ZIP}"

# 3. Create zip archive with strict exclusion list
echo "🗜️ Packaging project files into ${ZIP_NAME}..."
zip -r "${OUTPUT_ZIP}" . \
  -x "*.venv*" \
  -x "*venv*" \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pytest_cache*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "*.DS_Store" \
  -x "*qa_artifacts/scratch_runs*" \
  -x "*scratch*" \
  -x "*brain*" \
  -x "testforge_trace.jsonl" \
  -x "*.sqlite*" \
  -x "${ZIP_NAME}" > /dev/null

ZIP_SIZE=$(du -h "${OUTPUT_ZIP}" | cut -f1)
echo "🎉 Successfully built submission archive: ${OUTPUT_ZIP} (${ZIP_SIZE})"
echo "📋 Summary of packaged deliverables:"
unzip -l "${OUTPUT_ZIP}" | grep -E "FINAL_15_SLIDE_DECK|Dockerfile|render.yaml|cloudrun.sh|crewai_agents.py|symbolic_solver.py" || true
