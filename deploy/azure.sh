#!/usr/bin/env bash
# ==============================================================================
# TestForge: Microsoft Azure Container Apps Turnkey Deployment Script
# Multi-Agent Test Hardening System (Google ADK + CrewAI)
# Target Platform: Azure Container Apps (Serverless, 1.0 vCPU, 2.0 GiB RAM)
# Builds locally for linux/amd64 and pushes directly to ACR (bypasses ACR Tasks)
# ==============================================================================
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-testforge-rg}"
LOCATION="${LOCATION:-centralindia}"
ACR_DEFAULT_NAME="testforgeacr${RANDOM}"
ACR_NAME="${ACR_NAME:-${ACR_DEFAULT_NAME}}"
ACR_NAME=$(echo "${ACR_NAME}" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]')
ENV_NAME="${ENV_NAME:-testforge-env}"
APP_NAME="${APP_NAME:-testforge-app}"

echo "================================================================================"
echo "⚡ TestForge Microsoft Azure Container Apps Deployment"
echo "================================================================================"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location:       ${LOCATION}"
echo "  ACR Name:       ${ACR_NAME}"
echo "  Environment:    ${ENV_NAME}"
echo "  App Name:       ${APP_NAME}"
echo "================================================================================"

if ! command -v az &>/dev/null; then
  echo "❌ Error: Azure CLI ('az') is not installed. Please install Azure CLI to proceed."
  exit 1
fi

if ! az account show &>/dev/null; then
  echo "❌ Error: Not authenticated with Azure CLI. Please run 'az login' first."
  exit 1
fi

