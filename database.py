import glob
import json
import logging
import os

import psycopg2
from psycopg2 import pool
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self.db_params = {
            "dbname": os.getenv("DB_NAME", "lexuz_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "12345"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5433"),
        }

        self.pool = psycopg2.pool.ThreadedConnectionPool(1, 20, **self.db_params)
        logger.info("DB connection pool created.")

        logger.info("Loading embedding model and reranker…")
        self.embed_model = SentenceTransformer("intfloat/multilingual-e5-base")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self._initialized = True
        logger.info("Models and DB pool ready.")

    def get_conn(self):
        return self.pool.getconn()

    def put_conn(self, conn) -> None:
        self.pool.putconn(conn)

    def setup_database(self) -> None:
        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("DROP TABLE IF EXISTS documents;")
            cur.execute("""
                CREATE TABLE documents (
                    id        SERIAL PRIMARY KEY,
                    source    VARCHAR(255),
                    content   TEXT,
                    embedding vector(768)
                );
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS embedding_idx "
                "ON documents USING ivfflat (embedding vector_cosine_ops);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS content_ts_idx "
                "ON documents USING GIN (to_tsvector('simple', content));"
            )
            conn.commit()
            logger.info("Documents table created (768-dim).")
        except Exception:
            logger.exception("setup_database failed.")
            raise
        finally:
            self.put_conn(conn)

    def upload_data(self, folder: str = "lex_structured") -> None:
        files = glob.glob(f"{folder}/*.json")
        if not files:
            logger.warning("No JSON files found in %s.", folder)
            return

        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
            for f_path in files:
                source = (
                    os.path.basename(f_path).replace(".json", "").replace("_", " ")
                )
                logger.info("Uploading: %s", source)
                with open(f_path, "r", encoding="utf-8") as f:
                    data: dict = json.load(f)

                for art_data in data.values():
                    content: str = art_data.get("content", "")
                    if len(content.strip()) < 50:
                        continue
                    embedding = self.embed_model.encode(
                        f"passage: {content}"
                    ).tolist()
                    cur.execute(
                        "INSERT INTO documents (source, content, embedding) "
                        "VALUES (%s, %s, %s::vector)",
                        (source, content, embedding),
                    )
                conn.commit()
            logger.info("All data uploaded successfully.")
        except Exception:
            logger.exception("upload_data failed.")
            conn.rollback()
            raise
        finally:
            self.put_conn(conn)

    def hybrid_search(self, query: str, top_k: int = 8) -> List[Dict]:
        conn = self.get_conn()
        try:
            query_vec = self.embed_model.encode(f"query: {query}").tolist()
            cur = conn.cursor()
            cur.execute(
                """
                WITH vector_matches AS (
                    SELECT id, content, source,
                           1 - (embedding <=> %s::vector) AS v_score
                    FROM documents
                    ORDER BY embedding <=> %s::vector
                    LIMIT 20
                ),
                text_matches AS (
                    SELECT id, content, source,
                           ts_rank_cd(
                               to_tsvector('simple', content),
                               websearch_to_tsquery('simple', %s)
                           ) AS t_score
                    FROM documents
                    WHERE to_tsvector('simple', content)
                          @@ websearch_to_tsquery('simple', %s)
                    LIMIT 20
                )
                SELECT
                    COALESCE(v.content, t.content),
                    COALESCE(v.source,  t.source),
                    COALESCE(v.v_score, 0) + COALESCE(t.t_score, 0) AS score
                FROM vector_matches v
                FULL OUTER JOIN text_matches t ON v.id = t.id
                ORDER BY score DESC
                LIMIT 15;
                """,
                (query_vec, query_vec, query, query),
            )
            candidates = cur.fetchall()
            if not candidates:
                return []

            passages = [c[0] for c in candidates]
            rerank_scores = self.reranker.predict([(query, p) for p in passages])

            results = [
                {
                    "content": candidates[i][0],
                    "source": candidates[i][1],
                    "score": float(score),
                }
                for i, score in enumerate(rerank_scores)
            ]
            return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        finally:
            self.put_conn(conn)


def search_lexuz_tool(query: str) -> str:
    results = DatabaseManager().hybrid_search(query)
    if not results:
        return "Bazada ushbu mavzu bo'yicha ma'lumot topilmadi."
    lines = ["📚 TASDIQLANGAN MANBALAR:\n"]
    for res in results:
        lines.append(f"📄 {res['source']}:\n{res['content']}\n{'—' * 30}")
    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    db = DatabaseManager()
    db.setup_database()
    db.upload_data("lex_structured")