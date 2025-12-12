# import os
# import autogen
# from database import search_lexuz_tool
#
# # 1. API KEY
# raw_api_key = os.getenv("OPENAI_API_KEY", "")
# api_key = raw_api_key.strip().strip('"').strip("'")
# if not api_key: raise ValueError("API Key yo'q!")
#
# config_list = [{"model": "gpt-3.5-turbo-0125", "api_key": api_key}]
#
# # ==============================================================================
# # 1. AGENTLARNI YARATISH
# # ==============================================================================
#
# # --- ROUTER (DISPETCHER) ---
# # Uning vazifasi faqat qaror qabul qilish.
# router = autogen.AssistantAgent(
#     name="Router",
#     system_message="""
#     Sen dispetchersan. Foydalanuvchi xabarini tahlil qil va yo'nalishni aniqla.
#
#     QOIDALAR:
#     1. Agar savol Qonun, Pul, Oylik, Ish, Sud, Hujjat, Ariza, Jarima haqida bo'lsa -> "LEGAL" deb yoz.
#     2. Agar savol Salomlashish, Hol-ahvol yoki Tanishuv bo'lsa -> "CASUAL" deb yoz.
#
#     Javobing faqat bitta so'z bo'lsin.
#     """,
#     llm_config={"config_list": config_list, "temperature": 0}
# )
#
# # --- SOCIAL BOT (ODDIY SUHBAT) ---
# social_bot = autogen.AssistantAgent(
#     name="SocialBot",
#     system_message="""
#     Sen Lexi - samimiy yordamchisan.
#     Vazifang: Foydalanuvchi bilan salomlashish va kayfiyatini ko'tarish.
#
#     Qoidalar:
#     - Qonuniy maslahat berma.
#     - Agar qonun so'rasa, "Yurist hamkasbimga yuzlaning" de.
#     - Javob oxirida TERMINATE deb yoz.
#     """,
#     llm_config={"config_list": config_list, "temperature": 0.7}
# )
#
# # --- LEGAL BOT (YURIST) ---
# # Tool sxemasi
# tool_schema = {
#     "type": "function",
#     "function": {
#         "name": "search_lexuz_tool",
#         "description": "PostgreSQL bazasidan qonun qidirish",
#         "parameters": {
#             "type": "object",
#             "properties": {"sorov": {"type": "string"}},
#             "required": ["sorov"]
#         }
#     }
# }
#
# legal_bot = autogen.AssistantAgent(
#     name="LegalBot",
#     system_message="""
#     Sen Professional Yuristsan.
#
#     Vazifang:
#     1. Har doim 'search_lexuz_tool' funksiyasini chaqirib, bazadan javob izla.
#     2. Topilgan matnga asoslanib, aniq va lo'nda javob ber.
#     3. Javob oxirida TERMINATE deb yoz.
#     """,
#     llm_config={
#         "config_list": config_list,
#         "temperature": 0,
#         "tools": [tool_schema]
#     }
# )
#
# # --- USER PROXY (IJROCHI) ---
# user_proxy = autogen.UserProxyAgent(
#     name="UserProxy",
#     human_input_mode="NEVER",
#     max_consecutive_auto_reply=10,
#     code_execution_config=False
# )
#
# # Toolni ro'yxatdan o'tkazish
# user_proxy.register_function(function_map={"search_lexuz_tool": search_lexuz_tool})
#
#
# # ==============================================================================
# # 2. BOSHQARUV LOGIKASI (CUSTOM SPEAKER SELECTION)
# # Bu AutoGenning eng kuchli qismi. Kim gapirishini biz kod bilan hal qilamiz.
# # ==============================================================================
# # ... (tepadagi kodlar o'sha-o'sha)
#
# # ==============================================================================
# # BOSHQARUV LOGIKASI
# # ==============================================================================
# def state_transition(last_speaker, groupchat):
#     messages = groupchat.messages
#
#     # 1. Boshlanishi -> Router
#     if last_speaker is user_proxy:
#         return router
#
#     # 2. Router -> Legal yoki Casual
#     if last_speaker is router:
#         last_msg = messages[-1]["content"].strip().upper()
#         if "LEGAL" in last_msg:
#             return legal_bot
#         else:
#             return social_bot
#
#     # 3. LegalBot logikasi
#     if last_speaker is legal_bot:
#         # Agar tool chaqirsa -> UserProxy bajarsin
#         if messages[-1].get("tool_calls") or messages[-1].get("function_call"):
#             return user_proxy
#         # Agar javob bersa -> TUGATISH
#         return None
#
#         # 4. SocialBot -> TUGATISH
#     if last_speaker is social_bot:
#         return None
#
#     # 5. UserProxy (Tool natijasi) -> LegalBot
#     if last_speaker is user_proxy:
#         return legal_bot
#
#     return None
#
#
# # GroupChat va Manager
# groupchat = autogen.GroupChat(
#     agents=[user_proxy, router, legal_bot, social_bot],
#     messages=[],
#     max_round=10,
#     speaker_selection_method=state_transition
# )
#
# manager = autogen.GroupChatManager(
#     groupchat=groupchat,
#     llm_config={"config_list": config_list}
# )


