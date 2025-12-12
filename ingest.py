# import os
# import psycopg2
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv
#
# load_dotenv()
#
# DB_PARAMS = {
#     "dbname": "lexuz_db",
#     "user": "postgres",
#     "password": os.getenv("DB_PASSWORD", "12345"),
#     "host": "localhost",
#     "port": "5432"
# }
#
#
# def ingest():
#     print("🚀 Model yuklanmoqda (birinchi marta biroz vaqt oladi)...")
#     model = SentenceTransformer('all-MiniLM-L6-v2')
#
#     conn = psycopg2.connect(**DB_PARAMS)
#     cur = conn.cursor()
#
#     # Jadvalni tozalash (qayta yuklashda eski ma'lumot qolmasligi uchun)
#     cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
#
#     data_folder = "lex_data"
#     files = [f for f in os.listdir(data_folder) if f.endswith('.txt')]
#
#     print(f"📂 {len(files)} ta fayl topildi. Bazaga yozish boshlandi...")
#
#     for file in files:
#         file_path = os.path.join(data_folder, file)
#         with open(file_path, "r", encoding="utf-8") as f:
#             text = f.read()
#
#         # Chunking (1000 belgidan bo'laklash)
#         chunk_size = 1000
#         chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
#
#         for chunk in chunks:
#             if len(chunk) < 50: continue  # Juda kichik bo'laklarni tashlaymiz
#
#             vector = model.encode(chunk).tolist()
#
#             cur.execute(
#                 "INSERT INTO documents (source, content, embedding) VALUES (%s, %s, %s)",
#                 (file, chunk, vector)
#             )
#
#         print(f"💾 {file} bazaga yuklandi ({len(chunks)} bo'lak).")
#         conn.commit()
#
#     cur.close()
#     conn.close()
#     print("🎉 Barcha ma'lumotlar tayyor!")
#
#
# if __name__ == "__main__":
#     ingest()