import os
import json
import re
import glob
import autogen
from database import search_lexuz_tool
from knowledge_base import search_guide_by_tags
from typing import Dict, List, Optional, Union, Any

# ==============================================================================
# CONFIGURATION
# ==============================================================================
STRUCTURED_FOLDER = "lex_structured"

# API Key Handling
raw_api_key = os.getenv("OPENAI_API_KEY", "")
api_key = raw_api_key.strip().strip('"').strip("'")
if not api_key:
    raise ValueError("⚠️ OPENAI_API_KEY topilmadi!")

config_list = [{"model": "gpt-4o-mini", "api_key": api_key}]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def search_article_direct(query: str) -> Optional[str]:
    """
    Search for a specific article in the JSON files directly.
    
    Examples:
    - "Konstitutsiya 80-modda"
    - "Mehnat kodeksi 131-modda"
    - "80-modda prezident"
    """
    # 1. Map document names
    json_files = glob.glob(f"{STRUCTURED_FOLDER}/*.json")
    doc_mapping: Dict[str, str] = {}

    for jf in json_files:
        basename = os.path.basename(jf).replace(".json", "")
        clean_name = basename.lower().replace("_", " ")
        
        # 1. Full name
        doc_mapping[clean_name] = basename
        
        # 2. First word (if long enough)
        parts = clean_name.split()
        if parts and len(parts[0]) > 3:
            doc_mapping[parts[0]] = basename
            
        # 3. Variations
        if "kodeks" in clean_name:
            doc_mapping[clean_name.replace(" kodeksi", "")] = basename
        if "qonun" in clean_name:
            doc_mapping[clean_name.replace(" qonuni", "")] = basename

    manual_aliases = {
        "konstitutsiya": "Konstitutsiya",
        "mamuriy": "Ma'muriy_Javobgarlik_Kodeksi",
        "ma'muriy": "Ma'muriy_Javobgarlik_Kodeksi",
        "cyber": "Kiberxavfsizlik_Qonuni"
    }
    doc_mapping.update(manual_aliases)

    query_lower = query.lower()
    doc_name: Optional[str] = None

    # Find document match (longest match first)
    sorted_keys = sorted(doc_mapping.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in query_lower:
            doc_name = doc_mapping[key]
            break

    # 2. Find article number
    article_match = re.search(r'(\d+)-(?:модда|modda)', query_lower)
    if not article_match:
        article_match = re.search(r'(?:модда|modda)\s*(\d+)', query_lower)
    if not article_match:
        article_match = re.search(r'(\d+)', query_lower)

    # CASE A: Document found AND Article found
    if article_match:
        article_num = article_match.group(1)

        # If we have a doc name, look in that specific file
        if doc_name:
            return _get_article_from_file(doc_name, article_num)
        
        # If no doc name, search ALL files
        return _search_article_in_all_files(article_num, json_files)

    # CASE B: Document found BUT Article NOT found -> Return Summary
    if doc_name and not article_match:
        return _get_document_summary(doc_name)

    # CASE C: Neither found -> List available laws
    if json_files:
        law_names = sorted([
            os.path.basename(f).replace(".json", "").replace("_", " ")
            for f in json_files
        ])
        law_list = "\n".join([f"  {i+1}. {name}" for i, name in enumerate(law_names)])
        return f"""📚 LEX.UZ BAZASIDAGI QONUNLAR RO'YXATI:

{law_list}

💡 Aniq ma'lumot olish uchun qonun nomi va modda raqamini ko'rsating.
   Masalan: "Mehnat kodeksi 131-modda" yoki "Konstitutsiya 1-modda"
"""
    return None

def _get_article_from_file(doc_name: str, article_num: str) -> Optional[str]:
    """Helper to read a specific article from a specific JSON file."""
    json_path = f"{STRUCTURED_FOLDER}/{doc_name}.json"
    if not os.path.exists(json_path):
         return f"❌ {doc_name}.json fayli topilmadi."

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        if article_num in articles:
            article = articles[article_num]
            return f"""📚 QONUN BAZASIDAN TOPILGAN ANIQ MODDA:

============================================================
📄 Hujjat: {doc_name.replace('_', ' ')}
🎯 Modda: {article_num}
📌 Sarlavha: {article['title']}

MAZMUNI:
{article['content']}

============================================================
✅ Ma'lumot to'liq va rasmiy manba asosida"""
        return None
    except Exception as e:
        return f"❌ Xato: {str(e)}"

def _search_article_in_all_files(article_num: str, json_files: List[str]) -> Optional[str]:
    """Helper to search for an article number across all JSON files."""
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
        result_text = f"📚 {article_num}-MODDA QUYIDAGI HUJJATLARDA TOPILDI:\n\n"
        for i, res in enumerate(results, 1):
            result_text += f"{'=' * 60}\n"
            result_text += f"📄 {i}. {res['doc'].replace('_', ' ')}\n"
            result_text += f"📌 {res['article']['title']}\n\n"
            result_text += f"{res['article']['content']}\n\n"
        result_text += f"{'=' * 60}\n"
        result_text += f"✅ Jami {len(results)} ta hujjatda topildi"
        return result_text
    
    return None

def _get_document_summary(doc_name: str) -> str:
    """Helper to return a summary of a document."""
    json_path = f"{STRUCTURED_FOLDER}/{doc_name}.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            total_articles = len(articles)
            
            # Validation: Check if it's potentially a bad parse (few articles but huge text)
            if total_articles < 4:
                full_content = "".join([a.get("content", "") for a in articles.values()])
                if len(full_content) < 3000: 
                    return None

            first_articles = sorted(articles.keys(), key=lambda x: int(x) if x.isdigit() else 999)[:5]
            
            return f"""📚 {doc_name.replace('_', ' ')} HAQIDA UMUMIY MA'LUMOT:


============================================================
📄 Hujjat: {doc_name.replace('_', ' ')}
📊 Jami bo'limlar/moddalar: {total_articles}
📌 Dastlabki qismlar: {', '.join(first_articles)}...

💡 Aniq modda haqida ma'lumot olish uchun modda raqamini ko'rsating.
   Masalan: "{doc_name.replace('_', ' ')} 1-modda"

============================================================
✅ Ma'lumot rasmiy manba asosida"""
        except Exception as e:
            return f"❌ Xato: {str(e)}"
    return None


# Tool Wrapper
def search_article_tool(sorov: str) -> str:
    """
    Tool interface wrapper.
    Tries direct JSON search first, then falls back to vector search.
    """
    result = search_article_direct(sorov)
    if result:
        return result
    else:
        # Fallback to vector/keyword search in DB
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
    llm_config={"config_list": config_list, "temperature": 0.5}
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
        "temperature": 0.0,
        "tools": [{
            "type": "function",
            "function": {
                "name": "search_article_tool",
                "description": "Qonun bazasidan qidirish (JSON va embeddings)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sorov": {
                            "type": "string",
                            "description": "Qidiruv so'rovi (masalan: 'Mehnat kodeksi 131-modda' yoki 'ta'til muddati')"
                        }
                    },
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

    Vazifang: Legal Searcher topgan qonun matnlarini tahlil qilib, foydalanuvchi savoliga javob berish.

    QOIDALAR:
    1. Faqat berilgan qonun matniga asoslan (MATNDA YO'Q NARSA HAQIDA GAPIRMA)
    2. Javob formatini saqla:
       - Mavzu (bold)
       - Javob (aniq va lo'nda)
       - Asos (Qonun nomi va Modda raqami)
    3. Agar topilgan matn savolga javob bermasa, "Berilgan ma'lumotlar asosida javob bera olmayman" de.
    4. Javobingni O'zbek tilida, professional va xatolarsiz yoz.
    """,
    llm_config={"config_list": config_list, "temperature": 0.3}
)

# ==============================================================================
# 7. RESPONSE FORMATTER - Javob Formatlash Agenti
# ==============================================================================
response_formatter = autogen.AssistantAgent(
    name="ResponseFormatter",
    system_message="""Sen javoblarni yakuniy formatlovchisan.

    Vazifang:
    1. Boshqa agentlar (ayniqsa LegalAnalyzer) bergan javobni o'qib chiq.
    2. Agar javobda texnik belgilar, tool chaqiruvlari yoki ortiqcha takrorlashlar bo'lsa, tozalab tashla.
    3. Javobni chiroyli Markdown formatiga keltir.
    4. Eng oxirida TERMINATE deb yoz.

    AGAR RASM BO'LSA:
    - Rasm linkini saqlab qol (📷 Rasm: ...)
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

# Tool Registration
user_proxy.register_function(function_map={
    "search_article_tool": search_article_tool,
    "search_guide_by_tags": search_guide_by_tags
})


# ==============================================================================
# STATE MACHINE - Holatlar Mashinasi
# ==============================================================================
def intelligent_speaker_selection(last_speaker: autogen.Agent, groupchat: autogen.GroupChat) -> Optional[autogen.Agent]:
    """
    State machine for agent transitions.
    Defines who speaks next based on the last speaker and message content.
    """
    messages = groupchat.messages

    if not messages:
        return orchestrator

    last_msg = messages[-1]
    content = last_msg.get("content", "").strip().upper()
    speaker_name = last_speaker.name if last_speaker else None

    # 1. Start: UserProxy -> Orchestrator
    if speaker_name == "UserProxy" and len(messages) == 1:
        return orchestrator

    # 2. Orchestrator Decision
    if speaker_name == "Orchestrator":
        if "SOCIAL" in content:
            return social_bot
        elif "CLASSIFIER" in content:
            return classifier
        return classifier  # Default to classifier for safety

    # 3. Classifier Decision
    if speaker_name == "Classifier":
        if "KNOWLEDGE" in content:
            return knowledge_bot
        elif "LEGAL" in content:
            return legal_searcher
        return legal_searcher # Default to legal

    # 4. Social Bot -> Formatter
    if speaker_name == "SocialBot":
        return response_formatter

    # 5. Knowledge Bot -> Formatter
    if speaker_name == "KnowledgeBot":
        # Check if tool was called
        if last_msg.get("tool_calls") or last_msg.get("function_call"):
            return user_proxy
        return response_formatter

    # 6. Legal Searcher -> Tool or Analyzer
    if speaker_name == "LegalSearcher":
        if last_msg.get("tool_calls") or last_msg.get("function_call"):
            return user_proxy
        return legal_analyzer

    # 7. User Proxy (Tool Executor)
    if speaker_name == "UserProxy" and len(messages) > 1:
        prev_speaker = messages[-2].get("name")
        if prev_speaker == "LegalSearcher":
            return legal_analyzer
        if prev_speaker == "KnowledgeBot":
            return knowledge_bot # Return to KnowledgeBot to formulate answer

    # 8. Legal Analyzer -> Formatter
    if speaker_name == "LegalAnalyzer":
        return response_formatter

    # 9. Response Formatter -> END
    if speaker_name == "ResponseFormatter":
        return None

    return None


# ==============================================================================
# GROUP CHAT MANAGER
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

if __name__ == "__main__":
    print("🧪 Agent System Test Mode")
    print("Agents loaded:", [agent.name for agent in groupchat.agents])