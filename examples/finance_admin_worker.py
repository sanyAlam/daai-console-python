from __future__ import annotations

import os

from daai_console import DaaiActionRunner, DaaiClient, SQLitePendingStore


client = DaaiClient(
    base_url=os.environ["DAAI_BASE_URL"],
    api_key=os.environ["DAAI_API_KEY"],
    workspace_key=os.environ["DAAI_WORKSPACE_KEY"],
)
store = SQLitePendingStore("daai_pending_actions.sqlite3")


def send_invoice_reminder(payload: dict) -> dict:
    # Keep the existing business execution here.
    return {"result_summary": f"sent reminder for {payload['invoice_id']}"}


runner = DaaiActionRunner(client=client, pending_store=store)
runner.when_executable("send_invoice_reminder", send_invoice_reminder)

executed = runner.run_pending_once()
print(f"executed={executed}")
