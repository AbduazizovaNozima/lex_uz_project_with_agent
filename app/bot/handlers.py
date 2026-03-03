import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode

from app.bot.formatters import format_legal_response, escape_md, truncate_for_telegram

logger = logging.getLogger(__name__)
router = Router()

_user_sessions: dict[int, str] = {}


def _get_services():
    from app.api.main import agent_service, session_svc
    return agent_service, session_svc


def _get_or_create_session(user_id: int) -> str:
    _, session_svc = _get_services()
    if user_id not in _user_sessions:
        sid = session_svc.create_session(user_id=str(user_id))
        _user_sessions[user_id] = sid
    return _user_sessions[user_id]


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    _, session_svc = _get_services()
    sid = session_svc.create_session(user_id=str(message.from_user.id))
    _user_sessions[message.from_user.id] = sid
    welcome = (
        "⚖️ *LexAI Professional* ga xush kelibsiz\\!\n\n"
        "Men O'zbekiston Respublikasi qonunchiligi bo'yicha "
        "ixtisoslashgan AI yordamchiman\\.\n\n"
        "*Nima qila olaman:*\n"
        "• 📚 Qonun va kodekslar bo'yicha ma'lumot berish\n"
        "• ⚖️ Modda talqini va huquqiy tahlil\n"
        "• 🔍 Lex\\.uz manbalaridan qidirish\n\n"
        "Savolingizni yozing\\! 👇"
    )
    await message.answer(welcome, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    help_text = (
        "📋 *Yordam*\n\n"
        "*Buyruqlar:*\n"
        "/start — Yangi suhbat boshlash\n"
        "/help — Yordam ko'rsatish\n"
        "/new — Yangi sessiya yaratish\n\n"
        "*Misol savollar:*\n"
        "• _Jinoyat kodeksining 168\\-moddasi nima deyadi?_\n"
        "• _Mehnat shartnomasi buzilsa, ish beruvchi javob beradimi?_\n\n"
        "Savolingizni oddiy matn sifatida yuboring\\."
    )
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(Command("new"))
async def cmd_new(message: Message) -> None:
    _, session_svc = _get_services()
    sid = session_svc.create_session(user_id=str(message.from_user.id))
    _user_sessions[message.from_user.id] = sid
    await message.answer(
        escape_md("✅ Yangi suhbat boshlandi. Savolingizni yozing."),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@router.message(F.text)
async def handle_message(message: Message) -> None:
    question = message.text.strip()
    if not question:
        return

    user_id = message.from_user.id
    agent_svc, session_svc = _get_services()
    sid = _get_or_create_session(user_id)
    history = session_svc.get_formatted_history(sid, limit=4)

    logger.info("bot | user=%d | sid=%.8s | question=%r", user_id, sid, question)

    waiting_msg = await message.answer("⏳", parse_mode=None)

    try:
        answer = await agent_svc.get_response(question, history)
    except Exception:
        logger.exception("bot | agent error | user=%d", user_id)
        answer = "Kechirasiz, texnik xato yuz berdi. Iltimos qayta urinib ko'ring."
    finally:
        try:
            await waiting_msg.delete()
        except Exception:
            pass

    session_svc.add_message(sid, "user", question)
    session_svc.add_message(sid, "assistant", answer)

    logger.info("bot | user=%d | response_len=%d", user_id, len(answer))

    formatted = truncate_for_telegram(format_legal_response(answer))
    try:
        await message.answer(formatted, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.warning("bot | MarkdownV2 failed — sending as plain text.", exc_info=True)
        await message.answer(answer[:4096], parse_mode=None)
