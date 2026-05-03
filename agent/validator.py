"""
Claude pre-deploy validation agent.

Validates deployment manifests before they reach ArgoCD.
Returns approved/rejected with detailed reasoning.
"""

import os
import json
from typing import Any
from anthropic import Anthropic

from agent.cost_estimator import estimate_cost
from agent.security_checker import check_security

client = Anthropic()

VALIDATION_SYSTEM_PROMPT = """You are a Kubernetes deployment validation expert.
Analyze the deployment manifest and return ONLY a JSON object with this exact structure:

{
  "approved": true or false,
  "risk_level": "low" | "medium" | "high" | "critical",
  "issues": ["list of problems found"],
  "warnings": ["list of non-blocking warnings"],
  "optimizations": ["list of suggested improvements"],
  "summary": "one sentence summary"
}

Rules:
- approved=false if: privileged containers, missing resource limits, cpu_limit > 4000m for dev/staging,
  memory_limit > 2Gi for dev/staging, replicas > 10 for dev
- approved=false if risk_level is "critical"
- Respond ONLY with the JSON object, no markdown, no explanation"""


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """
    Validate a deployment manifest using Claude + static checks.

    Args:
        manifest: dict with service_name, image, replicas, cpu_request,
                  cpu_limit, memory_request, memory_limit, namespace, environment

    Returns:
        dict with approved, risk_level, issues, warnings, optimizations,
        summary, cost_estimate, security_score
    """
    # Static checks first (no API cost)
    security_result = check_security(manifest)
    cost_result = estimate_cost(manifest)

    # If critical security violation — reject without calling Claude
    if security_result["score"] == 0:
        return {
            "approved": False,
            "risk_level": "critical",
            "issues": security_result["violations"],
            "warnings": [],
            "optimizations": [],
            "summary": "Critical security violation detected. Deployment blocked.",
            "cost_estimate": cost_result,
            "security_score": 0,
        }

    # Claude validation
    prompt = f"""Validate this Kubernetes deployment manifest:

{json.dumps(manifest, indent=2)}

Static analysis results:
- Security score: {security_result['score']}/100
- Security violations: {security_result['violations']}
- Security warnings: {security_result['warnings']}
- Estimated monthly cost: ${cost_result['monthly_usd']:.2f}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=VALIDATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    claude_result = json.loads(raw)

    return {
        **claude_result,
        "cost_estimate": cost_result,
        "security_score": security_result["score"],
    }
