"""
InfraGuard Webhook Server (FastAPI)

Receives GitHub App webhook events and dispatches PR scans.

Endpoints:
  POST /webhook/github   — GitHub event receiver
  GET  /health           — Health check
  GET  /api/scans        — List recent scans (with optional ?repo= filter)
  GET  /api/scans/{id}   — Single scan detail
"""

from __future__ import annotations
import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db
from .pr_scanner import scan_pull_request

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("infraguard.webhook")


# ─── App lifecycle ────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    log.info("InfraGuard webhook server started. DB initialized.")
    yield


app = FastAPI(title="InfraGuard", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Signature verification ───────────────────────────────────────────────────


def _verify_signature(body: bytes, signature_header: str | None) -> bool:
    """Verify GitHub's HMAC-SHA256 webhook signature."""
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        log.warning("GITHUB_WEBHOOK_SECRET not set — skipping signature verification")
        return True  # Allow in dev; enforce in prod
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ─── Event handlers ───────────────────────────────────────────────────────────


def _handle_pull_request(payload: dict) -> None:
    """Process a pull_request event in the background."""
    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        log.info("Ignoring pull_request action: %s", action)
        return

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    installation = payload.get("installation", {})

    owner = repo.get("owner", {}).get("login", "")
    repo_name = repo.get("name", "")
    pr_number = pr.get("number")
    commit_sha = pr.get("head", {}).get("sha", "")
    installation_id = installation.get("id")

    if not all([owner, repo_name, pr_number, commit_sha, installation_id]):
        log.error("Missing required fields in pull_request payload")
        return

    dashboard_url = os.environ.get("DASHBOARD_BASE_URL", "")

    log.info("Scanning PR #%d in %s/%s", pr_number, owner, repo_name)
    try:
        scan_pull_request(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number,
            commit_sha=commit_sha,
            installation_id=installation_id,
            dashboard_base_url=dashboard_url,
        )
    except Exception as e:
        log.exception(
            "PR scan failed for %s/%s #%d: %s", owner, repo_name, pr_number, e
        )


# ─── Routes ───────────────────────────────────────────────────────────────────


@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive and dispatch GitHub webhook events."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    event_type = request.headers.get("X-GitHub-Event", "")

    # 1. Verify signature
    if not _verify_signature(body, signature):
        log.warning("Invalid webhook signature — rejecting request")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    log.info("GitHub event: %s action=%s", event_type, payload.get("action", "n/a"))

    # 3. Dispatch (in background so GitHub's 10s timeout isn't hit)
    if event_type == "pull_request":
        background_tasks.add_task(_handle_pull_request, payload)

    elif event_type == "ping":
        log.info("GitHub ping received — webhook configured successfully")

    elif event_type == "installation":
        action = payload.get("action")
        inst = payload.get("installation", {})
        log.info("App %s on account %s", action, inst.get("account", {}).get("login"))

    # Always return 200 quickly — processing happens in background
    return JSONResponse({"status": "accepted", "event": event_type})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "infraguard-webhook",
        "github_app_id": os.environ.get("GITHUB_APP_ID", "not-set"),
    }


@app.get("/api/scans")
def list_scans(repo: str | None = None, limit: int = 50):
    """List recent scan results. Optionally filter by ?repo=owner/name."""
    try:
        scans = db.get_scans(repo=repo, limit=min(limit, 200))
        return {"scans": scans, "count": len(scans)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: str):
    """Get full details of a single scan."""
    scan = db.get_scan_by_id(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.post("/chat")
async def chat_with_nova(request: Request):
    """Handle interactive chat sessions with Nova about a specific scan."""
    try:
        body = await request.json()
        message = body.get("message")
        scan_id = body.get("scan_id")
        history = body.get("history", [])

        if not message:
            raise HTTPException(status_code=400, detail="Missing message")

        # 1. Gather context if scan_id exists
        context_str = ""
        if scan_id:
            scan = db.get_scan_by_id(scan_id)
            if scan:
                # Truncate results for prompt brevity
                findings_summary = []
                for res in scan.get("results", {}).get("file_results", []):
                    for f in res.get("findings", []):
                        findings_summary.append(
                            f"{f['severity']} in {res['file']}: {f['message']}"
                        )

                context_str = f"Context: The user is looking at Scan ID {scan_id} for repo {scan['repo']}. Findings: {', '.join(findings_summary[:10])}\n\n"

        # 2. Build prompt
        from nova_client import NovaClient

        nova = NovaClient(api_key=os.environ.get("AWS_BEARER_TOKEN_BEDROCK"))

        chat_prompt = f"{context_str}User: {message}\n\nNova: "
        # For simplicity, we're not doing full history management here, but it can be added

        response = nova.invoke(
            f"You are the Nova DevOps Assistant. Be concise and technical. {chat_prompt}"
        )

        return {"response": response}
    except Exception as e:
        log.exception("Chat failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    print(f"InfraGuard webhook server starting on http://127.0.0.1:{port}")
    uvicorn.run(
        "github_app.webhook_server:app", host="127.0.0.1", port=port, reload=True
    )
