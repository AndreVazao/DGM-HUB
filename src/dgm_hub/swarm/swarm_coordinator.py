import uuid
from collections import defaultdict


class SwarmCoordinator:

    def __init__(self, agents, voting_system, debate_engine):
        self.agents = agents
        self.voting = voting_system
        self.debate = debate_engine

    def execute_task(self, task: str):

        proposals = defaultdict(list)

        # 1. THINK PHASE (paralelo lógico)
        for agent in self.agents:

            result = agent.think(task)
            proposals[agent.role].append(result)

        # 2. DEBATE PHASE
        refined = self.debate.resolve(proposals)

        # 3. VOTING PHASE
        winner = self.voting.select_best(refined)

        return {
            "task": task,
            "winner": winner,
            "all_proposals": dict(proposals)
        }
