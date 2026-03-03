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

logger = logging.getLogger(__name__)

agent_service: AgentService | None = None
session_svc: SessionService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_service, session_svc

    setup_logging()
    logger.info("%s v%s — starting up.", API_TITLE, API_VERSION)

    db_repo = None
    try:
        from app.repository.database import DatabaseRepository
        db_repo = DatabaseRepository()
    except Exception:
        logger.warning(
            "Database unavailable — agent will use the legacy search_lexuz_tool fallback.",
            exc_info=True,
        )

    agent_service = AgentService(db_repository=db_repo)
    session_svc = SessionService()
    logger.info("All services ready.")

    yield

    logger.info("%s — shutting down.", API_TITLE)


def create_app() -> FastAPI:
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on %s:\n%s", request.url.path, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error."},
        )

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root() -> FileResponse:
        return FileResponse("web/index.html")

    try:
        app.mount("/web", StaticFiles(directory="web"), name="web")
    except Exception:
        logger.debug("Static 'web' directory not found — skipping static mount.")

    return app


app = create_app()
