class BaseFixAgent:
    def propose_fix(self, error: str) -> dict:
        raise NotImplementedError


class LogicAgent(BaseFixAgent):
    def propose_fix(self, error: str):
        return {
            "agent": "logic",
            "patch": f"# logic fix for {error}",
            "confidence": 0.6
        }


class SafetyAgent(BaseFixAgent):
    def propose_fix(self, error: str):
        return {
            "agent": "safety",
            "patch": f"# safe conservative fix for {error}",
            "confidence": 0.8
        }


class AggressiveAgent(BaseFixAgent):
    def propose_fix(self, error: str):
        return {
            "agent": "aggressive",
            "patch": f"# aggressive rewrite fix for {error}",
            "confidence": 0.4
        }
