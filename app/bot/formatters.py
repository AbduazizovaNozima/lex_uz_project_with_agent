import re

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
    return text[: max_len - 4] + r"\.\.\."
