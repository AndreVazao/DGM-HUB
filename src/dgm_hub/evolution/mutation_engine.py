import random


class MutationEngine:

    def mutate(self,plan):

        mutated=dict(plan)

        if plan["tool"]=="git":

            mutated["operation"]="status"

        elif plan["tool"]=="repo":

            mutated["operation"]="tree"

        elif plan["tool"]=="cmd":

            mutated["command"]="echo mutation"

        return mutated
