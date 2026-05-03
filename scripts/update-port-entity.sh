#!/usr/bin/env bash
# Update Port.io entity scorecard after deployment

set -euo pipefail

SERVICE_NAME="${1:?service_name required}"
SECURITY_SCORE="${2:-0}"
MONTHLY_COST="${3:-0}"
DEPLOY_STATUS="${4:-success}"

PORT_CLIENT_ID="${PORT_CLIENT_ID:?PORT_CLIENT_ID not set}"
PORT_CLIENT_SECRET="${PORT_CLIENT_SECRET:?PORT_CLIENT_SECRET not set}"

echo "🔄 Updating Port.io entity: ${SERVICE_NAME}..."

# Get token
TOKEN=$(curl -s -X POST "https://api.getport.io/v1/auth/access_token" \
  -H "Content-Type: application/json" \
  -d "{\"clientId\": \"${PORT_CLIENT_ID}\", \"clientSecret\": \"${PORT_CLIENT_SECRET}\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

# Update entity
curl -s -X PATCH "https://api.getport.io/v1/blueprints/service/entities/${SERVICE_NAME}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"properties\": {
      \"security_score\": ${SECURITY_SCORE},
      \"monthly_cost_usd\": ${MONTHLY_COST},
      \"last_deploy_status\": \"${DEPLOY_STATUS}\",
      \"last_deployed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
      \"monitoring_enabled\": true
    }
  }" && echo "✅ Port.io entity updated" || echo "⚠️  Port.io update failed (non-blocking)"
