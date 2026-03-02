import re
import logging

logger = logging.getLogger(__name__)

_ESCAPE_RE = re.compile(r"([\\\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])")


def escape_md(text: str) -> str:
    return _ESCAPE_RE.sub(r"\\\1", text)


def format_legal_response(text: str) -> str:
    safe = escape_md(text)
    safe = re.sub(
        r"(\d+\\[-–]\s*(?:modda|bob|qism|band|paragraf))",
        lambda m: f"*{m.group(1)}*",
        safe,
        flags=re.IGNORECASE,
    )
    safe = re.sub(
        r"^(📄[^\n:]+:)",
        lambda m: f"*{m.group(1)}*",
        safe,
        flags=re.MULTILINE,
    )
    return safe


def truncate_for_telegram(text: str, max_len: int = 4000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 4] + r"\.\.\."


def make_lex_deeplink(doc_name: str) -> str:
    from app.core.constants import LAWS_TO_SCRAPE
    url = LAWS_TO_SCRAPE.get(doc_name)
    if not url:
        return ""
    display = escape_md(doc_name.replace("_", " "))
    safe_url = url.replace(")", "\\)")
    return f"[{display}]({safe_url})"
