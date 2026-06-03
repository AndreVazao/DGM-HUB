from pathlib import Path


class RepositoryContextGenerator:

    def build(self, root: str):

        root_path = Path(root)

        result = {
            'root': str(root_path),
            'files': [],
            'directories': []
        }

        for item in root_path.iterdir():

            if item.is_dir():
                result['directories'].append(item.name)
            else:
                result['files'].append(item.name)

        return result
