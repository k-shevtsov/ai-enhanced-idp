"""Unit tests for cost_estimator.py"""

import pytest
from agent.cost_estimator import parse_cpu, parse_memory_gb, estimate_cost


# ── parse_cpu ────────────────────────────────────────────────────────────────

class TestParseCpu:
    def test_millicores(self):
        assert parse_cpu("500m") == pytest.approx(0.5)

    def test_millicores_100(self):
        assert parse_cpu("100m") == pytest.approx(0.1)

    def test_whole_cores(self):
        assert parse_cpu("2") == pytest.approx(2.0)

    def test_whole_cores_string(self):
        assert parse_cpu("1") == pytest.approx(1.0)

    def test_fractional_cores(self):
        assert parse_cpu("1500m") == pytest.approx(1.5)

    def test_none_returns_zero(self):
        assert parse_cpu(None) == 0.0

    def test_zero_millicores(self):
        assert parse_cpu("0m") == 0.0


# ── parse_memory_gb ──────────────────────────────────────────────────────────

class TestParseMemoryGb:
    def test_mebibytes(self):
        assert parse_memory_gb("512Mi") == pytest.approx(0.5)

    def test_gibibytes(self):
        assert parse_memory_gb("2Gi") == pytest.approx(2.0)

    def test_128mi(self):
        assert parse_memory_gb("128Mi") == pytest.approx(0.125)

    def test_1gi(self):
        assert parse_memory_gb("1Gi") == pytest.approx(1.0)

    def test_gigabytes(self):
        assert parse_memory_gb("1G") == pytest.approx(1.0)

    def test_megabytes(self):
        assert parse_memory_gb("1024M") == pytest.approx(1.0)

    def test_none_returns_zero(self):
        assert parse_memory_gb(None) == 0.0


# ── estimate_cost ────────────────────────────────────────────────────────────

class TestEstimateCost:
    def test_basic_estimate(self, valid_manifest):
        result = estimate_cost(valid_manifest)
        assert "monthly_usd" in result
        assert result["monthly_usd"] >= 0

    def test_replicas_multiply_cost(self):
        manifest_1 = {"replicas": 1, "cpu_request": "100m", "memory_request": "128Mi"}
        manifest_3 = {"replicas": 3, "cpu_request": "100m", "memory_request": "128Mi"}
        cost_1 = estimate_cost(manifest_1)["monthly_usd"]
        cost_3 = estimate_cost(manifest_3)["monthly_usd"]
        assert cost_3 == pytest.approx(cost_1 * 3, rel=1e-3)

    def test_result_structure(self, valid_manifest):
        result = estimate_cost(valid_manifest)
        assert "monthly_usd" in result
        assert "cpu_cores_total" in result
        assert "memory_gb_total" in result
        assert "replicas" in result
        assert "breakdown" in result
        assert "cpu_cost_usd" in result["breakdown"]
        assert "memory_cost_usd" in result["breakdown"]

    def test_zero_resources(self):
        # estimate_cost uses defaults "100m" and "128Mi" when keys are absent,
        # so cost is never truly 0. Test structure instead.
        manifest = {"replicas": 1}
        result = estimate_cost(manifest)
        assert result["monthly_usd"] >= 0.0
        assert result["replicas"] == 1

    def test_high_replicas(self):
        manifest = {"replicas": 10, "cpu_request": "500m", "memory_request": "512Mi"}
        result = estimate_cost(manifest)
        assert result["cpu_cores_total"] == pytest.approx(5.0)
        assert result["memory_gb_total"] == pytest.approx(5.0)

    def test_cost_breakdown_sums_to_total(self, valid_manifest):
        result = estimate_cost(valid_manifest)
        total = result["breakdown"]["cpu_cost_usd"] + result["breakdown"]["memory_cost_usd"]
        assert total == pytest.approx(result["monthly_usd"], abs=0.01)
