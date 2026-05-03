"""Unit tests for validator.py — Claude with no use API."""

import pytest
import json
from unittest.mock import patch, MagicMock
from agent.validator import validate_manifest


def _mock_client(response: dict) -> MagicMock:
    mock = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(response))]
    mock.messages.create.return_value = msg
    return mock


APPROVED_RESPONSE = {
    "approved": True,
    "risk_level": "low",
    "issues": [],
    "warnings": [],
    "optimizations": ["Add readiness probe"],
    "summary": "Manifest is valid for dev environment.",
}

REJECTED_RESPONSE = {
    "approved": False,
    "risk_level": "high",
    "issues": ["cpu_limit 8000m is excessive"],
    "warnings": [],
    "optimizations": ["Reduce cpu_limit to 2000m"],
    "summary": "Resource limits too high for staging.",
}


class TestValidateManifest:

    # Return structure
    def test_returns_approved_key(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert "approved" in result

    def test_returns_risk_level(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert "risk_level" in result

    def test_returns_cost_estimate(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert "cost_estimate" in result
        assert "monthly_usd" in result["cost_estimate"]

    def test_returns_security_score(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert "security_score" in result

    def test_returns_issues_list(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert isinstance(result["issues"], list)

    def test_returns_optimizations_list(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert isinstance(result["optimizations"], list)

    # Approval logic
    def test_valid_manifest_approved(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert result["approved"] is True

    def test_high_resources_rejected(self, high_resources_manifest):
        with patch("agent.validator.client", _mock_client(REJECTED_RESPONSE)):
            result = validate_manifest(high_resources_manifest)
        assert result["approved"] is False

    # Critical security — no Claude call
    def test_privileged_blocked_without_claude(self, privileged_manifest):
        """Privileged containers must be blocked before Claude is called."""
        mock = MagicMock()
        with patch("agent.validator.client", mock):
            result = validate_manifest(privileged_manifest)
        mock.messages.create.assert_not_called()
        assert result["approved"] is False
        assert result["risk_level"] == "critical"
        assert result["security_score"] == 0

    def test_privileged_contains_violation_message(self, privileged_manifest):
        with patch("agent.validator.client", MagicMock()):
            result = validate_manifest(privileged_manifest)
        assert len(result["issues"]) > 0

    # Claude response merging
    def test_claude_summary_in_result(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert result["summary"] == APPROVED_RESPONSE["summary"]

    def test_claude_optimizations_preserved(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert "Add readiness probe" in result["optimizations"]

    # Security score from static checker
    def test_valid_manifest_security_score_100(self, valid_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(valid_manifest)
        assert result["security_score"] == 100

    def test_missing_limits_lower_security_score(self, missing_limits_manifest):
        with patch("agent.validator.client", _mock_client(APPROVED_RESPONSE)):
            result = validate_manifest(missing_limits_manifest)
        assert result["security_score"] < 100
