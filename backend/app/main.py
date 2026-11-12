"""FastAPI application entry point.  Run with:  uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import APP_NAME, APP_VERSION, database
from .config import get_settings
from .routers.api import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    # Experiments interrupted by a server restart can never finish; mark them honestly.
    with database.connect() as connection:
        connection.execute(
            "UPDATE experiments SET status = 'failed', error = 'interrupted: the server stopped "
            "before this experiment finished', finished_at = ? WHERE status IN ('pending', 'running')",
            (database.utc_now(),))
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=f"{APP_NAME} API", version=APP_VERSION, lifespan=lifespan,
        description="Evaluating prompt-engineering strategies against indirect prompt injection.")
    application.add_middleware(
        CORSMiddleware, allow_origins=get_settings().cors_origins, allow_methods=["*"],
        allow_headers=["*"], expose_headers=["Content-Disposition"])
    application.include_router(router)
    return application


app = create_app()
