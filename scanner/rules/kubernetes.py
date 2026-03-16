"""
Kubernetes Rules — checks k8s/*.yaml, manifests/*.yaml, helm/values.yaml files.
"""

from __future__ import annotations
import re
import yaml
from typing import Any
from ..models import Finding


def _safe_load_all(content: str) -> list[Any]:
    """Load all YAML documents from content."""
    try:
        return list(yaml.safe_load_all(content)) or []
    except Exception:
        return []


def _find_line(lines: list[str], text: str, start: int = 0) -> int:
    for i, line in enumerate(lines[start:], start + 1):
        if text in line:
            return i
    return 0


# ─── Rules ────────────────────────────────────────────────────────────────────

def rule_no_resource_limits(lines, content) -> list[Finding]:
    """REL-006 — Containers without CPU/memory limits can starve other pods."""
    findings = []
    docs = _safe_load_all(content)

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        name = (doc.get("metadata") or {}).get("name", "unknown")
        if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob", "Pod"):
            continue

        spec = doc.get("spec", {}) or {}
        # Unwrap job template
        if kind in ("CronJob",):
            spec = (spec.get("jobTemplate") or {}).get("spec", {}) or {}
        template = spec.get("template", {}) or {}
        pod_spec = template.get("spec", {}) or {}
        containers = pod_spec.get("containers", []) or []

        for container in containers:
            if not isinstance(container, dict):
                continue
            resources = container.get("resources") or {}
            limits = resources.get("limits") or {}
            if not limits.get("cpu") or not limits.get("memory"):
                cname = container.get("name", "unnamed")
                line_no = _find_line(lines, cname)
                findings.append(Finding(
                    id="REL-006",
                    severity="HIGH",
                    category="reliability",
                    line=line_no,
                    message=f'Container "{cname}" in {kind} "{name}" has no CPU/memory limits. '
                            f'A runaway container can starve all other pods on the node.',
                    suggestion="Add resources.limits.cpu and resources.limits.memory. "
                               "Start with: limits: {cpu: 500m, memory: 512Mi}",
                    resource=f"{kind}/{name}/{cname}",
                ))
    return findings


def rule_privileged_container(lines, content) -> list[Finding]:
    """SEC-013 — Privileged containers have full host access."""
    findings = []
    docs = _safe_load_all(content)

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        name = (doc.get("metadata") or {}).get("name", "unknown")
        spec = doc.get("spec", {}) or {}
        template = spec.get("template", {}) or {}
        pod_spec = template.get("spec", {}) or {}
        containers = pod_spec.get("containers", []) or []

        for container in containers:
            if not isinstance(container, dict):
                continue
            security_context = container.get("securityContext") or {}
            if security_context.get("privileged"):
                cname = container.get("name", "unnamed")
                line_no = _find_line(lines, "privileged: true")
                findings.append(Finding(
                    id="SEC-013",
                    severity="CRITICAL",
                    category="security",
                    line=line_no,
                    message=f'Container "{cname}" in {kind} "{name}" runs as privileged. '
                            f'This gives the container full access to the host kernel — effectively root on the node.',
                    suggestion="Remove securityContext.privileged: true. "
                               "Use specific capabilities with securityContext.capabilities.add if needed.",
                    resource=f"{kind}/{name}/{cname}",
                ))
    return findings


def rule_no_liveness_probe(lines, content) -> list[Finding]:
    """REL-007 — Containers without liveness probes can get stuck silently."""
    findings = []
    docs = _safe_load_all(content)

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        if kind not in ("Deployment", "StatefulSet", "DaemonSet"):
            continue
        name = (doc.get("metadata") or {}).get("name", "unknown")
        spec = doc.get("spec", {}) or {}
        template = spec.get("template", {}) or {}
        pod_spec = template.get("spec", {}) or {}
        containers = pod_spec.get("containers", []) or []

        for container in containers:
            if not isinstance(container, dict):
                continue
            if not container.get("livenessProbe"):
                cname = container.get("name", "unnamed")
                line_no = _find_line(lines, cname)
                findings.append(Finding(
                    id="REL-007",
                    severity="MEDIUM",
                    category="reliability",
                    line=line_no,
                    message=f'Container "{cname}" in {kind} "{name}" has no livenessProbe. '
                            f"Kubernetes can't detect deadlocks or hung processes.",
                    suggestion="Add livenessProbe with httpGet or exec. "
                               "Example: livenessProbe: {httpGet: {path: /health, port: 8080}, initialDelaySeconds: 15}",
                    resource=f"{kind}/{name}/{cname}",
                ))
    return findings