# import os
# import autogen
# from database import search_lexuz_tool
# from typing import Dict, List, Optional
#
# # API sozlamalari
# raw_api_key = os.getenv("OPENAI_API_KEY", "")
# api_key = raw_api_key.strip().strip('"').strip("'")
# if not api_key:
#     raise ValueError("⚠️ OPENAI_API_KEY topilmadi!")
#
# config_list = [{"model": "gpt-4o-mini", "api_key": api_key}]
#
# # ==============================================================================
# # 1. ORCHESTRATOR - Bosh Boshqaruvchi Agent
# # ==============================================================================
# orchestrator = autogen.AssistantAgent(
#     name="Orchestrator",
#     system_message="""Sen bosh koordinatorsan. Vazifang:
#     1. Foydalanuvchi savolini tahlil qilish
#     2. Qaysi agentga yo'naltirishni aniqlash
#     3. Jarayonni kuzatish
#
#     Yo'naltirish qoidalari:
#     - "Salom", "Qalay", "Kim" - SOCIAL agentga
#     - Qonun, Oylik, Ish, Sud, Huquq - CLASSIFIER agentga
#     - Noaniq holatlarda CLASSIFIER dan yordam so'ra
#
#     Javobda faqat agent nomini yoz: SOCIAL yoki CLASSIFIER""",
#     llm_config={"config_list": config_list, "temperature": 0}
# )
#
# # ==============================================================================
# # 2. CLASSIFIER - Savol Tasniflovchi
# # ==============================================================================
# classifier = autogen.AssistantAgent(
#     name="Classifier",
#     system_message="""Sen savollarni tasniflash mutaxassisisan.
#
#     Vazifang: Savol qonuniy yoki oddiy ekanligini aniqlash.
#
#     QONUNIY SAVOLLAR:
#     - Oylik, ish haqi, mehnat to'lovi
#     - Ishdan bo'shatish, ish shartnomasi
#     - Fuqarolik, jinoyat, sud jarayonlari
#     - Huquq, majburiyat, javobgarlik
#     - Soliq, jarima, litsenziya
#
#     ODDIY SAVOLLAR:
#     - Salomlashish, tanishish
#     - Umumiy savol-javob
#     - Bot haqida ma'lumot
#
#     Javobda faqat bitta so'z yoz: LEGAL yoki CASUAL""",
#     llm_config={"config_list": config_list, "temperature": 0}
# )
#
# # ==============================================================================
# # 3. SOCIAL BOT - Oddiy Suhbat Agenti
# # ==============================================================================
# social_bot = autogen.AssistantAgent(
#     name="SocialBot",
#     system_message="""Sen Lexi - Lex.uz saytining do'stona yordamchisisan.
#
#     Shaxsiyating:
#     - Mehribon va samimiy
#     - Aniq va qisqa javob beruvchi
#     - O'zbek tilida professional gaplashuvchi
#
#     Vazifalaringiz:
#     1. Salomlashish va tanishish
#     2. Bot imkoniyatlari haqida ma'lumot berish
#     3. Foydalanuvchini yo'naltirish
#
#     MUHIM:
#     - Qonuniy maslahat BERMA (yuristga yo'nalt)
#     - Javobda bot kabi emas, odam kabi gapir
#     - Emoji ishlatma, professional bo'l
#     - Javob oxirida TERMINATE yozma
#
#     Misol javoblar:
#     "Assalomu alaykum! Men Lexi, sizga qanday yordam bera olaman?"
#     "Men O'zbekiston qonunchiligini tushuntirib berishda yordam beraman."
#     "Qonuniy savolingiz bo'lsa, batafsil so'rang - men tegishli moddalani topaman."
#     """,
#     llm_config={"config_list": config_list, "temperature": 0.8}
# )
#
# # ==============================================================================
# # 4. LEGAL SEARCHER - Bazadan Qidiruvchi
# # ==============================================================================
# legal_searcher = autogen.AssistantAgent(
#     name="LegalSearcher",
#     system_message="""Sen qonun bazasidan qidirish mutaxassisisan.
#
#     Vazifang:
#     1. Har doim 'search_lexuz_tool' funksiyasini ishlatish
#     2. Topilgan natijalarni Legal Analyzer ga uzatish
#     3. Agar natija bo'lmasa, xabar berish
#
#     MUHIM: Javob berma, faqat qidiruv natijasini uzat!""",
#     llm_config={
#         "config_list": config_list,
#         "temperature": 0,
#         "tools": [{
#             "type": "function",
#             "function": {
#                 "name": "search_lexuz_tool",
#                 "description": "PostgreSQL bazasidan qonun qidirish",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {"sorov": {"type": "string"}},
#                     "required": ["sorov"]
#                 }
#             }
#         }]
#     }
# )
#
# # ==============================================================================
# # 5. LEGAL ANALYZER - Qonuniy Tahlilchi
# # ==============================================================================
# legal_analyzer = autogen.AssistantAgent(
#     name="LegalAnalyzer",
#     system_message="""Sen professional yurist-tahlilchisan.
#
#     Vazifang: Topilgan qonun matnlarini tahlil qilib, aniq javob berish.
#
#     Javob formati:
#
#     📋 [Mavzu]
#
#     Javob: [Aniq va tushunarli tushuntirish]
#
#     📚 Qonuniy asos:
#     - [Qonun nomi, modda raqami]
#
#     💡 Maslahat: [Amaliy tavsiya]
#
#     QOIDALAR:
#     1. Faqat berilgan kontekstga asoslan
#     2. Modda raqamlarini ko'rsat
#     3. Oddiy tilda yoz, yuridik jargonsiz
#     4. Agar ma'lumot yetarli bo'lmasa, ochiq ayt
#     5. Emoji kam ishlatma (faqat bo'limlar uchun)
#     """,
#     llm_config={"config_list": config_list, "temperature": 0.3}
# )
#
# # ==============================================================================
# # 6. RESPONSE FORMATTER - Javob Formatlash Agenti
# # ==============================================================================
# response_formatter = autogen.AssistantAgent(
#     name="ResponseFormatter",
#     system_message="""Sen javoblarni formatlash va tekshirish mutaxassisisan.
#
#     Vazifang:
#     1. Javobni yakuniy formatga keltirish
#     2. Ortiqcha ma'lumotlarni tozalash
#     3. Foydalanuvchiga qulay ko'rinish berish
#
#     TOZALASH qoidalari:
#     - "TERMINATE" so'zini o'chir
#     - Tool chaqiruvlarini ko'rsatma
#     - Agent nomlarini olib tashlama
#     - Formatni saqla
#
#     So'nggi javobni shu holatda qaytar.""",
#     llm_config={"config_list": config_list, "temperature": 0}
# )
#
# # ==============================================================================
# # 7. USER PROXY - Ijrochi Agent
# # ==============================================================================
# user_proxy = autogen.UserProxyAgent(
#     name="UserProxy",
#     human_input_mode="NEVER",
#     max_consecutive_auto_reply=15,
#     code_execution_config=False,
#     is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE")
# )
#
# # Tool ro'yxatga olish
# user_proxy.register_function(function_map={"search_lexuz_tool": search_lexuz_tool})
#
#
# # ==============================================================================
# # STATE MACHINE - Holatlar Mashinasi
# # ==============================================================================
# def intelligent_speaker_selection(last_speaker, groupchat):
#     """
#     Bu funksiya qaysi agent navbatda gaplashishini aniqlaydi.
#     AutoGenning eng kuchli xususiyati - to'liq boshqaruv.
#     """
#     messages = groupchat.messages
#
#     if not messages:
#         return orchestrator
#
#     last_msg = messages[-1]
#     content = last_msg.get("content", "").strip().upper()
#     speaker_name = last_speaker.name if last_speaker else None
#
#     # 1. BOSHLANG'ICH: UserProxy → Orchestrator
#     if speaker_name == "UserProxy" and len(messages) == 1:
#         return orchestrator
#
#     # 2. ORCHESTRATOR QAROR QABUL QILDI
#     if speaker_name == "Orchestrator":
#         if "SOCIAL" in content:
#             return social_bot
#         elif "CLASSIFIER" in content:
#             return classifier
#         return None  # Noaniq holat
#
#     # 3. CLASSIFIER TASNIFI
#     if speaker_name == "Classifier":
#         if "CASUAL" in content:
#             return social_bot
#         elif "LEGAL" in content:
#             return legal_searcher
#         return None
#
#     # 4. SOCIAL BOT JAVOB BERDI
#     if speaker_name == "SocialBot":
#         return response_formatter
#
#     # 5. LEGAL SEARCHER QIDIRUV QILMOQDA
#     if speaker_name == "LegalSearcher":
#         # Agar tool chaqiruvchi bo'lsa
#         if last_msg.get("tool_calls") or last_msg.get("function_call"):
#             return user_proxy  # Tool bajarish uchun
#         # Tool natijasi kelganidan keyin
#         return legal_analyzer
#
#     # 6. USER PROXY TOOL BAJARIBDI
#     if speaker_name == "UserProxy" and len(messages) > 1:
#         prev_speaker = messages[-2].get("name")
#         if prev_speaker == "LegalSearcher":
#             return legal_analyzer
#
#     # 7. LEGAL ANALYZER TAHLIL QILDI
#     if speaker_name == "LegalAnalyzer":
#         return response_formatter
#
#     # 8. RESPONSE FORMATTER YAKUNLADI
#     if speaker_name == "ResponseFormatter":
#         return None  # Tugadi
#
#     return None
#
#
# # ==============================================================================
# # GROUP CHAT VA MANAGER
# # ==============================================================================
# groupchat = autogen.GroupChat(
#     agents=[
#         user_proxy,
#         orchestrator,
#         classifier,
#         social_bot,
#         legal_searcher,
#         legal_analyzer,
#         response_formatter
#     ],
#     messages=[],
#     max_round=20,
#     speaker_selection_method=intelligent_speaker_selection
# )
#
# manager = autogen.GroupChatManager(
#     groupchat=groupchat,
#     llm_config={"config_list": config_list}
# )
#
# # ==============================================================================
# # TESTING
# # ==============================================================================
# if __name__ == "__main__":
#     print("🧪 Agent tizimi test rejimida ishga tushdi")
#     print("Barcha agentlar:")
#     for agent in groupchat.agents:
#         print(f"  ✓ {agent.name}")


