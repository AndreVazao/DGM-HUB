from pathlib import Path

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime


def main():
    config_path = Path("config/default_config.yaml")

    config = ConfigLoader(
        str(config_path)
    ).load()

    runtime = build_runtime(config)

    runtime.start()


if __name__ == "__main__":
    main()
