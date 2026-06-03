from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Session:
    repo_path: str
    active_plans: List[str] = field(default_factory=list)
    state: Dict = field(default_factory=dict)


class SessionManager:
    def __init__(self):
        self.sessions = {}

    def get_session(self, repo_path: str):
        if repo_path not in self.sessions:
            self.sessions[repo_path] = Session(repo_path=repo_path)
        return self.sessions[repo_path]

    def attach_plan(self, repo_path: str, plan_id: str):
        session = self.get_session(repo_path)
        session.active_plans.append(plan_id)
