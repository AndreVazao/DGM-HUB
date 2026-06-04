from dgm_hub.connector.approval_connector import ApprovalConnector, ActionRequest
import uuid


class ConnectorRouter:

    def __init__(self):
        self.connector = ApprovalConnector()

    def request_patch(self, file: str, content: str):

        action = ActionRequest(
            id=str(uuid.uuid4()),
            type="patch",
            description=f"Modify file {file}",
            payload={
                "file": file,
                "content": content
            }
        )

        return self.connector.request_action(action)

    def request_shell(self, cmd: str, cwd: str):

        action = ActionRequest(
            id=str(uuid.uuid4()),
            type="shell",
            description=f"Execute command: {cmd}",
            payload={
                "cmd": cmd,
                "cwd": cwd
            }
        )

        return self.connector.request_action(action)
