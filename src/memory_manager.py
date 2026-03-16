"""
FAME Agent Memory Manager - DynamoDB persistence layer.

Manages session state across Lambda invocations.
Table: FameAgentMemory
  - Partition Key: session_id (String)
  - Sort Key: invocation_id (String)
"""

import json
import os
from datetime import datetime
from typing import Any

import boto3


class MemoryManager:
    """Helper class for DynamoDB interactions with FameAgentMemory table."""

    def __init__(self, table_name: str | None = None):
        self._table_name = table_name or os.environ.get("FAME_MEMORY_TABLE", "FameAgentMemory")
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(self._table_name)

    def save(
        self,
        session_id: str,
        invocation_id: str,
        *,
        plan: str | None = None,
        tool_outputs: str | None = None,
        reasoning: str | None = None,
        result: str | None = None,
    ) -> None:
        """
        Save state to DynamoDB.

        Args:
            session_id: Partition key - identifies the session.
            invocation_id: Sort key - identifies the invocation.
            plan: The planner's step-by-step plan.
            tool_outputs: Output from the Actor (iac_tool scan results).
            reasoning: Nova's reasoning chain.
            result: Final evaluator report.
        """
        item: dict[str, Any] = {
            "session_id": session_id,
            "invocation_id": invocation_id,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        if plan is not None:
            item["plan"] = plan
        if tool_outputs is not None:
            item["tool_outputs"] = tool_outputs
        if reasoning is not None:
            item["reasoning"] = reasoning
        if result is not None:
            item["result"] = result

        self._table.put_item(Item=item)

    def get_item(self, session_id: str, invocation_id: str) -> dict | None:
        """Get a single item by session_id and invocation_id."""
        response = self._table.get_item(
            Key={
                "session_id": session_id,
                "invocation_id": invocation_id,
            }
        )
        return response.get("Item")

    def get_session_history(self, session_id: str) -> list[dict]:
        """
        Retrieve all items for a session (for Planner context).
        Returns items sorted by invocation_id ascending.
        """
        response = self._table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id},
            ScanIndexForward=True,
        )
        return response.get("Items", [])

    def get_session_context(self, session_id: str) -> str:
        """
        Build a context string from session history for the Planner prompt.
        Returns empty string if no history.
        """
        items = self.get_session_history(session_id)
        if not items:
            return ""

        parts = []
        for item in items:
            inv_id = item.get("invocation_id", "?")
            if item.get("plan"):
                parts.append(f"[{inv_id}] Plan: {item['plan']}")
            if item.get("tool_outputs"):
                parts.append(f"[{inv_id}] Tool Outputs: {item['tool_outputs']}")
            if item.get("result"):
                parts.append(f"[{inv_id}] Result: {item['result']}")

        return "\n\n".join(parts) if parts else ""