import os
import json
import re
import autogen
from database import search_lexuz_tool
from typing import Dict, List, Optional

# API sozlamalari
raw_api_key = os.getenv("OPENAI_API_KEY", "")
api_key = raw_api_key.strip().strip('"').strip("'")
if not api_key:
    raise ValueError("⚠️ OPENAI_API_KEY topilmadi!")

config_list = [{"model": "gpt-4o-mini", "api_key": api_key}]

STRUCTURED_FOLDER = "lex_structured"


# ==============================================================================
# YANGI: JSON DAN ANIQ MODDA QIDIRISH
# ==============================================================================
def search_article_direct(query: str) -> str:
    """
    Aniq modda raqami so'ralganda JSON dan qidirish

    Masalan:
    - "Konstitutsiya 80-modda"
    - "Mehnat kodeksi 131-modda"
    - "80-modda prezident"
    - "88-modda" (barcha kodekslardan qidiradi)
    """

    # 1. Hujjat nomini aniqlash
    doc_mapping = {
        "konstitutsiya": "Konstitutsiya",
        "mehnat": "Mehnat_Kodeksi",
        "fuqarolik": "Fuqarolik_Kodeksi",
        "jinoyat": "Jinoyat_Kodeksi",
        "oila": "Oila_Kodeksi",
        "ma'muriy": "Ma'muriy_Javobgarlik_Kodeksi",
        "mamuriy": "Ma'muriy_Javobgarlik_Kodeksi",
        "soliq": "Soliq_Kodeksi",
        "yer": "Yer_Kodeksi",
        "uy-joy": "Uy_Joy_Kodeksi",
        "uy joy": "Uy_Joy_Kodeksi",
        "suv": "Suv_Kodeksi",
        # Kiberxavfsizlik - ko'p variantlar
        "kiberxavfsizlik": "Kiberxavfsizlik_Qonuni",
        "kiber xavfsizlik": "Kiberxavfsizlik_Qonuni",
        "kibir xafsizlik": "Kiberxavfsizlik_Qonuni",  # typo variant
        "kibir xavfsizlik": "Kiberxavfsizlik_Qonuni",
        "kiber": "Kiberxavfsizlik_Qonuni",
        "cyber": "Kiberxavfsizlik_Qonuni",
        # Axborotlashtirish - ko'p variantlar
        "axborotlashtirish": "Axborotlashtirish_Qonuni",
        "axborot": "Axborotlashtirish_Qonuni",
        "informatizatsiya": "Axborotlashtirish_Qonuni",
        # Shaxsiy ma'lumotlar
        "shaxsiy ma'lumot": "Shaxsiy_Malumotlar_Qonuni",
        "shaxsiy malumot": "Shaxsiy_Malumotlar_Qonuni",
        "shaxsiy": "Shaxsiy_Malumotlar_Qonuni",
        # Ta'lim
        "ta'lim": "Talim_Qonuni",
        "talim": "Talim_Qonuni",
        "maktabgacha": "Maktabgacha_Talim_Qonuni",
        # Boshqalar
        "tadbirkorlik": "Tadbirkorlik_Kafolatlari_Qonuni",
        "tabiat": "Tabiatni_Muhofaza_Qilish_Qonuni",
        "jinoyat protsessual": "Jinoyat_Protsessual_Kodeksi",
        "fuqarolik protsessual": "Fuqarolik_Protsessual_Kodeksi",
        "iqtisodiy protsessual": "Iqtisodiy_Protsessual_Kodeksi",
        "ma'muriy sud": "Mamuriy_Sud_Ishlarini_Yuritish_Kodeksi",
        "budjet": "Budjet_Kodeksi",
        "shaharsozlik": "Shaharsozlik_Kodeksi",
        "bojxona": "Bojxona_Kodeksi",
        "havo": "Havo_Kodeksi",
        "jinoyat ijroiya": "Jinoyat_Ijroiya_Kodeksi",
        "saylov": "Saylov_Kodeksi"
    }

    query_lower = query.lower()
    doc_name = None

    for key, value in doc_mapping.items():
        if key in query_lower:
            doc_name = value
            break

    # 2. Modda raqamini topish
    article_match = re.search(r'(\d+)-(?:модда|modda)', query_lower)
    if not article_match:
        article_match = re.search(r'(?:модда|modda)\s*(\d+)', query_lower)
    
    # Agar faqat raqam bo'lsa (masalan "88-modda")
    if not article_match:
        article_match = re.search(r'(\d+)', query_lower)

    # Agar modda raqami yo'q va faqat hujjat nomi bo'lsa
    if not article_match and doc_name:
        json_path = f"{STRUCTURED_FOLDER}/{doc_name}.json"
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                
                total_articles = len(articles)
                first_articles = sorted(articles.keys(), key=int)[:5]
                
                result = f"""📚 {doc_name.replace('_', ' ')} HAQIDA UMUMIY MA'LUMOT:

============================================================
📄 Hujjat: {doc_name.replace('_', ' ')}
📊 Jami moddalar soni: {total_articles}
📌 Dastlabki moddalar: {', '.join(first_articles)}...

💡 Aniq modda haqida ma'lumot olish uchun modda raqamini ko'rsating.
   Masalan: "{doc_name.replace('_', ' ')} 1-modda"

============================================================
✅ Ma'lumot rasmiy manba asosida"""
                
                return result
            except Exception as e:
                return f"❌ Xato: {str(e)}"
        else:
            return None

    if not article_match:
        return None  # Modda raqami yo'q

    article_num = article_match.group(1)

    # 3. Agar hujjat nomi yo'q bo'lsa, barcha JSON fayllardan qidirish
    if not doc_name:
        import glob
        json_files = glob.glob(f"{STRUCTURED_FOLDER}/*.json")
        
        results = []
        for json_path in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                
                if article_num in articles:
                    doc_name_from_file = os.path.basename(json_path).replace('.json', '')
                    article = articles[article_num]
                    results.append({
                        'doc': doc_name_from_file,
                        'article': article
                    })
            except:
                continue
        
        if results:
            # Agar bir nechta topilsa, barchasini ko'rsatish
            result_text = f"📚 {article_num}-MODDA QUYIDAGI HUJJATLARDA TOPILDI:\n\n"
            
            for i, res in enumerate(results, 1):
                result_text += f"{'=' * 60}\n"
                result_text += f"📄 {i}. {res['doc'].replace('_', ' ')}\n"
                result_text += f"📌 {res['article']['title']}\n\n"
                result_text += f"{res['article']['content']}\n\n"
            
            result_text += f"{'=' * 60}\n"
            result_text += f"✅ Jami {len(results)} ta hujjatda topildi"
            
            return result_text
        else:
            return None  # Hech qayerda topilmadi

    # 4. Aniq hujjatdan qidirish
    json_path = f"{STRUCTURED_FOLDER}/{doc_name}.json"

    if not os.path.exists(json_path):
        return f"❌ {doc_name}.json fayli topilmadi. Scraper'ni ishga tushiring."

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        if article_num in articles:
            article = articles[article_num]

            result = f"""📚 QONUN BAZASIDAN TOPILGAN ANIQ MODDA:

============================================================
📄 Hujjat: {doc_name.replace('_', ' ')}
🎯 Modda: {article_num}
📌 Sarlavha: {article['title']}

MAZMUNI:
{article['content']}

============================================================
✅ Ma'lumot to'liq va rasmiy manba asosida"""

            return result
        else:
            available = sorted(articles.keys(), key=int)[:10]
            return f"""❌ {article_num}-modda topilmadi.

💡 {doc_name}da mavjud moddalar (dastlabki 10 ta):
{', '.join(available)}...

Iltimos, modda raqamini tekshiring."""

    except Exception as e:
        return f"❌ Xato: {str(e)}"


