from pathlib import Path
import yaml


class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)

    def load(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
