from __future__ import annotations

import os

from daai_console import DaaiClient


client = DaaiClient(
    base_url=os.environ["DAAI_BASE_URL"],
    api_key=os.environ["DAAI_API_KEY"],
    workspace_key=os.environ["DAAI_WORKSPACE_KEY"],
)

proposal = client.intercept(
    action="send_invoice_reminder",
    payload={"invoice_id": "INV-1025", "amount": 1250},
    idempotency_key="invoice-reminder:INV-1025",
)

print(proposal.governance_status.value)
print(f"executable={proposal.executable}")