def rule_single_replica_no_hpa(lines, content) -> list[Finding]:
    """REL-008 — Single replica with no HPA is a reliability risk."""
    findings = []
    docs = _safe_load_all(content)
    has_hpa = any(
        isinstance(d, dict) and d.get("kind") == "HorizontalPodAutoscaler"
        for d in docs
    )

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        if kind not in ("Deployment", "StatefulSet"):
            continue
        name = (doc.get("metadata") or {}).get("name", "unknown")
        spec = doc.get("spec", {}) or {}
        replicas = spec.get("replicas", 1)

        if replicas == 1 and not has_hpa:
            line_no = _find_line(lines, "replicas: 1") or _find_line(lines, name)
            findings.append(Finding(
                id="REL-008",
                severity="MEDIUM",
                category="reliability",
                line=line_no,
                message=f'{kind} "{name}" has replicas: 1 and no HPA. '
                        f'A single pod restart causes downtime.',
                suggestion="Set replicas: 2 for zero-downtime deploys, or add a HorizontalPodAutoscaler with minReplicas: 2.",
                resource=f"{kind}/{name}",
            ))
    return findings


def rule_latest_image_tag(lines, content) -> list[Finding]:
    """SEC-006 — Using :latest image tag in Kubernetes manifests."""
    findings = []
    docs = _safe_load_all(content)

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        spec = doc.get("spec", {}) or {}
        template = spec.get("template", {}) or {}
        pod_spec = template.get("spec", {}) or {}
        containers = pod_spec.get("containers", []) or []

        for container in containers:
            if not isinstance(container, dict):
                continue
            image = container.get("image", "")
            if image.endswith(":latest") or (":" not in image and image):
                cname = container.get("name", "unnamed")
                line_no = _find_line(lines, image)
                findings.append(Finding(
                    id="SEC-006",
                    severity="HIGH",
                    category="security",
                    line=line_no,
                    message=f'Container "{cname}" uses image "{image}" with mutable :latest tag. '
                            f'Deployments become non-deterministic and can pull malicious updates.',
                    suggestion=f"Pin to an immutable digest: {image.split(':')[0]}@sha256:<digest>",
                    resource=cname,
                ))
    return findings


def rule_run_as_non_root(lines, content) -> list[Finding]:
    """SEC-016 — Pod/Container not configured to run as non-root."""
    findings = []
    docs = _safe_load_all(content)

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")
        if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Pod"):
            continue
        name = (doc.get("metadata") or {}).get("name", "unknown")
        spec = doc.get("spec", {}) or {}
        template = spec.get("template", {}) or {}
        pod_spec = template.get("spec", {}) or {}
        pod_sc = pod_spec.get("securityContext") or {}

        if not pod_sc.get("runAsNonRoot") and not pod_sc.get("runAsUser"):
            line_no = _find_line(lines, name)
            findings.append(Finding(
                id="SEC-016",
                severity="MEDIUM",
                category="security",
                line=line_no,
                message=f'{kind} "{name}" does not enforce non-root execution. '
                        f'Containers may default to running as root.',
                suggestion="Add securityContext.runAsNonRoot: true at the pod level, "
                           "or specify runAsUser: 1000.",
                resource=f"{kind}/{name}",
            ))
    return findings


# ─── Rule runner ──────────────────────────────────────────────────────────────

_RULES = [
    rule_no_resource_limits,
    rule_privileged_container,
    rule_no_liveness_probe,
    rule_single_replica_no_hpa,
    rule_latest_image_tag,
    rule_run_as_non_root,
]


def run_rules(content: str) -> list[Finding]:
    lines = content.splitlines()
    findings: list[Finding] = []
    for rule in _RULES:
        try:
            findings.extend(rule(lines, content))
        except Exception:
            pass
    return findings
