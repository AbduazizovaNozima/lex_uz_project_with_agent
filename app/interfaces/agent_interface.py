from abc import ABC, abstractmethod


class AbstractAgentService(ABC):
    @abstractmethod
    def classify_intent(self, question: str) -> str: ...

    @abstractmethod
    async def get_response(self, question: str, history: str) -> str: ...
