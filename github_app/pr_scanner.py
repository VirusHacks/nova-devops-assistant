"""
PR Scanner — orchestrates the full InfraGuard review pipeline for a GitHub PR.

Flow:
  1. Fetch changed files from GitHub
  2. Filter to infra files we support
  3. Fetch full file content (not just patch) for each
  4. Run scanner engine → structured findings + score
  5. Call Nova to explain each finding + generate a code fix
  6. Build GitHub review comments (file, line, body with fix)
  7. Post the review + summary comment to the PR
  8. Set commit status (pass if no CRITICAL, fail otherwise)
  9. Save to SQLite
"""

from __future__ import annotations
import os
import logging
from typing import Any

from scanner.engine import scan_file, scan_repo
from scanner.detector import is_infra_file
from nova_client import NovaClient, ThrottlingException
from .auth import get_installation_token
from .github_client import GitHubClient
from . import db

log = logging.getLogger("infraguard.pr_scanner")


# ─── Nova prompt templates ────────────────────────────────────────────────────

_EXPLAIN_PROMPT = """\
You are InfraGuard, an infrastructure security and cost expert.

A static analysis scan found this issue in a {file_type} file:

Rule ID: {rule_id}
Severity: {severity}
Category: {category}
Message: {message}
Suggestion: {suggestion}
File: {file_path}
Line: {line}

Relevant file content (excerpt around the issue):
```
{excerpt}
```

Write a concise GitHub PR review comment. 
CRITICAL: If the issue can be fixed by changing code, provide a GitHub Suggestion block in this exact format:
```suggestion
[CORRECTED CODE]
```
The suggestion must be valid for the {file_type} and replace the line(s) indicated.

Include:
1. A brief explanation of the risk ($, security, or reliability).
2. The suggestion block.
3. Guidance on why the fix works.

Reply only with the comment body. Use markdown."""


_SUMMARY_PROMPT = """\
You are InfraGuard. A PR scan produced these results:

Overall score: {score}/100 ({grade})
Files scanned: {files_scanned}
Findings: {total_findings} total ({critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW)

Top findings:
{top_findings}

Write a concise PR summary comment (max 200 words). Include:
- A one-sentence verdict
- The 2-3 most important findings to fix
- Whether the deploy should be blocked

Format as markdown with a table for the score breakdown."""


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_excerpt(content: str, line: int, context: int = 4) -> str:
    """Return ±context lines around the target line."""
    lines = content.splitlines()
    start = max(0, line - 1 - context)
    end = min(len(lines), line + context)
    numbered = [f"{i+1:4}: {l}" for i, l in enumerate(lines[start:end], start)]
    return "\n".join(numbered)


def _format_severity_emoji(severity: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}.get(
        severity, "⚪"
    )


def _build_review_body(scan_summary: dict) -> str:
    score = scan_summary.get("overall_score", 0)
    grade = scan_summary.get("overall_grade", "F")
    counts = scan_summary.get("severity_counts", {})
    files = scan_summary.get("files_scanned", 0)
    total = scan_summary.get("total_findings", 0)

    grade_emoji = {"A": "✅", "B": "✅", "C": "⚠️", "D": "❌", "F": "🚫"}.get(grade, "❓")

    lines = [
        f"## 🔐 InfraGuard Report {grade_emoji}",
        "",
        f"**Score: {score}/100 (Grade {grade})** · {files} file(s) scanned · {total} finding(s)",
        "",
        "| Category | Score | Findings |",
        "|----------|-------|---------|",
    ]

    for file_result in scan_summary.get("file_results", []):
        lines.append(
            f"| `{file_result['file']}` | {file_result['score']}/100 ({file_result['grade']}) "
            f"| {len(file_result['findings'])} |"
        )

    lines += [
        "",
        "| Severity | Count |",
        "|----------|-------|",
        f"| 🔴 CRITICAL | {counts.get('CRITICAL', 0)} |",
        f"| 🟠 HIGH | {counts.get('HIGH', 0)} |",
        f"| 🟡 MEDIUM | {counts.get('MEDIUM', 0)} |",
        f"| 🔵 LOW | {counts.get('LOW', 0)} |",
        "",
    ]

    if counts.get("CRITICAL", 0) > 0:
        lines.append("⛔ **Merge blocked** — resolve CRITICAL findings before deploying.")
    elif counts.get("HIGH", 0) > 0:
        lines.append("⚠️ **Review required** — HIGH findings should be addressed before merge.")
    else:
        lines.append("✅ **Ready to merge** — no blocking issues found.")

    return "\n".join(lines)


# ─── Nova integration ─────────────────────────────────────────────────────────

def _nova_explain_finding(
    nova: NovaClient,
    finding: dict,
    file_type: str,
    file_path: str,
    content: str,
) -> str:
    """Ask Nova to explain a finding and suggest a fix. Falls back to raw message."""
    excerpt = _extract_excerpt(content, finding.get("line", 1))
    prompt = _EXPLAIN_PROMPT.format(
        file_type=file_type,
        rule_id=finding.get("id", ""),
        severity=finding.get("severity", ""),
        category=finding.get("category", ""),
        message=finding.get("message", ""),
        suggestion=finding.get("suggestion", ""),
        file_path=file_path,
        line=finding.get("line", 0),
        excerpt=excerpt,
    )
    try:
        return nova.invoke(prompt)
    except ThrottlingException:
        return (
            f"**{_format_severity_emoji(finding['severity'])} [{finding['id']}] {finding['severity']}**\n\n"
            f"{finding['message']}\n\n💡 {finding['suggestion']}"
        )
    except Exception as e:
        log.warning("Nova call failed: %s", e)
        return (
            f"**{_format_severity_emoji(finding['severity'])} [{finding['id']}] {finding['severity']}**\n\n"
            f"{finding['message']}\n\n💡 {finding['suggestion']}"
        )


