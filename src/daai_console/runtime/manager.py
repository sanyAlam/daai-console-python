from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from daai_console.client import DaaiClient
from daai_console.store import PendingAction, PendingStore
from daai_console.types import ActionTicket, GovernanceStatus


class PendingActionManager:
    def __init__(self, client: DaaiClient, pending_store: PendingStore) -> None:
        self._client = client
        self._pending_store = pending_store

    def propose(
        self,
        action: str,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> ActionTicket:
        """Propose an action and persist it locally only when approval is pending."""
        action_payload = payload or {}
        response = self._client.intercept(
            action=action,
            payload=action_payload,
            idempotency_key=idempotency_key,
        )

        stored_for_later = response.governance_status == GovernanceStatus.PENDING_APPROVAL
        if stored_for_later:
            self._pending_store.put(
                PendingAction(
                    action_run_id=response.action_run_id,
                    action=action,
                    payload=action_payload,
                    idempotency_key=idempotency_key,
                    created_at=datetime.now(timezone.utc),
                )
            )

        return ActionTicket(
            action_run_id=response.action_run_id,
            action=action,
            payload=action_payload,
            idempotency_key=idempotency_key,
            governance_status=response.governance_status,
            execution_status=response.execution_status,
            governance_reason=response.governance_reason,
            executable=response.executable,
            idempotent_replay=response.idempotent_replay,
            stored_for_later=stored_for_later,
        )
