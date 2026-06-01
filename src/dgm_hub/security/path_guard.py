from pathlib import Path


class PathGuard:
    def __init__(self, allowed_paths: list[str]):
        self.allowed = [Path(p).resolve() for p in allowed_paths]

    def is_allowed(self, path: str) -> bool:
        target = Path(path).resolve()

        for allowed in self.allowed:
            try:
                target.relative_to(allowed)
                return True
            except Exception:
                pass

        return False
