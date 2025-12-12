# # from fastapi import FastAPI, HTTPException
# # from pydantic import BaseModel
# # from typing import List, Dict
# # import autogen
# # from agents import user_proxy, manager, groupchat  # Agentlarni chaqiramiz
# #
# # app = FastAPI()
# #
# #
# # class ChatRequest(BaseModel):
# #     question: str
# #     history: List[Dict[str, str]] = []
# #
# #
# # @app.post("/chat")
# # async def chat_endpoint(req: ChatRequest):
# #     print(f"\n📩 [API] Savol: {req.question}")
# #
# #     # 1. Chat tarixini tozalash (MUHIM: .reset() ishlatamiz)
# #     # Bu metod nafaqat xabarlarni, balki agentlarning ichki xotirasini ham tozalaydi
# #     groupchat.reset()
# #     user_proxy.reset()
# #     manager.reset()
# #
# #     # 2. Tarixni tayyorlash
# #     context = ""
# #     if req.history:
# #         context = "ESLATMA (Suhbat Tarixi):\n"
# #         for msg in req.history[-4:]:
# #             context += f"{msg['role']}: {msg['content']}\n"
# #
# #     full_message = f"{context}\nYANGI SAVOL: {req.question}"
# #
# #     # Natijani saqlash uchun o'zgaruvchi
# #     messages = []
# #
# #     try:
# #         # 3. Chatni boshlash
# #         await user_proxy.a_initiate_chat(
# #             manager,
# #             message=full_message
# #         )
# #         # Agar xatosiz tugasa, tarixni managerdan olamiz
# #         messages = groupchat.messages
# #
# #     except Exception as e:
# #         error_msg = str(e)
# #         if "returned None" in error_msg:
# #             print("✅ Suhbat muvaffaqiyatli yakunlandi (Navbat tugadi).")
# #             # Xato berib to'xtagan bo'lsa ham, tarix baribir groupchat ichida saqlanib qoladi
# #             messages = groupchat.messages
# #         else:
# #             print(f"❌ Xato: {e}")
# #             return {"response": f"Texnik xatolik: {error_msg}"}
# #
# #     # 4. JAVOBNI OLIŞ
# #     final_answer = "Javobni aniqlab bo'lmadi."
# #
# #     print(f"📊 Jami xabarlar soni: {len(messages)}")
# #
# #     # Tarixni oxiridan boshiga qarab o'qiymiz
# #     for msg in reversed(messages):
# #         name = msg.get("name", "Noma'lum")
# #         content = msg.get("content", "")
# #
# #         # Terminalga chiqarib ko'ramiz
# #         print(f"🔎 Tekshirilmoqda -> Kim: {name} | Matn: {str(content)[:30]}...")
# #
# #         # Router yoki UserProxy (savol beruvchi) bo'lsa -> o'tkazib yubor
# #         if name in ["Router", "UserProxy"]:
# #             continue
# #
# #         # Agar Tool ishlatilayotgan bo'lsa -> o'tkazib yubor
# #         if "tool_calls" in msg or "function_call" in msg:
# #             continue
# #
# #         # Agar mazmun bo'sh bo'lsa -> o'tkazib yubor
# #         if not content:
# #             continue
# #
# #         # Javob topildi!
# #         final_answer = content.replace("TERMINATE", "").strip()
# #         print("🎯 Javob topildi!")
# #         break
# #
# #     return {"response": final_answer}




# #api.py
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Dict, Optional
# import asyncio
# from datetime import datetime
# from agents import user_proxy, manager, groupchat
# from session_manager import session_manager

# app = FastAPI(
#     title="Lex.uz AI Assistant",
#     description="O'zbekiston qonunchilik yordamchisi",
#     version="2.0.0"
# )

# # CORS sozlamalari
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.on_event("startup")
# async def startup_event():
#     """Server ishga tushganda bajariladigan amallar"""
#     print("🧹 Cleaning up empty sessions...")
#     count = session_manager.cleanup_empty_sessions()
#     print(f"✅ Removed {count} empty sessions")


# class ChatRequest(BaseModel):
#     question: str
#     history: List[Dict[str, str]] = []
#     session_id: Optional[str] = None  # Session ID for conversation tracking


# class ChatResponse(BaseModel):
#     response: str
#     agent_path: List[str] = []
#     message_count: int = 0
#     image_path: Optional[str] = None  # Rasm yo'li (agar mavjud bo'lsa)
#     session_id: Optional[str] = None  # Session ID


# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(req: ChatRequest):
#     """
#     Asosiy chat endpoint
#     """
#     print(f"\n{'=' * 70}")
#     print(f"📩 YANGI SAVOL: {req.question}")
#     if req.session_id:
#         print(f"🎫 SESSION ID: {req.session_id}")
#     print(f"{'=' * 70}")

#     # 1. Session boshqarish
#     session_id = req.session_id
#     if not session_id:
#         # Yangi session yaratish
#         session_id = session_manager.create_session()
#         print(f"✨ Yangi session yaratildi: {session_id}")
#     else:
#         # Mavjud sessionni tekshirish
#         session = session_manager.get_session(session_id)
#         if not session:
#             print(f"⚠️ Session topilmadi, yangi session yaratilmoqda")
#             session_id = session_manager.create_session()

#     # Foydalanuvchi xabarini saqlash
#     print(f"💾 Saving user message to session...")
#     session_manager.add_message(session_id, "user", req.question)
#     print(f"✅ Message saved")

#     # 2. Reset agent instances for this request
#     print("🔄 Resetting agents...")
#     groupchat.reset()
#     print("  ✓ groupchat reset")
#     user_proxy.reset()
#     print("  ✓ user_proxy reset")
#     manager.reset()
#     print("  ✓ manager reset")

#     # 3. Kontekst tayyorlash - session history'dan
#     context = ""
#     if session_id:
#         # Session history'dan kontekst olish
#         context = session_manager.get_formatted_history(session_id, limit=10)
    
#     # Agar request'da history bo'lsa (fallback)
#     if not context and req.history:
#         filtered_history = [
#             msg for msg in req.history
#             if msg.get('role') in ['user', 'assistant'] and
#             'tool_calls' not in msg.get('content', '').lower()
#         ]
        
#         recent_history = filtered_history[-10:]
        
#         if recent_history:
#             context = "SUHBAT TARIXI:\n"
#             for msg in recent_history:
#                 role = "Siz" if msg['role'] == 'user' else "Bot"
#                 content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
#                 context += f"{role}: {content}\n"
#             context += "\n"

#     full_message = f"{context}SAVOL: {req.question}"

#     # 4. Chat boshlash with timeout protection
#     print(f"🚀 Chat boshlanyapti...")
#     print(f"📝 Full message: {full_message[:100]}...")
    
#     try:
#         # Add timeout using asyncio
#         print("⏳ Waiting for chat completion (30s timeout)...")
#         await asyncio.wait_for(
#             user_proxy.a_initiate_chat(
#                 manager,
#                 message=full_message
#             ),
#             timeout=30.0  # 30 second timeout
#         )
#         print("✅ Chat completed successfully")
#     except asyncio.TimeoutError:
#         print("⏱️ Chat timeout - taking too long")
#         # Return a default response
#         session_manager.add_message(session_id, "assistant", 
#             "Kechirasiz, javob tayyorlash juda uzoq davom etdi. Iltimos, qaytadan urinib ko'ring.")
#         return ChatResponse(
#             response="Kechirasiz, javob tayyorlash juda uzoq davom etdi. Iltimos, qaytadan urinib ko'ring.",
#             agent_path=["Timeout"],
#             message_count=0,
#             session_id=session_id
#         )
#     except Exception as e:
#         error_msg = str(e)
#         if "returned None" in error_msg or "speaker_selection" in error_msg:
#             print("✅ Chat yakunlandi (navbat tugadi)")
#         else:
#             print(f"⚠️ Kutilmagan xato: {error_msg}")
#             import traceback
#             import os
#             # Create logs directory if it doesn't exist
#             os.makedirs("logs", exist_ok=True)
#             with open("logs/api_errors.log", "a") as f:
#                 f.write(f"\n{'='*60}\n")
#                 f.write(f"Vaqt: {datetime.now()}\n")
#                 f.write(f"Session: {session_id}\n")
#                 f.write(f"Savol: {req.question}\n")
#                 f.write(f"Xato: {error_msg}\n")
#                 f.write(f"Traceback:\n{traceback.format_exc()}\n")

#     # 5. Javobni olish - improved logic
#     messages = groupchat.messages
#     agent_path = []
#     final_answer = "Kechirasiz, javob tayyorlashda muammo yuz berdi."

