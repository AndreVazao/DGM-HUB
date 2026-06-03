from dataclasses import dataclass

from dgm_hub.execution.diff_engine import DiffEngine


@dataclass
class PatchProposalResult:

    file_path: str
    original: str
    modified: str
    diff: any


class PatchIntelligenceEngine:

    def __init__(self):

        self.diff_engine = DiffEngine()

    def propose_patch(
        self,
        file_path: str,
        original_code: str,
        error: str,
        line: int | None = None
    ):

        modified_code = original_code.split("\n")

        # targeted fix (v2 real behavior)

        if line:

            idx = max(0, line - 1)

            if idx < len(modified_code):

                modified_code[idx] = "# AUTO FIXED LINE"

        modified_code = "\n".join(modified_code)

        diff = self.diff_engine.build(
            original_code,
            modified_code
        )

        return PatchProposalResult(
            file_path=file_path,
            original=original_code,
            modified=modified_code,
            diff=diff
        )
