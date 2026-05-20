from __future__ import annotations

import os
import sys
from typing import Any

from daai_console import DaaiClient, GovernanceStatus
from daai_console.exceptions import DaaiApiError, DaaiError

DEFAULT_ACTION_NAME = "send_invoice_reminder"
SETUP_INSTRUCTIONS = (
    "Set required values before running:\n"
    'export DAAI_API_KEY="..."\n'
    'export DAAI_WORKSPACE_KEY="..."\n'
    'export DAAI_BASE_URL="https://stage.api.daaihq.com"\n'
)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}\n\n"
            f"{SETUP_INSTRUCTIONS}"
        )
    return value.strip()


def load_config() -> dict[str, str]:
    api_key = require_env("DAAI_API_KEY")
    workspace_key = require_env("DAAI_WORKSPACE_KEY")
    base_url = require_env("DAAI_BASE_URL").rstrip("/")
    if "stage.daaihq.com" in base_url and "stage.api.daaihq.com" not in base_url:
        raise RuntimeError(
            "DAAI_BASE_URL must point to the API, not the dashboard. "
            "Use https://stage.api.daaihq.com for staging."
        )

    return {
        "api_key": api_key,
        "workspace_key": workspace_key,
        "base_url": base_url,
        "action_name": os.getenv("DAAI_TEST_ACTION_NAME", DEFAULT_ACTION_NAME).strip()
        or DEFAULT_ACTION_NAME,
    }


def build_payload() -> dict[str, Any]:
    # Keep the payload simple and synthetic. Do not put real secrets here.
    return {
        "invoice_id": "ALPHA-INV-001",
        "customer_name": "Alpha Test Customer",
        "customer_email": "customer@example.com",
        "amount": 1250,
    }


def print_unknown_action_help() -> None:
    print("\nBlocked or unknown action explanation:")
    print("  This usually means the action is not registered in this workspace,")
    print("  the API/workspace key belongs to another workspace, or the action")
    print("  name does not match exactly.")
    print("  Register the action in the dashboard first, then rerun this script")
    print("  with the same action name.")


def print_api_error_help(exc: DaaiApiError) -> None:
    print(f"ERROR: DAAI API request failed: {exc}", file=sys.stderr)
    detail = exc.body.get("detail") if isinstance(exc.body, dict) else exc.body
    if detail and "unknown_action" in str(detail):
        print_unknown_action_help()


def main() -> int:
    try:
        config = load_config()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("DAAI Console live client smoke test")
    print(f"API base URL: {config['base_url']}")
    print(f"Action name: {config['action_name']}")
    print("Reminder: this action must already be registered in your workspace.")

    client = DaaiClient(
        base_url=config["base_url"],
        api_key=config["api_key"],
        workspace_key=config["workspace_key"],
    )

    try:
        # intercept() proposes the action. It does not execute your business action.
        intercept = client.intercept(
            action=config["action_name"],
            payload=build_payload(),
            idempotency_key="alpha-smoke-client:ALPHA-INV-001",
        )

        print("\nIntercept result:")
        print(f"  action_run_id: {intercept.action_run_id}")
        print(f"  governance_status: {intercept.governance_status.value}")
        print(f"  execution_status: {intercept.execution_status.value}")
        print(f"  executable: {str(intercept.executable).lower()}")
        print(f"  governance_reason: {intercept.governance_reason}")
        if intercept.receipt is not None:
            print(f"  receipt_id: {intercept.receipt.id}")

        if intercept.governance_status == GovernanceStatus.PENDING_APPROVAL:
            print("\nPending approval:")
            print("  Approve this action from the approval email or dashboard.")
            print("  This script will not auto-approve or bypass governance.")
            return 0

        if intercept.governance_status in (GovernanceStatus.BLOCKED, GovernanceStatus.REJECTED):
            print("\nAction must not execute because DAAI Console blocked or rejected it.")
            if (
                intercept.governance_status == GovernanceStatus.BLOCKED
                or "unknown_action" in intercept.governance_reason
            ):
                print_unknown_action_help()
            return 0

        if not intercept.executable:
            print("\nAction is not executable yet. Do not run the business action.")
            return 0

        # This is a smoke test, so execution is simulated. No real invoice reminder is sent.
        report = client.report_executed(
            intercept.action_run_id,
            execution_result={
                "result_summary": "Alpha smoke test simulated execution completed.",
            },
        )
        print("\nSimulated execution reported:")
        print(f"  execution_status: {report.execution_status.value}")
        print(f"  execution_reported_at: {report.execution_reported_at}")
        return 0
    except DaaiApiError as exc:
        print_api_error_help(exc)
        return 1
    except DaaiError as exc:
        print(f"ERROR: DAAI request failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
