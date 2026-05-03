.PHONY: up down demo test test-int validate status clean help

CLUSTER_NAME := ai-idp
ARGOCD_NAMESPACE := argocd
KUBECONFIG_CONTEXT := k3d-$(CLUSTER_NAME)

# ──────────────────────────────────────────────
# Core targets
# ──────────────────────────────────────────────

up: ## Start k3d cluster + ArgoCD + wait for ready
	@echo "🚀 Starting AI-Enhanced IDP..."
	@bash scripts/setup-cluster.sh
	@echo "✅ Cluster ready. Run 'make status' to verify."

down: ## Stop k3d cluster
	@echo "⏹ Stopping cluster $(CLUSTER_NAME)..."
	@k3d cluster stop $(CLUSTER_NAME) 2>/dev/null || echo "Cluster not running"

clean: ## Delete k3d cluster (full reset)
	@echo "🗑 Deleting cluster $(CLUSTER_NAME)..."
	@k3d cluster delete $(CLUSTER_NAME) 2>/dev/null || echo "Cluster not found"
	@echo "✅ Cluster deleted."

status: ## Show cluster + ArgoCD apps status
	@echo "═══════════════════════════════════════"
	@echo "  Cluster: $(CLUSTER_NAME)"
	@echo "═══════════════════════════════════════"
	@kubectl config use-context $(KUBECONFIG_CONTEXT) 2>/dev/null || echo "Context not found"
	@kubectl get nodes 2>/dev/null || echo "Cluster not running"
	@echo ""
	@echo "ArgoCD Applications:"
	@kubectl get applications -n $(ARGOCD_NAMESPACE) 2>/dev/null || echo "ArgoCD not installed"
	@echo ""
	@echo "Deployed services:"
	@kubectl get pods -A --field-selector=metadata.namespace!=kube-system,metadata.namespace!=argocd 2>/dev/null || true

# ──────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────

test: ## Run unit tests (no API key required)
	@echo "🧪 Running unit tests..."
	@cd agent && python -m pytest tests/ -v --ignore=tests/test_integration.py -m "not integration"

test-int: ## Run integration tests (requires ANTHROPIC_API_KEY)
	@echo "🧪 Running integration tests (real Claude API)..."
	@python -m pytest tests/integration/ -v -m integration

validate: ## Validate a sample manifest through Claude agent
	@echo "🤖 Running Claude validation on sample manifest..."
	@python -c "from agent.validator import validate_manifest; import json; \
		result = validate_manifest({'service_name': 'demo-service', 'cpu_request': '100m', \
		'cpu_limit': '2000m', 'memory_request': '128Mi', 'memory_limit': '512Mi', \
		'replicas': 2, 'namespace': 'dev', 'environment': 'dev', \
		'image': 'ghcr.io/k-shevtsov/demo:latest'}); \
		print(json.dumps(result, indent=2))"

# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

demo: ## Run full demo flow (Port.io → ArgoCD → k3d)
	@echo "🎬 Starting AI-Enhanced IDP demo..."
	@echo "Step 1: Validating manifest with Claude agent..."
	@make validate
	@echo ""
	@echo "Step 2: Checking ArgoCD apps..."
	@kubectl get applications -n $(ARGOCD_NAMESPACE) 2>/dev/null || echo "No apps deployed yet"
	@echo ""
	@echo "✅ Demo complete. See README.md for full flow."

# ──────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
