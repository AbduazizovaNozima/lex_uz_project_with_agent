import logging
import os
from typing import Dict

from app.interfaces.scraper_interface import AbstractScraper
from app.core.config import get_settings
from app.core.constants import LAWS_TO_SCRAPE

logger = logging.getLogger(__name__)


class ScraperService(AbstractScraper):
    def __init__(self) -> None:
        self._settings = get_settings()
        self._output_dir = self._settings.LEX_STRUCTURED_DIR
        import scraper as _scraper
        self._scraper = _scraper

    def scrape_one(self, doc_name: str) -> Dict[str, dict]:
        if doc_name not in LAWS_TO_SCRAPE:
            logger.warning("scrape_one | unknown doc: %s", doc_name)
            return {}
        url = LAWS_TO_SCRAPE[doc_name]
        articles = self._scraper.scrape_law_document(url, doc_name)
        if articles:
            self._scraper.save_to_json(articles, f"{doc_name}.json")
        return articles

    def scrape_all(self) -> None:
        self._scraper.scrape_all_laws()

    def list_scraped(self) -> list[str]:
        if not os.path.exists(self._output_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(self._output_dir) if f.endswith(".json")]
