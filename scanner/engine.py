"""
InfraGuard Scanner Engine

Main entry point: scan_file(path, content) → structured JSON with risk score.
Supports: terraform, dockerfile, docker_compose, github_actions, kubernetes, sam.
"""

from __future__ import annotations
from dataclasses import asdict
from typing import Any
import json

from .models import Finding
from .detector import detect_file_type
from .rules import terraform, dockerfile, github_actions, kubernetes, sam


# Re-export Finding so callers can import it from engine too
__all__ = ["Finding", "scan_file", "scan_repo", "scan_content_legacy"]


# ─── Severity weights ─────────────────────────────────────────────────────────

_WEIGHTS = {
    "CRITICAL": 25,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 2,
    "INFO": 0,
}

_GRADES = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (45, "D"),
    (0,  "F"),
]


def _calculate_score(findings: list[Finding]) -> int:
    penalty = sum(_WEIGHTS.get(f.severity, 0) for f in findings)
    return max(0, 100 - penalty)


def _score_to_grade(score: int) -> str:
    for threshold, grade in _GRADES:
        if score >= threshold:
            return grade
    return "F"


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts


# ─── Rule dispatch ────────────────────────────────────────────────────────────

_RULE_MAP = {
    "terraform":      terraform.run_rules,
    "dockerfile":     dockerfile.run_rules,
    "docker_compose": dockerfile.run_rules_compose,
    "github_actions": github_actions.run_rules,
    "kubernetes":     kubernetes.run_rules,
    "sam":            sam.run_rules,
}


# ─── Public API ───────────────────────────────────────────────────────────────

def scan_file(file_path: str, content: str) -> dict[str, Any] | None:
    """
    Scan a single file and return a structured result dict, or None if the
    file type is not supported.

    Return shape:
    {
        "file": str,
        "type": str,
        "score": int,        # 0-100
        "grade": str,        # A-F
        "findings": [...],
        "severity_counts": {...},
        "supported": True
    }
    """
    file_type = detect_file_type(file_path)
    if file_type is None or file_type not in _RULE_MAP:
        return None

    rule_fn = _RULE_MAP[file_type]
    findings: list[Finding] = rule_fn(content)
    
    # Enrich findings with metadata (Phase 2)
    enriched_findings = []
    for f in findings:
        fd = asdict(f)
        
        # Simple Cost Prediction for Terraform
        if file_type == "terraform":
            if "instance_type" in content:
                # Mock logic: detect large instances
                if any(x in content for x in ["p3", "g4", "r5", "16xlarge"]):
                    fd["cost_impact"] = "$$$ (High) — High-performance instance detected"
                else:
                    fd["cost_impact"] = "$ (Low) — Standard instance"
        
        # Simple Compliance Mapping
        if "security" in fd["category"].lower():
            fd["compliance"] = "CIS AWS Benchmarks 1.2, SOC2 CC6.1"
        elif "cost" in fd["category"].lower():
            fd["compliance"] = "FinOps Foundation Best Practices"
            
        enriched_findings.append(fd)

    score = _calculate_score(findings)
    grade = _score_to_grade(score)

    return {
        "file": file_path,
        "type": file_type,
        "score": score,
        "grade": grade,
        "findings": enriched_findings,
        "severity_counts": _severity_counts(findings),
        "supported": True,
    }


def scan_repo(files: dict[str, str]) -> dict[str, Any]:
    """
    Scan multiple files at once.
    `files` is a dict of {file_path: content}.

    Returns a repo-level summary:
    {
        "overall_score": int,
        "overall_grade": str,
        "files_scanned": int,
        "file_results": [...],
        "total_findings": int,
        "severity_counts": {...}
    }
    """
    results = []
    total_counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

    for path, content in files.items():
        result = scan_file(path, content)
        if result is not None:
            results.append(result)
            for sev, cnt in result["severity_counts"].items():
                total_counts[sev] = total_counts.get(sev, 0) + cnt

    if results:
        overall_score = int(sum(r["score"] for r in results) / len(results))
    else:
        overall_score = 100

    return {
        "overall_score": overall_score,
        "overall_grade": _score_to_grade(overall_score),
        "files_scanned": len(results),
        "file_results": results,
        "total_findings": sum(len(r["findings"]) for r in results),
        "severity_counts": total_counts,
    }


def scan_content_legacy(content: str, file_name: str = "infra.tf") -> str:
    """Backward-compatible shim for iac_tool.scan_terraform_content."""
    result = scan_file(file_name, content)
    if result is None:
        return json.dumps({"error": f"Unsupported file type: {file_name}"})
    return json.dumps(result, indent=2)
