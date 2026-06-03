from dataclasses import dataclass


@dataclass
class ApprovalRequest:
    title: str
    description: str
    required: bool = True


class ApprovalWorkflow:
    def should_apply(self, approval: ApprovalRequest, approved: bool) -> bool:
        if not approval.required:
            return True

        return approved
