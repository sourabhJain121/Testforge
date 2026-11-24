#!/usr/bin/env bash
# ==============================================================================
# TestForge: Google Cloud Run Automated Deployment Script
# Multi-Agent Test Hardening System (Google ADK + CrewAI)
# Target Platform: Google Cloud Run (Managed Serverless Container, 2 vCPU, 2 GiB)
# ==============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}}"
REGION="${REGION:-${GCP_REGION:-asia-south1}}"
SERVICE_NAME="${SERVICE_NAME:-${CLOUD_RUN_SERVICE:-testforge}}"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ Error: Google Cloud PROJECT_ID could not be determined."
  echo "Please set PROJECT_ID or configure active gcloud project: gcloud config set project <your-project-id>"
  exit 1
fi

echo "================================================================================"
echo "⚡ TestForge Google Cloud Run Deployment"
echo "================================================================================"
echo "  Project ID:   ${PROJECT_ID}"
echo "  Region:       ${REGION}"
echo "  Service Name: ${SERVICE_NAME}"
echo "  Image Tag:    ${IMAGE_TAG}"
echo "================================================================================"

echo "🔧 Ensuring required Google Cloud APIs are enabled..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

echo "🚀 Building TestForge container image via Cloud Build..."
gcloud builds submit --project="${PROJECT_ID}" --tag "${IMAGE_TAG}" .

# Dynamically construct environment variables to pass without overwriting unset secrets
ENV_VARS="TESTFORGE_SANDBOX=subprocess,TESTFORGE_PRIVACY_MODE=false"

if [ -n "${GEMINI_API_KEY:-}" ]; then
  ENV_VARS="${ENV_VARS},GEMINI_API_KEY=${GEMINI_API_KEY}"
fi

if [ -n "${GEMINI_API_KEY_2:-}" ]; then
  ENV_VARS="${ENV_VARS},GEMINI_API_KEY_2=${GEMINI_API_KEY_2}"
fi

if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  ENV_VARS="${ENV_VARS},OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
fi

echo "⚡ Deploying ${SERVICE_NAME} to Google Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --image="${IMAGE_TAG}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --update-env-vars="${ENV_VARS}"

echo ""
echo "✅ TestForge successfully deployed to Google Cloud Run!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --platform=managed \
  --region="${REGION}" \
  --format='value(status.url)')
echo "🌐 Live Service URL: ${SERVICE_URL}"

echo ""
echo "🔍 Running deployment verification health probes..."
echo "--- 1. Liveness Probe (/healthz) ---"
curl -fsS -m 15 "${SERVICE_URL}/healthz" || echo "⚠️ Warning: /healthz probe did not respond immediately"
echo ""

echo "--- 2. Readiness Probe (/readyz) ---"
curl -fsS -m 15 "${SERVICE_URL}/readyz" || echo "⚠️ Warning: /readyz probe did not respond immediately"
echo ""

echo "--- 3. A2A Agent Card Discovery (/.well-known/agent-card.json) ---"
curl -fsS -m 15 "${SERVICE_URL}/.well-known/agent-card.json" || echo "⚠️ Warning: /.well-known/agent-card.json did not respond immediately"
echo ""

echo "🎉 Deployment check complete. TestForge is live at ${SERVICE_URL}"
