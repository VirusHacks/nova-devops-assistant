"""
NovaClient - AWS Bedrock Runtime wrapper for Amazon Nova model.
Uses the Converse API with extended thinking enabled.
"""

import os

import boto3
from botocore.exceptions import ClientError


class NovaClient:
    """Client for invoking Amazon Nova model via AWS Bedrock Converse API."""

    MODEL_ID = "global.amazon.nova-2-lite-v1:0"
    REGION = "us-east-1"

    def __init__(self, api_key: str | None = None):
        if api_key is not None:
            os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=self.REGION,
        )

    def invoke(self, prompt: str) -> str:
        messages = [
            {"role": "user", "content": [{"text": prompt}]},
        ]
        request_kwargs = {
            "modelId": self.MODEL_ID,
            "messages": messages,
            "additionalModelRequestFields": {
                "reasoningConfig": {"type": "enabled", "maxReasoningEffort": "low"}
            },
        }
        try:
            response = self._client.converse(**request_kwargs)
            return self._parse_response(response)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ThrottlingException":
                raise ThrottlingException(
                    "Rate limit exceeded. Please retry after a short delay."
                ) from e
            raise

    def _parse_response(self, response: dict) -> str:
        output = response.get("output", {})
        message = output.get("message", {})
        content = message.get("content", [])
        text_parts = [b["text"] for b in content if b.get("text")]
        return "".join(text_parts)


class ThrottlingException(Exception):
    """Raised when Bedrock returns a ThrottlingException."""
    pass
