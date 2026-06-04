from pathlib import Path
import sys


def enable_src_imports() -> None:
    src_path = Path(__file__).resolve().parent / "src"
    src = str(src_path)
    if src not in sys.path:
        sys.path.insert(0, src)
