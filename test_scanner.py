# -*- coding: utf-8 -*-
"""
Quick smoke test - verifies all scanner rules fire correctly on known-bad input.
Run with: python test_scanner.py
"""
import sys
import os
import io

# Force UTF-8 stdout on Windows to handle any unicode in output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

from scanner.engine import scan_file, scan_repo
from scanner.detector import detect_file_type

errors = []

def check(name, condition, detail=""):
    if condition:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} {detail}")
        errors.append(name)

# --- File Type Detector ---
print("\n--- File Type Detector ---")
check("Terraform .tf", detect_file_type("infra/main.tf") == "terraform")
check("Terraform .tfvars", detect_file_type("prod.tfvars") == "terraform")
check("Dockerfile", detect_file_type("Dockerfile") == "dockerfile")
check("Dockerfile variant", detect_file_type("Dockerfile.prod") == "dockerfile")
check("docker-compose", detect_file_type("docker-compose.yml") == "docker_compose")
check("GH Actions", detect_file_type(".github/workflows/ci.yml") == "github_actions")
check("K8s manifest", detect_file_type("k8s/deployment.yaml") == "kubernetes")
check("SAM template", detect_file_type("template.yaml") == "sam")
check("Python file ignored", detect_file_type("app.py") is None)
check("Readme ignored", detect_file_type("README.md") is None)

# --- Terraform Scanner ---
print("\n--- Terraform Scanner ---")

BAD_TF = """
provider "aws" { region = "us-east-1" }
resource "aws_instance" "app" {
  instance_type = "m5.24xlarge"
  tags = { Environment = "dev" }
}
resource "aws_nat_gateway" "ng" { allocation_id = "x" subnet_id = "y" }
resource "aws_db_instance" "db" {
  multi_az = true
  publicly_accessible = true
  tags = { Environment = "dev" }
}
resource "aws_s3_bucket" "b" { acl = "public-read-write" }
"""
result = scan_file("main.tf", BAD_TF)
check("Terraform file detected", result is not None)
check("Score < 100 on bad tf", result["score"] < 80)
ids = {f["id"] for f in result["findings"]}
check("COST-001 xlarge in dev fires", "COST-001" in ids, str(ids))
check("COST-002 NAT Gateway fires", "COST-002" in ids, str(ids))
check("COST-006 Multi-AZ dev fires", "COST-006" in ids, str(ids))
check("SEC-003 Public S3 fires", "SEC-003" in ids, str(ids))
check("SEC-004 Public RDS fires", "SEC-004" in ids, str(ids))

CLEAN_TF = """
provider "aws" { region = "us-east-1" }
resource "aws_instance" "app" {
  instance_type = "t3.medium"
  tags = { Environment = "prod", Owner = "team" }
}
"""
clean = scan_file("clean.tf", CLEAN_TF)
check("Clean Terraform gets high score", clean["score"] >= 80, f"score={clean['score']}")

# --- Dockerfile Scanner ---
print("\n--- Dockerfile Scanner ---")

BAD_DOCKERFILE = """FROM ubuntu:latest
ENV PASSWORD=supersecret123
RUN apt-get update
ADD . /app
CMD ["./app"]
"""
df_result = scan_file("Dockerfile", BAD_DOCKERFILE)
check("Dockerfile scanned", df_result is not None)
df_ids = {f["id"] for f in df_result["findings"]}
check("SEC-006 latest tag fires", "SEC-006" in df_ids, str(df_ids))
check("SEC-008 no USER fires", "SEC-008" in df_ids, str(df_ids))
check("REL-002 no HEALTHCHECK fires", "REL-002" in df_ids, str(df_ids))
check("PERF-002 ADD vs COPY fires", "PERF-002" in df_ids, str(df_ids))

# --- GitHub Actions Scanner ---
print("\n--- GitHub Actions Scanner ---")

BAD_GHA = """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: echo done
"""
gha_result = scan_file(".github/workflows/ci.yml", BAD_GHA)
check("GH Actions scanned", gha_result is not None)
gha_ids = {f["id"] for f in gha_result["findings"]}
check("SEC-007 unpinned action fires", "SEC-007" in gha_ids, str(gha_ids))
check("REL-005 no timeout fires", "REL-005" in gha_ids, str(gha_ids))
check("SEC-012 no permissions fires", "SEC-012" in gha_ids, str(gha_ids))

GOOD_GHA = """
name: CI
on: [push]
permissions: read-all
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
"""
good_gha = scan_file(".github/workflows/ci.yml", GOOD_GHA)
check("Clean GH Actions fewer findings", len(good_gha["findings"]) < len(gha_result["findings"]))

# --- SAM Template Scanner ---
print("\n--- SAM Template Scanner ---")

BAD_SAM = """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Globals:
  Function:
    Timeout: 900
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: python3.11
      Policies:
        - Statement:
            - Effect: Allow
              Action: "*"
              Resource: "*"
  MyLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /aws/my-log-group
"""
sam_result = scan_file("template.yaml", BAD_SAM)
check("SAM scanned", sam_result is not None)
sam_ids = {f["id"] for f in sam_result["findings"]}
check("REL-001 Lambda no DLQ fires", "REL-001" in sam_ids, str(sam_ids))
check("SEC-001 IAM wildcard fires", "SEC-001" in sam_ids, str(sam_ids))
check("COST-004 high timeout fires", "COST-004" in sam_ids, str(sam_ids))
check("REL-003 no log retention fires", "REL-003" in sam_ids, str(sam_ids))

# --- Repo-level Scan ---
print("\n--- Repo-level Scan ---")
repo_scan = scan_repo({
    "infra/main.tf": BAD_TF,
    "Dockerfile": BAD_DOCKERFILE,
    ".github/workflows/ci.yml": BAD_GHA,
    "template.yaml": BAD_SAM,
    "README.md": "# Hello",   # should be ignored
})
check("Files scanned = 4", repo_scan["files_scanned"] == 4,
      f"got {repo_scan['files_scanned']}")
check("Overall score 0-100", 0 <= repo_scan["overall_score"] <= 100)
check("README ignored", not any(r["file"] == "README.md" for r in repo_scan["file_results"]))
check("Total findings > 5", repo_scan["total_findings"] > 5,
      f"got {repo_scan['total_findings']}")

# Print per-file scores for reference
print("\n  Scores per file:")
for r in repo_scan["file_results"]:
    print(f"    {r['file']}: {r['score']}/100 ({r['grade']}) | {len(r['findings'])} findings")
print(f"  Overall: {repo_scan['overall_score']}/100 ({repo_scan['overall_grade']})")
print(f"  Severity breakdown: {repo_scan['severity_counts']}")

# --- Summary ---
print(f"\n{'='*50}")
if errors:
    print(f"{len(errors)} test(s) FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("All tests passed!")