# Tool funksiyasi sifatida ro'yxatga olish uchun
def search_article_tool(sorov: str) -> str:
    """
    Tool interface uchun wrapper
    """
    result = search_article_direct(sorov)
    if result:
        return result
    else:
        # Agar aniq modda topilmasa, oddiy qidiruvga o'tadi
        return search_lexuz_tool(sorov)


# ==============================================================================
# 1. ORCHESTRATOR - Bosh Boshqaruvchi Agent
# ==============================================================================
orchestrator = autogen.AssistantAgent(
    name="Orchestrator",
    system_message="""Sen bosh koordinatorsan. Vazifang:
    1. Foydalanuvchi savolini tahlil qilish
    2. Qaysi agentga yo'naltirishni aniqlash
    3. Jarayonni kuzatish

    Yo'naltirish qoidalari:
    - "Salom", "Qalay", "Kim", "Nima qila olasan" - SOCIAL agentga
    - Lex.uz saytidan foydalanish (registratsiya, til, qidiruv, sozlamalar) - KNOWLEDGE agentga
    - Qonun, Oylik, Ish, Sud, Huquq, Kodeks, Modda - CLASSIFIER agentga
    - Noaniq holatlarda CLASSIFIER dan yordam so'ra

    Javobda faqat agent nomini yoz: SOCIAL, KNOWLEDGE yoki CLASSIFIER""",
    llm_config={"config_list": config_list, "temperature": 0}
)

