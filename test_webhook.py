"""
Integration test for InfraGuard Webhook Server.
Simulates a GitHub pull_request event and verifies signature/dispatch.

Usage:
  1. Start server: python -m uvicorn github_app.webhook_server:app --port 8001
  2. Run test:   python test_webhook.py
"""

import hmac
import hashlib
import json
import time
import httpx

# Configuration
TEST_URL = "http://127.0.0.1:8001/webhook/github"
WEBHOOK_SECRET = "test_secret_123"

# Dummy pull_request payload
PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "number": 1,
        "head": {"sha": "c0ffee1234567890abcdef1234567890abcdef12"},
        "base": {"ref": "main"},
    },
    "repository": {
        "name": "infraguard-test-repo",
        "owner": {"login": "daksh-test"},
    },
    "installation": {
        "id": 12345678,
    }
}

def test_webhook():
    body = json.dumps(PAYLOAD).encode()
    
    # Generate HMAC-SHA256 signature
    signature = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    print(f"Sending test payload to {TEST_URL}...")
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json",
    }

    try:
        # Note: We expect this to fail if GITHUB_WEBHOOK_SECRET in .env doesn't match 'test_secret_123'
        # unless we set the env var for the server process.
        response = httpx.post(TEST_URL, content=body, headers=headers, timeout=5)
        
        print(f"Status: {response.status_code}")
        print(f"Body:   {response.text}")
        
        if response.status_code == 200:
            print("\n[PASS] Webhook accepted and signature verified!")
        elif response.status_code == 401:
            print("\n[FAIL] Signature verification failed. Check if GITHUB_WEBHOOK_SECRET matches.")
        else:
            print(f"\n[FAIL] Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"\n[ERROR] Could not connect to server: {e}")
        print("Make sure the server is running on port 8001 with GITHUB_WEBHOOK_SECRET=test_secret_123")

if __name__ == "__main__":
    # To run this properly, the user should execute:
    # $env:GITHUB_WEBHOOK_SECRET="test_secret_123"
    # python -m uvicorn github_app.webhook_server:app --port 8001
    test_webhook()
