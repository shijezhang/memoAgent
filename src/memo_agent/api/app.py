import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memo_agent.api.routes import chat, memory, knowledge, reflection
from memo_agent.api.deps import init_app, get_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_app()
    logger.info("MemoAgent API started")
    yield
    logger.info("MemoAgent API shutting down")


def create_app() -> FastAPI:
    app = FastAPI(title="MemoAgent API", version="0.2.0", lifespan=lifespan)

    config = get_config()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api_cors_origins if config else ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(memory.router, prefix="/api", tags=["memory"])
    app.include_router(knowledge.router, prefix="/api", tags=["knowledge"])
    app.include_router(reflection.router, prefix="/api", tags=["reflection"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