# ==============================================================================
# 2. CLASSIFIER - Savol Tasniflovchi
# ==============================================================================
classifier = autogen.AssistantAgent(
    name="Classifier",
    system_message="""Sen savollarni tasniflash mutaxassisisan.

    Vazifang: Savol qonuniy yoki sayt foydalanish haqida ekanligini aniqlash.

    QONUNIY SAVOLLAR (LEGAL):
    - Oylik, ish haqi, mehnat to'lovi
    - Ishdan bo'shatish, ish shartnomasi
    - Fuqarolik, jinoyat, sud jarayonlari
    - Huquq, majburiyat, javobgarlik
    - Soliq, jarima, litsenziya
    - Kodeks, modda, qonun matni

    SAYT FOYDALANISH SAVOLLARI (KNOWLEDGE):
    - Lex.uz saytidan qanday foydalanish
    - Registratsiya, kirish, akkaunt
    - Til o'zgartirish
    - Hujjat qidirish, yuklab olish
    - Sozlamalar, bildirishnomalar

    Javobda faqat bitta so'z yoz: LEGAL yoki KNOWLEDGE""",
    llm_config={"config_list": config_list, "temperature": 0}
)

# ==============================================================================
# 3. SOCIAL BOT - Oddiy Suhbat Agenti
# ==============================================================================
social_bot = autogen.AssistantAgent(
    name="SocialBot",
    system_message="""Sen Lexi - Lex.uz saytining professional va do'stona yordamchisisan.

    ASOSIY QOIDALAR:
    1. Har doim QISQA va ANIQ javob ber (maksimum 2-3 gap)
    2. Har safar TURLICHA javob ber, takrorlanma
    3. Tabiiy va samimiy bo'l, robot kabi emas
    4. Javob oxirida TERMINATE yoz

    JAVOB USLUBI:
    - Salomlashish: Qisqa salom + yordam taklifi
      Misol: "Salom! Nima haqida gaplashamiz?"
    - Imkoniyatlar: Qisqa va aniq
      Misol: "Men qonunlar va Lex.uz sayti bo'yicha yordam beraman."
    - Umumiy savol: To'g'ridan-to'g'ri javob
      Misol: "Albatta! Qanday yordam kerak?"

    QILMA:
    - Uzun javoblar berma
    - Bir xil gaplarni takrorlama
    - "Yuristga murojaat qiling" dema
    - Ortiqcha tushuntirma berma
    """,
    llm_config={"config_list": config_list, "temperature": 0.9}
)

