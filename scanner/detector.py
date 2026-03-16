"""
File type detector — maps a file path to its infrastructure type.
Returns None for files that should not be scanned.
"""

import re
from pathlib import Path


# Ordered list of (pattern, file_type) — first match wins
_PATTERNS = [
    # GitHub Actions workflows
    (r"\.github[/\\]workflows[/\\].+\.(yml|yaml)$", "github_actions"),
    # CircleCI
    (r"\.circleci[/\\]config\.(yml|yaml)$", "github_actions"),
    # Terraform
    (r"\.tf$", "terraform"),
    (r"\.tfvars$", "terraform"),
    # SAM / CloudFormation — before generic yaml so template.yaml is caught
    (r"template\.(yml|yaml)$", "sam"),
    (r"serverless\.(yml|yaml)$", "sam"),
    # Kubernetes manifests
    (r"k8s[/\\].+\.(yml|yaml)$", "kubernetes"),
    (r"kubernetes[/\\].+\.(yml|yaml)$", "kubernetes"),
    (r"manifests[/\\].+\.(yml|yaml)$", "kubernetes"),
    (r"helm[/\\].+\.(yml|yaml)$", "kubernetes"),
    # Docker Compose
    (r"docker-compose.*\.(yml|yaml)$", "docker_compose"),
    # Dockerfile
    (r"(^|[/\\])Dockerfile(\.[a-zA-Z0-9]+)?$", "dockerfile"),
    # Buildspec (AWS CodeBuild)
    (r"buildspec\.(yml|yaml)$", "github_actions"),  # Same rule set applies
    # Jenkinsfile
    (r"(^|[/\\])Jenkinsfile$", "jenkinsfile"),
]

_COMPILED = [(re.compile(pat, re.IGNORECASE), ft) for pat, ft in _PATTERNS]


def detect_file_type(file_path: str) -> str | None:
    """
    Detect infrastructure file type from path.

    Returns one of: 'terraform', 'dockerfile', 'docker_compose',
    'github_actions', 'kubernetes', 'sam', 'jenkinsfile', or None.
    """
    normalized = file_path.replace("\\", "/")
    for pattern, file_type in _COMPILED:
        if pattern.search(normalized):
            return file_type
    return None


def is_infra_file(file_path: str) -> bool:
    """Returns True if the file should be scanned by InfraGuard."""
    return detect_file_type(file_path) is not None
