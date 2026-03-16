"""
SQLite persistence for InfraGuard scan results.

Schema:
  scans(id, repo, pr_number, commit_sha, overall_score, overall_grade,
        files_scanned, total_findings, severity_counts_json, results_json,
        created_at)
"""

from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "infraguard.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                repo TEXT NOT NULL,
                pr_number INTEGER,
                commit_sha TEXT,
                overall_score INTEGER,
                overall_grade TEXT,
                files_scanned INTEGER,
                total_findings INTEGER,
                severity_counts TEXT,   -- JSON
                results TEXT,           -- JSON (full scan output)
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_repo ON scans(repo)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at)")
        conn.commit()


def save_scan(
    repo: str,
    scan_result: dict[str, Any],
    pr_number: int | None = None,
    commit_sha: str | None = None,
) -> str:
    """Persist a scan result. Returns the new scan ID."""
    scan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO scans
              (id, repo, pr_number, commit_sha, overall_score, overall_grade,
               files_scanned, total_findings, severity_counts, results, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id,
                repo,
                pr_number,
                commit_sha,
                scan_result.get("overall_score"),
                scan_result.get("overall_grade"),
                scan_result.get("files_scanned"),
                scan_result.get("total_findings"),
                json.dumps(scan_result.get("severity_counts", {})),
                json.dumps(scan_result),
                now,
            ),
        )
        conn.commit()
    return scan_id


def get_scans(repo: str | None = None, limit: int = 50) -> list[dict]:
    """Fetch recent scan summaries (no full results blob)."""
    with _connect() as conn:
        if repo:
            rows = conn.execute(
                "SELECT id, repo, pr_number, commit_sha, overall_score, overall_grade, "
                "files_scanned, total_findings, severity_counts, created_at "
                "FROM scans WHERE repo = ? ORDER BY created_at DESC LIMIT ?",
                (repo, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, repo, pr_number, commit_sha, overall_score, overall_grade, "
                "files_scanned, total_findings, severity_counts, created_at "
                "FROM scans ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

    results = []
    for row in rows:
        d = dict(row)
        d["severity_counts"] = json.loads(d["severity_counts"] or "{}")
        results.append(d)
    return results


def get_scan_by_id(scan_id: str) -> dict | None:
    """Fetch a single scan with full results."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["severity_counts"] = json.loads(d["severity_counts"] or "{}")
    d["results"] = json.loads(d["results"] or "{}")
    return d