# ==============================================================================
# 4. KNOWLEDGE BOT - Sayt Foydalanish Yordamchisi
# ==============================================================================
knowledge_bot = autogen.AssistantAgent(
    name="KnowledgeBot",
    system_message="""Sen Lex.uz saytidan foydalanish bo'yicha mutaxassis yordamchisan.

    Vazifang:
    1. Foydalanuvchi savolidan kalit so'zlarni ajratib ol.
    2. 'search_guide_by_tags' funksiyasini ishlatib, yo'riqnoma qidir.
    3. Topilgan ma'lumotni foydalanuvchiga tushunarli qilib yetkazish.
    4. Agar rasm mavjud bo'lsa, uni ko'rsatish.

    MUHIM:
    - Har doim avval tool chaqir, keyin javob ber.
    - Javobingni do'stona va tushunarli qil.
    - Agar ma'lumot topilmasa, "Afsuski, bu mavzu bo'yicha ma'lumot yo'q" deb javob ber.
    """,
    llm_config={
        "config_list": config_list,
        "temperature": 0.5,
        "tools": [{
            "type": "function",
            "function": {
                "name": "search_guide_by_tags",
                "description": "Lex.uz saytidan foydalanish bo'yicha yo'riqnoma qidirish",
                "parameters": {
                    "type": "object",
                    "properties": {"user_query": {"type": "string"}},
                    "required": ["user_query"]
                }
            }
        }]
    }
)

