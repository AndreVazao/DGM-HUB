from pathlib import Path

from dgm_hub.security.path_guard import PathGuard
from dgm_hub.tools.base import Tool


class FilesystemTool(Tool):
    name = "filesystem"

    def __init__(self, guard: PathGuard):
        self.guard = guard

    def execute(self, operation: str, path: str, content: str | None = None):

        if not self.guard.is_allowed(path):
            raise PermissionError(f"Path denied: {path}")

        target = Path(path)

        if operation == "read":

            raw = target.read_bytes()

            # UTF-8 normal
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                pass

            # UTF-16 LE (Windows / PowerShell redirects)
            try:
                return raw.decode("utf-16-le")
            except UnicodeDecodeError:
                pass

            # fallback seguro
            return raw.decode("latin-1", errors="replace")

        if operation == "write":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content or "", encoding="utf-8")
            return {"status": "written"}

        raise ValueError("Unsupported filesystem operation")