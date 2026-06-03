from dataclasses import dataclass
from typing import Any


@dataclass
class ToolRequest:
    tool: str
    payload: dict


@dataclass
class ToolResponse:
    success: bool
    result: Any = None
    error: str | None = None


class ToolContractError(Exception):
    pass


def validate_request(request: ToolRequest):
    if not request.tool:
        raise ToolContractError("tool missing")

    if not isinstance(request.payload, dict):
        raise ToolContractError("payload must be dict")
