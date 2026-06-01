from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, knowledge, model_configs, rfp
from app.core.config import get_settings
from app.db.init_db import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(rfp.router, prefix=settings.api_prefix)
app.include_router(knowledge.router, prefix=settings.api_prefix)
app.include_router(model_configs.router, prefix=settings.api_prefix)
