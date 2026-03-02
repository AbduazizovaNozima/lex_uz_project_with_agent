import logging
import traceback

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.schemas import ChatRequest, ChatResponse, HealthResponse
from app.core.constants import API_TITLE, API_VERSION
from app.services.agent_service import AgentService
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_agent_service() -> AgentService:
    from app.api.main import agent_service
    return agent_service


def get_session_service() -> SessionService:
    from app.api.main import session_svc
    return session_svc


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    agent_svc: AgentService = Depends(get_agent_service),
    session_svc: SessionService = Depends(get_session_service),
) -> ChatResponse:
    is_new = not req.session_id or not req.session_id.strip()
    sid = session_svc.create_session() if is_new else req.session_id.strip()
    question = req.question.strip()
    history = session_svc.get_formatted_history(sid, limit=4)
    is_first_message = not history

    logger.info("\n%s\n🌐 WEB | sid=%s…\n❓ Savol   : %s\n%s", "═"*60, sid[:8], question, "═"*60)

    try:
        final_res = await agent_svc.get_response(question, history)
    except Exception:
        logger.error("chat | pipeline error:\n%s", traceback.format_exc())
        final_res = "Kechirasiz, so'rovni qayta ishlashda xato yuz berdi. Iltimos qayta urinib ko'ring."

    if not is_first_message:
        for greet in ["Salom! ", "Salom, ", "Assalomu alaykum! ", "Assalomu alaykum, "]:
            if final_res.startswith(greet):
                final_res = final_res[len(greet):].strip()
                break

    logger.info("✅ Javob    :\n%s\n%s", final_res, "═"*60)

    session_svc.add_message(sid, "user", question)
    session_svc.add_message(sid, "assistant", final_res)

    return ChatResponse(response=final_res, session_id=sid)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=API_TITLE, version=API_VERSION)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, session_svc: SessionService = Depends(get_session_service)):
    return {"deleted": session_svc.delete_session(session_id), "session_id": session_id}


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, session_svc: SessionService = Depends(get_session_service)):
    return {"session_id": session_id, "messages": session_svc.get_history(session_id, limit=50)}
