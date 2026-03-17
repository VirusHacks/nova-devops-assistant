# 🛡️ Nova Guardian

### **AI-Powered DevOps Security Agent**
*Autonomous infrastructure security, cost optimization, and compliance — powered by Amazon Nova 2 Lite.*

---

## 🚀 Overview

**Nova Guardian** is a next-generation GitHub App designed to be your virtual Senior SRE. It automatically scans every Pull Request (PR) containing Infrastructure-as-Code (IaC) files, providing real-time security reviews, cost impact predictions, and one-click code fixes.

By leveraging **Amazon Nova 2 Lite**'s advanced reasoning, Nova Guardian doesn't just find bugs—it understands the context, explains the risk, and suggests the exact code change needed to fix it.

---

## ✨ Key Features

- **🤖 Multi-Agent Orchestration**: A specialized 4-agent pipeline (Parse → Scan → Reason → Report) that executes in under 4 seconds.
- **🛡️ Multi-Format Support**: Scans Terraform (HCL), Kubernetes YAML, Dockerfiles, GitHub Actions, and AWS SAM templates.
- **💡 AI Reasoning**: Uses Nova 2 Lite's *Extended Thinking* to map findings to compliance frameworks (CIS, SOC2) and generate human-readable explanations.
- **💸 Cost & Compliance**: Estimates the financial impact of infrastructure changes and ensures alignment with security best practices.
- **⚡ Inline PR Reviews**: Posts suggestions directly into the GitHub PR diff, allowing developers to "Commit suggestion" instantly.
- **📊 Live Dashboard**: A Neo-Brutalist real-time interface to visualize scan history, agent execution traces, and interact with a project-aware AI chat assistant.

---

## 🛠️ Architecture: The Agentic Pipeline

Nova Guardian operates via a sophisticated agentic chain:

1.  **The Fetcher**: Retrieves modified files from the GitHub PR.
2.  **The Scanner**: Performs static analysis against security and cost anti-patterns.
3.  **The Brain (Nova 2 Lite)**: Analyzes findings, generates context-aware fixes, and maps compliance.
4.  **The Reporter**: Posts inline reviews and updates commit statuses (blocking merge on `CRITICAL` issues).

---

## 🏁 Getting Started

### Prerequisites
- Python 3.11+ & Node.js 18+
- [ngrok](https://ngrok.com/) account for local webhook tunneling.
- AWS Bedrock access for Amazon Nova.

### 1. Setup Backend
1. Clone the repo and navigate to `Finops/`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Configure `.env` with your `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY_PATH`, and `AWS_BEARER_TOKEN_BEDROCK`.

### 2. Start Webhook Server & ngrok
```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Start Webhook Server
python -m uvicorn github_app.webhook_server:app --host 127.0.0.1 --port 8000 --reload
```
*Note: Update your GitHub App Webhook URL with the ngrok address.*

### 3. Setup Frontend
```bash
cd finops-frontend
npm install
npm run dev
```
Visit `http://localhost:3000/dashboard` to see your scans in action!

---

## 🏗️ Built With

- **AI**: Amazon Nova 2 Lite (via AWS Bedrock Converse API)
- **Backend**: Python (Flask/FastAPI), AWS Step Functions, SQLite
- **Frontend**: Next.js 15, Tailwind CSS, Lucide Icons
- **Integration**: GitHub Apps API, Webhooks

---

## 🗺️ Roadmap
- [ ] **Nova Act Integration**: Fully automated self-healing infrastructure.
- [ ] **Multi-Repo Analytics**: Organization-wide security posture dashboards.
- [ ] **Custom Policies**: YAML-based custom rule definition for teams.
- [ ] **ChatOps**: Slack and Microsoft Teams notification routing.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Created for the [Amazon Nova AI Hackathon](https://amazon-nova.devpost.com/).*
