"""
Dockerfile Rules — checks Dockerfiles and docker-compose files.
"""

from __future__ import annotations
import re
from ..models import Finding


# ─── Dockerfile Rules ─────────────────────────────────────────────────────────

def rule_latest_tag(lines, content) -> list[Finding]:
    """SEC-006 — Using :latest image tag is a supply chain risk."""
    findings = []
    pattern = re.compile(r'^FROM\s+(\S+):latest\b', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        m = pattern.match(line.strip())
        if m:
            findings.append(Finding(
                id="SEC-006",
                severity="HIGH",
                category="security",
                line=i,
                message=f'Image "{m.group(1)}:latest" uses the mutable :latest tag. '
                        f'A compromised upstream update will silently affect your builds.',
                suggestion=f'Pin to a specific digest: FROM {m.group(1)}@sha256:<digest>',
                resource=m.group(1),
            ))
    return findings


def rule_running_as_root(lines, content) -> list[Finding]:
    """SEC-008 — Container runs as root (no USER instruction)."""
    findings = []
    has_user = any(re.match(r'^\s*USER\s+(?!root\b)', line, re.IGNORECASE)
                   for line in lines)
    has_from = any(re.match(r'^\s*FROM\s+', line, re.IGNORECASE) for line in lines)

    if has_from and not has_user:
        # Find line of last FROM
        last_from = 0
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*FROM\s+', line, re.IGNORECASE):
                last_from = i
        findings.append(Finding(
            id="SEC-008",
            severity="HIGH",
            category="security",
            line=last_from,
            message="Container runs as root — no USER instruction found. "
                    "A container breakout gives full root access to the host.",
            suggestion="Add 'RUN useradd -r appuser && USER appuser' before CMD/ENTRYPOINT.",
        ))
    return findings


def rule_secrets_in_env(lines, content) -> list[Finding]:
    """SEC-005 — Secrets hardcoded in ENV instructions."""
    findings = []
    secret_pattern = re.compile(
        r'^\s*ENV\s+(?:PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|ACCESS_KEY|AUTH)\s*[=\s]',
        re.IGNORECASE
    )
    value_pattern = re.compile(
        r'ENV\s+\S*(?:PASSWORD|SECRET|TOKEN|KEY|AUTH)\S*\s+"?(?!"\$|\$)[^"\s]{4,}',
        re.IGNORECASE
    )
    for i, line in enumerate(lines, 1):
        if secret_pattern.match(line) or value_pattern.search(line):
            findings.append(Finding(
                id="SEC-005",
                severity="CRITICAL",
                category="security",
                line=i,
                message="Possible secret value hardcoded in Dockerfile ENV instruction. "
                        "Secrets baked into images are visible in `docker history`.",
                suggestion="Use Docker secrets, build args at runtime, or inject via orchestrator env vars. "
                           "Never bake credentials into an image layer.",
            ))
    return findings


def rule_no_healthcheck(lines, content) -> list[Finding]:
    """REL-002 — No HEALTHCHECK instruction."""
    findings = []
    has_healthcheck = any(
        re.match(r'^\s*HEALTHCHECK\s+', line, re.IGNORECASE) for line in lines
    )
    has_from = any(re.match(r'^\s*FROM\s+', line, re.IGNORECASE) for line in lines)

    if has_from and not has_healthcheck:
        # Report on the CMD/ENTRYPOINT line if present, else line 1
        report_line = 1
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*(CMD|ENTRYPOINT)\s+', line, re.IGNORECASE):
                report_line = i
                break
        findings.append(Finding(
            id="REL-002",
            severity="MEDIUM",
            category="reliability",
            line=report_line,
            message="Dockerfile has no HEALTHCHECK instruction. "
                    "Docker/Kubernetes can't detect if your application is actually serving traffic.",
            suggestion="Add: HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/health || exit 1",
        ))
    return findings


def rule_add_vs_copy(lines, content) -> list[Finding]:
    """PERF-002 — ADD used for local files instead of COPY."""
    findings = []
    pattern = re.compile(r'^\s*ADD\s+(?!https?://)', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        if pattern.match(line):
            findings.append(Finding(
                id="PERF-002",
                severity="LOW",
                category="performance",
                line=i,
                message="ADD used for local files. ADD has hidden behaviour (auto-extracts tarballs, fetches URLs) — use COPY for simple file copies.",
                suggestion="Replace ADD with COPY for local file copies. Only use ADD for URLs or tar auto-extraction.",
            ))
    return findings


def rule_multiple_run_layers(lines, content) -> list[Finding]:
    """PERF-003 — Multiple consecutive RUN instructions inflate image size."""
    findings = []
    run_lines = [i for i, line in enumerate(lines, 1)
                 if re.match(r'^\s*RUN\s+', line, re.IGNORECASE)]

    # If there are 5+ RUN instructions, flag the first set
    if len(run_lines) >= 5:
        findings.append(Finding(
            id="PERF-003",
            severity="LOW",
            category="performance",
            line=run_lines[0],
            message=f"Found {len(run_lines)} RUN instructions. Each creates a new layer, inflating image size.",
            suggestion="Chain commands with && and use a single RUN: RUN apt-get update && apt-get install -y pkg1 pkg2 && rm -rf /var/lib/apt/lists/*",
        ))
    return findings


# ─── Docker Compose Rules ─────────────────────────────────────────────────────

def rule_compose_privileged(lines, content) -> list[Finding]:
    """SEC-013 — Privileged containers in docker-compose."""
    findings = []
    pattern = re.compile(r'privileged\s*:\s*true', re.IGNORECASE)
    for i in [j for j, line in enumerate(lines, 1) if pattern.search(line)]:
        findings.append(Finding(
            id="SEC-013",
            severity="CRITICAL",
            category="security",
            line=i,
            message="Container runs in privileged mode — has unrestricted access to the host kernel.",
            suggestion="Remove 'privileged: true'. Use specific capabilities with 'cap_add' instead.",
        ))
    return findings


def rule_compose_host_network(lines, content) -> list[Finding]:
    """SEC-014 — Host network mode bypasses network isolation."""
    findings = []
    pattern = re.compile(r'network_mode\s*:\s*["\']?host["\']?')
    for i in [j for j, line in enumerate(lines, 1) if pattern.search(line)]:
        findings.append(Finding(
            id="SEC-014",
            severity="HIGH",
            category="security",
            line=i,
            message="Container uses host network mode — bypasses Docker network isolation.",
            suggestion="Use bridge networking and expose only required ports with 'ports:' mapping.",
        ))
    return findings


# ─── Rule runners ─────────────────────────────────────────────────────────────

_DOCKERFILE_RULES = [
    rule_latest_tag,
    rule_running_as_root,
    rule_secrets_in_env,
    rule_no_healthcheck,
    rule_add_vs_copy,
    rule_multiple_run_layers,
]

_COMPOSE_RULES = [
    rule_compose_privileged,
    rule_compose_host_network,
]


def run_rules(content: str) -> list[Finding]:
    """Run Dockerfile rules."""
    lines = content.splitlines()
    findings: list[Finding] = []
    for rule in _DOCKERFILE_RULES:
        try:
            findings.extend(rule(lines, content))
        except Exception:
            pass
    return findings


def run_rules_compose(content: str) -> list[Finding]:
    """Run docker-compose rules."""
    lines = content.splitlines()
    findings: list[Finding] = []
    for rule in _COMPOSE_RULES:
        try:
            findings.extend(rule(lines, content))
        except Exception:
            pass
    return findings
