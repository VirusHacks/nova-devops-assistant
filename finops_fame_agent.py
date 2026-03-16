"""
FinOps FAME Agent - Shift Left Infrastructure Cost Analysis

Orchestrates:
1. Actor (iac_tool): Scans Terraform for expensive resources
2. Evaluator (Nova): Generates natural language FinOps report
"""

from iac_tool import scan_terraform_code
from nova_client import NovaClient, ThrottlingException


def run_finops_agent(infra_file: str = "infra.tf") -> None:
    """Run the full FinOps analysis pipeline."""
    print("=" * 60)
    print("FINOPS FAME AGENT - Pre-Flight Infrastructure Analysis")
    print("=" * 60)

    # Step 1: Actor scans Terraform (the "Hands")
    print("\n[1/2] Scanning Terraform...")
    scan_result = scan_terraform_code(infra_file)
    print(scan_result)

    # Step 2: Evaluator (Nova) generates report
    print("\n[2/2] Generating FinOps report via Nova...")

    evaluator_prompt = f"""You are a FinOps expert. An infrastructure scan produced these findings:

{scan_result}

Generate a concise, professional FinOps audit report (2-4 paragraphs). Include:
- A brief intro stating you audited the file
- Numbered list of each cost risk with clear explanation
- A final recommendation paragraph
- Keep it actionable and aligned with FinOps best practices (Shift Left, cost optimization)

Write the report in natural language. Do not include JSON or code blocks."""

    try:
        client = NovaClient()
        report = client.invoke(evaluator_prompt)

        print("\n" + "🚀 FINOPS AGENT REPORT " + "=" * 40)
        print(report)
    except ThrottlingException as e:
        print(f"\n⚠ Throttled: {e}. Retry in a moment.")
    except Exception as e:
        print(f"\n⚠ Error generating report: {e}")


if __name__ == "__main__":
    run_finops_agent("infra.tf")
