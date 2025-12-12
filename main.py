# # import os
# # import json
# # from dotenv import load_dotenv
# # from fastapi import FastAPI
# # from fastapi.middleware.cors import CORSMiddleware
# # from fastapi.staticfiles import StaticFiles
# # from pydantic import BaseModel, Field
# # from typing import List, Optional
# #
# # # LangChain va Tools
# # from langchain_openai import ChatOpenAI
# # from langchain_core.prompts import ChatPromptTemplate
# # from langchain_core.tools import tool
# # from langchain_core.messages import SystemMessage, HumanMessage
# #
# # # Bizning yordamchi modullar
# # from scraper import KunUzScraper
# # from knowledge_base import search_guide_by_tags
# #
# # load_dotenv()
# #
# # # --- SETUP ---
# # app = FastAPI(title="Kun.uz AI Chatbot (Agent)")
# #
# # # CORS
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )
# #
# # # Static fayllar (Rasmlar uchun)
# # app.mount("/static", StaticFiles(directory="static"), name="static")
# #
# # # API KEY
# # OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# # scraper = KunUzScraper()
# #
# #
# # # --- MODELLAR ---
# #
# # # Frontendga qaytadigan javob strukturasi
# # class NewsItemResponse(BaseModel):
# #     title: str
# #     url: str
# #     image_url: str
# #     date: str
# #     description: str
# #
# #
# # class ChatResponse(BaseModel):
# #     response: str
# #     news: List[NewsItemResponse] = []
# #     guide_image: Optional[str] = None  # <--- YORDAMCHI RASM UCHUN
# #
# #
# # class ChatRequest(BaseModel):
# #     question: str
# #
# #
# # # AI Xulosa Modeli (Structured Output uchun)
# # class SingleNewsSummary(BaseModel):
# #     index: int = Field(description="Yangilik tartib raqami")
# #     ai_summary: str = Field(description="Yangilik xulosasi")
# #
# #
# # class AIAnalysisResult(BaseModel):
# #     general_chat_response: str = Field(description="Umumiy javob")
# #     summaries: List[SingleNewsSummary] = Field(description="Xulosalar")
# #
# #
# # @tool
# # def get_news_tool(category: str = None):
# #     """
# #     Foydalanuvchi yangiliklar, xabarlar yoki ma'lum bir soha bo'yicha ma'lumot so'rasa ishlating.
# #
# #     Category uchun quyidagi qiymatlardan eng mosini tanlang (faqat bittasini):
# #     - 'uzbekistan': O'zbekiston ichidagi siyosat va voqealar.
# #     - 'jahon': Dunyo, xalqaro xabarlar, urushlar, tashqi siyosat.
# #     - 'iqtisodiyot': Dollar kursi, banklar, iqtisodiy o'zgarishlar.
# #     - 'jamiyat': Aholi muammolari, svet/gaz, ijtimoiy masalalar.
# #     - 'sport': Futbol, boks, sport musobaqalari.
# #     - 'texnologiya': IT, telefonlar, gadjetlar, internet, AI.
# #     - 'talim': Maktab, bog'cha, universitet, o'qish, kontrakt, talabalar.
# #     - 'moliya': Soliqlar, kreditlar, oylik maoshlar, byudjet.
# #     - 'avto': Mashinalar, GM, Chevrolet, BYD, yo'l harakati, GAI, radar.
# #     - 'kuchmas-mulk': Uy-joy, kvartira narxlari, qurilish, ijara.
# #     - 'ayollar-dunyosi': Ayollar, moda, psixologiya, oila.
# #     - 'soglom-hayot': Tibbiyot, kasalliklar, dorilar, sog'liq.
# #     - 'turizm': Sayohat, viza, dam olish maskanlari, chiptalar.
# #     - 'biznes': Tadbirkorlik, kompaniyalar, savdo.
# #     - None: Agar aniq kategoriya so'ralmasa (umumiy yangiliklar).
# #     """
# #     # Bu funksiya shunchaki AIni yo'naltiradi, logikasi pastda yozilgan
# #     return "news_requested"
# #
# #
# # @tool
# # def get_visual_guide_tool(query: str):
# #     """
# #     Foydalanuvchi sayt funksiyalari, rasm yoki yordam so'raganda ishlatiladi.
# #
# #     MUHIM: Foydalanuvchi gapini shundayligicha yuborma! Quyidagi ro'yxatdan eng mos keladigan KALIT SO'ZNI (KEY) tanlab yubor:
# #
# #     1. AKKAUNT: 'register' (ro'yxatdan o'tish), 'login' (kirish), 'logout', 'profile', 'search', 'menu'.
# #     2. FUNKSIYALAR: 'night_mode', 'font_size', 'comments', 'share', 'save', 'video', 'audio', 'currency', 'weather', 'contact', 'telegram'.
# #
# #     Misol:
# #     - User: "Ro'yhatdan o'tish qanaqa?" -> Query: "register"
# #     - User: "Tungi rejim bormi?" -> Query: "night_mode"
# #     """
# #     # Bu funksiya AIni yo'naltiradi, logikasi pastda
# #     return "guide_requested"
# #
# #
# # # --- MAIN LOGIC ---
# #
# # # 1. Router LLM (Qaror qabul qiluvchi)
# # llm_router = ChatOpenAI(model="gpt-4o", temperature=0)
# # llm_with_tools = llm_router.bind_tools([get_news_tool, get_visual_guide_tool])
# #
# # # 2. Summarizer LLM (Yangiliklarni chiroyli qiluvchi)
# # llm_summarizer = ChatOpenAI(model="gpt-4o", temperature=0.3)
# # structured_summarizer = llm_summarizer.with_structured_output(AIAnalysisResult)
# #
# #
# # @app.post("/chat", response_model=ChatResponse)
# # async def chat_endpoint(request: ChatRequest):
# #     user_input = request.question
# #     print(f"📥 USER: {user_input}")
# #
# #     # 1-QADAM: AI qaror qabul qiladi (Routing)
# #     system_msg = """Sen Kun.uz rasmiy AI yordamchisissan.
# #
# #     VAZIFANG: Foydalanuvchi nima xohlayotganini aniqla:
# #     1. Agar YANGILIK so'rasa -> `get_news_tool` ni chaqir.
# #     2. Agar YORDAM, REGISTRATSIYA, RASM yoki SAYT FUNKSIYASI so'rasa -> `get_visual_guide_tool` ni chaqir.
# #     3. Agar shunchaki GAPLASHSA -> Hech qanday tool chaqirma, shunchaki javob ber.
# #
# #     Qoida: Faqat O'zbek tilida gaplash.
# #     """
# #
# #     ai_decision = llm_with_tools.invoke([
# #         SystemMessage(content=system_msg),
# #         HumanMessage(content=user_input)
# #     ])
# #
# #     # 2-QADAM: Tool chaqirildimi?
# #     if ai_decision.tool_calls:
# #         tool_call = ai_decision.tool_calls[0]
# #         tool_name = tool_call["name"]
# #         tool_args = tool_call["args"]
# #
# #         print(f"🤖 AI Qarori: {tool_name} ishlatilmoqda...")
# #
# #         # --- A) YANGILIKLAR LOGIKASI ---
# #         if tool_name == "get_news_tool":
# #             category = tool_args.get("category")
# #             print(f"📰 Yangiliklar yuklanmoqda (Kategoriya: {category})...")
# #
# #             # Scraper ishlashi
# #             raw_news = await scraper.get_news_async(category=category, limit=5)
# #
# #             if not raw_news:
# #                 return ChatResponse(response="Kechirasiz, yangiliklarni yuklay olmadim.", news=[])
# #
# #             # AI Summarization
# #             news_context = ""
# #             for i, item in enumerate(raw_news):
# #                 news_context += f"ID: {i}\nSARLAVHA: {item['title']}\nMATN: {item.get('raw_text', '')[:1000]}\n\n"
# #
# #             sum_prompt = ChatPromptTemplate.from_messages([
# #                 ("system", "Sen Kun.uz muharririsan. Yangiliklarga qisqa xulosa yoz va umumiy javob ber."),
# #                 ("human", f"Savol: {user_input}\n\nYangiliklar:\n{news_context}")
# #             ])
# #
# #             summary_result = structured_summarizer.invoke(
# #                 sum_prompt.format_messages(question=user_input, context=news_context))
# #
# #             # Response yig'ish
# #             final_news = []
# #             DEFAULT_IMG = "https://storage.kun.uz/source/thumbnails/_medium/11/default-news_medium.jpg"
# #             summary_map = {s.index: s.ai_summary for s in summary_result.summaries}
# #
# #             for i, item in enumerate(raw_news):
# #                 ai_desc = summary_map.get(i, "Batafsil ma'lumot saytda...")
# #                 final_news.append(NewsItemResponse(
# #                     title=item["title"],
# #                     url=item["url"],
# #                     image_url=item.get("image_url") or DEFAULT_IMG,
# #                     date=item.get("date", "Bugun"),
# #                     description=ai_desc
# #                 ))
# #
# #             return ChatResponse(
# #                 response=summary_result.general_chat_response,
# #                 news=final_news
# #             )
# #
# #         # --- B) VIZUAL QO'LLANMA (GUIDE) LOGIKASI ---
# #         elif tool_name == "get_visual_guide_tool":
# #             query = tool_args.get("query")
# #             print(f"📸 Qo'llanma qidirilmoqda: {query}")
# #
# #             guide_data = search_guide_by_tags(query)  # knowledge_base dan qidirish
# #
# #             if guide_data:
# #                 response_text = f"Siz so'ragan mavzu bo'yicha ma'lumot:\n\n{guide_data['text']}\n\nQuyidagi rasmda ko'rsatilgan:"
# #                 return ChatResponse(
# #                     response=response_text,
# #                     guide_image=guide_data["image"]  # Rasmni frontendga yuboramiz
# #                 )
# #             else:
# #                 return ChatResponse(
# #                     response="Kechirasiz, bu mavzu bo'yicha menda rasmli qo'llanma yo'q ekan. Boshqa narsa so'rab ko'ring.",
# #                     guide_image=None
# #                 )
# #
# #     # 3-QADAM: Agar Tool chaqirilmasa (ODDIY SUHBAT)
# #     print("💬 Oddiy suhbat...")
# #     return ChatResponse(
# #         response=ai_decision.content,  # AIning o'z javobi
# #         news=[],
# #         guide_image=None
# #     )
#
#
# #---------------------------------------------------------------------




