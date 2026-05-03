"""Shared fixtures for AI-Enhanced IDP tests."""

import pytest
from unittest.mock import MagicMock, patch


# ── Sample manifests ─────────────────────────────────────────────────────────

@pytest.fixture
def valid_manifest():
    return {
        "service_name": "payment-service",
        "image": "ghcr.io/k-shevtsov/payment-service:v1.2.0",
        "replicas": 2,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "memory_request": "128Mi",
        "memory_limit": "512Mi",
        "namespace": "dev",
        "environment": "dev",
    }


@pytest.fixture
def privileged_manifest():
    return {
        "service_name": "bad-service",
        "image": "ghcr.io/k-shevtsov/bad-service:v1.0.0",
        "replicas": 1,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "memory_request": "128Mi",
        "memory_limit": "512Mi",
        "namespace": "dev",
        "environment": "dev",
        "privileged": True,
    }


@pytest.fixture
def missing_limits_manifest():
    return {
        "service_name": "no-limits-service",
        "image": "ghcr.io/k-shevtsov/svc:v1.0.0",
        "replicas": 2,
        "namespace": "dev",
        "environment": "dev",
    }


@pytest.fixture
def high_resources_manifest():
    return {
        "service_name": "heavy-service",
        "image": "ghcr.io/k-shevtsov/heavy:v2.0.0",
        "replicas": 3,
        "cpu_request": "2000m",
        "cpu_limit": "8000m",
        "memory_request": "4Gi",
        "memory_limit": "8Gi",
        "namespace": "staging",
        "environment": "staging",
    }


@pytest.fixture
def latest_tag_manifest():
    return {
        "service_name": "latest-service",
        "image": "ghcr.io/k-shevtsov/svc:latest",
        "replicas": 2,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "memory_request": "128Mi",
        "memory_limit": "512Mi",
        "namespace": "dev",
        "environment": "dev",
    }


# ── Claude mock ──────────────────────────────────────────────────────────────

def make_claude_mock(response_json: dict) -> MagicMock:
    """Create a mock Anthropic client that returns a fixed JSON response."""
    import json
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(response_json))]
    mock_client.messages.create.return_value = mock_message
    return mock_client


@pytest.fixture
def mock_claude_approved():
    return make_claude_mock({
        "approved": True,
        "risk_level": "low",
        "issues": [],
        "warnings": [],
        "optimizations": ["Consider adding readiness probe"],
        "summary": "Manifest looks good for dev environment.",
    })


@pytest.fixture
def mock_claude_rejected():
    return make_claude_mock({
        "approved": False,
        "risk_level": "high",
        "issues": ["cpu_limit 8000m is excessive for staging"],
        "warnings": ["memory_limit 8Gi is high"],
        "optimizations": ["Reduce cpu_limit to 2000m"],
        "summary": "Resource limits are too high for staging environment.",
    })
