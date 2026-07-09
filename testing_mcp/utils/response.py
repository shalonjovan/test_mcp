from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from testing_mcp.exceptions import ToolError

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ToolResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: ErrorDetail | None = None


def success(data: T) -> ToolResponse[T]:
    return ToolResponse(success=True, data=data)


def failure(error: ToolError) -> ToolResponse[None]:
    return ToolResponse(
        success=False,
        error=ErrorDetail(
            code=error.code,
            message=error.message,
            details=error.details,
        ),
    )
