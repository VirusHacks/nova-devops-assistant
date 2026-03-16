"""
Terraform Rules — checks *.tf and *.tfvars files.

Each rule is a function: (lines: list[str], content: str) -> list[Finding]
run_rules() collects all findings from every rule.
"""

from __future__ import annotations
import re
from ..models import Finding


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _find_line(lines: list[str], pattern: re.Pattern) -> int:
    """Return 1-indexed line number of first match, or 0."""
    for i, line in enumerate(lines, 1):
        if pattern.search(line):
            return i
    return 0


def _find_all_lines(lines: list[str], pattern: re.Pattern) -> list[int]:
    return [i for i, line in enumerate(lines, 1) if pattern.search(line)]


def _env_tag(content: str) -> str:
    """Extract environment tag value if present."""
    m = re.search(r'(?:Environment|environment|env)\s*=\s*"([^"]+)"', content)
    return m.group(1).lower() if m else ""


def _is_dev_env(content: str) -> bool:
    env = _env_tag(content)
    return any(kw in env for kw in ("dev", "test", "staging", "qa", "sandbox"))


# ─── Individual Rules ─────────────────────────────────────────────────────────

def rule_expensive_instance(lines, content) -> list[Finding]:
    """COST-001 — Oversized EC2/RDS instance types."""
    findings = []
    pattern = re.compile(r'instance_type\s*=\s*"([^"]+)"')
    class_pattern = re.compile(r'instance_class\s*=\s*"([^"]+)"')

    expensive = re.compile(
        r"\b(p[2-9]|g[3-9]|inf[0-9]|x1|x2|u-|z1d|.+\.24xlarge|.+\.16xlarge"
        r"|.+\.12xlarge|.+\.metal|.+\.(?:2?4|16|12)xlarge)\b"
    )

    for i, line in enumerate(lines, 1):
        for pat in (pattern, class_pattern):
            m = pat.search(line)
            if m:
                inst = m.group(1)
                if expensive.search(inst):
                    qualifier = " in a Dev/Test environment" if _is_dev_env(content) else ""
                    findings.append(Finding(
                        id="COST-001",
                        severity="CRITICAL" if _is_dev_env(content) else "HIGH",
                        category="cost",
                        line=i,
                        message=f'Oversized instance "{inst}"{qualifier}. '
                                f'This can cost $1,000–$10,000+/month.',
                        suggestion='Use t3.medium or c5.large for dev; right-size prod with CloudWatch metrics.',
                        resource=inst,
                    ))
    return findings


def rule_nat_gateway(lines, content) -> list[Finding]:
    """COST-002 — NAT Gateway has high per-GB data transfer costs."""
    findings = []
    pattern = re.compile(r'resource\s+"aws_nat_gateway"')
    for i in _find_all_lines(lines, pattern):
        findings.append(Finding(
            id="COST-002",
            severity="MEDIUM",
            category="cost",
            line=i,
            message="NAT Gateway charges $0.045/GB processed. High-traffic workloads see thousands of dollars/month.",
            suggestion="Use VPC Endpoints (PrivateLink) for AWS services (S3, DynamoDB, etc.) to eliminate NAT costs.",
        ))
    return findings


def rule_gp2_ebs(lines, content) -> list[Finding]:
    """COST-003 — GP2 EBS is superseded by GP3 (same perf, 20% cheaper)."""
    findings = []
    pattern = re.compile(r'volume_type\s*=\s*"gp2"')
    for i in _find_all_lines(lines, pattern):
        findings.append(Finding(
            id="COST-003",
            severity="LOW",
            category="cost",
            line=i,
            message='EBS volume uses type "gp2". GP3 provides the same performance at 20% lower cost.',
            suggestion='Change volume_type = "gp3". No downtime required for in-place migration.',
        ))
    return findings


def rule_no_s3_lifecycle(lines, content) -> list[Finding]:
    """COST-005 — S3 bucket with no lifecycle policy."""
    findings = []
    bucket_pattern = re.compile(r'resource\s+"aws_s3_bucket"\s+"([^"]+)"')
    lifecycle_pattern = re.compile(r'lifecycle_rule|lifecycle_configuration')

    for i, line in enumerate(lines, 1):
        m = bucket_pattern.search(line)
        if m and not lifecycle_pattern.search(content):
            findings.append(Finding(
                id="COST-005",
                severity="LOW",
                category="cost",
                line=i,
                message=f'S3 bucket "{m.group(1)}" has no lifecycle policy. Old objects accumulate indefinitely.',
                suggestion="Add lifecycle_configuration to transition objects to S3-IA after 30d and Glacier after 90d.",
                resource=m.group(1),
            ))
            break  # one finding per bucket block is enough
    return findings


