#!/usr/bin/env bash
# Register deployed service in aiops-anomaly-detector monitoring
# Uses health check to verify service is reachable, then logs to Prometheus via pushgateway

set -euo pipefail

SERVICE_NAME="${1:?Usage: register-service.sh <service_name> <namespace> <image>}"
NAMESPACE="${2:?namespace required}"
IMAGE="${3:?image required}"

ANOMALY_DETECTOR_URL="${ANOMALY_DETECTOR_URL:-http://localhost:8090}"
PUSHGATEWAY_URL="${PUSHGATEWAY_URL:-http://localhost:9091}"

echo "📡 Registering ${SERVICE_NAME} in monitoring..."

# 1. Verify anomaly-detector is reachable
HEALTH=$(curl -sf "${ANOMALY_DETECTOR_URL}/health" 2>/dev/null || echo "unreachable")
if echo "${HEALTH}" | grep -q "unreachable"; then
  echo "⚠️  anomaly-detector unreachable at ${ANOMALY_DETECTOR_URL} (non-blocking)"
else
  echo "✅ anomaly-detector healthy"
fi

# 2. Push registration metric to Prometheus Pushgateway
DEPLOYED_AT=$(date +%s)
PUSH_RESULT=$(curl -sf --data-binary @- \
  "${PUSHGATEWAY_URL}/metrics/job/idp_deployment/service/${SERVICE_NAME}/namespace/${NAMESPACE}" << METRICS 2>/dev/null || echo "pushgateway_unreachable")
# TYPE idp_service_deployed gauge
# HELP idp_service_deployed Timestamp of last deployment via AI-Enhanced IDP
idp_service_deployed{service="${SERVICE_NAME}",namespace="${NAMESPACE}",image="${IMAGE}",deployed_by="${GITHUB_ACTOR:-local}"} ${DEPLOYED_AT}
METRICS

if echo "${PUSH_RESULT}" | grep -q "pushgateway_unreachable"; then
  echo "⚠️  Pushgateway unreachable (non-blocking)"
else
  echo "✅ Deployment metric pushed to Prometheus"
fi

echo "📋 Registration summary:"
echo "   Service:   ${SERVICE_NAME}"
echo "   Namespace: ${NAMESPACE}"
echo "   Image:     ${IMAGE}"
echo "   Time:      $(date -u +%Y-%m-%dT%H:%M:%SZ)"
