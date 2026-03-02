import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.constants import API_TITLE, API_VERSION
from app.core.logging import setup_logging
from app.api.routes import router
from app.services.agent_service import AgentService
from app.services.session_service import SessionService

agent_service: AgentService | None = None
session_svc: SessionService | None = None

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_service, session_svc
    setup_logging()
    logger.info("🚀 %s v%s starting…", API_TITLE, API_VERSION)
    settings = get_settings()
    try:
        from app.repository.database import DatabaseRepository
        db_repo = DatabaseRepository()
    except Exception as exc:
        logger.error("DB init failed: %s. Using legacy fallback.", exc)
        db_repo = None
    agent_service = AgentService(db_repository=db_repo)
    session_svc = SessionService()
    logger.info("✅ All services ready.")
    yield
    logger.info("🛑 Shutting down…")


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Global exception:\n%s", traceback.format_exc())
        return JSONResponse(
            status_code=200,
            content={"response": "Kechirasiz, texnik xato yuz berdi.", "session_id": ""},
        )

    app.include_router(router)

    @app.get("/")
    async def root():
        return FileResponse("web/index.html")

    try:
        app.mount("/web", StaticFiles(directory="web"), name="web")
    except Exception:
        pass

    return app


app = create_app()
