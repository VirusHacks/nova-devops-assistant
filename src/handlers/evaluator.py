"""
Lambda Evaluator - Narrative Variance Analysis using Nova 2 Lite.
Identifies Financial Tech Debt, quantifies NAT Gateway vs VPC Endpoint costs.
Saves final result to DynamoDB.
"""

import json
import os

from memory_manager import MemoryManager
from nova_client import NovaClient, ThrottlingException


def lambda_handler(event: dict, context: object) -> dict:
    """
    Event: { session_id, invocation_id, plan, tool_output, ... }
    Returns: { ...passthrough, result }
    """
    session_id = event.get("session_id", "")
    invocation_id = event.get("invocation_id", "")
    plan = event.get("plan", "")
    tool_output = event.get("tool_output", "{}")

    evaluator_prompt = f"""You are a FinOps expert performing Narrative Variance Analysis on infrastructure scan results.

Plan: {plan}

Tool output (Terraform scan findings):
{tool_output}

Generate a concise FinOps audit report. You must:
1. Identify Financial Tech Debt clearly
2. QUANTIFY costs where possible: NAT Gateway (~$0.045/GB data processed + ~$32/month) vs VPC Endpoint for S3/DynamoDB (often free or much cheaper)
3. Mention EC2 instance over-provisioning costs if present
4. Provide actionable recommendations aligned with Shift Left FinOps
5. Write in natural language, 2-4 paragraphs, professional tone

Do not include JSON or code blocks."""

    try:
        client = NovaClient(api_key=os.environ.get("AWS_BEARER_TOKEN_BEDROCK"))
        result = client.invoke(evaluator_prompt)
    except ThrottlingException as e:
        result = f"Report generation throttled. Please retry. ({e})"
    except Exception as e:
        result = f"Report generation failed: {e}"

    memory = MemoryManager(table_name=os.environ.get("FAME_MEMORY_TABLE"))
    memory.save(
        session_id,
        invocation_id,
        plan=plan,
        tool_outputs=tool_output,
        result=result,
    )

    return {
        **event,
        "result": result,
    }
