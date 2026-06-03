from pathlib import Path


class FileLoader:

    def read(self, path: str) -> str:

        p = Path(path)

        if not p.exists():

            raise FileNotFoundError(path)

        return p.read_text(encoding="utf-8")

    def write(self, path: str, content: str):

        p = Path(path)

        p.write_text(content, encoding="utf-8")
