#!/usr/bin/env bash
# Register a newly deployed service in aiops-anomaly-detector

set -euo pipefail

SERVICE_NAME="${1:?Usage: register-service.sh <service_name> <namespace> <image>}"
NAMESPACE="${2:?namespace required}"
IMAGE="${3:?image required}"
ANOMALY_DETECTOR_URL="${ANOMALY_DETECTOR_URL:-http://localhost:8080}"

echo "📡 Registering ${SERVICE_NAME} in anomaly-detector..."

curl -s -X POST "${ANOMALY_DETECTOR_URL}/api/v1/services/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"service_name\": \"${SERVICE_NAME}\",
    \"namespace\":    \"${NAMESPACE}\",
    \"metrics_port\": 8080,
    \"deployed_at\":  \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"deployed_by\":  \"${GITHUB_ACTOR:-local}\",
    \"image\":        \"${IMAGE}\"
  }" && echo "✅ Registered" || echo "⚠️  Registration failed (non-blocking)"
