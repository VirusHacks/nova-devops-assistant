# InfraGuard — Setup Guide

## Prerequisites
- Python 3.11+
- Node.js 18+
- [ngrok](https://ngrok.com/download) (free account for local dev)
- AWS Bedrock API key for Amazon Nova

---

## Step 1 — Register a GitHub App

1. Go to https://github.com/settings/apps → **New GitHub App**
2. Fill in:
   - **App name**: `InfraGuard` (or any unique name)
   - **Homepage URL**: `http://localhost:3000`
   - **Webhook URL**: `https://YOUR-NGROK-URL.ngrok-free.app/webhook/github`
     *(you'll update this after starting ngrok — see Step 4)*
   - **Webhook secret**: generate a random string and save it
3. **Permissions** (Repository):
   - Pull requests: **Read & write**
   - Commit statuses: **Write**
   - Contents: **Read**
4. **Subscribe to events**:
   - ✅ Pull request
   - ✅ Push (optional, for push-based scans)
5. Click **Create GitHub App**
6. On the app page, scroll to **Private keys** → **Generate a private key**
   - Save the downloaded `.pem` file to the `Finops/` directory

---

## Step 2 — Configure Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

```env
GITHUB_APP_ID=123456                          # From your GitHub App settings page
GITHUB_PRIVATE_KEY_PATH=./private-key.pem    # Path to the downloaded .pem file
GITHUB_WEBHOOK_SECRET=your_random_secret      # What you set in Step 1
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_key    # From AWS Console
DASHBOARD_BASE_URL=http://localhost:3000      # Next.js dev server URL
```

---

## Step 3 — Install Python Dependencies

```powershell
cd c:\Users\daksh\OneDrive\Desktop\Hackathons\amazon-nova\Finops

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 4 — Start ngrok

In a new terminal:

```powershell
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL and:
- Go to your GitHub App settings → **Webhook URL** → paste it as:
  `https://xxxx.ngrok-free.app/webhook/github`
- Click **Save changes**

---

## Step 5 — Start the InfraGuard Webhook Server

```powershell
cd c:\Users\daksh\OneDrive\Desktop\Hackathons\amazon-nova\Finops
.\venv\Scripts\Activate.ps1

python -m uvicorn github_app.webhook_server:app --host 127.0.0.1 --port 8000 --reload
```

You should see:
```
InfraGuard webhook server started. DB initialized.
```

---

## Step 6 — Install the GitHub App on a Test Repo

1. Go to your GitHub App page → **Install App**
2. Choose a repo (ideally one that has `.tf`, `Dockerfile`, or `.github/workflows/` files)
3. Click **Install**

GitHub will now send webhook events to your server whenever a PR is opened.

---

## Step 7 — Start the Frontend Dashboard

```powershell
cd finops-frontend
npm install
npm run dev
```

Open http://localhost:3000/dashboard

---

## Step 8 — Test It!

Open a PR in your test repo touching any of these files:
- `*.tf` (Terraform)
- `Dockerfile`
- `.github/workflows/*.yml`
- `k8s/*.yaml`
- `template.yaml` (SAM)

**Expected result within ~10 seconds:**
- InfraGuard posts inline review comments on risky lines
- A summary comment appears with score table
- Commit status shows ✅ or ❌

---

## Running the Old Terraform Analyzer (Frontend)

The original paste-and-analyze UI is still available at http://localhost:3000

The Flask backend is no longer needed for the GitHub App flow, but you can still run it for the manual scan:

```powershell
python backend_server.py   # runs on port 5000
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GITHUB_APP_ID not set` | Check your `.env` file is in the `Finops/` directory |
| No comments on PR | Check ngrok is running and webhook URL is correct in GitHub App settings |
| `Invalid signature` | Verify `GITHUB_WEBHOOK_SECRET` matches what you set in GitHub App |
| `NoCredentialsError` | Set `AWS_BEARER_TOKEN_BEDROCK` in `.env` |
| Dashboard empty | Make sure webhook server is running on port 8000 and a PR scan has been triggered |
