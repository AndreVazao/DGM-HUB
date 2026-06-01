from abc import ABC, abstractmethod


class Tool(ABC):
    name: str

    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError
