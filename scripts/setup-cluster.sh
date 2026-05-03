#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="ai-idp"
ARGOCD_VERSION="v2.13.3"
ARGOCD_NAMESPACE="argocd"

echo "══════════════════════════════════════════════"
echo "  AI-Enhanced IDP — Cluster Setup"
echo "  Cluster: k3d-${CLUSTER_NAME}"
echo "══════════════════════════════════════════════"

# ── 1. k3d cluster ──────────────────────────────
if k3d cluster list | grep -q "^${CLUSTER_NAME}"; then
  echo "✅ Cluster '${CLUSTER_NAME}' already exists"
  k3d cluster start "${CLUSTER_NAME}" 2>/dev/null || true
else
  echo "📦 Creating k3d cluster '${CLUSTER_NAME}'..."
  k3d cluster create "${CLUSTER_NAME}" \
    --servers 1 \
    --agents 2 \
    --port "8080:80@loadbalancer" \
    --port "8443:443@loadbalancer" \
    --wait
  echo "✅ Cluster created"
fi

kubectl config use-context "k3d-${CLUSTER_NAME}"

# ── 2. Wait for nodes ───────────────────────────
echo "⏳ Waiting for nodes to be Ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=120s

# ── 3. ArgoCD ───────────────────────────────────
if kubectl get namespace "${ARGOCD_NAMESPACE}" &>/dev/null; then
  echo "✅ ArgoCD namespace already exists"
else
  echo "📦 Installing ArgoCD ${ARGOCD_VERSION}..."
  kubectl create namespace "${ARGOCD_NAMESPACE}"
  kubectl apply -n "${ARGOCD_NAMESPACE}" \
    -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
fi

# ── 4. Wait for ArgoCD ──────────────────────────
echo "⏳ Waiting for ArgoCD to be ready (this takes ~90s)..."
kubectl wait --for=condition=available deployment/argocd-server \
  -n "${ARGOCD_NAMESPACE}" --timeout=180s

# ── 5. Get initial admin password ───────────────
ARGOCD_PASSWORD=$(kubectl -n "${ARGOCD_NAMESPACE}" get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d 2>/dev/null || echo "password not ready yet")

# ── 6. Create app namespaces ────────────────────
for ns in dev staging; do
  kubectl get namespace "${ns}" &>/dev/null || kubectl create namespace "${ns}"
done

echo ""
echo "══════════════════════════════════════════════"
echo "  ✅ Setup complete!"
echo "══════════════════════════════════════════════"
echo ""
echo "  Cluster context: k3d-${CLUSTER_NAME}"
echo "  ArgoCD UI:       http://localhost:8080/argocd (after port-forward)"
echo "  ArgoCD login:    admin / ${ARGOCD_PASSWORD}"
echo ""
echo "  Port-forward ArgoCD UI:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8081:443"
echo ""
