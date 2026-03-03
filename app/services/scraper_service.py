import logging
import os
from typing import Dict

import scraper as _scraper

from app.interfaces.scraper_interface import AbstractScraper
from app.core.config import get_settings
from app.core.constants import LAWS_TO_SCRAPE

logger = logging.getLogger(__name__)


class ScraperService(AbstractScraper):
    def __init__(self) -> None:
        self._output_dir = get_settings().LEX_STRUCTURED_DIR

    def scrape_one(self, doc_name: str) -> Dict[str, dict]:
        if doc_name not in LAWS_TO_SCRAPE:
            logger.warning("scrape_one | unknown document: %s", doc_name)
            return {}
        url = LAWS_TO_SCRAPE[doc_name]
        articles = _scraper.scrape_law_document(url, doc_name)
        if articles:
            _scraper.save_to_json(articles, f"{doc_name}.json")
        return articles

    def scrape_all(self) -> None:
        _scraper.scrape_all_laws()

    def list_scraped(self) -> list[str]:
        if not os.path.exists(self._output_dir):
            return []
        return [
            f.replace(".json", "")
            for f in os.listdir(self._output_dir)
            if f.endswith(".json")
        ]