# ─── Main public function ─────────────────────────────────────────────────────

def scan_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    commit_sha: str,
    installation_id: int,
    dashboard_base_url: str = "",
) -> dict[str, Any]:
    """
    Full PR scan pipeline. Posts review + sets commit status.
    Returns the scan result dict.
    """
    log.info("Starting scan: %s/%s PR#%d sha=%s", owner, repo, pr_number, commit_sha)

    # 1. Authenticate
    token = get_installation_token(installation_id)
    gh = GitHubClient(token)

    # 2. Set pending status immediately
    gh.set_commit_status(
        owner, repo, commit_sha,
        state="pending",
        description="InfraGuard is scanning your infrastructure files…",
    )

    try:
        # 3. Fetch PR files
        all_files = gh.get_pr_files(owner, repo, pr_number)
        infra_files = [f for f in all_files if is_infra_file(f["filename"])]

        if not infra_files:
            gh.set_commit_status(
                owner, repo, commit_sha,
                state="success",
                description="No infrastructure files changed — nothing to scan.",
            )
            return {"message": "no_infra_files", "files_scanned": 0}

        log.info("Found %d infra files to scan", len(infra_files))

        # 4. Fetch full content + scan each file
        file_contents: dict[str, str] = {}
        for f in infra_files:
            content = gh.get_file_content(owner, repo, f["filename"], commit_sha)
            if content:
                file_contents[f["filename"]] = content

        scan_summary = scan_repo(file_contents)

        # 5. For each finding, call Nova for explanation
        nova = NovaClient(api_key=os.environ.get("AWS_BEARER_TOKEN_BEDROCK"))
        review_comments = []

        for file_result in scan_summary["file_results"]:
            file_path = file_result["file"]
            file_type = file_result["type"]
            content = file_contents.get(file_path, "")

            for finding in file_result["findings"]:
                # Skip INFO in PR comments to avoid noise
                if finding["severity"] == "INFO":
                    continue

                comment_body = _nova_explain_finding(nova, finding, file_type, file_path, content)
                emoji = _format_severity_emoji(finding["severity"])
                
                # Check for cost/compliance metadata
                metadata_lines = []
                if "cost_impact" in finding:
                    metadata_lines.append(f"💰 **Est. Cost Impact:** {finding['cost_impact']}")
                if "compliance" in finding:
                    metadata_lines.append(f"⚖️ **Compliance:** {finding['compliance']}")
                
                metadata_str = "\n".join(metadata_lines) + "\n\n" if metadata_lines else ""
                full_body = f"{emoji} **[{finding['id']}] {finding['severity']}** — {finding['category'].upper()}\n\n{metadata_str}{comment_body}"

                review_comments.append({
                    "path": file_path,
                    "line": finding.get("line", 1) or 1,
                    "body": full_body,
                })

        # 6. Build and post the PR review
        review_body = _build_review_body(scan_summary)
        counts = scan_summary["severity_counts"]
        has_critical = counts.get("CRITICAL", 0) > 0
        review_event = "REQUEST_CHANGES" if has_critical else "COMMENT"

        if review_comments:
            try:
                gh.post_review(
                    owner, repo, pr_number, commit_sha,
                    body=review_body,
                    comments=review_comments,
                    event=review_event,
                )
            except Exception as e:
                log.warning("Review post failed, falling back to plain comment: %s", e)
                gh.post_comment(owner, repo, pr_number, review_body)
        else:
            gh.post_comment(owner, repo, pr_number, review_body)

        # 7. Save to DB
        repo_full = f"{owner}/{repo}"
        scan_id = db.save_scan(repo_full, scan_summary, pr_number, commit_sha)

        # 8. Set final commit status
        score = scan_summary["overall_score"]
        grade = scan_summary["overall_grade"]
        target_url = f"{dashboard_base_url}/scans/{scan_id}" if dashboard_base_url else ""

        if has_critical:
            gh.set_commit_status(
                owner, repo, commit_sha,
                state="failure",
                description=f"InfraGuard: {counts['CRITICAL']} CRITICAL issue(s) — score {score}/100 ({grade}). Merge blocked.",
                target_url=target_url,
            )
        elif counts.get("HIGH", 0) > 0:
            gh.set_commit_status(
                owner, repo, commit_sha,
                state="failure",
                description=f"InfraGuard: {counts['HIGH']} HIGH issue(s) — score {score}/100 ({grade}). Review required.",
                target_url=target_url,
            )
        else:
            gh.set_commit_status(
                owner, repo, commit_sha,
                state="success",
                description=f"InfraGuard: score {score}/100 ({grade}) — no blocking issues.",
                target_url=target_url,
            )

        log.info("Scan complete: score=%d grade=%s critical=%d", score, grade, counts.get("CRITICAL", 0))
        return {**scan_summary, "scan_id": scan_id}

    except Exception as exc:
        log.exception("Scan pipeline failed: %s", exc)
        gh.set_commit_status(
            owner, repo, commit_sha,
            state="error",
            description=f"InfraGuard encountered an error: {str(exc)[:100]}",
        )
        raise
