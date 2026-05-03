"""
Cost estimation for Kubernetes deployments.

Uses CPU/memory requests (not limits) for cost calculation —
this matches how cloud providers bill for reserved resources.
"""

from typing import Any

# Approximate GCP/AWS pricing for reference (USD per unit per month)
CPU_COST_PER_CORE_MONTH = 30.0       # ~$30/core/month (e2-standard equivalent)
MEMORY_COST_PER_GB_MONTH = 4.0       # ~$4/GB/month


def parse_cpu(cpu_str: str) -> float:
    """Convert CPU string to cores. '500m' → 0.5, '2' → 2.0"""
    if cpu_str is None:
        return 0.0
    cpu_str = str(cpu_str).strip()
    if cpu_str.endswith("m"):
        return float(cpu_str[:-1]) / 1000.0
    return float(cpu_str)


def parse_memory_gb(mem_str: str) -> float:
    """Convert memory string to GB. '512Mi' → 0.5, '2Gi' → 2.0, '1024' → ~0.001"""
    if mem_str is None:
        return 0.0
    mem_str = str(mem_str).strip()
    if mem_str.endswith("Gi"):
        return float(mem_str[:-2])
    if mem_str.endswith("Mi"):
        return float(mem_str[:-2]) / 1024.0
    if mem_str.endswith("G"):
        return float(mem_str[:-1])
    if mem_str.endswith("M"):
        return float(mem_str[:-1]) / 1024.0
    # bare bytes
    return float(mem_str) / (1024 ** 3)


def estimate_cost(manifest: dict[str, Any]) -> dict[str, Any]:
    """
    Estimate monthly cost based on resource requests × replicas.

    Returns:
        dict with monthly_usd, cpu_cores_total, memory_gb_total, breakdown
    """
    replicas = int(manifest.get("replicas", 1))
    cpu_cores = parse_cpu(manifest.get("cpu_request", "100m"))
    memory_gb = parse_memory_gb(manifest.get("memory_request", "128Mi"))

    cpu_cores_total = cpu_cores * replicas
    memory_gb_total = memory_gb * replicas

    cpu_cost = cpu_cores_total * CPU_COST_PER_CORE_MONTH
    memory_cost = memory_gb_total * MEMORY_COST_PER_GB_MONTH
    monthly_usd = cpu_cost + memory_cost

    return {
        "monthly_usd": round(monthly_usd, 2),
        "cpu_cores_total": round(cpu_cores_total, 3),
        "memory_gb_total": round(memory_gb_total, 3),
        "replicas": replicas,
        "breakdown": {
            "cpu_cost_usd": round(cpu_cost, 2),
            "memory_cost_usd": round(memory_cost, 2),
        },
    }
