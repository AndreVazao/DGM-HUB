from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class PatchProposal:
    file_path: str
    original: str
    modified: str
    reason: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def requires_approval(self):
        return self.original != self.modified
