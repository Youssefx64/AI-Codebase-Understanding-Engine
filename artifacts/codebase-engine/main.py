"""FastAPI application entry point.

Creates the app, mounts all routers, registers middleware, and wires up
startup/shutdown lifecycle hooks for database and vector store initialisation.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.middleware.logging import RequestLoggingMiddleware
from api.routes import analyze, graph, issues, qa, refactor, summary
from core.config import get_settings
from core.exceptions import AppError
from core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler: startup → yield → shutdown."""
    setup_logging()
    logger.info("Starting AI Codebase Understanding Engine")

    # Initialise database tables
    from infrastructure.database.postgres import init_db
    await init_db()

    # Initialise data directories
    settings = get_settings()
    os.makedirs(settings.repos_base_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs("./data/graphs", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

    logger.info("Application ready")
    yield

    logger.info("Shutting down")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered system that analyses GitHub repositories and provides "
            "deep insights including architecture explanation, dependency graphs, "
            "code summaries, bug detection, and developer Q&A."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "Application error",
            code=exc.code,
            status=exc.status_code,
            message=exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(analyze.router)
    app.include_router(summary.router)
    app.include_router(graph.router)
    app.include_router(qa.router)
    app.include_router(issues.router)
    app.include_router(refactor.router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health() -> dict:
        from infrastructure.database.postgres import health_check
        db_ok = await health_check()
        return {
            "status": "ok",
            "version": settings.app_version,
            "database": "ok" if db_ok else "unavailable",
        }

    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


# ── Entry point ────────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
