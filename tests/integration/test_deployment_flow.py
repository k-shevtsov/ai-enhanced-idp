"""
Integration tests for AI-Enhanced IDP deployment flow.
Requires: ANTHROPIC_API_KEY, running k3d clusters.
Mark: pytest -m integration
"""

import os
import json
import pytest
import subprocess

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def sample_manifest():
    return {
        "service_name": "integration-test-svc",
        "image": "ghcr.io/k-shevtsov/demo:v1.0.0",
        "replicas": 2,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "memory_request": "128Mi",
        "memory_limit": "512Mi",
        "namespace": "dev",
        "environment": "dev",
    }


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
def test_full_validation_flow(sample_manifest):
    """Full Claude validation with real API call."""
    from agent.validator import validate_manifest
    result = validate_manifest(sample_manifest)

    assert "approved" in result
    assert "security_score" in result
    assert "cost_estimate" in result
    assert result["security_score"] == 100
    assert result["approved"] is True
    assert result["cost_estimate"]["monthly_usd"] > 0


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
def test_privileged_rejected_by_claude(sample_manifest):
    """Privileged manifest must be rejected without Claude call."""
    from agent.validator import validate_manifest
    manifest = {**sample_manifest, "privileged": True}
    result = validate_manifest(manifest)
    assert result["approved"] is False
    assert result["security_score"] == 0


def test_register_script_exists():
    """register-service.sh must exist and be executable."""
    assert os.path.isfile("scripts/register-service.sh")
    assert os.access("scripts/register-service.sh", os.X_OK)


def test_register_script_runs():
    """register-service.sh must run without error even if services unreachable."""
    result = subprocess.run(
        ["bash", "scripts/register-service.sh",
         "test-svc", "dev", "ghcr.io/k-shevtsov/test:v1.0.0"],
        capture_output=True, text=True,
        env={**os.environ, "ANOMALY_DETECTOR_URL": "http://localhost:19999",
             "PUSHGATEWAY_URL": "http://localhost:19998"}
    )
    # Script must exit 0 even when services unreachable (non-blocking)
    assert result.returncode == 0
    assert "Registration summary" in result.stdout


def test_gitops_structure_exists():
    """GitOps overlay directories must exist."""
    assert os.path.isdir("gitops/overlays/dev")
    assert os.path.isdir("gitops/overlays/staging")


def test_argocd_manifests_valid():
    """ArgoCD manifests must be valid YAML."""
    import yaml
    for fname in [
        "argocd/apps/app-of-apps.yaml",
        "argocd/apps/dev-services.yaml",
        "argocd/apps/staging-services.yaml",
        "argocd/projects/idp-project.yaml",
    ]:
        with open(fname) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) >= 1, f"{fname} is empty"


def test_helm_chart_valid():
    """Helm chart must have required files."""
    required = [
        "helm/service-template/Chart.yaml",
        "helm/service-template/values.yaml",
        "helm/service-template/templates/deployment.yaml",
        "helm/service-template/templates/service.yaml",
    ]
    for f in required:
        assert os.path.isfile(f), f"Missing: {f}"
