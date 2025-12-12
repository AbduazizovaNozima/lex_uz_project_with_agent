# import os
# import psycopg2
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv
#
# load_dotenv()
#
# DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
#
# DB_PARAMS = {
#     "dbname": "lexuz_db",
#     "user": "postgres",
#     "password": DB_PASSWORD,
#     "host": "localhost",
#     "port": "5432"
# }
#
# # 2. MODELNI YUKLASH
# # Bu jarayon og'ir bo'lgani uchun fayl boshida bir marta bajariladi.
# # Har safar funksiya chaqirilganda qayta yuklamaslik kerak.
# print("📚 [Database] Embedding modeli yuklanmoqda... (Biroz kuting)")
# try:
#     embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
#     print("✅ [Database] Model tayyor!")
# except Exception as e:
#     print(f"❌ [Database] Model yuklashda xatolik: {e}")
#     raise e
#
#
# # 3. TOOL FUNKSIYASI (Legal Agent uchun)
# def search_lexuz_tool(sorov: str) -> str:
#     """
#     Bu funksiya Legal Agent (Yurist) uchun 'ko'z' va 'qo'l' vazifasini bajaradi.
#     PostgreSQL bazasidan pgvector yordamida eng o'xshash qonunlarni topadi.
#
#     Args:
#         sorov (str): Foydalanuvchi bergan savol yoki kalit so'zlar.
#
#     Returns:
#         str: Topilgan qonun manbalari va matnlari birlashtirilgan string holatida.
#     """
#     print(f"\n🔍 [DB TOOL] Bazadan qidirilmoqda: {sorov}")
#
#     conn = None
#     try:
#         # 1. Savolni vektorga o'giramiz
#         query_vec = embedding_model.encode(sorov).tolist()
#
#         # 2. Bazaga ulanamiz
#         conn = psycopg2.connect(**DB_PARAMS)
#         cur = conn.cursor()
#
#         # 3. SQL so'rov (Kosinus masofasi bo'yicha qidirish)
#         # <=> operatori pgvector da masofani o'lchaydi
#         # LIMIT 4 - Eng mos 4 ta parchani olamiz (kontekst yetarli bo'lishi uchun)
#         sql = """
#             SELECT source, content
#             FROM documents
#             ORDER BY embedding <=> %s::vector
#             LIMIT 4;
#         """
#
#         cur.execute(sql, (query_vec,))
#         rows = cur.fetchall()
#
#         # 4. Natijalarni formatlash
#         if not rows:
#             return "Afsuski, bazadan so'rovingizga mos hech qanday ma'lumot topilmadi."
#
#         result_text = "TIZIM: Qidiruv natijasida quyidagi qonun hujjatlari topildi:\n\n"
#
#         for i, (source, content) in enumerate(rows, 1):
#             # Matn juda uzun bo'lsa, GPT tokeni to'lib qolmasligi uchun 1500 belgida kesamiz
#             clean_content = content.strip()[:1500]
#             result_text += f"--- {i}-MANBA: {source} ---\nMATN: {clean_content}\n\n"
#
#         return result_text
#
#     except psycopg2.Error as db_err:
#         return f"Bazaga ulanishda xatolik: {db_err}"
#
#     except Exception as e:
#         return f"Texnik xatolik yuz berdi: {e}"
#
#     finally:
#         # Ulanishni albatta yopish kerak
#         if conn:
#             conn.close()
#
#
# # Test uchun (faqat shu faylni o'zini ishlatsangiz tekshirish uchun)
# if __name__ == "__main__":
#     print("Test qidiruv: Konstitutsiya")
#     print(search_lexuz_tool("Konstitutsiya"))


import os
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from typing import List, Tuple

load_dotenv()

# ============================================================================
# KONFIGURATSIYA
# ============================================================================
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
DB_PARAMS = {
    "dbname": "lexuz_db",
    "user": "postgres",
    "password": DB_PASSWORD,
    "host": "localhost",
    "port": "5432"
}

# ============================================================================
# EMBEDDING MODEL (Bir marta yuklanadi)
# ============================================================================
print("🔄 [Database] Embedding modeli yuklanmoqda...")
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ [Database] Model tayyor!")
except Exception as e:
    print(f"❌ [Database] Model yuklash xatosi: {e}")
    raise


