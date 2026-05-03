"""Unit tests for security_checker.py"""

import pytest
from agent.security_checker import check_security, _parse_cpu_millicores, _parse_memory_mi


# ── _parse_cpu_millicores ────────────────────────────────────────────────────

class TestParseCpuMillicores:
    def test_millicores(self):
        assert _parse_cpu_millicores("500m") == 500

    def test_whole_cores(self):
        assert _parse_cpu_millicores("2") == 2000

    def test_100m(self):
        assert _parse_cpu_millicores("100m") == 100

    def test_empty_string(self):
        assert _parse_cpu_millicores("") == 0


# ── _parse_memory_mi ─────────────────────────────────────────────────────────

class TestParseMemoryMi:
    def test_mebibytes(self):
        assert _parse_memory_mi("512Mi") == pytest.approx(512.0)

    def test_gibibytes(self):
        assert _parse_memory_mi("2Gi") == pytest.approx(2048.0)

    def test_gigabytes(self):
        assert _parse_memory_mi("1G") == pytest.approx(1024.0)


# ── check_security ───────────────────────────────────────────────────────────

class TestCheckSecurity:

    # Score structure
    def test_returns_required_keys(self, valid_manifest):
        result = check_security(valid_manifest)
        assert "score" in result
        assert "violations" in result
        assert "warnings" in result

    def test_valid_manifest_high_score(self, valid_manifest):
        result = check_security(valid_manifest)
        assert result["score"] == 100
        assert result["violations"] == []

    # Privileged container — hard block
    def test_privileged_container_score_zero(self, privileged_manifest):
        result = check_security(privileged_manifest)
        assert result["score"] == 0

    def test_privileged_container_in_violations(self, privileged_manifest):
        result = check_security(privileged_manifest)
        assert any("privileged" in v for v in result["violations"])

    # Missing limits
    def test_missing_cpu_limit_reduces_score(self, missing_limits_manifest):
        result = check_security(missing_limits_manifest)
        assert result["score"] < 100
        assert any("cpu_limit" in v for v in result["violations"])

    def test_missing_memory_limit_reduces_score(self, missing_limits_manifest):
        result = check_security(missing_limits_manifest)
        assert any("memory_limit" in v for v in result["violations"])

    def test_all_missing_limits_cumulative(self, missing_limits_manifest):
        result = check_security(missing_limits_manifest)
        # Missing: cpu_limit(30) + memory_limit(30) + cpu_request(20) + memory_request(20) = 80
        # But image has no tag → "latest_tag" warning (no score impact)
        # Total deduction = 100, score = max(0, 0) = 0
        assert result["score"] == 0
        assert len(result["violations"]) == 4

    # Warnings
    def test_high_cpu_limit_warning(self, high_resources_manifest):
        result = check_security(high_resources_manifest)
        assert any("cpu_limit_high" in w for w in result["warnings"])

    def test_high_memory_limit_warning(self, high_resources_manifest):
        result = check_security(high_resources_manifest)
        assert any("memory_limit_high" in w for w in result["warnings"])

    def test_latest_tag_warning(self, latest_tag_manifest):
        result = check_security(latest_tag_manifest)
        assert any("latest_tag" in w for w in result["warnings"])

    def test_single_replica_warning(self):
        manifest = {
            "image": "ghcr.io/k-shevtsov/svc:v1.0.0",
            "replicas": 1,
            "cpu_request": "100m",
            "cpu_limit": "500m",
            "memory_request": "128Mi",
            "memory_limit": "512Mi",
        }
        result = check_security(manifest)
        assert any("replicas_low" in w for w in result["warnings"])

    # Root user
    def test_root_user_violation(self, valid_manifest):
        valid_manifest["run_as_user"] = 0
        result = check_security(valid_manifest)
        assert any("root_user" in v for v in result["violations"])

    # Score never negative
    def test_score_never_negative(self):
        manifest = {
            "privileged": True,
            "host_network": True,
            "host_pid": True,
            "run_as_user": 0,
        }
        result = check_security(manifest)
        assert result["score"] >= 0

    # host_network / host_pid
    def test_host_network_violation(self, valid_manifest):
        valid_manifest["host_network"] = True
        result = check_security(valid_manifest)
        assert any("host_network" in v for v in result["violations"])

    def test_host_pid_violation(self, valid_manifest):
        valid_manifest["host_pid"] = True
        result = check_security(valid_manifest)
        assert any("host_pid" in v for v in result["violations"])
