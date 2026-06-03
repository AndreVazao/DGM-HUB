import difflib

class DiffEngine:

    def build(self, original:str, modified:str):
        result = difflib.ndiff(
            original.splitlines(),
            modified.splitlines()
        )
        return list(result)
