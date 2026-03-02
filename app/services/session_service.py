import uuid
import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.constants import SESSION_EXPIRY_HOURS, SESSION_HISTORY_LIMIT

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self) -> None:
        settings = get_settings()
        self._storage_dir = settings.SESSIONS_DIR
        os.makedirs(self._storage_dir, exist_ok=True)
        self._sessions: Dict[str, dict] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._load_active_sessions()

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    def create_session(self, user_id: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "messages": [],
        }
        self._save_session(session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        if session_id in self._sessions:
            return self._sessions[session_id]
        path = os.path.join(self._storage_dir, f"{session_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._sessions[session_id] = data
                return data
            except Exception as exc:
                logger.warning("get_session | load failed: %s", exc)
        return None

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        session["last_active"] = datetime.now().isoformat()
        self._save_session(session_id)
        return True

    def get_history(self, session_id: str, limit: int = SESSION_HISTORY_LIMIT) -> List[dict]:
        session = self.get_session(session_id)
        if not session:
            return []
        msgs = session["messages"]
        return msgs[-limit:] if limit else msgs

    def get_formatted_history(self, session_id: str, limit: int = 4) -> str:
        history = self.get_history(session_id, limit)
        if not history:
            return ""
        lines = ["SUHBAT TARIXI:"]
        for msg in history:
            role = "Foydalanuvchi" if msg["role"] == "user" else "Bot"
            content = msg["content"][:200] + ("…" if len(msg["content"]) > 200 else "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines) + "\n"

    def delete_session(self, session_id: str) -> bool:
        self._sessions.pop(session_id, None)
        self._locks.pop(session_id, None)
        path = os.path.join(self._storage_dir, f"{session_id}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as exc:
                logger.warning("delete_session | remove failed: %s", exc)
        return False

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        msgs = session["messages"]
        first_user = next((m for m in msgs if m["role"] == "user"), None)
        title = (first_user["content"][:50] + "…") if first_user else "Yangi Chat"
        return {
            "session_id": session_id,
            "title": title,
            "created_at": session["created_at"],
            "last_active": session["last_active"],
            "message_count": len(msgs),
        }

    def _save_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if not session:
            return
        path = os.path.join(self._storage_dir, f"{session_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error("_save_session | failed: %s", exc)

    def _load_active_sessions(self) -> None:
        cutoff = datetime.now() - timedelta(hours=SESSION_EXPIRY_HOURS)
        if not os.path.exists(self._storage_dir):
            return
        for filename in os.listdir(self._storage_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self._storage_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if datetime.fromisoformat(data["last_active"]) >= cutoff:
                    self._sessions[data["session_id"]] = data
            except Exception as exc:
                logger.warning("_load_active_sessions | skip %s: %s", filename, exc)


session_service = SessionService()