#     print(f"\n📊 Jami xabarlar: {len(messages)}")
#     print("🔄 Agent ketma-ketligi:")

#     for i, msg in enumerate(messages, 1):
#         agent_name = msg.get("name", "Unknown")
#         content = msg.get("content", "")

#         # Agent yo'lini yig'ish
#         if agent_name not in agent_path:
#             agent_path.append(agent_name)

#         print(f"  {i}. {agent_name}: {content[:50]}...")

#     # Javobni topish - oxiridan boshlab
#     for msg in reversed(messages):
#         agent_name = msg.get("name", "Unknown")
#         content = msg.get("content", "")
        
#         # Skip empty messages
#         if not content or not isinstance(content, str):
#             continue
            
#         # Skip tool calls
#         if "tool_calls" in msg or "function_call" in msg:
#             continue
            
#         # Skip UserProxy and Router
#         if agent_name in ["UserProxy", "Router", "Orchestrator", "Classifier"]:
#             continue
        
#         # Found a real response
#         if agent_name in ["ResponseFormatter", "SocialBot", "LegalAnalyzer", "KnowledgeBot"]:
#             final_answer = content.replace("TERMINATE", "").strip()
#             print(f"✅ Javob topildi: {agent_name}")
#             break

#     # 5. Javobni tozalash va rasm yo'lini ajratish
#     final_answer = final_answer.replace("TERMINATE", "").strip()
    
#     # Rasm yo'lini barcha xabarlardan qidirish (📷 Rasm: static/xxx.png formatida)
#     image_path = None
#     import re
    
#     # Barcha xabarlardan rasm yo'lini qidirish
#     for msg in messages:
#         content = msg.get("content", "")
#         if isinstance(content, str):
#             image_match = re.search(r'📷 Rasm: (static/[^\s\n]+)', content)
#             if image_match:
#                 image_path = image_match.group(1)
#                 break

#     # Tool chaqiruvlarini olib tashlash
#     if "tool_calls" in final_answer or "function" in final_answer:
#         final_answer = "Texnik muammo yuz berdi. Iltimos, qaytadan urinib ko'ring."

#     print(f"\n{'=' * 70}")
#     print(f"📤 JAVOB: {final_answer[:100]}...")
#     if image_path:
#         print(f"🖼️ RASM: {image_path}")
#     print(f"🛤️ Agent yo'li: {' → '.join(agent_path)}")
#     print(f"🎫 SESSION: {session_id}")
#     print(f"{'=' * 70}\n")

#     # Assistant javobini saqlash
#     session_manager.add_message(session_id, "assistant", final_answer, agent_path)

#     return ChatResponse(
#         response=final_answer,
#         agent_path=agent_path,
#         message_count=len(messages),
#         image_path=image_path,
#         session_id=session_id
#     )


# @app.get("/")
# async def root():
#     return {
#         "message": "Lex.uz AI Assistant API",
#         "version": "2.0",
#         "endpoints": {
#             "/chat": "POST - Savol yuborish",
#             "/health": "GET - Tizim holati"
#         }
#     }


# @app.get("/health")
# async def health_check():
#     """
#     Tizim holatini tekshirish
#     """
#     return {
#         "status": "healthy",
#         "agents": [agent.name for agent in groupchat.agents],
#         "agent_count": len(groupchat.agents)
#     }


# # ==============================================================================
# # SESSION MANAGEMENT ENDPOINTS
# # ==============================================================================

# @app.post("/sessions/new")
# async def create_new_session(user_id: Optional[str] = None):
#     """
#     Yangi session (ticket) yaratish
#     """
#     session_id = session_manager.create_session(user_id)
#     session = session_manager.get_session(session_id)
    
#     return {
#         "session_id": session_id,
#         "created_at": session["created_at"],
#         "message": "Yangi chat yaratildi"
#     }


# @app.get("/sessions")
# async def list_sessions(user_id: Optional[str] = None):
#     """
#     Barcha sessionlarni ro'yxatini olish
#     """
#     if user_id:
#         sessions = session_manager.list_user_sessions(user_id)
#     else:
#         # Barcha sessionlar
#         sessions = []
#         for session_id, session_data in session_manager.sessions.items():
#             sessions.append({
#                 "session_id": session_id,
#                 "user_id": session_data.get("user_id"),
#                 "created_at": session_data["created_at"],
#                 "last_active": session_data["last_active"],
#                 "message_count": len(session_data["messages"])
#             })
    
