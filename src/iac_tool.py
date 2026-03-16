"""
IaC Scanner - Terraform cost analysis tool.
Supports both file path (local) and content string (Lambda).
"""

import json
import re


def _scan_content(content: str, file_name: str = "infra.tf") -> str:
    """Core scan logic - operates on content string."""
    findings = []

    instances = re.findall(r'instance_type\s*=\s*"([^"]+)"', content)
    for inst in instances:
        if "xlarge" in inst or "metal" in inst:
            findings.append({
                "resource_type": "EC2 Instance",
                "value": inst,
                "risk": "High Cost",
                "suggestion": "Check if a smaller instance (e.g., t3.medium) suffices for Dev."
            })

    if "aws_nat_gateway" in content:
        findings.append({
            "resource_type": "NAT Gateway",
            "value": "aws_nat_gateway",
            "risk": "Technical Debt / High Data Cost",
            "suggestion": "Consider using a VPC Endpoint (PrivateLink) to save on data processing fees."
        })

    return json.dumps({
        "file_scanned": file_name,
        "findings": findings,
        "status": "issues_found" if findings else "clean"
    }, indent=2)


def scan_terraform_code(file_path: str) -> str:
    """
    Scans a Terraform file for expensive resources (local use).
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return json.dumps({"error": f"File {file_path} not found."})

    return _scan_content(content, file_path)


def scan_terraform_content(content: str, file_name: str = "infra.tf") -> str:
    """
    Scans Terraform content string for expensive resources (Lambda use).
    """
    if not content:
        return json.dumps({"error": "No content provided."})
    return _scan_content(content, file_name)
