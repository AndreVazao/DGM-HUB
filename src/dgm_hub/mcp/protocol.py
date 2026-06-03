from dataclasses import dataclass
from typing import Any

@dataclass
class MCPRequest:
    tool: str
    payload: dict
    session_id: str

@dataclass
class MCPResponse:
    success: bool
    result: Any = None
    error: str | None = None
