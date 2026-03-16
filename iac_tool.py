"""
iac_tool.py — backward-compatible shim.

The real implementation now lives in scanner.engine.
This file keeps the original API intact so backend_server.py
and finops_fame_agent.py continue to work unchanged.
"""

import json
from scanner.engine import scan_content_legacy, scan_file


def scan_terraform_content(content: str, file_name: str = "infra.tf") -> str:
    """Scan Terraform content string. Returns structured JSON string."""
    return scan_content_legacy(content, file_name)


def scan_terraform_code(file_path: str) -> str:
    """
    Scan a Terraform file from disk.
    Simulates an MCP Tool for the 'Actor' agent.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return json.dumps({"error": f"File {file_path} not found."})
    return scan_content_legacy(content, file_path)


if __name__ == "__main__":
    print(scan_terraform_code("infra.tf"))