# ============================================================================
# BAZANI TAYYORLASH
# ============================================================================
def setup_database():
    """
    Dastlabki baza strukturasini yaratish
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # pgvector kengaytmasini faollashtirish
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Jadval yaratish
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                source VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Index yaratish (tezroq qidiruv uchun)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS embedding_idx 
            ON documents USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

        conn.commit()
        print("✅ [Database] Baza strukturasi tayyor")

    except Exception as e:
        print(f"❌ [Database] Setup xatosi: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


# ============================================================================
# MATNLARNI BAZAGA YUKLASH
# ============================================================================
def insert_documents_from_folder(folder_path: str = "./lex_data"):
    """
    Scrape qilingan fayllarni bazaga yuklash
    """
    import glob

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Oldingi ma'lumotlarni o'chirish (yangilash uchun)
        cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")

        files = glob.glob(f"{folder_path}/*.txt")
        print(f"\n📁 {len(files)} ta fayl topildi")

        total_chunks = 0

        for file_path in files:
            source = os.path.basename(file_path)
            print(f"📄 {source} ishlanmoqda...")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Matnni bo'laklarga ajratish (1500 belgilik qismlar)
            chunks = split_text(content, chunk_size=1500)

            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 100:  # Juda qisqa bo'laklar kerak emas
                    continue

                # Embedding yaratish
                embedding = embedding_model.encode(chunk).tolist()

                # Bazaga yozish
                cur.execute("""
                    INSERT INTO documents (source, content, embedding)
                    VALUES (%s, %s, %s::vector)
                """, (source, chunk, embedding))

                total_chunks += 1

            print(f"  ✅ {len(chunks)} ta bo'lak yuklandi")

        conn.commit()
        print(f"\n🎉 Jami {total_chunks} ta yozuv bazaga qo'shildi!")

    except Exception as e:
        print(f"❌ [Database] Yuklash xatosi: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def split_text(text: str, chunk_size: int = 1500) -> List[str]:
    """
    Matnni mantiqiy bo'laklarga ajratish
    """
    # Paragraflar bo'yicha ajratish
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# ============================================================================
# QIDIRUV FUNKSIYASI (Agent uchun)
# ============================================================================
def search_lexuz_tool(sorov: str) -> str:
    """
    Vector search orqali eng mos qonunlarni topish

    Args:
        sorov: Foydalanuvchi savoli

    Returns:
        Formatlangan qidiruv natijalari
    """
    print(f"\n🔍 [Tool] Qidiruv: {sorov}")

    conn = None
    try:
        # Savolni vektorga aylantirish
        query_vec = embedding_model.encode(sorov).tolist()

        # Bazaga ulanish
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Vector qidiruv (Cosine similarity)
        sql = """
            SELECT source, content, 1 - (embedding <=> %s::vector) as similarity
            FROM documents 
            WHERE 1 - (embedding <=> %s::vector) > 0.3
            ORDER BY embedding <=> %s::vector 
            LIMIT 5;
        """

        cur.execute(sql, (query_vec, query_vec, query_vec))
        rows = cur.fetchall()

        # Natijalarni formatlash
        if not rows:
            return """
❌ Afsuski, so'rovingizga mos ma'lumot topilmadi.

💡 Tavsiya:
- Savolingizni boshqacha so'zlar bilan ifoda qiling
- Aniqroq atamalar ishlating (masalan: "oylik" o'rniga "ish haqi")
"""

        result = "📚 QONUN BAZASIDAN TOPILGAN MA'LUMOTLAR:\n\n"

        for i, (source, content, similarity) in enumerate(rows, 1):
            # O'xshashlik foizini ko'rsatish
            match_percent = int(similarity * 100)

            # Matnni kesish
            clean_content = content.strip()[:1200]

            result += f"{'=' * 60}\n"
            result += f"📄 Manba #{i}: {source}\n"
            result += f"🎯 Mos kelish: {match_percent}%\n\n"
            result += f"{clean_content}\n\n"

        result += f"{'=' * 60}\n"
        result += f"✅ Jami {len(rows)} ta manba topildi"

        print(f"✅ [Tool] {len(rows)} ta natija qaytarildi")
        return result

    except psycopg2.Error as db_err:
        error_msg = f"❌ Bazaga ulanishda xatolik: {db_err}"
        print(error_msg)
        return error_msg

    except Exception as e:
        error_msg = f"❌ Qidiruv xatosi: {e}"
        print(error_msg)
        return error_msg

    finally:
        if conn:
            conn.close()


# ============================================================================
# BAZANI TEKSHIRISH
# ============================================================================
def check_database():
    """
    Bazadagi ma'lumotlarni tekshirish
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM documents;")
        count = cur.fetchone()[0]

        cur.execute("SELECT DISTINCT source FROM documents;")
        sources = [row[0] for row in cur.fetchall()]

        print(f"\n📊 BAZA HOLATI:")
        print(f"  📝 Jami yozuvlar: {count}")
        print(f"  📚 Manba fayllar: {len(sources)}")
        for source in sources:
            cur.execute("SELECT COUNT(*) FROM documents WHERE source = %s", (source,))
            s_count = cur.fetchone()[0]
            print(f"    - {source}: {s_count} ta bo'lak")

    except Exception as e:
        print(f"❌ Tekshirish xatosi: {e}")
    finally:
        if conn:
            conn.close()


# ============================================================================
# TEST VA INITIALIZATION
# ============================================================================
if __name__ == "__main__":
    print("🔧 Database moduli ishga tushdi\n")

    # Bazani tayyorlash
    setup_database()

    # Ma'lumotlarni yuklash (agar kerak bo'lsa)
    if input("\n📥 Fayllarni bazaga yuklash? (y/n): ").lower() == 'y':
        insert_documents_from_folder()

    # Bazani tekshirish
    check_database()

    # Test qidiruv
    if input("\n🧪 Test qidiruv o'tkazish? (y/n): ").lower() == 'y':
        test_query = input("Savol: ")
        result = search_lexuz_tool(test_query)
        print("\n" + result)




