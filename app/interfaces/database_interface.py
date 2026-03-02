from abc import ABC, abstractmethod
from typing import List, Dict


class AbstractDatabase(ABC):
    @abstractmethod
    def hybrid_search(self, query: str, top_k: int = 8) -> List[Dict]: ...

    @abstractmethod
    def upload_data(self, folder: str) -> None: ...

    @abstractmethod
    def setup_database(self) -> None: ...
