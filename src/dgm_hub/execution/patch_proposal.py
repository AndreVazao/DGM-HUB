from dataclasses import dataclass
from datetime import datetime


@dataclass
class PatchProposal:
    file_path: str
    original: str
    modified: str
    reason: str
    created_at: str = datetime.utcnow().isoformat()

    def requires_approval(self):
        return self.original != self.modified