import os
import autogen
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb

# 1. API KALITNI SOZLASH
# Tavsiya: Xavfsizlik uchun bu yerni o'zgartiring yoki muhit o'zgaruvchisidan oling
os.environ["OPENAI_API_KEY"] = "sk-..."

config_list = [
    {
        "model": "gpt-4-turbo-preview",  # Yoki "gpt-3.5-turbo-0125" (arzonroq)
        "api_key": os.environ["OPENAI_API_KEY"],
    }
]

llm_config = {
    "config_list": config_list,
    "timeout": 60,
    "temperature": 0.1,  # Aniq faktik javoblar uchun pastroq harorat
}

# 2. QONUNSHUNOS AGENT (Javob beruvchi)
assistant = autogen.AssistantAgent(
    name="qonun_maslahatchisi",
    system_message="""
    Sen O'zbekiston qonunchiligi bo'yicha professional yurist-maslahatchisan.
    Sening vazifang: Foydalanuvchi savoliga TAQDIM ETILGAN KONTEKST (Context) asosida javob berish.

    Qoidalar:
    1. Javobni har doim O'zbek tilida ber.
    2. Javobingda aniq moddalar yoki qonun nomlarini keltirib o't (agar kontekstda bo'lsa).
    3. Agar taqdim etilgan ma'lumotlarda javob bo'lmasa, "Kechirasiz, bazamda bu bo'yicha aniq ma'lumot topilmadi" deb ayt. O'zingdan to'qib chiqarma.
    4. Javobing lo'nda va tushunarli bo'lsin.
    """,
    llm_config=llm_config,
)

