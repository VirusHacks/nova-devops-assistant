"""
GitHub App Authentication

Generates JWT tokens and exchanges them for installation access tokens.
The GitHub App uses RS256 JWT signing with the private key you download
when registering the app at https://github.com/settings/apps.

Usage:
    token = get_installation_token(
        app_id=os.environ["GITHUB_APP_ID"],
        private_key=os.environ["GITHUB_PRIVATE_KEY"],
        installation_id=int(event["installation"]["id"])
    )
"""

from __future__ import annotations
import os
import time
from pathlib import Path

import jwt
import httpx


_GITHUB_API = "https://api.github.com"


def _load_private_key() -> str:
    """Load private key from env var (PEM string) or file path."""
    key = os.environ.get("GITHUB_PRIVATE_KEY", "")
    if key.startswith("-----BEGIN"):
        return key
    # Maybe it's a file path
    key_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "")
    if key_path:
        return Path(key_path).read_text()
    raise ValueError(
        "Set GITHUB_PRIVATE_KEY (PEM string) or GITHUB_PRIVATE_KEY_PATH (file path)"
    )


def generate_jwt(app_id: str | None = None, private_key: str | None = None) -> str:
    """
    Generate a short-lived JWT for authenticating as the GitHub App itself.
    Valid for 10 minutes. Used only to fetch installation tokens.
    """
    app_id = app_id or os.environ["GITHUB_APP_ID"]
    private_key = private_key or _load_private_key()

    now = int(time.time())
    payload = {
        "iat": now - 60,          # issued 60s ago (handles clock skew)
        "exp": now + (9 * 60),    # expires in 9 minutes (GitHub max = 10)
        "iss": str(app_id),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(
    installation_id: int,
    app_id: str | None = None,
    private_key: str | None = None,
) -> str:
    """
    Exchange a JWT for an installation access token.
    The token expires in 1 hour and is scoped to the specific installation.

    Returns the token string.
    """
    app_jwt = generate_jwt(app_id, private_key)

    response = httpx.post(
        f"{_GITHUB_API}/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["token"]
