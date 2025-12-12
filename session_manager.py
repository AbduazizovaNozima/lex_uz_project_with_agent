"""
Session Management for Multi-User Support
Handles user sessions, conversation history, and concurrent requests
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class SessionManager:
    """Manages user sessions and conversation history"""
    
    def __init__(self, storage_dir="sessions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.sessions: Dict[str, dict] = {}
        self.load_active_sessions()
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "messages": [],
            "metadata": {}
        }
        
        self.sessions[session_id] = session_data
        self.save_session(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try loading from disk
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    self.sessions[session_id] = session_data
                    return session_data
            except:
                pass
        
        return None
    
    def add_message(self, session_id: str, role: str, content: str, agent_path: List[str] = None, image_path: str = None):
        """Add message to session history"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent_path": agent_path or [],
            "image_path": image_path
        }
        
        session["messages"].append(message)
        session["last_active"] = datetime.now().isoformat()
        
        # Save asynchronously to avoid blocking
        try:
            self.save_session(session_id)
        except:
            pass  # Don't block if save fails
        
        return True
    
    def get_history(self, session_id: str, limit: int = 10) -> List[dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session["messages"]
        return messages[-limit:] if limit else messages
    
    def get_formatted_history(self, session_id: str, limit: int = 10) -> str:
        """
        Get formatted history for agent context
        Returns a string formatted for agent consumption
        """
        history = self.get_history(session_id, limit)
        if not history:
            return ""
        
        formatted = "SUHBAT TARIXI:\\n"
        for msg in history:
            role = "Foydalanuvchi" if msg["role"] == "user" else "Bot"
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            formatted += f"{role}: {content}\\n"
        
        return formatted + "\\n"
    
    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """
        Get session summary (title, last message, etc.)
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        messages = session["messages"]
        
        # Generate title from first user message
        title = "Yangi Chat"
        if messages:
            first_user_msg = next((m for m in messages if m["role"] == "user"), None)
            if first_user_msg:
                title = first_user_msg["content"][:50] + ("..." if len(first_user_msg["content"]) > 50 else "")
        
        # Get last message
        last_message = messages[-1] if messages else None
        
        return {
            "session_id": session_id,
            "title": title,
            "created_at": session["created_at"],
            "last_active": session["last_active"],
            "message_count": len(messages),
            "last_message": last_message["content"][:100] if last_message else None
        }
    
    def update_session_metadata(self, session_id: str, metadata: dict):
        """Update session metadata"""
        session = self.get_session(session_id)
        if session:
            session["metadata"].update(metadata)
            self.save_session(session_id)
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except:
                pass
            return True
        
        return False
    
    def list_user_sessions(self, user_id: str) -> List[dict]:
        """List all sessions for a user (only non-empty ones)"""
        user_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.get("user_id") == user_id:
                # Faqat xabari bor sessionlarni ko'rsatish
                if not session.get("messages"):
                    continue
                    
                summary = self.get_session_summary(session_id)
                if summary:
                    user_sessions.append(summary)
        
        # Sort by last_active (newest first)
        user_sessions.sort(key=lambda x: x["last_active"], reverse=True)
        
        return user_sessions
    
    def cleanup_empty_sessions(self):
        """Remove sessions with no messages"""
        sessions_to_delete = []
        
        for session_id, session in self.sessions.items():
            if not session.get("messages"):
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            self.delete_session(session_id)
            
        return len(sessions_to_delete)
    
    def cleanup_old_sessions(self, hours: int = 24):
        """Remove sessions older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        sessions_to_delete = []
        
        for session_id, session in self.sessions.items():
            try:
                last_active = datetime.fromisoformat(session["last_active"])
                if last_active < cutoff_time:
                    sessions_to_delete.append(session_id)
            except:
                pass
        
        for session_id in sessions_to_delete:
            self.delete_session(session_id)
        
        return len(sessions_to_delete)
    
    def save_session(self, session_id: str):
        """Save session to disk"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def load_active_sessions(self):
        """Load recent sessions from disk"""
        if not os.path.exists(self.storage_dir):
            return
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                session_file = os.path.join(self.storage_dir, filename)
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    last_active = datetime.fromisoformat(session_data["last_active"])
                    if last_active >= cutoff_time:
                        session_id = session_data["session_id"]
                        self.sessions[session_id] = session_data
                except Exception as e:
                    print(f"Error loading session {filename}: {e}")


# Global session manager instance
session_manager = SessionManager()
