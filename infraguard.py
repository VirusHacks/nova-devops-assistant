"""
InfraGuard CLI Utility.

Features:
  - scan: Run local scan on a directory
  - install-hook: Install a Git pre-commit hook to block bad deploys
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner.engine import scan_repo


def _install_hook(repo_dir: str):
    """Installs a .git/hooks/pre-commit script."""
    git_dir = Path(repo_dir) / ".git"
    if not git_dir.exists():
        print(f"Error: {repo_dir} is not a Git repository.")
        sys.exit(1)

    hook_path = git_dir / "hooks" / "pre-commit"
    
    hook_content = f"""#!/usr/bin/env python
import sys
import os
import subprocess

# Run InfraGuard pre-commit scan
print("🔐 InfraGuard: Scanning staged files for risks...")

# Get staged files
try:
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], 
        text=True
    ).splitlines()
except Exception:
    print("Error getting staged files")
    sys.exit(1)

if not staged:
    sys.exit(0)

# Import and run scanner
# Note: In a real app, this would use a pip-installed 'infraguard' package.
# For this hackathon, we assume the script is run from the project root.
sys.path.insert(0, r"{Path(__file__).parent.absolute()}")
from scanner.engine import scan_file
from scanner.detector import is_infra_file

findings_found = 0
critical_found = 0

for file_path in staged:
    if not is_infra_file(file_path) or not os.path.exists(file_path):
        continue
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    result = scan_file(file_path, content)
    if result and result["findings"]:
        print(f"\\n  FILE: {{file_path}} (Grade {{result['grade']}})")
        for f in result["findings"]:
            findings_found += 1
            emoji = {{"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}}.get(f["severity"], "🔵")
            print(f"    {{emoji}} [{{f['severity']}}] {{f['id']}}: {{f['message']}}")
            if f["severity"] == "CRITICAL":
                critical_found += 1

if critical_found > 0:
    print(f"\\n🚫 COMMIT BLOCKED: InfraGuard found {{critical_found}} CRITICAL issues.")
    print("Resolve these risks before committing or use --no-verify to bypass.")
    sys.exit(1)

if findings_found > 0:
    print(f"\\n✅ Scan complete. Found {{findings_found}} non-critical issues. Proceeding.")
else:
    print("✅ No infra issues found.")

sys.exit(0)
"""
    
    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)
    
    # Make executable on Unix-like systems
    if os.name != "nt":
        os.chmod(hook_path, 0o755)
    
    print(f"✅ Git pre-commit hook installed to {hook_path}")
    print("It will now automatically block any commit containing CRITICAL infrastructure risks.")


def main():
    parser = argparse.ArgumentParser(description="InfraGuard CLI")
    subparsers = parser.add_subparsers(dest="command")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan a directory")
    scan_parser.add_argument("path", default=".", help="Path to directory or file")

    # install-hook command
    hook_parser = subparsers.add_parser("install-hook", help="Install Git pre-commit hook")
    hook_parser.add_argument("--dir", default=".", help="Git repo root")

    args = parser.parse_args()

    if args.command == "scan":
        path = Path(args.path)
        if path.is_file():
            # Scan single file
            from scanner.engine import scan_file
            content = path.read_text(encoding="utf-8")
            result = scan_file(str(path), content)
            print(json.dumps(result, indent=2))
        else:
            # Scan directory
            from scanner.detector import is_infra_file
            files = {}
            for p in path.glob("**/*"):
                if p.is_file() and is_infra_file(str(p)):
                    files[str(p)] = p.read_text(encoding="utf-8", errors="replace")
            
            result = scan_repo(files)
            print(f"Scanned {result['files_scanned']} files. Score: {result['overall_score']}/100 ({result['overall_grade']})")
            print(f"Findings: {result['total_findings']}")
            if result["total_findings"] > 0:
                print(json.dumps(result["severity_counts"], indent=2))

    elif args.command == "install-hook":
        _install_hook(args.dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