# 3. RAG AGENT (Qidiruvchi va Foydalanuvchi vakili)
rag_proxy = RetrieveUserProxyAgent(
    name="foydalanuvchi_vakili",
    human_input_mode="ALWAYS",  # Har bir javobdan keyin sizdan input so'raydi
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "qa",  # Question Answering
        "docs_path": "./lex_data",  # Biz scrape qilgan papka
        "chunk_token_size": 1000,  # Matnni bo'laklash hajmi
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="./chromadb_data"),  # Vektor baza joyi
        "collection_name": "lexuz_db",
        "get_or_create": True,
        # Agar embedding model kerak bo'lsa (default: all-MiniLM-L6-v2 ishlatiladi yoki OpenAI):
        # "embedding_model": "all-MiniLM-L6-v2",
    },
    code_execution_config=False,  # Kod yozish shart emas, faqat matn
)


# 4. CHATNI BOSHLASH FUNKSIYASI
def start_chat():
    print("\n--- LEX.UZ AI YORDAMCHISI ---")
    print("Qonunchilik bo'yicha savolingizni yozing (chiqish uchun 'exit').")

    # Dastlabki kontekstni yuklash uchun "dummy" savol bilan ishga tushirishimiz mumkin
    # yoki to'g'ridan to'g'ri foydalanuvchi savolini kutishimiz mumkin.

    rag_proxy.initiate_chat(
        assistant,
        problem="O'zbekiston Konstitutsiyasiga ko'ra inson huquqlari qanday himoya qilinadi?",
        # Birinchi avtomatik savol (start uchun)
        n_results=3,  # Eng mos 3 ta parchani topib beradi
    )


if __name__ == "__main__":
    # ChromaDB xatoliklarini oldini olish uchun (ixtiyoriy)
    try:
        import pysqlite3
        import sys

        sys.modules["sqlite3"] = pysqlite3
    except:
        pass

    start_chat()