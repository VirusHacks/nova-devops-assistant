"""
SAM / CloudFormation Rules — checks template.yaml, serverless.yml files.
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


def _find_line(lines: list[str], text: str) -> int:
    for i, line in enumerate(lines, 1):
        if text in line:
            return i
    return 0


def _get_resources(data: dict) -> dict:
    return (data or {}).get("Resources", {}) or {}


# ─── Rules ────────────────────────────────────────────────────────────────────

def rule_lambda_no_dlq(lines, content) -> list[Finding]:
    """REL-001 — Lambda function without a Dead Letter Queue."""
    findings = []
    data = _safe_load(content) or {}
    resources = _get_resources(data)

    for res_name, res in (resources or {}).items():
        if not isinstance(res, dict):
            continue
        if res.get("Type") not in ("AWS::Lambda::Function", "AWS::Serverless::Function"):
            continue
        props = res.get("Properties", {}) or {}
        dlq = props.get("DeadLetterConfig") or props.get("EventInvokeConfig")
        if not dlq:
            line_no = _find_line(lines, res_name)
            findings.append(Finding(
                id="REL-001",
                severity="HIGH",
                category="reliability",
                line=line_no,
                message=f'Lambda "{res_name}" has no Dead Letter Queue. '
                        f'Failed async invocations are silently discarded.',
                suggestion='Add DeadLetterConfig: {TargetArn: !GetAtt MyDLQ.Arn} and create an SQS queue resource.',
                resource=res_name,
            ))
    return findings


def rule_iam_resource_wildcard(lines, content) -> list[Finding]:
    """SEC-001 — SAM Policies with Resource: * grant full AWS access."""
    findings = []
    data = _safe_load(content) or {}
    resources = _get_resources(data)

    for res_name, res in (resources or {}).items():
        if not isinstance(res, dict):
            continue
        props = res.get("Properties", {}) or {}
        policies = props.get("Policies", []) or []

        for policy in policies:
            if not isinstance(policy, dict):
                continue
            statements = policy.get("Statement", []) or []
            for stmt in statements:
                if not isinstance(stmt, dict):
                    continue
                resource = stmt.get("Resource", "")
                action = stmt.get("Action", "")
                if resource == "*" or action == "*":
                    line_no = _find_line(lines, res_name)
                    findings.append(Finding(
                        id="SEC-001",
                        severity="CRITICAL" if action == "*" else "HIGH",
                        category="security",
                        line=line_no,
                        message=f'IAM policy on "{res_name}" uses {"Action: *" if action == "*" else "Resource: *"}. '
                                f'This grants {"all AWS actions" if action == "*" else "access to all resources"}.',
                        suggestion='Scope to specific actions and resource ARNs. Use SAM policy templates like DynamoDBCrudPolicy.',
                        resource=res_name,
                    ))
    return findings


def rule_lambda_high_timeout(lines, content) -> list[Finding]:
    """COST-004 — Lambda timeout over 300s balloons costs on runaway functions."""
    findings = []
    data = _safe_load(content) or {}

    # Check Globals first
    globals_ = (data or {}).get("Globals", {}) or {}
    global_timeout = (globals_.get("Function") or {}).get("Timeout", 0)
    if global_timeout and int(global_timeout) > 300:
        line_no = _find_line(lines, "Timeout")
        findings.append(Finding(
            id="COST-004",
            severity="MEDIUM",
            category="cost",
            line=line_no,
            message=f"Global Lambda timeout is {global_timeout}s. "
                    f"If a function hangs, it bills at maximum duration ({global_timeout}s × invocations).",
            suggestion="Use a timeout proportional to p99 execution time + 20%. Typically 30-60s for API functions.",
        ))
        return findings  # No need to check individual functions

    resources = _get_resources(data)
    for res_name, res in (resources or {}).items():
        if not isinstance(res, dict):
            continue
        if res.get("Type") not in ("AWS::Lambda::Function", "AWS::Serverless::Function"):
            continue
        props = res.get("Properties", {}) or {}
        timeout = props.get("Timeout", 0)
        if timeout and int(timeout) > 300:
            line_no = _find_line(lines, res_name)
            findings.append(Finding(
                id="COST-004",
                severity="MEDIUM",
                category="cost",
                line=line_no,
                message=f'Lambda "{res_name}" timeout is {timeout}s. '
                        f'Runaway invocations bill at full duration.',
                suggestion="Reduce timeout to expected p99 + buffer. Add alarming on Duration metric approaching timeout.",
                resource=res_name,
            ))
    return findings


def rule_no_log_retention(lines, content) -> list[Finding]:
    """REL-003 — CloudWatch Log Groups with no retention policy (logs forever)."""
    findings = []
    data = _safe_load(content) or {}
    resources = _get_resources(data)

    for res_name, res in (resources or {}).items():
        if not isinstance(res, dict):
            continue
        if res.get("Type") != "AWS::Logs::LogGroup":
            continue
        props = res.get("Properties", {}) or {}
        if not props.get("RetentionInDays"):
            line_no = _find_line(lines, res_name)
            findings.append(Finding(
                id="REL-003",
                severity="LOW",
                category="cost",
                line=line_no,
                message=f'Log group "{res_name}" has no retention policy. '
                        f'Logs accumulate forever, increasing CloudWatch storage costs.',
                suggestion="Add RetentionInDays: 30 (or 7 for dev, 90 for prod audit requirements).",
                resource=res_name,
            ))
    return findings


def rule_lambda_no_xray(lines, content) -> list[Finding]:
    """PERF-001 — Lambda functions without X-Ray tracing enabled."""
    findings = []
    data = _safe_load(content) or {}

    # Check Globals
    globals_ = (data or {}).get("Globals", {}) or {}
    global_tracing = (globals_.get("Function") or {}).get("Tracing", "")
    if global_tracing and global_tracing.lower() == "active":
        return []  # Enabled globally — no issue

    resources = _get_resources(data)
    for res_name, res in (resources or {}).items():
        if not isinstance(res, dict):
            continue
        if res.get("Type") not in ("AWS::Lambda::Function", "AWS::Serverless::Function"):
            continue
        props = res.get("Properties", {}) or {}
        tracing = props.get("Tracing", "") or props.get("TracingConfig", {})
        if isinstance(tracing, dict):
            tracing = tracing.get("Mode", "")

        if str(tracing).lower() not in ("active", "passthrough"):
            line_no = _find_line(lines, res_name)
            findings.append(Finding(
                id="PERF-001",
                severity="LOW",
                category="performance",
                line=line_no,
                message=f'Lambda "{res_name}" has no X-Ray tracing. '
                        f'Cold starts and latency spikes will be invisible in production.',
                suggestion='Add Tracing: Active in the function properties or in Globals.Function.',
                resource=res_name,
            ))
    return findings


def rule_api_gateway_no_throttling(lines, content) -> list[Finding]:
    """REL-009 — API Gateway stage with no throttling can be abused."""
    findings = []
    data = _safe_load(content) or {}
    resources = _get_resources(data)

    for res_name, res in (resources or {}).items():
        if not isinstance(res, dict):
            continue
        if res.get("Type") not in ("AWS::Serverless::Api", "AWS::ApiGateway::Stage"):
            continue
        props = res.get("Properties", {}) or {}
        throttling = props.get("MethodSettings") or props.get("BurstLimit") or \
                     (props.get("Auth") or {}).get("UsagePlan")
        if not throttling:
            line_no = _find_line(lines, res_name)
            findings.append(Finding(
                id="REL-009",
                severity="MEDIUM",
                category="reliability",
                line=line_no,
                message=f'API Gateway "{res_name}" has no throttling configured. '
                        f'A traffic spike or abuse can trigger runaway Lambda costs.',
                suggestion="Add ThrottlingBurstLimit and ThrottlingRateLimit in MethodSettings, "
                           "or use a UsagePlan with quota limits.",
                resource=res_name,
            ))
    return findings


# ─── Rule runner ──────────────────────────────────────────────────────────────

_RULES = [
    rule_lambda_no_dlq,
    rule_iam_resource_wildcard,
    rule_lambda_high_timeout,
    rule_no_log_retention,
    rule_lambda_no_xray,
    rule_api_gateway_no_throttling,
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