# ==============================================================================
# 5. LEGAL SEARCHER - Bazadan Qidiruvchi (YANGILANGAN)
# ==============================================================================
legal_searcher = autogen.AssistantAgent(
    name="LegalSearcher",
    system_message="""Sen qonun bazasidan qidirish mutaxassisisan.

    Vazifang:
    1. Foydalanuvchi savolidan kalit so'zlarni va agar mavjud bo'lsa, aniq modda raqamini ajratib ol.
    2. 'search_article_tool' funksiyasini ishlatib, bazadan ma'lumot qidir.
    3. Topilgan natijalarni Legal Analyzer ga uzatish.
    4. Agar natija bo'lmasa, "Afsuski, bazadan ma'lumot topilmadi" deb javob ber.

    MUHIM: 
    - Har doim faqat bitta tool chaqirish yetarli.
    - Javob berma, faqat qidiruv natijasini uzat!
    - Agar foydalanuvchi aniq moddani so'rasa (masalan "131-modda"), so'rovda buni aniq ko'rsat.
    """,
    llm_config={
        "config_list": config_list,
        "temperature": 0,
        "tools": [{
            "type": "function",
            "function": {
                "name": "search_article_tool",
                "description": "Qonun bazasidan qidirish (JSON va embeddings)",
                "parameters": {
                    "type": "object",
                    "properties": {"sorov": {"type": "string"}},
                    "required": ["sorov"]
                }
            }
        }]
    }
)

# ==============================================================================
# 6. LEGAL ANALYZER - Qonuniy Tahlilchi
# ==============================================================================
legal_analyzer = autogen.AssistantAgent(
    name="LegalAnalyzer",
    system_message="""Sen professional yurist-tahlilchisan.

    VAZIFA: Qonun matnlarini oddiy tilda tushuntirish.

    JAVOB FORMATI:
    📋 [Qisqa sarlavha]

    [Asosiy javob - oddiy va tushunarli. Yuridik atamalarni izohla.]

    📚 Qonuniy asos:
    - [Aniq qonun/kodeks nomi va modda raqami]

    💡 Amaliy maslahat:
    [Foydalanuvchi nima qilishi kerak]

    QOIDALAR:
    1. Faqat berilgan ma'lumotga asoslan
    2. Agar ma'lumot yetarli bo'lmasa: "Afsuski, bazada bu mavzu bo'yicha batafsil ma'lumot yo'q"
    3. Modda raqamlarini doimo ko'rsat
    4. Oddiy va tushunarli yoz, jargon ishlatma
    5. Javob hajmi: 3-5 gap (juda qisqa)
    6. Agar aniq modda topilgan bo'lsa, uning asosiy qismini keltir
    """,
    llm_config={"config_list": config_list, "temperature": 0.2}
)

# ==============================================================================
# 7. RESPONSE FORMATTER - Javob Formatlash Agenti
# ==============================================================================
response_formatter = autogen.AssistantAgent(
    name="ResponseFormatter",
    system_message="""Sen javoblarni yakuniy ko'rinishga keltiruvchisan.

    VAZIFA: Javobni foydalanuvchi uchun qulay formatga keltir.

    TOZALASH:
    1. "TERMINATE" so'zini o'chir
    2. Tool chaqiruvlarini ko'rsatma
    3. Texnik ma'lumotlarni olib tashla
    4. Emoji va formatni saqla
    5. Agent nomlarini ko'rsatma
    6. MUHIM: Agar matnda rasm (image) linklari yoki markdown formatdagi rasmlar bo'lsa, ularni albatta saqlab qol!

    QOIDA: Faqat javob matnini qaytar, boshqa hech narsa qo'shma.
    """,
    llm_config={"config_list": config_list, "temperature": 0}
)

# ==============================================================================
# 8. USER PROXY - Ijrochi Agent
# ==============================================================================
user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=15,
    code_execution_config=False,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE")
)

# Tool'larni ro'yxatga olish
from knowledge_base import search_guide_by_tags

user_proxy.register_function(function_map={
    "search_article_tool": search_article_tool,
    "search_lexuz_tool": search_lexuz_tool,  # Backup uchun
    "search_guide_by_tags": search_guide_by_tags  # Sayt foydalanish uchun
})


