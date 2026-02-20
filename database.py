import os
import json
import glob
import re
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple, Union

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
DB_PORT = os.getenv("DB_PORT", "5433")  # PostgreSQL default port is 5432, but using 5433 here
DB_HOST = "localhost"
DB_USER = "postgres"
DB_NAME = "lexuz_db"

DB_PARAMS = {
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "host": DB_HOST,
    "port": DB_PORT
}

# Model Configuration
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 800

# ============================================================================
# EMBEDDING MODEL (loaded once at startup)
# ============================================================================
print("🔄 [Database] Loading embedding model...")
try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("✅ [Database] Model ready!")
except Exception as e:
    print(f"❌ [Database] Model load error: {e}")
    raise

# ============================================================================
# DATABASE SETUP
# ============================================================================
def get_db_connection():
    """Establishes and returns a database connection."""
    return psycopg2.connect(**DB_PARAMS)

def setup_database() -> None:
    """Create documents table and pgvector extension if not exists."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create documents table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                source VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create index for fast cosine search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS embedding_idx 
            ON documents USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

        conn.commit()
        print("✅ [Database] Table structure ready")

    except Exception as e:
        print(f"❌ [Database] Setup error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# ============================================================================
# TEXT SPLITTING
# ============================================================================
# def split_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
#     """
#     Split text into logical chunks.
#     Priority:
#     1. Split by double newline (\n\n)
#     2. Split by single newline (\n)
#     3. Split by sentence/space (if paragraph is huge)
#     """
#     text = text.strip()
#     if not text:
#         return []

#     # Strategy 1: Split by paragraphs (\n\n)
#     paragraphs = text.split('\n\n')
    
#     # If we only got 1 huge paragraph, try splitting by single newlines
#     if len(paragraphs) == 1 and len(text) > chunk_size:
#         paragraphs = text.split('\n')

#     chunks = []
#     current_chunk = ""

#     for para in paragraphs:
#         para = para.strip()
#         if not para:
#             continue
            
#         # If a single paragraph is still HUGE (bigger than chunk_size), hard split it
#         if len(para) > chunk_size:
#             # Check if we have a current chunk pending
#             if current_chunk:
#                 chunks.append(current_chunk.strip())
#                 current_chunk = ""
            
#             # Simple fixed-size splitting for huge blob
#             for i in range(0, len(para), chunk_size):
#                 chunks.append(para[i:i + chunk_size])
#             continue

#         if len(current_chunk) + len(para) < chunk_size:
#             current_chunk += para + "\n\n"
#         else:
#             if current_chunk:
#                 chunks.append(current_chunk.strip())
#             current_chunk = para + "\n\n"

#     if current_chunk:
#         chunks.append(current_chunk.strip())

#     return chunks

