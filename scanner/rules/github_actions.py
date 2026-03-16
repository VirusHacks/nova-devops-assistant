"""
GitHub Actions Rules — checks .github/workflows/*.yml and buildspec.yml files.
"""

from __future__ import annotations
import re
import yaml
from typing import Any
from ..models import Finding


def _safe_load(content: str) -> Any:
    try:
        return yaml.safe_load(content)
    except Exception:
        return None


# ─── Rules ────────────────────────────────────────────────────────────────────

def rule_unpinned_action(lines, content) -> list[Finding]:
    """SEC-007 — GitHub Actions not pinned to a full commit SHA."""
    findings = []
    # Matches: uses: actions/something@v3 or @main or @master (not @abc1234...)
    pattern = re.compile(r'uses:\s*(\S+)@(v\d+[\w.]*|main|master|latest|HEAD)', re.IGNORECASE)
    sha_pattern = re.compile(r'@[0-9a-f]{40}')

    for i, line in enumerate(lines, 1):
        m = pattern.search(line)
        if m and not sha_pattern.search(line):
            action = m.group(1)
            ref = m.group(2)
            findings.append(Finding(
                id="SEC-007",
                severity="HIGH",
                category="security",
                line=i,
                message=f'Action "{action}@{ref}" uses a mutable ref. '
                        f'If the action maintainer moves the tag, malicious code could run in your CI.',
                suggestion=f'Pin to a full commit SHA: uses: {action}@<full-40-char-sha> # {ref}',
                resource=action,
            ))
    return findings


def rule_no_job_timeout(lines, content) -> list[Finding]:
    """REL-005 — Workflow jobs with no timeout-minutes."""
    findings = []
    data = _safe_load(content)
    if not isinstance(data, dict):
        return findings

    jobs = data.get("jobs", {})
    if not isinstance(jobs, dict):
        return findings

    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            continue
        if "timeout-minutes" not in job_config:
            # Find the line of this job definition
            job_line = 0
            job_pattern = re.compile(rf'^\s*{re.escape(job_name)}\s*:', re.MULTILINE)
            m = job_pattern.search(content)
            if m:
                job_line = content[:m.start()].count("\n") + 1
            findings.append(Finding(
                id="REL-005",
                severity="MEDIUM",
                category="reliability",
                line=job_line,
                message=f'Job "{job_name}" has no timeout-minutes. '
                        f"A hung step consumes GitHub Actions minutes for up to 6 hours.",
                suggestion=f'Add timeout-minutes: 30 under the "{job_name}" job.',
                resource=job_name,
            ))
    return findings


def rule_hardcoded_secrets(lines, content) -> list[Finding]:
    """SEC-010 — Hardcoded secrets or tokens in workflow env vars."""
    findings = []
    # Detects patterns like: TOKEN: "abc123" or PASSWORD: mysecret (not ${{ secrets.X }})
    secret_pattern = re.compile(
        r'(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|ACCESS_KEY)\s*:\s*(?!"\s*\$\{\{|\$\{\{)["\']?[A-Za-z0-9+/=_\-]{8,}',
        re.IGNORECASE
    )
    for i, line in enumerate(lines, 1):
        if secret_pattern.search(line) and "${{" not in line:
            findings.append(Finding(
                id="SEC-010",
                severity="CRITICAL",
                category="security",
                line=i,
                message="Possible hardcoded secret in workflow env variable. "
                        "Anyone with repo access can read workflow files.",
                suggestion='Use ${{ secrets.YOUR_SECRET_NAME }} and store values in GitHub Secrets.',
            ))
    return findings


def rule_pull_request_target_injection(lines, content) -> list[Finding]:
    """SEC-011 — pull_request_target + checkout of PR code = script injection risk."""
    findings = []
    has_prt = bool(re.search(r'pull_request_target', content))
    if not has_prt:
        return findings

    has_checkout_pr = bool(re.search(
        r'ref.*pull_request|pull_request.*ref|head\.ref|head\.sha',
        content
    ))
    if has_checkout_pr:
        line_no = next(
            (i for i, line in enumerate(lines, 1) if 'pull_request_target' in line), 1
        )
        findings.append(Finding(
            id="SEC-011",
            severity="CRITICAL",
            category="security",
            line=line_no,
            message="pull_request_target trigger with PR head checkout is a known CI injection attack vector. "
                    "Malicious PRs can execute arbitrary code with write tokens.",
            suggestion="Avoid checking out PR code in pull_request_target workflows. "
                       "If needed, validate the PR author first or use environment protection rules.",
        ))
    return findings


def rule_no_permissions_block(lines, content) -> list[Finding]:
    """SEC-012 — Workflow has no permissions block (defaults to write-all)."""
    findings = []
    data = _safe_load(content)
    if not isinstance(data, dict):
        return findings

    has_top_permissions = "permissions" in data
    jobs = data.get("jobs", {}) or {}
    all_jobs_have_permissions = all(
        "permissions" in (job or {})
        for job in jobs.values()
        if isinstance(job, dict)
    )

    if not has_top_permissions and not all_jobs_have_permissions and jobs:
        findings.append(Finding(
            id="SEC-012",
            severity="MEDIUM",
            category="security",
            line=1,
            message="Workflow has no permissions block. Default is write access to all scopes — "
                    "a compromised step can push commits, create releases, or modify issues.",
            suggestion="Add 'permissions: read-all' at the top level, then grant specific write permissions per job.",
        ))
    return findings


def rule_self_hosted_runner(lines, content) -> list[Finding]:
    """SEC-015 — Self-hosted runners on public repos are dangerous."""
    findings = []
    pattern = re.compile(r'runs-on\s*:\s*self-hosted', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        if pattern.search(line):
            findings.append(Finding(
                id="SEC-015",
                severity="HIGH",
                category="security",
                line=i,
                message="Self-hosted runner detected. On public repos, any fork can trigger "
                        "workflows and execute code on your infrastructure.",
                suggestion="Ensure the workflow trigger requires approval for external contributors "
                           "or use GitHub-hosted runners for public repositories.",
            ))
    return findings


# ─── Rule runner ──────────────────────────────────────────────────────────────

_RULES = [
    rule_unpinned_action,
    rule_no_job_timeout,
    rule_hardcoded_secrets,
    rule_pull_request_target_injection,
    rule_no_permissions_block,
    rule_self_hosted_runner,
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