# ==============================================================================
# STATE MACHINE - Holatlar Mashinasi
# ==============================================================================
def intelligent_speaker_selection(last_speaker, groupchat):
    """
    Bu funksiya qaysi agent navbatda gaplashishini aniqlaydi.
    """
    messages = groupchat.messages
    
    # Debug logging
    print(f"🔄 [Speaker Selection] Last: {last_speaker.name if last_speaker else 'None'}, Messages: {len(messages)}")

    if not messages:
        return orchestrator

    last_msg = messages[-1]
    content = last_msg.get("content", "").strip().upper()
    speaker_name = last_speaker.name if last_speaker else None
    
    print(f"   Content preview: {content[:50]}...")

    # 1. BOSHLANG'ICH: UserProxy → Orchestrator
    if speaker_name == "UserProxy" and len(messages) == 1:
        print("   → Orchestrator")
        return orchestrator

    # 2. ORCHESTRATOR QAROR QABUL QILDI
    if speaker_name == "Orchestrator":
        if "SOCIAL" in content:
            print("   → SocialBot")
            return social_bot
        elif "KNOWLEDGE" in content:
            print("   → KnowledgeBot")
            return knowledge_bot
        elif "CLASSIFIER" in content:
            print("   → Classifier")
            return classifier
        print("   → None (Orchestrator unclear)")
        return None

    # 3. CLASSIFIER TASNIFI
    if speaker_name == "Classifier":
        if "KNOWLEDGE" in content:
            print("   → KnowledgeBot")
            return knowledge_bot
        elif "LEGAL" in content:
            print("   → LegalSearcher")
            return legal_searcher
        print("   → None (Classifier unclear)")
        return None

    # 4. SOCIAL BOT JAVOB BERDI
    if speaker_name == "SocialBot":
        # SocialBot should always terminate after responding
        # Auto-append TERMINATE if not present to ensure termination
        if last_msg.get("content"):
            content_raw = last_msg.get("content", "")
            if "TERMINATE" not in content_raw:
                # Append TERMINATE to the message
                last_msg["content"] = content_raw + "\n\nTERMINATE"
                content = last_msg["content"].strip().upper()  # Update content variable
                print("   ⚠️ Auto-appended TERMINATE to SocialBot response")
        
        # Check if TERMINATE is in the message
        if "TERMINATE" in content:
            print("   → None (SocialBot terminated)")
            return None
        print("   → ResponseFormatter")
        return response_formatter

    # 5. KNOWLEDGE BOT QIDIRUV QILMOQDA
    if speaker_name == "KnowledgeBot":
        # Agar tool chaqiruvchi bo'lsa
        if last_msg.get("tool_calls") or last_msg.get("function_call"):
            print("   → UserProxy (tool execution)")
            return user_proxy  # Tool bajarish uchun
        # Tool natijasi kelganidan keyin
        print("   → ResponseFormatter")
        return response_formatter

    # 6. LEGAL SEARCHER QIDIRUV QILMOQDA
    if speaker_name == "LegalSearcher":
        if last_msg.get("tool_calls") or last_msg.get("function_call"):
            print("   → UserProxy (tool execution)")
            return user_proxy
        print("   → LegalAnalyzer")
        return legal_analyzer

    # 7. USER PROXY TOOL BAJARIBDI
    if speaker_name == "UserProxy" and len(messages) > 1:
        prev_speaker = messages[-2].get("name")
        if prev_speaker == "LegalSearcher":
            print("   → LegalAnalyzer")
            return legal_analyzer
        elif prev_speaker == "KnowledgeBot":
            print("   → KnowledgeBot")
            return knowledge_bot  # KnowledgeBot o'zi javob beradi

    # 8. LEGAL ANALYZER TAHLIL QILDI
    if speaker_name == "LegalAnalyzer":
        print("   → ResponseFormatter")
        return response_formatter

    # 9. RESPONSE FORMATTER YAKUNLADI
    if speaker_name == "ResponseFormatter":
        print("   → None (conversation ended)")
        return None

    print(f"   → None (no match for {speaker_name})")
    return None


# ==============================================================================
# GROUP CHAT VA MANAGER
# ==============================================================================
groupchat = autogen.GroupChat(
    agents=[
        user_proxy,
        orchestrator,
        classifier,
        social_bot,
        knowledge_bot,
        legal_searcher,
        legal_analyzer,
        response_formatter
    ],
    messages=[],
    max_round=20,
    speaker_selection_method=intelligent_speaker_selection
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config={"config_list": config_list}
)

# ==============================================================================
# TESTING
# ==============================================================================
if __name__ == "__main__":
    print("🧪 Agent tizimi test rejimida ishga tushdi")
    print("Barcha agentlar:")
    for agent in groupchat.agents:
        print(f"  ✓ {agent.name}")

    print("\n📦 JSON qidiruv tizimi:")
    if os.path.exists(STRUCTURED_FOLDER):
        files = os.listdir(STRUCTURED_FOLDER)
        print(f"  ✅ {len(files)} ta JSON fayl topildi")
    else:
        print(f"  ⚠️ {STRUCTURED_FOLDER} papkasi yo'q. Scraper'ni ishga tushiring!")