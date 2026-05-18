from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class PendingAction:
    action_run_id: UUID
    action: str
    payload: dict[str, Any]
    idempotency_key: str | None
    created_at: datetime


class PendingStore(Protocol):
    def put(self, pending_action: PendingAction) -> None: ...

    def list_pending(self) -> list[PendingAction]: ...

    def remove(self, action_run_id: UUID | str) -> None: ...


class InMemoryPendingStore:
    def __init__(self) -> None:
        self._pending: dict[str, PendingAction] = {}

    def put(self, pending_action: PendingAction) -> None:
        self._pending[str(pending_action.action_run_id)] = pending_action

    def list_pending(self) -> list[PendingAction]:
        return sorted(
            self._pending.values(),
            key=lambda item: item.created_at,
        )

    def remove(self, action_run_id: UUID | str) -> None:
        self._pending.pop(str(action_run_id), None)


class SQLitePendingStore:
    def __init__(self, db_path: str | Path = "daai_console_pending_actions.sqlite3") -> None:
        self._db_path = str(db_path)
        self._ensure_schema()

    def put(self, pending_action: PendingAction) -> None:
        payload_json = json.dumps(pending_action.payload, separators=(",", ":"))

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pending_actions (
                    action_run_id,
                    action,
                    payload_json,
                    idempotency_key,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(action_run_id) DO UPDATE SET
                    action = excluded.action,
                    payload_json = excluded.payload_json,
                    idempotency_key = excluded.idempotency_key,
                    created_at = excluded.created_at
                """,
                (
                    str(pending_action.action_run_id),
                    pending_action.action,
                    payload_json,
                    pending_action.idempotency_key,
                    pending_action.created_at.isoformat(),
                ),
            )
            conn.commit()

    def list_pending(self) -> list[PendingAction]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT action_run_id, action, payload_json, idempotency_key, created_at
                FROM pending_actions
                ORDER BY created_at ASC
                """
            ).fetchall()

        pending: list[PendingAction] = []
        for row in rows:
            pending.append(
                PendingAction(
                    action_run_id=UUID(row["action_run_id"]),
                    action=row["action"],
                    payload=_parse_payload_json(row["payload_json"]),
                    idempotency_key=row["idempotency_key"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )

        return pending

    def remove(self, action_run_id: UUID | str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM pending_actions WHERE action_run_id = ?",
                (str(action_run_id),),
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_actions (
                    action_run_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    idempotency_key TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()


def _parse_payload_json(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if isinstance(parsed, dict):
        return parsed
    raise ValueError("pending payload must deserialize to an object")
