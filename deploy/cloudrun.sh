#!/usr/bin/env bash
# ==============================================================================
# TestForge: Google Cloud Run Automated Deployment Script
# Multi-Agent Test Hardening System (Google ADK + CrewAI)
# ==============================================================================
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-testforge}"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ Error: GCP_PROJECT_ID environment variable or active gcloud project is required."
  echo "Usage: GCP_PROJECT_ID=my-gcp-project ./deploy/cloudrun.sh"
  exit 1
fi

echo "🚀 Building TestForge container image: ${IMAGE_TAG}..."
gcloud builds submit --tag "${IMAGE_TAG}" .

echo "⚡ Deploying to Google Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "TESTFORGE_PRIVACY_MODE=false,TESTFORGE_SANDBOX_WORKERS=4"

echo "✅ TestForge successfully deployed to Google Cloud Run!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --format 'value(status.url)')
echo "🌐 Live Endpoint: ${SERVICE_URL}"
echo "🏥 Liveness Probe: ${SERVICE_URL}/healthz"
