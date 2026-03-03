import logging
from typing import List, Dict

from app.interfaces.database_interface import AbstractDatabase

logger = logging.getLogger(__name__)


class DatabaseRepository(AbstractDatabase):
    def __init__(self) -> None:
        from database import DatabaseManager

        self._db = DatabaseManager()
        logger.info("DatabaseRepository initialised.")

    def hybrid_search(self, query: str, top_k: int = 8) -> List[Dict]:
        logger.debug("hybrid_search | query=%r | top_k=%d", query, top_k)
        return self._db.hybrid_search(query, top_k)

    def upload_data(self, folder: str = "lex_structured") -> None:
        logger.info("upload_data | folder=%s", folder)
        self._db.upload_data(folder)

    def setup_database(self) -> None:
        logger.info("setup_database | resetting schema…")
        self._db.setup_database()

    def format_search_results(self, query: str) -> str:
        results = self.hybrid_search(query)
        if not results:
            return ""
        lines = ["📚 TASDIQLANGAN MANBALAR:\n"]
        for res in results:
            lines.append(f"📄 {res['source']}:\n{res['content']}\n{'—' * 30}")
        return "\n".join(lines)
