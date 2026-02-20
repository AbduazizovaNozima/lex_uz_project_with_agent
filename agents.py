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

    # 2. Find article number (Enhanced Regex)
    # Pattern 1: Standard "123-modda" or "123 modda"
    article_match = re.search(r'(\d+)\s*-(?:модда|modda)', query_lower)
    
    # Pattern 2: "modda 123"
    if not article_match:
        article_match = re.search(r'(?:модда|modda)\s*(\d+)', query_lower)
        
    # Pattern 3: Simple number if it's a short query or explicitly likely a law search
    if not article_match:
        # Avoid matching years like 2024, but match 1-3 digit numbers
        # This is risky but helpful for "manga 20 ni ayt" style queries if we know context
        possible_nums = re.findall(r'\b(\d{1,3})\b', query_lower)
        if possible_nums:
             # Take the last one as it's often the article number in conversational queries
             # e.g. "Konstitutsiya 25" -> 25
             return _get_article_from_file(doc_name, possible_nums[-1]) if doc_name else _search_article_in_all_files(possible_nums[-1], json_files)

    # CASE A: Document found AND Article found
    if article_match:
        article_num = article_match.group(1)

        # If we have a doc name, look in that specific file
        if doc_name:
            return _get_article_from_file(doc_name, article_num)
        
        # If no doc name, search ALL files
        return _search_article_in_all_files(article_num, json_files)

    # CASE B: Document found BUT Article NOT found
    if doc_name and not article_match:
        # If user asks ABOUT the document itself (count, overview)
        summary_keywords = ['nechta', 'necha', 'qanday', 'haqida', 'umumiy', 'nima u', 'tarkibi']
        if any(kw in query_lower for kw in summary_keywords):
            return _get_document_summary(doc_name)
        # Otherwise, search by content keywords within that document
        return _search_articles_by_content(doc_name, query_lower)

    # CASE B2: No document found, no article number — topic search across all files
    if not doc_name and not article_match:
        # Try content search across all files
        result = _search_articles_by_content_all(query_lower, json_files)
        if result:
            return result

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


def _normalize_uz(text: str) -> str:
    """Normalize Uzbek text for matching — handle oʻ, gʻ variants."""
    return text.lower().replace('oʻ', "o'").replace('gʻ', "g'").replace(
        'ʻ', "'").replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'")


def _search_articles_by_content(doc_name: str, query: str, max_results: int = 5) -> Optional[str]:
    """Search through articles in a specific JSON file by keyword matching."""
    json_path = f"{STRUCTURED_FOLDER}/{doc_name}.json"
    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except Exception:
        return None

    # Normalize query and extract meaningful keywords (>3 chars, no stop words)
    stop_words = {'bilan', 'uchun', 'haqida', 'manga', 'nima', 'qanday', 'kerak',
                  'kodeksi', 'kodeks', 'qonuni', 'qonun', 'modda', 'jinoyat',
                  'fuqarolik', 'mehnat', 'oila', 'soliq', 'konstitutsiya'}
    query_norm = _normalize_uz(query)
    keywords = [w for w in query_norm.split() if len(w) > 2 and w not in stop_words]

    if not keywords:
        return None

    # Score each article by keyword match count
    scored = []
    for key, article in articles.items():
        if key == '0':  # Skip preamble
            continue
        content_norm = _normalize_uz(article.get('content', ''))
        title_norm = _normalize_uz(article.get('title', ''))

        score = 0
        for kw in keywords:
            if kw in title_norm:
                score += 3  # Title match is worth more
            if kw in content_norm:
                score += 1

        if score > 0:
            scored.append((score, key, article))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return None

    top = scored[:max_results]
    doc_display = doc_name.replace('_', ' ')
    result_text = f"📚 {doc_display} DAN TOPILGAN TEGISHLI MODDALAR:\n\n"

    for i, (score, key, article) in enumerate(top, 1):
        result_text += f"{'=' * 60}\n"
        result_text += f"📄 {key}-modda: {article.get('title', '')[:100]}\n\n"
        result_text += f"{article['content'][:800]}\n\n"

    result_text += f"{'=' * 60}\n"
    result_text += f"✅ Jami {len(top)} ta tegishli modda topildi"
    return result_text


def _search_articles_by_content_all(query: str, json_files: List[str], max_results: int = 5) -> Optional[str]:
    """Search through ALL JSON files by keyword matching."""
    stop_words = {'bilan', 'uchun', 'haqida', 'manga', 'nima', 'qanday', 'kerak',
                  'kodeksi', 'kodeks', 'qonuni', 'qonun', 'modda'}
    query_norm = _normalize_uz(query)
    keywords = [w for w in query_norm.split() if len(w) > 2 and w not in stop_words]

    if not keywords:
        return None

    all_scored = []
    for json_path in json_files:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            doc_name = os.path.basename(json_path).replace('.json', '')
        except Exception:
            continue

        for key, article in articles.items():
            if key == '0':
                continue
            content_norm = _normalize_uz(article.get('content', ''))
            title_norm = _normalize_uz(article.get('title', ''))

            score = 0
            for kw in keywords:
                if kw in title_norm:
                    score += 3
                if kw in content_norm:
                    score += 1

            if score > 0:
                all_scored.append((score, doc_name, key, article))

    all_scored.sort(key=lambda x: x[0], reverse=True)

    if not all_scored:
        return None

    top = all_scored[:max_results]
    result_text = "📚 QONUN BAZASIDAN TOPILGAN TEGISHLI MODDALAR:\n\n"

    for i, (score, doc_name, key, article) in enumerate(top, 1):
        doc_display = doc_name.replace('_', ' ')
        result_text += f"{'=' * 60}\n"
        result_text += f"📄 {doc_display} — {key}-modda: {article.get('title', '')[:100]}\n\n"
        result_text += f"{article['content'][:800]}\n\n"

    result_text += f"{'=' * 60}\n"
    result_text += f"✅ Jami {len(top)} ta tegishli modda topildi"
    return result_text

