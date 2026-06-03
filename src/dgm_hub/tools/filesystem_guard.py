from pathlib import Path
from dgm_hub.security.permissions import PermissionManager


class FilesystemGuard:
    def __init__(self):
        self.permissions = PermissionManager()

    def read_text(self, path:str):
        self.permissions.require_allowed(path)
        return Path(path).read_text(encoding='utf-8')

    def write_text(self, path:str, content:str):
        self.permissions.require_allowed(path)
        Path(path).write_text(content, encoding='utf-8')

    def exists(self, path:str):
        self.permissions.require_allowed(path)
        return Path(path).exists()
