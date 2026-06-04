from pathlib import Path
import json

from dgm_hub.tools.base import Tool


class RepoTool(Tool):
    name = "repo_tool"
    aliases = ["repo"]

    def execute(self, operation: str, repo_path: str):

        repo = Path(repo_path)

        if not repo.exists():
            raise ValueError(f"Repo path does not exist: {repo_path}")

        if operation == "tree":
            tree = self._build_tree(repo)

            return {
                "root": str(repo),
                "tree": tree,
                "summary": self._build_summary(tree)
            }

        if operation == "summary":
            tree = self._build_tree(repo)
            return {
                "root": str(repo),
                "summary": self._build_summary(tree)
            }

        if operation == "json":
            tree = self._build_tree(repo)

            return json.dumps({
                "root": str(repo),
                "tree": tree,
                "summary": self._build_summary(tree)
            }, indent=2)

        if operation == "markdown":
            tree = self._build_tree(repo)
            return self._to_markdown(repo.name, tree)

        raise ValueError(f"Unsupported operation: {operation}")

    # -----------------------------
    # TREE BUILDER
    # -----------------------------
    def _build_tree(self, path: Path):

        ignore = {
            ".venv",
            "__pycache__",
            ".git",
            ".idea",
            ".vscode"
        }

        def scan(current: Path):

            node = {
                "name": current.name,
                "type": "dir" if current.is_dir() else "file",
                "children": []
            }

            if current.is_dir():

                for child in sorted(current.iterdir(), key=lambda x: x.name):

                    if child.name in ignore:
                        continue

                    node["children"].append(scan(child))

            return node

        return scan(path)

    # -----------------------------
    # SUMMARY
    # -----------------------------
    def _build_summary(self, tree):

        file_count = 0
        dir_count = 0

        def walk(node):
            nonlocal file_count, dir_count

            if node["type"] == "file":
                file_count += 1
            else:
                dir_count += 1
                for c in node.get("children", []):
                    walk(c)

        walk(tree)

        return {
            "files": file_count,
            "directories": dir_count
        }

    # -----------------------------
    # MARKDOWN VIEW
    # -----------------------------
    def _to_markdown(self, name, tree, depth=0):

        indent = "  " * depth
        output = f"{indent}- {name}/\n"

        for child in tree.get("children", []):
            if child["type"] == "dir":
                output += self._to_markdown(child["name"], child, depth + 1)
            else:
                output += f"{'  ' * (depth + 1)}- {child['name']}\n"

        return output
