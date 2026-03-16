"""
Shared data models for the InfraGuard scanner.
Kept in a separate module to avoid circular imports between engine and rules.
"""

from dataclasses import dataclass


@dataclass
class Finding:
    id: str            # e.g. "SEC-001"
    severity: str      # CRITICAL | HIGH | MEDIUM | LOW | INFO
    category: str      # cost | security | reliability | performance
    line: int          # 1-indexed line number (0 = whole-file finding)
    message: str       # Human-readable description of the issue
    suggestion: str    # One-liner remediation hint
    resource: str = "" # Resource name / block if identifiable
