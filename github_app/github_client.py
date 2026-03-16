"""
GitHub REST API client for InfraGuard.

Wraps: get PR files, post review comments, set commit status.
"""

from __future__ import annotations
from typing import Any
import httpx


_API = "https://api.github.com"
_HEADERS_BASE = {
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Max characters for a single review comment body (GitHub limit is ~65k)
_MAX_COMMENT_LEN = 4096


class GitHubClient:
    def __init__(self, token: str):
        self._headers = {**_HEADERS_BASE, "Authorization": f"Bearer {token}"}
        self._client = httpx.Client(headers=self._headers, timeout=30)

    # ── PR Files ──────────────────────────────────────────────────────────────

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """
        Returns list of changed files in a PR.
        Each item: {filename, status, patch, blob_url, additions, deletions}
        """
        files = []
        page = 1
        while True:
            resp = self._client.get(
                f"{_API}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return files

    def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        """Fetch raw file content at a given ref. Returns None if not found."""
        resp = self._client.get(
            f"{_API}/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        import base64
        data = resp.json()
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data.get("content", "")

    # ── Reviews ───────────────────────────────────────────────────────────────

    def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_sha: str,
        body: str,
        comments: list[dict],  # [{path, line, body}]
        event: str = "COMMENT",  # COMMENT | REQUEST_CHANGES | APPROVE
    ) -> dict:
        """Create a pull request review with inline comments."""
        payload: dict[str, Any] = {
            "commit_id": commit_sha,
            "body": body[:_MAX_COMMENT_LEN],
            "event": event,
            "comments": [
                {
                    "path": c["path"],
                    "line": c["line"],
                    "body": c["body"][:_MAX_COMMENT_LEN],
                    "side": "RIGHT",
                }
                for c in comments
                if c.get("line") and c.get("path")
            ],
        }
        resp = self._client.post(
            f"{_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def post_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        """Post a regular (non-inline) comment on the PR."""
        resp = self._client.post(
            f"{_API}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            json={"body": body[:_MAX_COMMENT_LEN]},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Commit Status (Check Runs) ─────────────────────────────────────────────

    def set_commit_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,       # success | failure | pending | error
        description: str,
        context: str = "InfraGuard",
        target_url: str = "",
    ) -> dict:
        """Set a commit status check (the ✅/❌ next to a commit)."""
        payload = {
            "state": state,
            "description": description[:140],  # GitHub limit
            "context": context,
        }
        if target_url:
            payload["target_url"] = target_url
        resp = self._client.post(
            f"{_API}/repos/{owner}/{repo}/statuses/{sha}",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._client.close()
