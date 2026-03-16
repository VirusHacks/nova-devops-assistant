"""
Local FinOps backend - stays running and handles POST /analyze from the frontend.
Run: python backend_server.py
Then the Next.js app (with BACKEND_URL=http://127.0.0.1:5000) will send requests here.
"""

import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from iac_tool import scan_terraform_content
from nova_client import NovaClient, ThrottlingException

app = Flask(__name__)
CORS(app)

EVALUATOR_PROMPT = """You are a FinOps expert. An infrastructure scan produced these findings:

{scan_result}

Generate a concise, professional FinOps audit report (2-4 paragraphs). Include:
- A brief intro stating you audited the file
- Numbered list of each cost risk with clear explanation
- A final recommendation paragraph
- Keep it actionable and aligned with FinOps best practices (Shift Left, cost optimization)

Write the report in natural language. Do not include JSON or code blocks."""


@app.route("/analyze", methods=["POST"])
def analyze():
    """Handle analysis request from frontend. Same flow as finops_fame_agent but over HTTP."""
    try:
        body = request.get_json() or {}
        terraform_content = body.get("terraform_content", "").strip()
        terraform_file_name = body.get("terraform_file_name", "infra.tf")
        _request = body.get("request", "Analyze Terraform for cost risks.")

        if not terraform_content:
            return jsonify({"error": "No Terraform content provided."}), 400

        # Step 1: Scan (Actor)
        scan_result = scan_terraform_content(terraform_content, terraform_file_name)

        # Step 2: Report via Nova (Evaluator)
        prompt = EVALUATOR_PROMPT.format(scan_result=scan_result)
        try:
            client = NovaClient(api_key=os.environ.get("AWS_BEARER_TOKEN_BEDROCK"))
            report = client.invoke(prompt)
        except ThrottlingException as e:
            return jsonify({"error": f"Rate limited. Retry in a moment. ({e})"}), 503
        except Exception as e:
            return jsonify({"error": f"Report generation failed: {e}"}), 500

        return jsonify({
            "result": report,
            "session_id": None,
            "invocation_id": None,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "finops-backend"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"FinOps backend running at http://127.0.0.1:{port}")
    print("POST /analyze - run analysis | GET /health - health check")
    app.run(host="127.0.0.1", port=port, debug=False)
