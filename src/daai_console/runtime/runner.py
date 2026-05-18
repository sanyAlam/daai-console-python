from __future__ import annotations

from typing import Any, Callable

from daai_console.client import DaaiClient
from daai_console.store import PendingStore
from daai_console.types import ExecutionStatus, GovernanceStatus


ActionExecutor = Callable[[dict[str, Any]], Any]


class DaaiActionRunner:
    def __init__(self, client: DaaiClient, pending_store: PendingStore) -> None:
        self._client = client
        self._pending_store = pending_store
        self._executors: dict[str, ActionExecutor] = {}

    def when_executable(
        self,
        action: str,
        run: ActionExecutor,
    ) -> None:
        """Register a developer-owned executor for one action name."""
        self._executors[action] = run

    def run_pending_once(self) -> int:
        """Poll pending actions once and execute only actions marked executable."""
        executed_count = 0
        pending_actions = self._pending_store.list_pending()

        for pending in pending_actions:
            status = self._client.status(pending.action_run_id)

            if status.governance_status in (
                GovernanceStatus.REJECTED,
                GovernanceStatus.BLOCKED,
            ):
                self._pending_store.remove(pending.action_run_id)
                continue

            if status.execution_status in (
                ExecutionStatus.EXECUTED,
                ExecutionStatus.FAILED,
            ):
                self._pending_store.remove(pending.action_run_id)
                continue

            if not status.executable:
                continue

            executor = self._executors.get(pending.action)
            if executor is None:
                continue

            try:
                result = executor(pending.payload)
                execution_result = _normalize_execution_result(result)
                self._client.report_executed(
                    action_run_id=pending.action_run_id,
                    execution_result=execution_result,
                )
                executed_count += 1
            except Exception as exc:
                self._client.report_failed(
                    action_run_id=pending.action_run_id,
                    execution_error=f"{type(exc).__name__}: {exc}",
                )
            finally:
                self._pending_store.remove(pending.action_run_id)

        return executed_count


def _normalize_execution_result(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, dict):
        return result
    return {"result": result}
