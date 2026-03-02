from abc import ABC, abstractmethod
from typing import Dict


class AbstractScraper(ABC):
    @abstractmethod
    def scrape_one(self, doc_name: str) -> Dict[str, dict]: ...

    @abstractmethod
    def scrape_all(self) -> None: ...

    @abstractmethod
    def list_scraped(self) -> list[str]: ...
