# Alpha Test Checklist

This checklist is written for cybersecurity-minded alpha testers evaluating the DAAI Console Python SDK.

## Setup Verification

- Install the SDK from the local wheel: `pip install ./dist/daai_console-0.1.0a1-py3-none-any.whl`
- Configure `DAAI_BASE_URL` in a server-side environment.
- Configure `DAAI_API_KEY` in a server-side environment.
- Configure `DAAI_WORKSPACE_KEY` in a server-side environment.
- Run `python examples/staging_alpha_test.py --dry-run` to confirm the example can load safely without making API calls.
- Run `python examples/staging_alpha_test.py` against the staging API when ready.

## Happy Path

- Propose a registered risky action with `intercept()` or `PendingActionManager.propose()`.
- Observe `governance_status=pending_approval` and `executable=false`.
- Receive the approval email at the configured approver address.
- Approve the action from the email approval link.
- Confirm `status()` returns `executable=true`.
- Run the local executor through `DaaiActionRunner.run_pending_once()` or your own guarded worker.
- Report successful execution with `report_executed()`.
- Verify the receipt in the dashboard action-run detail view.

## Negative Path

- Confirm a wrong API key fails clearly and does not expose secrets.
- Confirm a wrong workspace key fails clearly and does not expose secrets.
- Confirm an unknown action is blocked or rejected by the API.
- Confirm a pending action does not execute.
- Confirm a rejected action does not execute.
- Confirm a blocked action does not execute.

## Local Persistence Test

- Propose an action that requires approval using `SQLitePendingStore`.
- Confirm the pending run persists in the SQLite database.
- Stop and restart the worker process.
- Confirm the worker can resume later from the same SQLite file.
- Confirm the runner only executes when `executable=true`.

## Security Review Questions

- Are API keys and workspace keys handled safely?
- Does the SDK ever execute before approval?
- Are payloads unnecessarily exposed to DAAI Console or logs?
- Is the local SQLite store safe enough for the expected use case?
- Are errors clear without leaking secrets?
- Are audit receipts clear enough for the client or auditor?
- Is the approval boundary understandable to developers and approvers?
- Can a developer accidentally misuse the SDK and execute a risky action anyway?
- What should be made stricter before public release?

## Feedback Format

Please report findings with this structure:

```text
Security concern:
Severity:
Reproduction steps:
Expected behavior:
Actual behavior:
Suggested fix:
```
