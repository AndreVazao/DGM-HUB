import json
from pathlib import Path
from dgm_hub.evolution.genome import PatchGenome


class EvolutionMemory:
    """
    Stores successful and failed genomes for future mutation.
    """

    def __init__(self, path="runtime/evolution_memory.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def store(self, genome: PatchGenome):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(genome.__dict__) + "\n")

    def load_top(self, limit=10):
        if not self.path.exists():
            return []

        genomes = []
        for line in self.path.read_text().splitlines():
            genomes.append(json.loads(line))

        return sorted(
            genomes,
            key=lambda g: g.get("fitness", 0),
            reverse=True
        )[:limit]