#     return {"sessions": sessions, "total": len(sessions)}


# @app.get("/sessions/{session_id}")
# async def get_session_details(session_id: str):
#     """
#     Aniq session haqida ma'lumot
#     """
#     session = session_manager.get_session(session_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session topilmadi")
    
#     return {
#         "session_id": session_id,
#         "user_id": session.get("user_id"),
#         "created_at": session["created_at"],
#         "last_active": session["last_active"],
#         "message_count": len(session["messages"]),
#         "metadata": session.get("metadata", {})
#     }


# @app.get("/sessions/{session_id}/history")
# async def get_session_history(session_id: str, limit: int = 50):
#     """
#     Session chat tarixini olish
#     """
#     history = session_manager.get_history(session_id, limit)
#     if history is None:
#         raise HTTPException(status_code=404, detail="Session topilmadi")
    
#     return {
#         "session_id": session_id,
#         "messages": history,
#         "count": len(history)
#     }


# @app.delete("/sessions/{session_id}")
# async def delete_session(session_id: str):
#     """
#     Sessionni o'chirish
#     """
#     success = session_manager.delete_session(session_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Session topilmadi")
    
#     return {"message": "Session o'chirildi", "session_id": session_id}


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)






import os
import re
import asyncio
import traceback
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Loyiha ichidagi modullar
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

# CORS sozlamalari (Frontend ulanishi uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STATIC FILES (RASMLAR UCHUN MUHIM)
# "static" papkasi mavjudligini tekshiramiz va ulaymiz
if not os.path.exists("static"):
    os.makedirs("static")

# Bu qator rasmlarni http://localhost:8000/static/... orqali ochish imkonini beradi
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
async def startup_event():
    """Server ishga tushganda bajariladigan tozalash ishlari"""
    print("🧹 Bo'sh sessionlar tozalanmoqda...")
    count = session_manager.cleanup_empty_sessions()
    print(f"✅ {count} ta bo'sh session o'chirildi")
    
    # Loglar uchun papka
    os.makedirs("logs", exist_ok=True)


