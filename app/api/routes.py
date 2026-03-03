import logging
from typing import Annotated

from fastapi import APIRouter, Depends

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


AgentDep = Annotated[AgentService, Depends(get_agent_service)]
SessionDep = Annotated[SessionService, Depends(get_session_service)]


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, agent_svc: AgentDep, session_svc: SessionDep) -> ChatResponse:
    is_new = not req.session_id or not req.session_id.strip()
    sid = session_svc.create_session() if is_new else req.session_id.strip()
    question = req.question.strip()
    history = session_svc.get_formatted_history(sid, limit=4)
    is_first_message = not history

    logger.info("chat | sid=%.8s | question=%r", sid, question)

    try:
        answer = await agent_svc.get_response(question, history)
    except Exception:
        logger.exception("chat | pipeline error for sid=%.8s", sid)
        answer = "Kechirasiz, so'rovni qayta ishlashda xato yuz berdi. Iltimos qayta urinib ko'ring."

    if not is_first_message:
        for prefix in ("Salom! ", "Salom, ", "Assalomu alaykum! ", "Assalomu alaykum, "):
            if answer.startswith(prefix):
                answer = answer[len(prefix):].strip()
                break

    session_svc.add_message(sid, "user", question)
    session_svc.add_message(sid, "assistant", answer)

    logger.info("chat | sid=%.8s | response_len=%d", sid, len(answer))
    return ChatResponse(response=answer, session_id=sid)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=API_TITLE, version=API_VERSION)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, session_svc: SessionDep):
    return {"deleted": session_svc.delete_session(session_id), "session_id": session_id}


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, session_svc: SessionDep):
    return {"session_id": session_id, "messages": session_svc.get_history(session_id, limit=50)}
