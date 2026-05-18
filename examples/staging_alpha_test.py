from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from daai_console import DaaiClient, GovernanceStatus
from daai_console.exceptions import DaaiError

ACTION = "send_invoice_reminder"
PAYLOAD = {
    "invoice_id": "ALPHA-INV-1025",
    "customer_name": "Example Customer",
    "amount": 1250,
    "currency": "USD",
}
IDEMPOTENCY_KEY = "invoice-reminder:ALPHA-INV-1025"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a safe DAAI Console staging alpha SDK smoke test.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned action without calling the DAAI Console API.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("Dry run: no API call will be made.")
        print(f"Action: {ACTION}")
        print(f"Payload keys: {', '.join(sorted(PAYLOAD))}")
        print(f"Idempotency key: {IDEMPOTENCY_KEY}")
        return 0

    try:
        config = load_config()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    client = DaaiClient(
        base_url=config["base_url"],
        api_key=config["api_key"],
        workspace_key=config["workspace_key"],
    )

    action_run_id = None

    try:
        intercept = client.intercept(
            action=ACTION,
            payload=PAYLOAD,
            idempotency_key=IDEMPOTENCY_KEY,
        )
        action_run_id = intercept.action_run_id
        print("Intercept result:")
        print(f"  action_run_id: {intercept.action_run_id}")
        print(f"  governance_status: {intercept.governance_status.value}")
        print(f"  execution_status: {intercept.execution_status.value}")
        print(f"  executable: {str(intercept.executable).lower()}")
        print(f"  idempotent_replay: {str(intercept.idempotent_replay).lower()}")

        if intercept.governance_status == GovernanceStatus.PENDING_APPROVAL:
            print("Pending approval: approve or reject from the configured approval email.")

        status = client.status(intercept.action_run_id)
        print("Status check:")
        print(f"  governance_status: {status.governance_status.value}")
        print(f"  execution_status: {status.execution_status.value}")
        print(f"  executable: {str(status.executable).lower()}")

        if not status.executable:
            print("Execution skipped: DAAI Console has not marked this action executable.")
            return 0

        result = simulate_send_invoice_reminder(PAYLOAD)
        report = client.report_executed(
            intercept.action_run_id,
            execution_result=result,
        )
        print("Execution reported:")
        print(f"  execution_status: {report.execution_status.value}")
        print(f"  execution_reported_at: {report.execution_reported_at}")
        return 0
    except DaaiError as exc:
        print(f"ERROR: DAAI API request failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - keep alpha script output simple.
        if action_run_id is not None:
            try:
                client.report_failed(action_run_id, f"{type(exc).__name__}: {exc}")
            except Exception:
                pass
        print(f"ERROR: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


def load_config() -> dict[str, str]:
    missing = [
        name
        for name in ("DAAI_BASE_URL", "DAAI_API_KEY", "DAAI_WORKSPACE_KEY")
        if not os.environ.get(name, "").strip()
    ]
    if missing:
        raise RuntimeError("missing required env vars: " + ", ".join(missing))

    return {
        "base_url": os.environ["DAAI_BASE_URL"].strip().rstrip("/"),
        "api_key": os.environ["DAAI_API_KEY"].strip(),
        "workspace_key": os.environ["DAAI_WORKSPACE_KEY"].strip(),
    }


def simulate_send_invoice_reminder(payload: dict[str, Any]) -> dict[str, Any]:
    # Replace this with your real provider call after validating the approval path.
    return {
        "result_summary": "Simulated invoice reminder sent.",
        "invoice_id": payload["invoice_id"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
