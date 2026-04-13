from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import ingest
from app.core import redis
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    await redis.init_redis()
    yield
    # Shutdown actions
    await redis.close_redis()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.include_router(ingest.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
