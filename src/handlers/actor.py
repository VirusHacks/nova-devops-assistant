"""
Lambda Actor - Executes scan_terraform_code tool with S3 cache.
If file content hash unchanged, fetches cached result from S3.
"""

import hashlib
import os

import boto3
from botocore.exceptions import ClientError
from iac_tool import scan_terraform_content


def _get_s3_client():
    return boto3.client("s3")


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _get_cached_result(bucket: str, key: str) -> str | None:
    try:
        s3 = _get_s3_client()
        obj = s3.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read().decode("utf-8")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "NoSuchKey":
            return None
        raise
    except Exception:
        return None


def _put_cached_result(bucket: str, key: str, result: str) -> None:
    s3 = _get_s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=result.encode("utf-8"), ContentType="application/json")


def lambda_handler(event: dict, context: object) -> dict:
    """
    Event: { session_id, invocation_id, plan, terraform_content, terraform_file_name?, ... }
    Returns: { ...passthrough, tool_output }
    """
    terraform_content = event.get("terraform_content", "")
    terraform_file_name = event.get("terraform_file_name", "infra.tf")
    bucket = os.environ.get("FAME_CACHE_BUCKET", "")

    content_hash = _content_hash(terraform_content) if terraform_content else ""
    cache_key = f"cache/{content_hash}.json" if content_hash else ""

    tool_output = None
    if bucket and cache_key:
        tool_output = _get_cached_result(bucket, cache_key)

    if tool_output is None:
        tool_output = scan_terraform_content(terraform_content, terraform_file_name)
        if bucket and cache_key:
            _put_cached_result(bucket, cache_key, tool_output)

    return {
        **event,
        "tool_output": tool_output,
    }