# ============================================================================
# DATA INGESTION FROM JSON FILES
# ============================================================================
def insert_documents_from_json(json_folder: str = "./lex_structured") -> None:
    """
    Load law articles from lex_structured/*.json into the vector database.
    Each article's text is embedded and stored for semantic search.
    """
    json_files = glob.glob(f"{json_folder}/*.json")
    if not json_files:
        print(f"⚠️  No JSON files found in {json_folder}")
        return

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Clear existing data for a clean reload
        cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
        conn.commit()

        total_inserted = 0

        for json_path in sorted(json_files):
            source_name = os.path.basename(json_path).replace(".json", "").replace("_", " ")
            print(f"📄 Loading: {source_name}...")

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    articles: Dict[str, Dict[str, str]] = json.load(f)
            except Exception as e:
                print(f"  ⚠️  Could not read {json_path}: {e}")
                continue

            batch_count = 0
            for article_num, article_data in articles.items():
                title = article_data.get("title", "")
                content = article_data.get("content", "")

                if not content or len(content.strip()) < 30:
                    continue

                # Clean the content before splitting/embedding
                content = _clean_search_content(content)

                # If content is huge (full law in one block), split into chunks
                if len(content) > CHUNK_SIZE * 2:
                    chunks = split_text(content, chunk_size=CHUNK_SIZE)
                else:
                    # Small article: keep as single chunk
                    chunks = [content]

                for chunk_idx, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 50:
                        continue

                    prefix = f"{source_name}"
                    if title and title != source_name:
                        prefix += f" — {title}"
                    chunk_text = f"{prefix}\n\n{chunk}"

                    # Generate embedding
                    try:
                        embedding = embedding_model.encode(chunk_text).tolist()
                    except Exception as e:
                        print(f"  ⚠️  Embedding error (article {article_num}, chunk {chunk_idx}): {e}")
                        continue

                    cur.execute(
                        "INSERT INTO documents (source, content, embedding) VALUES (%s, %s, %s::vector)",
                        (source_name, chunk_text, embedding)
                    )
                    batch_count += 1

            conn.commit()
            total_inserted += batch_count
            print(f"  ✅ {batch_count} articles inserted")

        print(f"\n🎉 Total: {total_inserted} articles loaded into vector DB!")

    except Exception as e:
        print(f"❌ [Database] Ingestion error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# database.py ichidagi funksiyalarni almashtiring:

# database.py ichidagi ushbu funksiyalarni almashtiring:

def _clean_search_content(text: str) -> str:
    """Lex.uz texnik matnlarini tozalash."""
    if not text: return ""
    # Handle literal \\n
    cleaned = text.replace('\\n', '\n')
    noise = [
        r"Ҳужжатга таклиф юбориш", r"Аудиони тинглаш", 
        r"Ҳужжат элементидан ҳавола олиш", r"\[OKOZ:.*?\]",
        r"\[TSZ:.*?\]", r"LexUZ sharhi", r"Qarang:.*?\.",
        r"\d+\.\d+\.\d+\.\d+\.\d+[^\n]*",
        r"\b\d+\.\s*\n\s*\d+\.\d+\.\d+\.\d+[^\n]*",
        r"\b\d{1,2}\.\d{2}\.\d{2}\.\d{2}\b[^\n]*",
    ]
    for pattern in noise:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
    return re.sub(r'[ \t]+', ' ', cleaned).strip()

def split_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Matnni moddalar bo'yicha aniq bo'lish."""
    # Modda raqamlari bo'yicha bo'lish (masalan: 20-modda.)
    parts = re.split(r'(\b\d+-(?:modda|модда)\.?)', text)
    chunks = []
    
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            header = parts[i]
            body = parts[i+1] if i+1 < len(parts) else ""
            chunks.append(header + body)
    else:
        # Agar moddalar topilmasa, oddiy bo'laklash
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
    return chunks


# ============================================================================
# SEARCH FUNCTION (used by agents)
# ============================================================================
def search_lexuz_tool(sorov: str) -> str:
    """
    Semantic vector search — finds the most relevant law articles for the query.

    Args:
        sorov: User's question or keywords

    Returns:
        Formatted search results string
    """
    print(f"\n🔍 [Tool] Searching DB: {sorov}")

    conn = None
    try:
        # Encode query to vector
        query_vec = embedding_model.encode(sorov).tolist()
        
        conn = get_db_connection()
        cur = conn.cursor()

        limit = 5 # Number of results to retrieve from each search type

        # 1. Semantic Search (Vector)
        # Using cosine distance (1 - cosine similarity) -> Order by distance ASC
        cur.execute("""
            SELECT content, source, 1 - (embedding <=> %s::vector) as similarity
            FROM documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (query_vec, query_vec, limit))
        vector_results: List[Tuple[str, str, float]] = cur.fetchall()

        # 2. Keyword Search (Enhanced)
        # Split query into words to match source names partially
        words = sorov.split()
        keywords = [w for w in words if len(w) > 3]
        if not keywords:
            keywords = words

        # Build dynamic ILIKE clauses for source matching
        # Source must match AT LEAST ONE of the significant keywords
        source_conditions = []
        source_params = []
        for w in keywords:
            source_conditions.append("source ILIKE %s")
            source_params.append(f"%{w}%")
        
        source_clause = " OR ".join(source_conditions) if source_conditions else "FALSE"

        # Parameters for the query:
        # 1. websearch_to_tsquery (query)
        # 2. ... source_params ...
        # 3. limit
        params = [sorov] + source_params + [limit]

        query_sql = f"""
            SELECT content, source, 0.9 as similarity
            FROM documents
            WHERE to_tsvector('simple', content) @@ websearch_to_tsquery('simple', %s)
            OR ({source_clause})
            LIMIT %s;
        """

        cur.execute(query_sql, tuple(params))
        keyword_results: List[Tuple[str, str, float]] = cur.fetchall()

        # Merge results (deduplicate by content)
        seen_content = set()
        results: List[Dict[str, Any]] = []

        # Prioritize keyword matches if they are relevant laws
        for r in keyword_results:
            content = r[0]
            if content not in seen_content:
                results.append({"content": content, "source": r[1], "similarity": r[2]})
                seen_content.add(content)

        for r in vector_results:
            content = r[0]
            if content not in seen_content:
                results.append({"content": content, "source": r[1], "similarity": r[2]})
                seen_content.add(content)
        
        # Take the top N merged results
        final_rows = results[:limit]

        if not final_rows:
            return """❌ No matching results found in the database.

💡 Tips:
- Be more specific (e.g., "Mehnat kodeksi 131-modda")
- Use law name + article number for best results
"""

        result_text = "📚 RESULTS FROM LEGAL DATABASE:\n\n"

        for i, row in enumerate(final_rows, 1):
            source = row['source']
            content = row['content']
            similarity = row['similarity']
            
            match_percent = int(similarity * 100)
            
            # Clean the content to remove navigation links and noise
            clean_content = _clean_search_content(content)
            clean_content = clean_content.strip()[:1200]

            result_text += f"{'=' * 60}\n"
            result_text += f"📄 Source #{i}: {source}\n"
            result_text += f"🎯 Relevance: {match_percent}%\n\n"
            result_text += f"{clean_content}\n\n"

        result_text += f"{'=' * 60}\n"
        result_text += f"✅ Found {len(final_rows)} result(s)"

        print(f"✅ [Tool] Returned {len(final_rows)} results")
        return result_text

    except psycopg2.OperationalError as db_err:
        # DB not available — log only, don't expose raw error to agents
        print(f"❌ DB connection failed: {db_err}")
        return """❌ No results found in the database.

💡 Tips:
- Try specifying the law name and article number (e.g., "Mehnat kodeksi 131-modda")
- For general questions about available laws, try asking "qanday qonunlar mavjud"
"""

    except psycopg2.Error as db_err:
        print(f"❌ DB error: {db_err}")
        return "❌ Database error. Please try again."

    except Exception as e:
        error_msg = f"❌ Search error: {e}"
        print(error_msg)
        return error_msg

    finally:
        if conn:
            conn.close()

