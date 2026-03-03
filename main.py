import asyncio
import logging
import signal

import uvicorn

from app.core.logging import setup_logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def run_api() -> None:
    settings = get_settings()
    config = uvicorn.Config(
        "app.api.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
    server = uvicorn.Server(config)
    logger.info("FastAPI starting on http://%s:%d", settings.APP_HOST, settings.APP_PORT)
    await server.serve()


async def run_bot() -> None:
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled.")
        return
    from app.bot.main import start_bot
    await start_bot()


async def main() -> None:
    setup_logging()
    logger.info("LexAI Professional — starting all services.")

    loop = asyncio.get_running_loop()
    api_task = loop.create_task(run_api(), name="api")
    bot_task = loop.create_task(run_bot(), name="bot")
    tasks = {api_task, bot_task}

    def _shutdown(sig_name: str) -> None:
        logger.info("Received %s — initiating shutdown.", sig_name)
        for t in tasks:
            if not t.done():
                t.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig.name)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for task, result in zip(tasks, results):
        if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
            logger.error("Task %r raised: %s", task.get_name(), result)

    logger.info("All services stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
