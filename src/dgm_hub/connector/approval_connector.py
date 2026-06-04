import json
import requests
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ActionRequest:
    id: str
    type: str              # "shell" | "patch" | "test" | "git"
    payload: Dict[str, Any]
    description: str


class ApprovalConnector:

    def __init__(self):
        self.pending: Dict[str, ActionRequest] = {}

    def request_action(self, action: ActionRequest):
        self.pending[action.id] = action

        try:
            requests.post(
                "http://127.0.0.1:8765/submit",
                json={
                    "action_id": action.id,
                    "action_type": action.type,
                    "description": action.description,
                    "payload": action.payload
                },
                timeout=5
            )
        except Exception as e:
            # Fallback or log error if UI is not running
            print(f"Failed to submit action to UI: {e}")

        return {
            "status": "waiting_approval",
            "action_id": action.id
        }

    def approve(self, action_id: str):
        if action_id not in self.pending:
            return {"status": "not_found"}

        action = self.pending.pop(action_id)

        return {
            "status": "approved",
            "action": action
        }

    def reject(self, action_id: str):
        if action_id in self.pending:
            self.pending.pop(action_id)

        return {
            "status": "rejected",
            "action_id": action_id
        }

    def list_pending(self):
        return {
            "pending": list(self.pending.values())
        }
