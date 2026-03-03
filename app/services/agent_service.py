import logging

import autogen

from app.interfaces.agent_interface import AbstractAgentService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_LEGAL_KEYWORDS = (
    "qonun, modda, huquq, jazo, jinoyat, shartnoma, sud, "
    "konstitutsiya, kodeks, nizom, javobgarlik, huquqiy maslahat"
)

_SYSTEM_PROMPT = (
    "Siz O'zbekiston Respublikasi qonunchiligi bo'yicha "
    "20 yillik tajribaga ega professional huquqshunossiz."
)

_SOCIAL_SYSTEM_PROMPT = (
    "Siz LexAI — O'zbekiston Respublikasi qonunchiligi bo'yicha "
    "ixtisoslashgan professional huquqiy yordamchisiz.\n"
    "QOIDALAR:\n"
    "1. Birinchi murojaat bo'lsa: qisqacha salom bering va o'zingizni tanishtiring.\n"
    "2. Keyingi murojaatlarda 'Salom' YOZMANG, to'g'ri javob bering.\n"
    "3. Foydalanuvchini huquqiy savol berishga yo'naltiring.\n"
    "4. Qisqa va aniq javob bering."
)

_GENERAL_RULES = (
    "UMUMIY QOIDALAR:\n"
    "• 'Salom', 'Albatta', 'Rahmat', 'Keling ko'rib chiqaylik' kabi so'zlar YOZMANG\n"
    "• Faqat savol uchun zarur bo'lgan moddalarni keltiring, barchani emas\n"
    "• Javobni o'zbek tilida, aniq va professional tarzda bering\n"
    "• Keraksiz takrorlardan saqlaning"
)


class AgentService(AbstractAgentService):
    def __init__(self, db_repository=None) -> None:
        self._settings = get_settings()
        self._db_repo = db_repository
        self._client = autogen.OpenAIWrapper(
            config_list=[
                {
                    "model": self._settings.OPENAI_MODEL,
                    "api_key": self._settings.OPENAI_API_KEY,
                }
            ]
        )

    def classify_intent(self, question: str) -> str:
        prompt = (
            f'Savol: "{question}"\n\n'
            "Quyidagi kategoriyalardan FAQAT BITTASINI qaytaring:\n"
            f"SOCIAL  — salomlashish, tanishish yoki bot haqida savol\n"
            f"LEGAL   — {_LEGAL_KEYWORDS}\n"
            "UNKNOWN — boshqa barcha mavzular (ob-havo, tarix, sport, ovqat va h.k.)\n\n"
            "Faqat bitta so'z: SOCIAL, LEGAL yoki UNKNOWN"
        )
        try:
            res = self._client.create(messages=[{"role": "user", "content": prompt}])
            intent = res.choices[0].message.content.strip().upper()
            result = intent if intent in {"SOCIAL", "LEGAL", "UNKNOWN"} else "LEGAL"
            logger.info("classify_intent | intent=%s", result)
            return result
        except Exception:
            logger.warning("classify_intent failed — defaulting to LEGAL.", exc_info=True)
            return "LEGAL"

    async def get_response(self, question: str, history: str) -> str:
        intent = self.classify_intent(question)
        if intent == "UNKNOWN":
            return (
                "Men faqat O'zbekiston Respublikasi qonunchiligi bo'yicha "
                "huquqiy savollarga javob bera olaman. "
                "Iltimos, huquqiy mavzuda savol bering."
            )
        if intent == "SOCIAL":
            return self._handle_social(question, history)
        return await self._run_legal_pipeline(question, history)

    def _rewrite_query(self, question: str, history: str) -> str:
        if not history or len(question.split()) > 7:
            return question
        prompt = (
            f"Suhbat tarixi:\n{history}\n\n"
            f'Oxirgi savol: "{question}"\n\n'
            "QOIDA: Agar savol qisqa anafora bo'lsa ('Jazosi?', 'Nima deyilgan?', 'Unda?'), "
            "uni tarixdagi oxirgi mavzuga ulab to'liq qidiruv so'roviga aylantir. "
            "Agar savol mustaqil bo'lsa — aynan o'zini qaytargin. "
            "Faqat savol matnini qaytargin."
        )
        try:
            res = self._client.create(messages=[{"role": "user", "content": prompt}])
            rewritten = res.choices[0].message.content.strip().strip('"')
            if 5 <= len(rewritten) <= 400:
                return rewritten
        except Exception:
            logger.warning("_rewrite_query failed — using original.", exc_info=True)
        return question

    def _search_db(self, query: str) -> str:
        if self._db_repo:
            return self._db_repo.format_search_results(query)
        from database import search_lexuz_tool
        return search_lexuz_tool(query) or ""

    def _handle_social(self, question: str, history: str) -> str:
        messages = [{"role": "system", "content": _SOCIAL_SYSTEM_PROMPT}]
        if history:
            messages.append({"role": "assistant", "content": f"Oldingi suhbat:\n{history}"})
        messages.append({"role": "user", "content": question})
        try:
            res = self._client.create(messages=messages)
            return res.choices[0].message.content.strip()
        except Exception:
            logger.error("_handle_social failed.", exc_info=True)
            return "Salom! Men LexAI — huquqiy yordamchiman. Huquqiy savolingizni bering."

    def _synthesize_answer(self, query: str, raw_results: str) -> str:
        has_results = bool(raw_results and "TASDIQLANGAN MANBALAR" in raw_results)

        if has_results:
            task_instruction = (
                "Yuqoridagi TASDIQLANGAN MANBALAR asosida professional huquqiy javob bering.\n\n"
                "JAVOB FORMATI QO'YDALAR:\n"
                "1. Agar manba muayyan moddaga to'g'ridan-to'g'ri ishora qilsa:\n"
                "   [Qonun nomi] — [Modda №] — [Qisqa mazmun] — [Jazo/oqibat]\n"
                "2. Agar savol tushuntirish yoki tahlil talab qilsa:\n"
                "   Moddalarni sanab o'tirmay, ANIQ va TUSHUNARLI izohlab bering.\n"
                "3. Faqat manbalardagi ma'lumotdan foydalaning.\n"
                "4. Bir savolga bir nechta aloqasiz moddalarni tiqishtirmang."
            )
            sources_block = f"Topilgan manbalar:\n{raw_results}"
        else:
            task_instruction = (
                "Bazada aniq ma'lumot topilmadi. "
                "O'zbekiston qonunchiligi bo'yicha UMUMIY bilimingizdan "
                "qisqa va aniq javob bering. "
                "Javob oxirida: 'Aniq huquqiy maslahat uchun "
                "malakali huquqshunos bilan bog'laning.' qo'shing."
            )
            sources_block = "Bazada natija topilmadi."

        prompt = (
            f'Foydalanuvchi savoli: "{query}"\n\n'
            f"{sources_block}\n\n"
            f"{task_instruction}\n\n"
            f"{_GENERAL_RULES}"
        )
        try:
            res = self._client.create(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            return res.choices[0].message.content.strip()
        except Exception:
            logger.error("_synthesize_answer failed.", exc_info=True)
            return "Texnik xato yuz berdi. Iltimos qayta urinib ko'ring."

    async def _run_legal_pipeline(self, question: str, history: str) -> str:
        query = self._rewrite_query(question, history)
        logger.info("legal_pipeline | query=%r", query[:80])
        raw = self._search_db(query)
        logger.info("legal_pipeline | db_hit=%s", bool(raw and "TASDIQLANGAN MANBALAR" in raw))
        return self._synthesize_answer(query, raw)
