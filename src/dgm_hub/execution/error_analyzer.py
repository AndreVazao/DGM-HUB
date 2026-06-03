import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedError:

    file: Optional[str]
    line: Optional[int]
    message: str
    raw: str


class ErrorAnalyzer:

    def parse(self, raw_output: str) -> ParsedError:

        file_match = re.search(r'File "(.+?)"', raw_output)

        line_match = re.search(r'line (\d+)', raw_output)

        message_match = raw_output.strip().split("\n")[-1]

        return ParsedError(
            file=file_match.group(1) if file_match else None,
            line=int(line_match.group(1)) if line_match else None,
            message=message_match,
            raw=raw_output
        )
