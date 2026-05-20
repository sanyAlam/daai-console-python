from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from daai_console import (
    DaaiActionRunner,
    DaaiClient,
    GovernanceStatus,
    PendingActionManager,
    SQLitePendingStore,
)
from daai_console.exceptions import DaaiApiError, DaaiError

DEFAULT_ACTION_NAME = "send_invoice_reminder"
DEFAULT_DB_PATH = "./daai_alpha_pending.db"
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


def load_config(require_api: bool = True) -> dict[str, str]:
    action_name = os.getenv("DAAI_TEST_ACTION_NAME", DEFAULT_ACTION_NAME).strip()
    db_path = os.getenv("DAAI_PENDING_DB_PATH", DEFAULT_DB_PATH).strip()

    config = {
        "action_name": action_name or DEFAULT_ACTION_NAME,
        "db_path": db_path or DEFAULT_DB_PATH,
    }

    if not require_api:
        return config

    api_key = require_env("DAAI_API_KEY")
    workspace_key = require_env("DAAI_WORKSPACE_KEY")
    base_url = require_env("DAAI_BASE_URL").rstrip("/")
    if "stage.daaihq.com" in base_url and "stage.api.daaihq.com" not in base_url:
        raise RuntimeError(
            "DAAI_BASE_URL must point to the API, not the dashboard. "
            "Use https://stage.api.daaihq.com for staging."
        )

    config.update(
        {
            "api_key": api_key,
            "workspace_key": workspace_key,
            "base_url": base_url,
        }
    )
    return config


def build_payload() -> dict[str, Any]:
    # Keep the payload synthetic. The local SQLite store may persist this payload.
    return {
        "invoice_id": "ALPHA-INV-001",
        "customer_name": "Alpha Test Customer",
        "customer_email": "customer@example.com",
        "amount": 1250,
    }


def build_client(config: dict[str, str]) -> DaaiClient:
    return DaaiClient(
        base_url=config["base_url"],
        api_key=config["api_key"],
        workspace_key=config["workspace_key"],
    )


def build_store(config: dict[str, str]) -> SQLitePendingStore:
    return SQLitePendingStore(Path(config["db_path"]))


def fake_executor(payload: dict[str, Any]) -> dict[str, str]:
    # This executor intentionally simulates work only. It sends no email and calls no provider.
    invoice_id = str(payload.get("invoice_id", "unknown"))
    print(f"Simulating approved action for invoice_id={invoice_id}")
    return {"result_summary": "Alpha smoke test simulated execution completed."}


def print_unknown_action_help() -> None:
    print("\nBlocked or unknown action explanation:")
    print("  This usually means the action is not registered in this workspace,")
    print("  the API/workspace key belongs to another workspace, or the action")
    print("  name does not match exactly.")
    print("  Register the action in the dashboard first, then rerun this script")
    print("  with the same action name.")


def propose() -> int:
    config = load_config(require_api=True)
    print("DAAI Console live runtime smoke test: propose")
    print(f"API base URL: {config['base_url']}")
    print(f"Action name: {config['action_name']}")
    print(f"Local pending DB: {config['db_path']}")
    print("Reminder: this action must already be registered in your workspace.")

    client = build_client(config)
    try:
        store = build_store(config)
        manager = PendingActionManager(client=client, pending_store=store)
        ticket = manager.propose(
            action=config["action_name"],
            payload=build_payload(),
            idempotency_key="alpha-smoke-runtime:ALPHA-INV-001",
        )

        print("\nProposal result:")
        print(f"  action_run_id: {ticket.action_run_id}")
        print(f"  governance_status: {ticket.governance_status.value}")
        print(f"  execution_status: {ticket.execution_status.value}")
        print(f"  executable: {str(ticket.executable).lower()}")
        print(f"  governance_reason: {ticket.governance_reason}")
        print(f"  stored_for_later: {str(ticket.stored_for_later).lower()}")

        if ticket.governance_status == GovernanceStatus.PENDING_APPROVAL:
            print("\nPending approval:")
            print("  Approve this action from the approval email or dashboard.")
            print("  Then run: python examples/live_runtime_smoke.py run-pending")
        elif ticket.governance_status in (GovernanceStatus.BLOCKED, GovernanceStatus.REJECTED):
            print("\nAction must not execute because DAAI Console blocked or rejected it.")
            if (
                ticket.governance_status == GovernanceStatus.BLOCKED
                or "unknown_action" in ticket.governance_reason
            ):
                print_unknown_action_help()
        elif ticket.executable:
            print("\nAction is already executable. Run run-pending only if it was stored locally.")

        return 0
    except DaaiApiError as exc:
        print(f"ERROR: DAAI API request failed: {exc}", file=sys.stderr)
        detail = exc.body.get("detail") if isinstance(exc.body, dict) else exc.body
        if detail and "unknown_action" in str(detail):
            print_unknown_action_help()
        return 1
    except DaaiError as exc:
        print(f"ERROR: DAAI request failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


def run_pending() -> int:
    config = load_config(require_api=True)
    print("DAAI Console live runtime smoke test: run-pending")
    print(f"Action name: {config['action_name']}")
    print(f"Local pending DB: {config['db_path']}")

    client = build_client(config)
    try:
        store = build_store(config)
        runner = DaaiActionRunner(client=client, pending_store=store)
        runner.when_executable(action=config["action_name"], run=fake_executor)

        # The runner checks DAAI Console status and only calls fake_executor when executable=true.
        executed_count = runner.run_pending_once()
        print("\nRun-pending result:")
        print(f"  simulated_executions_reported: {executed_count}")
        if executed_count == 0:
            print("  No local pending action was executable yet.")
            print("  If the action is pending_approval, approve it from email/dashboard and rerun.")
        return 0
    except DaaiError as exc:
        print(f"ERROR: DAAI request failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


def list_pending() -> int:
    config = load_config(require_api=False)
    store = build_store(config)
    pending = store.list_pending()

    print("DAAI Console live runtime smoke test: list-pending")
    print(f"Local pending DB: {config['db_path']}")
    if not pending:
        print("No local pending actions found.")
        return 0

    print("Local pending actions:")
    for action in pending:
        print(f"  action_run_id: {action.action_run_id}")
        print(f"  action: {action.action}")
        print(f"  created_at: {action.created_at.isoformat()}")
        print("  payload: <not printed; may contain business data>")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run live DAAI Console runtime smoke-test helpers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("propose", help="Propose and locally store a pending action.")
    subparsers.add_parser("run-pending", help="Run locally stored actions if executable=true.")
    subparsers.add_parser("list-pending", help="List local pending action metadata.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "propose":
            return propose()
        if args.command == "run-pending":
            return run_pending()
        if args.command == "list-pending":
            return list_pending()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