# Tool Wrapper
def search_article_tool(sorov: str) -> str:
    """
    Tool interface wrapper.
    Tries direct JSON search first, then falls back to vector search.
    """
    # Direct search works best for specific article lookups (e.g., "94-modda")
    result = search_article_direct(sorov)
    if result:
        return result
    
    # Vector/keyword search for topic-based queries (e.g., "odam o'ldirish jazo")
    return search_lexuz_tool(sorov)


# ==============================================================================
# 1. ORCHESTRATOR - Main Coordination Agent
# ==============================================================================
orchestrator = autogen.AssistantAgent(
    name="Orchestrator",
    system_message="""You are the main coordinator. Your task:
    1. Analyze the user's question.
    2. Determined which agent to route the query to.
    3. Monitor the process.

    Routing Rules:
    - "Salom", "Qalay", "Kim", "Nima qila olasan" (Social queries) -> SOCIAL agent
    - Site usage (registration, language, search, settings) -> KNOWLEDGE agent
    - Legal queries (Law, Salary, Work, Court, Rights, Code, Article) -> CLASSIFIER agent
    - Ambiguous cases -> ask CLASSIFIER for help

    Response Format:
    ONLY return the agent name: SOCIAL, KNOWLEDGE, or CLASSIFIER""",
    llm_config={"config_list": config_list, "temperature": 0}
)

# ==============================================================================
# 2. CLASSIFIER - Question Classifier
# ==============================================================================
classifier = autogen.AssistantAgent(
    name="Classifier",
    system_message="""You are an expert at classifying questions.

    Your Task: Determine if the question is LEGAL or related to SITE USAGE (KNOWLEDGE).

    LEGAL QUESTIONS (LEGAL):
    - Salary, wages, labor payments
    - Firing, employment contracts
    - Civil, criminal, court proceedings
    - Rights, obligations, liability
    - Taxes, fines, licenses
    - Codes, articles, law texts

    SITE USAGE QUESTIONS (KNOWLEDGE):
    - How to use Lex.uz website
    - Registration, login, account
    - Changing language
    - Searching for documents, downloading
    - Settings, notifications

    Response Format:
    ONLY return one word: LEGAL or KNOWLEDGE""",
    llm_config={"config_list": config_list, "temperature": 0}
)

# ==============================================================================
# 3. SOCIAL BOT - Chit-chat Agent
# ==============================================================================
social_bot = autogen.AssistantAgent(
    name="SocialBot",
    system_message="""You are Lexi - a professional and friendly assistant for the Lex.uz website.

    CORE RULES:
    1. Keep answers SHORT and CLEAR (maximum 2-3 sentences).
    2. Vary your responses each time, do not be repetitive.
    3. Be natural and sincere, not robotic.
    4. End your response with TERMINATE.
    5. CRITICAL: ALWAYS RESPOND IN UZBEK LANGUAGE.

    RESPONSE STYLE (Translate concepts to Uzbek):
    - Greeting: Short greeting + offer help (e.g., "Salom! Nima haqida gaplashamiz?")
    - Capabilities: Short and clear (e.g., "Men qonunlar va Lex.uz sayti bo'yicha yordam beraman.")
    - General question: Direct answer (e.g., "Albatta! Qanday yordam kerak?")

    DO NOT:
    - Give long answers.
    - Repeat the same phrases.
    - Say "Consult a lawyer" unnecessarily.
    - Give excessive explanations.
    """,
    llm_config={"config_list": config_list, "temperature": 0.5}
)