def rule_rds_multaz_dev(lines, content) -> list[Finding]:
    """COST-006 — Multi-AZ RDS in Dev/Test environments (2× cost)."""
    findings = []
    if not _is_dev_env(content):
        return findings
    pattern = re.compile(r'multi_az\s*=\s*true')
    for i in _find_all_lines(lines, pattern):
        findings.append(Finding(
            id="COST-006",
            severity="HIGH",
            category="cost",
            line=i,
            message="Multi-AZ RDS enabled in a Dev/Test environment — doubles the instance cost with no benefit.",
            suggestion='Set multi_az = false for non-production environments.',
        ))
    return findings


def rule_iam_wildcard(lines, content) -> list[Finding]:
    """SEC-001 — IAM Action:* or Resource:* grants unlimited AWS permissions."""
    findings = []
    action_pat = re.compile(r'"[Aa]ction"\s*:\s*"\*"')
    resource_pat = re.compile(r'"[Rr]esource"\s*:\s*"\*"')

    # Also catch HCL format
    hcl_action = re.compile(r'actions\s*=\s*\[.*"\*".*\]')
    hcl_resource = re.compile(r'resources\s*=\s*\[.*"\*".*\]')

    for i, line in enumerate(lines, 1):
        if action_pat.search(line) or hcl_action.search(line):
            findings.append(Finding(
                id="SEC-001",
                severity="CRITICAL",
                category="security",
                line=i,
                message='IAM policy uses Action: "*" — grants unrestricted access to ALL AWS services.',
                suggestion='Scope actions to specific permissions: ["s3:GetObject", "dynamodb:PutItem"] etc.',
            ))
        if resource_pat.search(line) or hcl_resource.search(line):
            findings.append(Finding(
                id="SEC-001b",
                severity="HIGH",
                category="security",
                line=i,
                message='IAM policy uses Resource: "*" — applies permissions to ALL resources in the account.',
                suggestion='Scope to specific ARNs: "arn:aws:s3:::my-bucket/*"',
            ))
    return findings


def rule_open_ssh_rdp(lines, content) -> list[Finding]:
    """SEC-002 — Security group allows SSH/RDP from the internet."""
    findings = []
    cidr_any = re.compile(r'cidr_blocks\s*=\s*\[[^\]]*"0\.0\.0\.0/0"')
    port_ssh = re.compile(r'from_port\s*=\s*22\b|to_port\s*=\s*22\b')
    port_rdp = re.compile(r'from_port\s*=\s*3389\b|to_port\s*=\s*3389\b')

    # Simple block-level scan: find ingress blocks with 0.0.0.0/0 + port 22 or 3389
    blocks = re.finditer(
        r'ingress\s*\{([^}]+)\}', content, re.DOTALL
    )
    for block in blocks:
        body = block.group(1)
        if not re.search(r'"0\.0\.0\.0/0"', body):
            continue
        line_no = content[:block.start()].count("\n") + 1
        if re.search(r'from_port\s*=\s*22\b', body):
            findings.append(Finding(
                id="SEC-002",
                severity="CRITICAL",
                category="security",
                line=line_no,
                message="Security group allows SSH (port 22) from 0.0.0.0/0 — exposes instances to the entire internet.",
                suggestion="Restrict cidr_blocks to your office IP or use AWS Systems Manager Session Manager instead.",
            ))
        if re.search(r'from_port\s*=\s*3389\b', body):
            findings.append(Finding(
                id="SEC-002",
                severity="CRITICAL",
                category="security",
                line=line_no,
                message="Security group allows RDP (port 3389) from 0.0.0.0/0 — a common ransomware entry point.",
                suggestion="Restrict cidr_blocks to specific IP ranges or use a VPN.",
            ))
    return findings


def rule_public_s3(lines, content) -> list[Finding]:
    """SEC-003 — S3 bucket with public ACL."""
    findings = []
    pattern = re.compile(r'acl\s*=\s*"(public-read|public-read-write|authenticated-read)"')
    for i, line in enumerate(lines, 1):
        m = pattern.search(line)
        if m:
            severity = "CRITICAL" if "write" in m.group(1) else "HIGH"
            findings.append(Finding(
                id="SEC-003",
                severity=severity,
                category="security",
                line=i,
                message=f'S3 bucket ACL is "{m.group(1)}" — bucket contents are publicly accessible.',
                suggestion='Remove ACL or set acl = "private". Use bucket policies for controlled access.',
            ))
    return findings


