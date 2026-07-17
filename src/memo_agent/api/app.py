import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from memo_agent.api.routes import chat, memory, knowledge, reflection
from memo_agent.api.deps import init_app
from memo_agent.config import Config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_app()
    logger.info("MemoAgent API started")
    yield
    logger.info("MemoAgent API shutting down")


def create_app() -> FastAPI:
    app = FastAPI(title="MemoAgent API", version="0.2.0", lifespan=lifespan)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "detail": str(exc)},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config().api_cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(memory.router, prefix="/api", tags=["memory"])
    app.include_router(knowledge.router, prefix="/api", tags=["knowledge"])
    app.include_router(reflection.router, prefix="/api", tags=["reflection"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