# ============================================================================
# DATABASE STATUS CHECK
# ============================================================================
def check_database() -> None:
    """Print database statistics."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM documents;")
        count = cur.fetchone()[0]

        cur.execute("SELECT DISTINCT source FROM documents ORDER BY source;")
        sources = [row[0] for row in cur.fetchall()]

        print(f"\n📊 DATABASE STATUS:")
        print(f"  📝 Total records: {count}")
        print(f"  📚 Sources: {len(sources)}")
        for source in sources:
            cur.execute("SELECT COUNT(*) FROM documents WHERE source = %s", (source,))
            s_count = cur.fetchone()[0]
            print(f"    - {source}: {s_count} articles")

    except Exception as e:
        print(f"❌ Check error: {e}")
    finally:
        if conn:
            conn.close()

# ============================================================================
# MAIN — Run this once to initialize the database
# ============================================================================
if __name__ == "__main__":
    print("🔧 Database initialization started\n")
    print(f"📡 Connecting to: {DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['dbname']}")

    # Step 1: Create table structure
    print("\n[1/3] Setting up database schema...")
    setup_database()

    # Step 2: Load JSON data into vector DB
    print("\n[2/3] Loading law articles from lex_structured/...")
    insert_documents_from_json()

    # Step 3: Verify
    print("\n[3/3] Verifying database...")
    check_database()

    print("\n✅ Database ready! Restart api.py to apply changes.")