# ==============================================================================
# 4. CHAT ENDPOINT
# ==============================================================================
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Asosiy chat muloqot funksiyasi
    """
    print(f"\n{'=' * 70}")
    print(f"📩 YANGI SAVOL: {req.question}")
    
    # 1. Sessionni aniqlash yoki yaratish
    session_id = req.session_id
    if not session_id:
        session_id = session_manager.create_session()
        print(f"✨ Yangi session yaratildi: {session_id}")
    else:
        # Mavjudligini tekshirish
        if not session_manager.get_session(session_id):
            print(f"⚠️ Session topilmadi, yangi yaratilmoqda...")
            session_id = session_manager.create_session()
        else:
            print(f"🎫 Session ID: {session_id}")

    # Foydalanuvchi xabarini bazaga saqlash
    session_manager.add_message(session_id, "user", req.question)

    # 2. Agentlarni tozalash (Reset)
    # Har bir yangi savol uchun agentlar xotirasi yangilanadi (lekin umumiy kontekst tarixda bor)
    print("🔄 Agentlar tozalanmoqda (Reset)...")
    groupchat.reset()
    user_proxy.reset()
    manager.reset()

    # 3. Kontekstni tayyorlash
    context = session_manager.get_formatted_history(session_id, limit=10)
    
    # Agar session bo'sh bo'lsa-yu, requestda history kelsa (zaxira varianti)
    if not context and req.history:
        recent = req.history[-6:] # Oxirgi 6 ta xabar
        context = "SUHBAT TARIXI:\n" + "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent]) + "\n"

    full_message = f"{context}YANGI SAVOL: {req.question}"
    print(f"📝 Agentga yuborilayotgan matn: {full_message[:100]}...")

    # 4. Chat jarayoni (Timeout himoyasi bilan)
    try:
        print("⏳ Chat boshlandi (30 soniya vaqt)...")
        await asyncio.wait_for(
            user_proxy.a_initiate_chat(
                manager,
                message=full_message
            ),
            timeout=30.0
        )
        print("✅ Chat muvaffaqiyatli yakunlandi")
    
    except asyncio.TimeoutError:
        print("⏱️ Timeout: Javob juda uzoqqa cho'zildi")
        error_resp = "Kechirasiz, javob tayyorlash juda uzoq vaqt oldi. Iltimos, savolni qisqaroq qilib qayta bering."
        session_manager.add_message(session_id, "assistant", error_resp)
        return ChatResponse(
            response=error_resp,
            agent_path=["Timeout"],
            session_id=session_id
        )
    except Exception as e:
        # Ba'zan agent "gapirishni tugatdim" deb xato tashlaydi, bu normal holat
        error_str = str(e)
        if "returned None" in error_str or "speaker_selection" in error_str:
            print("✅ Chat yakunlandi (Agent to'xtadi)")
        else:
            print(f"❌ Xato yuz berdi: {error_str}")
            # Xatoni logga yozish
            with open("logs/api_errors.log", "a") as f:
                f.write(f"\n{datetime.now()} | {session_id} | {req.question} | {error_str}\n")
                f.write(traceback.format_exc())

    # 5. Javobni tahlil qilish
    messages = groupchat.messages
    agent_path = []
    final_answer = "Kechirasiz, javobni aniqlab bo'lmadi."

    # Agentlar ketma-ketligini olish
    for msg in messages:
        name = msg.get("name", "Unknown")
        if name not in agent_path and name not in ["UserProxy", "Router", "Orchestrator"]:
            agent_path.append(name)

    # Eng oxirgi mazmunli javobni qidirish
    for msg in reversed(messages):
        name = msg.get("name", "")
        content = msg.get("content", "")

        if not content: continue
        if "tool_calls" in msg or "function_call" in msg: continue
        if name in ["UserProxy", "Router", "Orchestrator", "Classifier"]: continue
        
        # Agar javob topilsa
        final_answer = content.replace("TERMINATE", "").strip()
        break

    # 6. Rasm yo'lini ajratib olish
    image_path = None
    
    # a) Markdown formatini tekshirish: ![alt](url)
    md_match = re.search(r'!\[.*?\]\((.*?)\)', final_answer)
    if md_match:
        image_path = md_match.group(1)
    
    # b) Agar markdown bo'lmasa, matn ichidan "http...static..." ni qidirish
    if not image_path:
        url_match = re.search(r'(http[s]?://[^\s\)]+/static/[^\s\)]+)', final_answer)
        if url_match:
            image_path = url_match.group(1)

    # c) Sandbox prefiksini olib tashlash
    if image_path and "sandbox:" in image_path:
        image_path = image_path.replace("sandbox:", "")

    # 7. Yakuniy tozalash
    if "tool_calls" in final_answer:
        final_answer = "Texnik nosozlik yuz berdi. Iltimos, qaytadan urinib ko'ring."

    print(f"📤 JAVOB: {final_answer[:100]}...")
    if image_path:
        print(f"🖼️ RASM: {image_path}")

    # Javobni tarixga saqlash (image_path bilan)
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
async def create_new_session(user_id: Optional[str] = None):
    """Yangi chat sessiyasini yaratish"""
    session_id = session_manager.create_session(user_id)
    session = session_manager.get_session(session_id)
    return {"session_id": session_id, "created_at": session["created_at"]}


@app.get("/sessions")
async def list_sessions(user_id: Optional[str] = None):
    """Mavjud sessiyalar ro'yxatini olish"""
    if user_id:
        sessions = session_manager.list_user_sessions(user_id)
    else:
        # Barchasini olish
        sessions = []
        for sid, sdata in session_manager.sessions.items():
            sessions.append({
                "session_id": sid,
                "created_at": sdata["created_at"],
                "last_active": sdata["last_active"],
                "message_count": len(sdata["messages"])
            })
    # Eng yangilari tepada tursin
    sessions.sort(key=lambda x: x["last_active"], reverse=True)
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50):
    """Aniq bir sessiyaning yozishmalar tarixi"""
    history = session_manager.get_history(session_id, limit)
    if history is None:
        raise HTTPException(status_code=404, detail="Session topilmadi")
    return {"session_id": session_id, "messages": history}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Sessiyani o'chirish"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session topilmadi")
    return {"message": "Muvaffaqiyatli o'chirildi", "session_id": session_id}


@app.get("/")
async def root():
    return {"message": "Lex.uz AI Assistant API is Running", "docs": "/docs"}


# ==============================================================================
# RUNNER
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    # Serverni ishga tushirish (0.0.0.0 barcha IP lardan kirishga ruxsat beradi)
    uvicorn.run(app, host="0.0.0.0", port=8000)