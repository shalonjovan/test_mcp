from __future__ import annotations

from typing import Any


class ToolError(Exception):
    """Base exception for all tool errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __init__(
        self, message: str, *, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class NotFoundError(ToolError):
    """Raised when a requested resource is not found."""

    def __init__(
        self, message: str, *, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, code="NOT_FOUND", details=details)


class PermissionError_(ToolError):
    """Raised when access is denied."""

    def __init__(
        self, message: str, *, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, code="PERMISSION_DENIED", details=details)


class TimeoutError_(ToolError):
    """Raised when an operation times out."""

    def __init__(
        self, message: str, *, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, code="TIMEOUT", details=details)
