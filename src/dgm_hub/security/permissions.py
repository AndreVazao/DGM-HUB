from pathlib import Path
import yaml


class PermissionManager:
    def __init__(self, config_path: str = "config/permissions.yaml"):
        path = Path(config_path)
        if not path.exists() and not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / config_path

        with path.open("r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def _normalize(self, path: str) -> str:
        return str(Path(path).resolve()).lower()

    def is_allowed(self, path: str) -> bool:
        target = self._normalize(path)

        blocked = [self._normalize(p) for p in self.config.get("blocked_paths", [])]
        allowed = [self._normalize(p) for p in self.config.get("allowed_paths", [])]

        if any(target.startswith(x) for x in blocked):
            return False

        return any(target.startswith(x) for x in allowed)

    def require_allowed(self, path: str):
        if not self.is_allowed(path):
            raise PermissionError(f"Access denied: {path}")
