"""
Static security policy checks for Kubernetes deployments.

Runs without Claude API — fast, free, deterministic.
Catches critical violations before wasting tokens on obvious issues.
"""

from typing import Any


# Score deductions per violation type
VIOLATION_WEIGHTS = {
    "privileged_container": 100,   # instant 0 score → blocks deploy
    "missing_cpu_limit": 30,
    "missing_memory_limit": 30,
    "missing_cpu_request": 20,
    "missing_memory_request": 20,
    "root_user": 25,
    "host_network": 40,
    "host_pid": 40,
}

WARNING_WEIGHTS = {
    "cpu_limit_high": 0,           # warning only, no score impact
    "memory_limit_high": 0,
    "replicas_low": 0,
    "latest_tag": 0,
}


def _parse_cpu_millicores(cpu_str: str) -> int:
    """Convert CPU string to millicores. '500m' → 500, '2' → 2000"""
    if not cpu_str:
        return 0
    cpu_str = str(cpu_str).strip()
    if cpu_str.endswith("m"):
        return int(cpu_str[:-1])
    return int(float(cpu_str) * 1000)


def _parse_memory_mi(mem_str: str) -> float:
    """Convert memory string to MiB."""
    if not mem_str:
        return 0.0
    mem_str = str(mem_str).strip()
    if mem_str.endswith("Gi"):
        return float(mem_str[:-2]) * 1024
    if mem_str.endswith("Mi"):
        return float(mem_str[:-2])
    if mem_str.endswith("G"):
        return float(mem_str[:-1]) * 1024
    if mem_str.endswith("M"):
        return float(mem_str[:-1])
    return float(mem_str) / (1024 ** 2)


def check_security(manifest: dict[str, Any]) -> dict[str, Any]:
    """
    Run static security checks on a deployment manifest.

    Returns:
        dict with score (0-100), violations (blocking), warnings (non-blocking)
    """
    violations = []
    warnings = []
    score = 100

    # ── Critical: privileged container ──────────
    if manifest.get("privileged", False):
        violations.append("privileged_container: containers must not run as privileged")
        score = 0  # hard block

    # ── Critical: host namespace sharing ────────
    if manifest.get("host_network", False):
        violations.append("host_network: hostNetwork=true is not allowed")
        score -= VIOLATION_WEIGHTS["host_network"]

    if manifest.get("host_pid", False):
        violations.append("host_pid: hostPID=true is not allowed")
        score -= VIOLATION_WEIGHTS["host_pid"]

    # ── Resource limits ──────────────────────────
    if not manifest.get("cpu_limit"):
        violations.append("missing_cpu_limit: cpu limit must be set")
        score -= VIOLATION_WEIGHTS["missing_cpu_limit"]

    if not manifest.get("memory_limit"):
        violations.append("missing_memory_limit: memory limit must be set")
        score -= VIOLATION_WEIGHTS["missing_memory_limit"]

    if not manifest.get("cpu_request"):
        violations.append("missing_cpu_request: cpu request must be set")
        score -= VIOLATION_WEIGHTS["missing_cpu_request"]

    if not manifest.get("memory_request"):
        violations.append("missing_memory_request: memory request must be set")
        score -= VIOLATION_WEIGHTS["missing_memory_request"]

    # ── Warnings: high limits ───────────────────
    cpu_limit = manifest.get("cpu_limit", "")
    if cpu_limit:
        cpu_mc = _parse_cpu_millicores(cpu_limit)
        if cpu_mc > 4000:
            warnings.append(
                f"cpu_limit_high: {cpu_limit} exceeds 4000m — consider reducing for dev/staging"
            )

    memory_limit = manifest.get("memory_limit", "")
    if memory_limit:
        mem_mi = _parse_memory_mi(memory_limit)
        if mem_mi > 2048:
            warnings.append(
                f"memory_limit_high: {memory_limit} exceeds 2Gi — review if necessary"
            )

    # ── Warnings: replicas ──────────────────────
    replicas = int(manifest.get("replicas", 1))
    if replicas < 2:
        warnings.append("replicas_low: single replica has no redundancy")

    # ── Warnings: image tag ──────────────────────
    image = manifest.get("image", "")
    if image.endswith(":latest") or ":" not in image:
        warnings.append("latest_tag: avoid ':latest' tag — use immutable image digests")

    # ── Root user ────────────────────────────────
    run_as_user = manifest.get("run_as_user")
    if run_as_user == 0:
        violations.append("root_user: containers must not run as root (runAsUser: 0)")
        score -= VIOLATION_WEIGHTS["root_user"]

    score = max(0, score)

    return {
        "score": score,
        "violations": violations,
        "warnings": warnings,
    }
