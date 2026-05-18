from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DaaiError(Exception):
    message: str
    status_code: int | None = None
    body: Any | None = None

    def __str__(self) -> str:
        if self.status_code is None:
            return self.message
        return f"{self.status_code}: {self.message}"


class DaaiUnauthorizedError(DaaiError):
    """Raised for 401 API responses."""


class DaaiNotFoundError(DaaiError):
    """Raised for 404 API responses."""


class DaaiConflictError(DaaiError):
    """Raised for 409 API responses."""


class DaaiValidationError(DaaiError):
    """Raised for 422 API responses."""


class DaaiApiError(DaaiError):
    """Raised for other non-success API responses."""
