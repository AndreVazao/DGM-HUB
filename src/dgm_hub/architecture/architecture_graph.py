from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Node:
    name: str
    type: str  # module / class / function
    dependencies: List[str] = field(default_factory=list)


class ArchitectureGraph:

    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def add_node(self, node: Node):
        self.nodes[node.name] = node

    def get_dependencies(self, name: str) -> List[str]:
        return self.nodes.get(name, Node(name, "")).dependencies

    def find_cycles(self):
        """
        Detect circular dependencies.
        """
        visited = set()
        stack = set()
        cycles = []

        def visit(node_name):
            if node_name in stack:
                cycles.append(node_name)
                return

            if node_name in visited:
                return

            visited.add(node_name)
            stack.add(node_name)

            node = self.nodes.get(node_name)
            if node:
                for dep in node.dependencies:
                    visit(dep)

            stack.remove(node_name)

        for n in self.nodes:
            visit(n)

        return cycles
