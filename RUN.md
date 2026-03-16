# Running FinOps: Backend + Frontend (connected)

## 1. Start the backend (Python – stays running)

From the **fINOPS** project root:

```bash
cd c:\Users\Vinisha\OneDrive\Desktop\fINOPS

# Activate venv if you use one
.venv\Scripts\Activate.ps1

# Install deps once
pip install -r requirements.txt

# Start the backend (leave this terminal open)
python backend_server.py
```

You should see: `FinOps backend running at http://127.0.0.1:5000`

## 2. Start the frontend (Next.js)

Open a **second terminal**:

```bash
cd c:\Users\Vinisha\OneDrive\Desktop\fINOPS\finops-frontend

npm install
npm run dev
```

Open **http://localhost:3000**. When you click **Run FinOps analysis**, the frontend sends the request to the Next.js API route (`/api/analyze`), which forwards to your **local backend** at `http://127.0.0.1:5000/analyze`. The backend handles it and returns the report.

## 3. Env (backend)

In **fINOPS** root, a `.env` file with your Bedrock key (for Nova) is used by the backend:

- `AWS_BEARER_TOKEN_BEDROCK=your_key`

## 4. Env (frontend)

In **finops-frontend/.env.local**:

- `BACKEND_URL=http://127.0.0.1:5000` → frontend uses the **local** backend (default).
- If you remove or comment out `BACKEND_URL`, the app will use `NEXT_PUBLIC_API_BASE_URL` (AWS API Gateway) instead.

## Summary

| Terminal 1 (backend) | Terminal 2 (frontend) |
|----------------------|------------------------|
| `python backend_server.py` | `npm run dev` |
| Listens on :5000        | Listens on :3000, proxies to :5000 |

Frontend and backend are connected when both are running and `BACKEND_URL` is set.