def rule_rds_public(lines, content) -> list[Finding]:
    """SEC-004 — RDS instance publicly accessible from the internet."""
    findings = []
    pattern = re.compile(r'publicly_accessible\s*=\s*true')
    for i in _find_all_lines(lines, pattern):
        findings.append(Finding(
            id="SEC-004",
            severity="CRITICAL",
            category="security",
            line=i,
            message="RDS instance is publicly accessible — the database endpoint is reachable from the internet.",
            suggestion='Set publicly_accessible = false and use a bastion host or VPN for access.',
        ))
    return findings


def rule_plaintext_secrets(lines, content) -> list[Finding]:
    """SEC-005 — Plaintext secrets in environment variables."""
    findings = []
    secret_key = re.compile(
        r'(?:password|secret|token|api_key|private_key|access_key|auth)\s*=\s*"(?!data\.|var\.|local\.|aws_|\$)[^"]{4,}"',
        re.IGNORECASE
    )
    for i, line in enumerate(lines, 1):
        if secret_key.search(line):
            findings.append(Finding(
                id="SEC-005",
                severity="CRITICAL",
                category="security",
                line=i,
                message="Possible plaintext secret in Terraform variable. Secrets should never be hardcoded.",
                suggestion="Use aws_ssm_parameter or aws_secretsmanager_secret data sources. Never commit secrets.",
            ))
    return findings


def rule_lambda_no_dlq(lines, content) -> list[Finding]:
    """REL-001 — Lambda function without a Dead Letter Queue."""
    findings = []
    lambda_blocks = list(re.finditer(
        r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{', content
    ))
    has_dlq = bool(re.search(r'dead_letter_config', content))

    for block in lambda_blocks:
        if not has_dlq:
            line_no = content[:block.start()].count("\n") + 1
            findings.append(Finding(
                id="REL-001",
                severity="HIGH",
                category="reliability",
                line=line_no,
                message=f'Lambda "{block.group(1)}" has no Dead Letter Queue. '
                        f'Failed async invocations are silently dropped.',
                suggestion='Add dead_letter_config { target_arn = aws_sqs_queue.dlq.arn } to the Lambda resource.',
                resource=block.group(1),
            ))
    return findings


def rule_missing_tags(lines, content) -> list[Finding]:
    """REL-004 — AWS resources missing required tags (Environment, Owner)."""
    findings = []
    resource_pattern = re.compile(r'^resource\s+"aws_', re.MULTILINE)
    has_env_tag = bool(re.search(r'"Environment"\s*:', content) or
                       re.search(r'Environment\s*=', content))
    has_owner_tag = bool(re.search(r'"Owner"\s*:', content) or
                         re.search(r'Owner\s*=', content))

    if not has_env_tag or not has_owner_tag:
        first_resource = resource_pattern.search(content)
        if first_resource:
            line_no = content[:first_resource.start()].count("\n") + 1
            missing = []
            if not has_env_tag:
                missing.append("Environment")
            if not has_owner_tag:
                missing.append("Owner")
            findings.append(Finding(
                id="REL-004",
                severity="LOW",
                category="reliability",
                line=line_no,
                message=f'Resources missing required tags: {", ".join(missing)}. '
                        f'Untagged resources cause attribution failures in FinOps reviews.',
                suggestion='Add tags block with at minimum: Environment, Owner, CostCenter.',
            ))
    return findings


# ─── Rule runner ──────────────────────────────────────────────────────────────

_RULES = [
    rule_expensive_instance,
    rule_nat_gateway,
    rule_gp2_ebs,
    rule_no_s3_lifecycle,
    rule_rds_multaz_dev,
    rule_iam_wildcard,
    rule_open_ssh_rdp,
    rule_public_s3,
    rule_rds_public,
    rule_plaintext_secrets,
    rule_lambda_no_dlq,
    rule_missing_tags,
]


def run_rules(content: str) -> list[Finding]:
    """Run all Terraform rules against file content. Returns list of Finding."""
    lines = content.splitlines()
    findings: list[Finding] = []
    for rule in _RULES:
        try:
            findings.extend(rule(lines, content))
        except Exception:
            pass  # never let a buggy rule crash a scan
    return findings
