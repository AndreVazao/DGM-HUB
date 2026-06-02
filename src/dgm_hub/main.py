from pathlib import Path

from dgm_hub.core.config import ConfigLoader

from dgm_hub.core.bootstrap import build_runtime

from dgm_hub.control.worker import Worker


def main():

    config = ConfigLoader(

        str(

            Path(

                "config/default_config.yaml"

            )

        )

    ).load()

    runtime = build_runtime(
        config
    )

    runtime.start()

    worker = Worker(
        runtime
    )

    worker.run()


if __name__ == "__main__":

    main()