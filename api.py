import os
import re
import asyncio
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Any, Set

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Project modules
from agents import user_proxy, manager, groupchat
from session_manager import session_manager

# ==============================================================================
# 1. APP CONFIGURATION
# ==============================================================================
app = FastAPI(
    title="Lex.uz AI Assistant",
    description="O'zbekiston qonunchilik yordamchisi API",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STATIC FILES
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")


# ==============================================================================
# 2. DATA MODELS
# ==============================================================================
class ChatRequest(BaseModel):
    question: str
    history: List[Dict[str, str]] = []
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    agent_path: List[str] = []
    message_count: int = 0
    image_path: Optional[str] = None
    session_id: Optional[str] = None


# ==============================================================================
# 3. STARTUP EVENTS
# ==============================================================================
@app.on_event("startup")
async def startup_event() -> None:
    """Operations to run when server starts."""
    print("🧹 Cleaning up empty sessions...")
    count = session_manager.cleanup_empty_sessions()
    print(f"✅ Removed {count} empty sessions")
    
    os.makedirs("logs", exist_ok=True)


# ==============================================================================
# 4. CHAT ENDPOINT
# ==============================================================================
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """
    Main chat interaction endpoint.
    Manages session context, invokes agents, and processes the final response.
    """
    print(f"\n{'=' * 70}")
    print(f"📩 NEW QUESTION: {req.question}")
    
    # 1. Session Management
    session_id = req.session_id
    if not session_id:
        session_id = session_manager.create_session()
        print(f"✨ New session created: {session_id}")
    else:
        if not session_manager.get_session(session_id):
            print(f"⚠️ Session not found, creating new one...")
            session_id = session_manager.create_session()
        else:
            print(f"🎫 Session ID: {session_id}")

    session_manager.add_message(session_id, "user", req.question)

    # 2. Reset Agents
    print("🔄 Resetting agents...")
    groupchat.reset()
    user_proxy.reset()
    manager.reset()

    # 3. Prepare Context
    context = session_manager.get_formatted_history(session_id, limit=10)
    
    # Context Injection Logic
    known_laws = [
        "Konstitutsiya", "Mehnat Kodeksi", "Jinoyat Kodeksi", "Fuqarolik Kodeksi",
        "Oila Kodeksi", "Soliq Kodeksi", "Ma'muriy Javobgarlik Kodeksi",
        "Saylov Kodeksi", "Yer Kodeksi", "Suv Kodeksi", "Uy Joy Kodeksi",
        "Kiberxavfsizlik Qonuni", "Axborotlashtirish Qonuni", "Ta'lim Qonuni"
    ]
    
    context_law: Optional[str] = None
    chat_history = session_manager.get_history(session_id)
    if chat_history:
        for msg in reversed(chat_history[-3:]):
            content = msg.get("content", "")
            for law in known_laws:
                if law.lower() in content.lower():
                    context_law = law
                    break
            if context_law:
                break
    
    final_query = req.question
    if context_law and len(req.question.split()) < 5 and context_law.lower() not in req.question.lower():
        print(f"🔍 [Context] Detected: {context_law}. Injecting into query...")
        final_query = f"{context_law} {req.question}"
        full_message = f"{context}YANGI SAVOL (Kontekst: {context_law}): {req.question}"
    else:
        full_message = f"{context}YANGI SAVOL: {req.question}"

    print(f"📝 Text to agent: {full_message[:100]}...")

    # 4. Agent Execution (with Timeout)
    try:
        print("⏳ Chat started (30s timeout)...")
        await asyncio.wait_for(
            user_proxy.a_initiate_chat(
                manager,
                message=full_message
            ),
            timeout=30.0
        )
        print("✅ Chat completed successfully")
    
    except asyncio.TimeoutError:
        print("⏱️ Timeout: Response took too long")
        error_resp = "Kechirasiz, javob tayyorlash juda uzoq vaqt oldi. Iltimos, savolni qisqaroq qilib qayta bering."
        session_manager.add_message(session_id, "assistant", error_resp)
        return ChatResponse(
            response=error_resp,
            agent_path=["Timeout"],
            session_id=session_id
        )
    except Exception as e:
        error_str = str(e)
        if "returned None" in error_str or "speaker_selection" in error_str:
            print("✅ Chat finished (Agent stopped)")
        else:
            print(f"❌ Error occurred: {error_str}")
            with open("logs/api_errors.log", "a") as f:
                f.write(f"\n{datetime.now()} | {session_id} | {req.question} | {error_str}\n")
                f.write(traceback.format_exc())

    # 5. Process Response
    messages = groupchat.messages
    agent_path: List[str] = []
    final_answer = "Kechirasiz, javobni aniqlab bo'lmadi."

    for msg in messages:
        name = msg.get("name", "Unknown")
        if name not in agent_path and name not in ["UserProxy", "Router", "Orchestrator"]:
            agent_path.append(name)

    # Find the last meaningful response
    for msg in reversed(messages):
        name = msg.get("name", "")
        content = msg.get("content", "")

        if not content: continue
        if "tool_calls" in msg or "function_call" in msg: continue
        if name in ["UserProxy", "Router", "Orchestrator", "Classifier"]: continue
        
        final_answer = content.replace("TERMINATE", "").strip()
        break

    # 6. Extract Image Path
    image_path: Optional[str] = None
    
    # Markdown Check: ![alt](url)
    md_match = re.search(r'!\[.*?\]\((.*?)\)', final_answer)
    if md_match:
        image_path = md_match.group(1)
    
    # URL Check
    if not image_path:
        url_match = re.search(r'(http[s]?://[^\s\)]+/static/[^\s\)]+)', final_answer)
        if url_match:
            image_path = url_match.group(1)

    # Cleanup Sandbox path
    if image_path and "sandbox:" in image_path:
        image_path = image_path.replace("sandbox:", "")

    # Clean technical errors
    if "tool_calls" in final_answer:
        final_answer = "Texnik nosozlik yuz berdi. Iltimos, qaytadan urinib ko'ring."

    print(f"📤 RESPONSE: {final_answer[:100]}...")
    if image_path:
        print(f"🖼️ IMAGE: {image_path}")

    session_manager.add_message(session_id, "assistant", final_answer, agent_path, image_path)
    
    return ChatResponse(
        response=final_answer,
        agent_path=agent_path,
        message_count=len(messages),
        image_path=image_path,
        session_id=session_id
    )


# ==============================================================================
# 5. SESSION MANAGEMENT ENDPOINTS
# ==============================================================================
@app.post("/sessions/new")
async def create_new_session(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new chat session."""
    session_id = session_manager.create_session(user_id)
    session = session_manager.get_session(session_id)
    return {"session_id": session_id, "created_at": session["created_at"]}


@app.get("/sessions")
async def list_sessions(user_id: Optional[str] = None) -> Dict[str, Any]:
    """List available sessions."""
    if user_id:
        sessions = session_manager.list_user_sessions(user_id)
    else:
        sessions = []
        for sid, sdata in session_manager.sessions.items():
            sessions.append({
                "session_id": sid,
                "created_at": sdata["created_at"],
                "last_active": sdata["last_active"],
                "message_count": len(sdata["messages"])
            })
    sessions.sort(key=lambda x: str(x["last_active"]), reverse=True)
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get chat history for a session."""
    history = session_manager.get_history(session_id, limit)
    if history is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": history}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """Delete a session."""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Success", "session_id": session_id}


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Lex.uz AI Assistant API is Running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)