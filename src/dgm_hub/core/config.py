from pathlib import Path
import yaml


class ConfigLoader:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        if not self.config_path.is_absolute():
            self.config_path = self.config_path.resolve()

    def load(self) -> dict:
        if not self.config_path.exists():
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            fallback_path = project_root / "config" / self.config_path.name
            if fallback_path.exists():
                self.config_path = fallback_path
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
