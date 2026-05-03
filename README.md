# AI-Enhanced IDP

> Evolution of [mini-idp](https://github.com/k-shevtsov/mini-idp) — from basic self-service deployments to an AI-Native Internal Developer Platform.

[![Tests](https://github.com/k-shevtsov/ai-enhanced-idp/actions/workflows/validate-manifest.yml/badge.svg)](https://github.com/k-shevtsov/ai-enhanced-idp/actions)

## Architecture
Developer → Port.io UI
↓
GitHub Actions
↓
Claude Agent (pre-deploy validation)
✓ Resource limits check
✓ Security policy check
✓ Cost estimation
↓
ArgoCD GitOps → k3d cluster (ai-idp)
↓
Auto-registration → aiops-anomaly-detector
↓
Port.io Scorecard update

## Quick Start

```bash
git clone https://github.com/k-shevtsov/ai-enhanced-idp
cd ai-enhanced-idp
cp .env.example .env
# fill in ANTHROPIC_API_KEY

make up       # start k3d cluster + ArgoCD
make status   # verify everything is running
make demo     # run demo validation flow
```

## Stack

| Component | Technology |
|-----------|-----------|
| Developer Portal | Port.io (free tier) |
| GitOps CD | ArgoCD |
| Cluster | k3d (`ai-idp`) |
| AI Validation | Claude Haiku (`claude-haiku-4-5`) |
| CI/CD | GitHub Actions |
| Monitoring | aiops-anomaly-detector integration |

## Related Projects

- [`aiops-anomaly-detector`](https://github.com/k-shevtsov/aiops-anomaly-detector) — anomaly detection platform (deployed services are auto-registered here)
- [`ai-incident-response`](https://github.com/k-shevtsov/ai-incident-response) — incident response automation
- [`mini-idp`](https://github.com/k-shevtsov/mini-idp) — predecessor (Port.io + kind + kubectl apply)

