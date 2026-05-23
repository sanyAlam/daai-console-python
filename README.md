# DAAI Console Python SDK

DAAI Console is a governance layer for AI automations. It lets developers intercept risky registered agent actions before execution, route them through policy and approval, and produce audit receipts.

This repository contains the public alpha Python SDK for DAAI Console.

## What DAAI Console Is Not

DAAI Console is intentionally narrow in alpha. It is not:

- Magic interception of arbitrary code
- A browser automation framework
- A replacement for MCP
- An OS-wide agent scanner
- A full enterprise security platform

## Execution Boundary

DAAI Console governs proposal, policy, approval, status, and receipts.

The developer application owns real business execution, local business logic, executor functions, external integrations, and worker or cron triggers. Place this SDK before risky functions. The SDK does not execute callbacks inside `intercept()`.

## Install

From PyPI:

```bash
pip install daai-console
```

Alpha pinning:

```bash
pip install daai-console==0.1.0a2
```

## Environment

Set these values in your server-side environment:

```bash
export DAAI_API_KEY="..."
export DAAI_WORKSPACE_KEY="..."
export DAAI_BASE_URL="https://your-daai-api.example.com"
```

Do not expose these values in browser code or frontend bundles.

## Minimal Client Example

```python
import os

from daai_console import DaaiClient

client = DaaiClient(
    base_url=os.environ["DAAI_BASE_URL"],
    api_key=os.environ["DAAI_API_KEY"],
    workspace_key=os.environ["DAAI_WORKSPACE_KEY"],
)

payload = {
    "invoice_id": "INV-1025",
    "customer_name": "Acme Finance",
    "amount": 1250,
}

proposal = client.intercept(
    action="send_invoice_reminder",
    payload=payload,
    idempotency_key="invoice-reminder:INV-1025",
)

print(proposal.governance_status.value)
print(proposal.executable)

status = client.status(proposal.action_run_id)

if status.executable:
    try:
        # Your app owns the real business execution.
        provider_result = send_invoice_reminder(payload)
        client.report_executed(
            proposal.action_run_id,
            execution_result={"provider_id": provider_result["id"]},
        )
    except Exception as exc:
        client.report_failed(
            proposal.action_run_id,
            execution_error=f"{type(exc).__name__}: {exc}",
        )
else:
    print("Not executable yet. Wait for approval or policy decision.")
```

## Runtime Helper Example

The runtime helpers make the safe path easier: propose once, persist pending approvals locally, and run only after DAAI Console reports `executable=true`.

```python
import os

from daai_console import (
    DaaiActionRunner,
    DaaiClient,
    PendingActionManager,
    SQLitePendingStore,
)

client = DaaiClient(
    base_url=os.environ["DAAI_BASE_URL"],
    api_key=os.environ["DAAI_API_KEY"],
    workspace_key=os.environ["DAAI_WORKSPACE_KEY"],
)
store = SQLitePendingStore("daai_pending_actions.sqlite3")
manager = PendingActionManager(client=client, pending_store=store)

manager.propose(
    action="send_invoice_reminder",
    payload={"invoice_id": "INV-1025", "amount": 1250},
    idempotency_key="invoice-reminder:INV-1025",
)


def send_invoice_reminder_executor(payload: dict) -> dict:
    # Keep your existing execution function here.
    return {"message_id": "example-local-result"}


runner = DaaiActionRunner(client=client, pending_store=store)
runner.when_executable(
    action="send_invoice_reminder",
    run=send_invoice_reminder_executor,
)

executed_count = runner.run_pending_once()
print(f"Executed {executed_count} approved action(s).")
```

## Live Alpha Smoke Tests

The unit tests in `tests/` are mocked SDK-internal tests. They do not call DAAI Console and should remain safe for normal local runs and CI.

The scripts in `examples/live_*.py` are opt-in live smoke tests for alpha testers with real DAAI Console credentials. They call the configured API and should be run manually against a staging or alpha workspace.

Before running live scripts, make sure the action is already registered in your DAAI Console workspace. The default expected action is `send_invoice_reminder`. You can override it with `DAAI_TEST_ACTION_NAME`.

Set required environment variables:

```bash
export DAAI_API_KEY="..."
export DAAI_WORKSPACE_KEY="..."
export DAAI_BASE_URL="https://stage.api.daaihq.com"
```

`DAAI_BASE_URL` must point to the API, not the dashboard. For staging, use `https://stage.api.daaihq.com`, not `https://stage.daaihq.com`.

Optional environment variables:

```bash
export DAAI_TEST_ACTION_NAME="send_invoice_reminder"
export DAAI_PENDING_DB_PATH="./daai_alpha_pending.db"
```

Run the low-level client smoke test:

```bash
python examples/live_client_smoke.py
```

Run the runtime smoke flow:

```bash
python examples/live_runtime_smoke.py propose
python examples/live_runtime_smoke.py list-pending
```

If the proposal returns `pending_approval`, approve it from the approval email or dashboard. The SDK does not auto-approve and does not bypass governance. After approval, run:

```bash
python examples/live_runtime_smoke.py run-pending
```

`run-pending` uses `DaaiActionRunner` and a fake executor. It only simulates execution, and only runs when DAAI Console reports `executable=true`.

If the API returns `blocked` or `unknown_action`, it usually means the action is not registered in the workspace, the API/workspace key belongs to another workspace, or the action name does not match exactly. Register the action in the dashboard first, then rerun the script with the same action name.

## Security Notes

- Store `DAAI_API_KEY` and `DAAI_WORKSPACE_KEY` server-side only.
- Do not expose keys in browser or frontend code.
- Approval links should not contain sensitive payload data.
- Local pending stores may contain business payloads; treat them as sensitive.
- The SDK does not execute callbacks inside `intercept()`.
- Rejected and blocked actions should not execute.

## Known Limitations

- Python SDK first.
- Cooperative interception only.
- Developers must register and gate actions explicitly.
- No automatic arbitrary-code interception.
- Staging alpha APIs may change.
- No enterprise RBAC in alpha.

## Alpha Docs

- [Alpha test checklist](docs/alpha-test-checklist.md)
- [Security model](docs/security-model.md)
- [Agency adoption prompt](docs/agency-adoption-prompt.md)
- [Known limitations](docs/known-limitations.md)
- [Staging alpha guide](docs/staging-alpha-guide.md)