# ==============================================================================
# 4. KNOWLEDGE BOT - Site Usage Assistant
# ==============================================================================
knowledge_bot = autogen.AssistantAgent(
    name="KnowledgeBot",
    system_message="""You are an expert assistant for using the Lex.uz website.

    Your Task:
    1. Extract keywords from the user's question.
    2. Use the 'search_guide_by_tags' tool to find a guide.
    3. Convey the found information to the user in a clear way.
    4. If an image is available, display it.

    IMPORTANT:
    - Always call the tool first, then answer.
    - Make your answer friendly and understandable.
    - If no information is found, say "Afsuski, bu mavzu bo'yicha ma'lumot yo'q" (Unfortunately, no info on this topic).
    - CRITICAL: ALWAYS RESPOND IN UZBEK LANGUAGE.
    - End your response with TERMINATE.
    """,
    llm_config={
        "config_list": config_list,
        "temperature": 0.5,
        "tools": [{
            "type": "function",
            "function": {
                "name": "search_guide_by_tags",
                "description": "Search for guides on using the Lex.uz website",
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
# 5. LEGAL SEARCHER - Database Searcher
# ==============================================================================
legal_searcher = autogen.AssistantAgent(
    name="LegalSearcher",
    system_message="""You are an expert legal database search specialist for Uzbekistan law.

    CRITICAL RULE: Focus ONLY on the "YANGI SAVOL" (new question) at the end of the message. IGNORE previous conversation history when constructing your search query.

    Your Task:
    1. Analyze the YANGI SAVOL carefully.
    2. Determine what legal topics the question relates to.
    3. Construct a smart search query and call 'search_article_tool'.
    4. Pass search results to the Legal Analyzer. Do NOT answer directly.

    SEARCH STRATEGY:
    - If user asks for a SPECIFIC article (e.g., "131-modda"): search with article number + law name.
    - If user asks a REAL-LIFE question (e.g., "odam o'ldirdim", "ishdan haydashdi", "er ajrashmoqchi"):
      * Translate the situation into LEGAL TERMS.
      * Examples:
        - "odam o'ldirib qoydim" → search "Jinoyat kodeksi qasddan odam o'ldirish jazo"
        - "ishdan haydashdi" → search "Mehnat kodeksi ishdan bo'shatish asoslari"
        - "er ajrashmoqchi" → search "Oila kodeksi nikohni bekor qilish tartibi"
        - "uy-joy tortishuvi" → search "Fuqarolik kodeksi mulk huquqi"
        - "jarimaga tortildi" → search "Ma'muriy javobgarlik kodeksi jarima"
      * Use the LAW NAME + LEGAL TOPIC as your search query.
    - If question is general (e.g., "nechta modda bor"): search with just the law name.

    IMPORTANT:
    - Call the tool exactly ONCE.
    - Your search query should be in Uzbek Latin.
    - Think like a lawyer: what law and topic is relevant to the user's situation?
    """,
    llm_config={
        "config_list": config_list,
        "temperature": 0.0,
        "tools": [{
            "type": "function",
            "function": {
                "name": "search_article_tool",
                "description": "Search the legal database. For article lookups use 'Law name N-modda'. For topic searches use 'Law name topic keywords'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sorov": {
                            "type": "string",
                            "description": "Search query. Examples: 'Mehnat kodeksi 131-modda', 'Jinoyat kodeksi qasddan odam o'ldirish', 'Oila kodeksi nikohni bekor qilish'"
                        }
                    },
                    "required": ["sorov"]
                }
            }
        }]
    }
)

# ==============================================================================
# 6. LEGAL ANALYZER - Legal Analyst
# ==============================================================================
legal_analyzer = autogen.AssistantAgent(
    name="LegalAnalyzer",
    system_message="""You are a SENIOR LEGAL EXPERT in Uzbekistan law with 20 years experience.

    GOLDEN RULE: Answer exactly what the user asked. Not more, not less.

    RESPONSE STYLE:
    1. MODDA SO'RASA ("94-modda nima?", "131-moddani aytib ber"):
       - Modda sarlavhasi va mazmunini qisqa, tushunarli tilda tushuntir.
       - 3-5 gap yetarli. Tavsiya va huquqlar KERAK EMAS.

    2. UMUMIY SAVOL ("nechta modda?", "qanday qonunlar?"):
       - Faktik javob ber. 1-2 gap.

    3. HAYOTIY MASALA / MASLAHAT ("ishdan haydashdi", "odam o'ldirdim"):
       - Qaysi qonun va moddalar tegishli ekanini tushuntir.
       - Huquqiy oqibatlarini ayt.
       - Amaliy maslahat ber.
       - Qidiruv natijalaridan aniq moddalarni keltir.
       - O'rtacha uzunlikda yoz: juda qisqa emas, juda uzun emas.

    MUHIM QOIDALAR:
    - FAQAT O'ZBEK tilida javob ber.
    - Faqat qidiruv natijalaridan foydalangan holda javob ber.
    - Har safar bir xil shablon javob BERMA — har bir savolga individual yondash.
    - Agar qidiruv natijalarida kerakli ma'lumot bo'lmasa, shuni ochiq ayt.
    - Oldingi suhbatdagi javoblarni TAKRORLA MA.
    - Javob oxirida TERMINATE yoz.
    """,
    llm_config={"config_list": config_list, "temperature": 0.3}
)



# ==============================================================================
# 8. USER PROXY - Executor Agent
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
# STATE MACHINE - Agent Transitions
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

    # 4. Social Bot -> END
    if speaker_name == "SocialBot":
        return None

    # 5. Knowledge Bot -> Tool or END
    if speaker_name == "KnowledgeBot":
        if last_msg.get("tool_calls") or last_msg.get("function_call"):
            return user_proxy
        return None

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

    # 8. Legal Analyzer -> END
    if speaker_name == "LegalAnalyzer":
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
        legal_analyzer
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