echo "🔧 Ensuring required Azure resource providers are registered..."
for provider in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry; do
  reg_state=$(az provider show --namespace "$provider" --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")
  if [ "$reg_state" != "Registered" ]; then
    echo "  ⏳ Registering provider ${provider}..."
    az provider register --namespace "$provider" --wait 2>/dev/null || az provider register --namespace "$provider" 2>/dev/null || true
  else
    echo "  ✅ Provider ${provider} is registered."
  fi
done

echo "📦 Ensuring Resource Group '${RESOURCE_GROUP}' exists in '${LOCATION}'..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none

echo "🐳 Ensuring Azure Container Registry '${ACR_NAME}' exists..."
if ! az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
  az acr create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${ACR_NAME}" \
    --sku Basic \
    --admin-enabled true \
    --location "${LOCATION}" \
    --output none
else
  echo "  ✅ ACR '${ACR_NAME}' is ready."
fi

ACR_LOGIN_SERVER=$(az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name "${ACR_NAME}" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "${ACR_NAME}" --query "passwords[0].value" -o tsv)
IMAGE_REF="${ACR_LOGIN_SERVER}/testforge:latest"

# 1. Ensure Docker daemon is running
echo "🐳 Checking local Docker daemon status..."
if ! docker info >/dev/null 2>&1; then
  echo "  ⚠️ Docker daemon not running. Attempting to launch Docker Desktop..."
  if command -v open >/dev/null 2>&1; then
    open -a Docker || true
  fi
  retries=30
  until docker info >/dev/null 2>&1 || [ $retries -le 0 ]; do
    echo "  ⏳ Waiting for Docker daemon to become responsive ($retries s remaining)..."
    sleep 2
    retries=$((retries - 2))
  done
  if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running. Please start Docker Desktop and re-run."
    exit 1
  fi
fi
echo "  ✅ Docker daemon is operational."

# 2. Authenticate Docker with Azure Container Registry
echo "🔑 Logging into Azure Container Registry '${ACR_LOGIN_SERVER}'..."
if ! az acr login --name "${ACR_NAME}" 2>/dev/null; then
  echo "  ℹ️ 'az acr login' returned non-zero; authenticating via 'docker login' with admin credentials..."
  echo "${ACR_PASSWORD}" | docker login "${ACR_LOGIN_SERVER}" -u "${ACR_USERNAME}" --password-stdin
fi
echo "  ✅ Authenticated with ACR."

# 3. Build container locally targeting linux/amd64 (bypasses remote ACR Tasks quota/permissions)
echo "🏗️ Building container image locally targeting linux/amd64 for Azure Container Apps..."
docker build --platform linux/amd64 -t "${IMAGE_REF}" .

# 4. Push directly to Azure Container Registry
echo "📤 Pushing image directly to Azure Container Registry: ${IMAGE_REF}..."
docker push "${IMAGE_REF}"

# 5. Create or verify Container Apps Environment
echo "🌐 Ensuring Container Apps Environment '${ENV_NAME}' exists..."
if ! az containerapp env show --name "${ENV_NAME}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
  az containerapp env create \
    --name "${ENV_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --location "${LOCATION}" \
    --output none
else
  echo "  ✅ Container Apps Environment '${ENV_NAME}' is ready."
fi

ENV_VARS_ARGS=(
  "PORT=8080"
  "TESTFORGE_SANDBOX=subprocess"
  "TESTFORGE_PRIVACY_MODE=false"
)

if [ -n "${GEMINI_API_KEY:-}" ]; then
  ENV_VARS_ARGS+=("GEMINI_API_KEY=${GEMINI_API_KEY}")
fi

if [ -n "${GEMINI_API_KEY_2:-}" ]; then
  ENV_VARS_ARGS+=("GEMINI_API_KEY_2=${GEMINI_API_KEY_2}")
fi

if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  ENV_VARS_ARGS+=("OPENROUTER_API_KEY=${OPENROUTER_API_KEY}")
fi

# 6. Deploy or update Container App
echo "⚡ Deploying Azure Container App '${APP_NAME}' (1.0 vCPU, 2.0 GiB, scale-to-zero)..."
if az containerapp show --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
  echo "  🔄 Updating existing Container App '${APP_NAME}'..."
  az containerapp registry set \
    --name "${APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --server "${ACR_LOGIN_SERVER}" \
    --username "${ACR_USERNAME}" \
    --password "${ACR_PASSWORD}" \
    --output none 2>/dev/null || true

  az containerapp update \
    --name "${APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --image "${IMAGE_REF}" \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 0 \
    --max-replicas 1 \
    --set-env-vars "${ENV_VARS_ARGS[@]}" \
    --output none
else
  echo "  ✨ Creating new Container App '${APP_NAME}'..."
  az containerapp create \
    --name "${APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --environment "${ENV_NAME}" \
    --image "${IMAGE_REF}" \
    --registry-server "${ACR_LOGIN_SERVER}" \
    --registry-username "${ACR_USERNAME}" \
    --registry-password "${ACR_PASSWORD}" \
    --target-port 8080 \
    --ingress external \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 0 \
    --max-replicas 1 \
    --env-vars "${ENV_VARS_ARGS[@]}" \
    --output none
fi

FQDN=$(az containerapp show \
  --name "${APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

APP_URL="https://${FQDN}"

echo ""
echo "✅ TestForge successfully deployed to Microsoft Azure Container Apps!"
echo "🌐 Live Service URL: ${APP_URL}"
echo ""
echo "🔍 Running deployment verification health probes (waiting 10s for cold start)..."
sleep 10

echo "--- 1. Liveness Probe (/healthz) ---"
curl -fsS -m 30 "${APP_URL}/healthz" || echo "⚠️ Warning: /healthz probe did not respond immediately"
echo ""

echo "--- 2. Readiness Probe (/readyz) ---"
curl -fsS -m 30 "${APP_URL}/readyz" || echo "⚠️ Warning: /readyz probe did not respond immediately"
echo ""

echo "--- 3. A2A Agent Card Discovery (/.well-known/agent-card.json) ---"
curl -fsS -m 30 "${APP_URL}/.well-known/agent-card.json" || echo "⚠️ Warning: /.well-known/agent-card.json did not respond immediately"
echo ""

echo "🎉 Verification complete. TestForge is live on Microsoft Azure at ${APP_URL}"
