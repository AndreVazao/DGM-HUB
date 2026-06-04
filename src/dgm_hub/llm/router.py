from typing import Dict, Any


class LLMRouter:

    def __init__(self, providers: Dict[str, Any]):
        """
        providers = {
            "ollama": OllamaClient,
            "claude": ClaudeClient,
            "codex": CodexClient
        }
        """
        self.providers = providers

    def ask_all(self, prompt: str):

        results = {}

        for name, client in self.providers.items():
            try:
                results[name] = client.ask(prompt)
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    def vote_best(self, results: dict):

        # hook para o teu swarm já existente
        scores = {}

        for k, v in results.items():
            if "error" in v:
                scores[k] = 0
            else:
                scores[k] = len(str(v))  # baseline simples

        return max(scores, key=scores.get)
