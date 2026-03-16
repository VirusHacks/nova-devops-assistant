"""
NovaClient - AWS Bedrock Runtime wrapper for Amazon Nova model.
Uses the Converse API with extended thinking enabled.
"""

import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Load .env if python-dotenv is available (for API key from file)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


class NovaClient:
    """Client for invoking Amazon Nova model via AWS Bedrock Converse API."""

    MODEL_ID = "global.amazon.nova-2-lite-v1:0"
    REGION = "us-east-1"

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Bedrock Runtime client in us-east-1.

        Args:
            api_key: Optional Bedrock API key. If provided, sets
                     AWS_BEARER_TOKEN_BEDROCK. Otherwise uses that env var.
        """
        if api_key is not None:
            os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=self.REGION,
        )

    def invoke(self, prompt: str) -> str:
        """
        Invoke the Nova model with the given prompt using the Converse API.

        Args:
            prompt: The user prompt to send to the model.

        Returns:
            The text content from the model's response.

        Raises:
            ClientError: On API errors (except ThrottlingException, which is retried).
        """
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ]

        request_kwargs = {
            "modelId": self.MODEL_ID,
            "messages": messages,
            "additionalModelRequestFields": {
                "reasoningConfig": {
                    "type": "enabled",
                    "maxReasoningEffort": "low",
                }
            },
        }

        try:
            response = self._client.converse(**request_kwargs)
            return self._parse_response(response)
        except NoCredentialsError as e:
            raise NoCredentialsError(
                "Unable to locate AWS credentials. If you are using a Bedrock API key, ensure "
                "AWS_BEARER_TOKEN_BEDROCK is set and your boto3/botocore version supports Bedrock API key auth. "
                "Alternatively configure IAM credentials (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or AWS profile)."
            ) from e
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ThrottlingException":
                raise ThrottlingException(
                    "Rate limit exceeded. Please retry after a short delay."
                ) from e
            raise

    def _parse_response(self, response: dict) -> str:
        """
        Extract text content from the Converse API response.

        Args:
            response: The raw response from bedrock-runtime.converse().

        Returns:
            Concatenated text content from the output message.
        """
        output = response.get("output", {})
        message = output.get("message", {})
        content = message.get("content", [])

        text_parts = []
        for block in content:
            if block.get("text"):
                text_parts.append(block["text"])

        return "".join(text_parts)


class ThrottlingException(Exception):
    """Raised when Bedrock returns a ThrottlingException."""

    pass


if __name__ == "__main__":
    print("Testing NovaClient...")
    try:
        client = NovaClient()
        response = client.invoke("Say hello in one sentence.")
        print("Response:", response)
    except ThrottlingException as e:
        print("Throttled:", e)
    except Exception as e:
        print("Error:", e)
