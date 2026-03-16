"""
Lambda Planner - Generates step-by-step plan using Nova 2 Lite.
Receives user request, retrieves session history from DynamoDB, returns plan.
"""

import json
import os
import uuid

from memory_manager import MemoryManager
from nova_client import NovaClient, ThrottlingException


def lambda_handler(event: dict, context: object) -> dict:
    """
    Event: { session_id, request, terraform_content?, terraform_file_name? }
    Returns: { session_id, invocation_id, plan, ...passthrough }
    """
    session_id = event.get("session_id") or str(uuid.uuid4())
    invocation_id = event.get("invocation_id") or str(uuid.uuid4())
    request = event.get("request", "Analyze Terraform for cost risks.")

    memory = MemoryManager(table_name=os.environ.get("FAME_MEMORY_TABLE"))
    history = memory.get_session_context(session_id)

    planner_prompt = f"""You are a FinOps planner. The user wants to analyze their Terraform infrastructure for cost risks.

User request: {request}

{"Previous session history (for context):\n" + history if history else "This is a new session."}

Generate a concise step-by-step plan (3-5 steps) for the FinOps analysis. The plan will be executed by:
1. An Actor that scans Terraform for expensive resources (NAT Gateways, xlarge instances)
2. An Evaluator that produces a natural language report

Output only the plan as plain text, no JSON. Be specific and actionable."""

    try:
        client = NovaClient(api_key=os.environ.get("AWS_BEARER_TOKEN_BEDROCK"))
        plan = client.invoke(planner_prompt)
    except ThrottlingException:
        plan = "1. Scan Terraform for expensive resources (NAT Gateway, xlarge instances). 2. Generate FinOps report with cost quantification."
    except Exception as e:
        plan = f"1. Scan Terraform for cost risks. 2. Generate report. (Planner error: {e})"

    memory.save(session_id, invocation_id, plan=plan)

    return {
        **event,
        "session_id": session_id,
        "invocation_id": invocation_id,
        "plan": plan,
        "request": request,
    }
