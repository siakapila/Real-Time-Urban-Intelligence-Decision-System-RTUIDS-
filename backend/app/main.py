from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI

from app.api import ingest, alerts
from app.core import redis
from app.core.config import settings
from app.core.db import engine
from app.models.base import Base
import app.models # ensure models are registered
from app.processor.stream_processor import process_stream

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init Database Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Init Redis
    await redis.init_redis()
    
    # Start background Stream Processor
    processor_task = asyncio.create_task(process_stream())
    
    yield
    
    # Shutdown actions
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass
        
    await redis.close_redis()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.include_router(ingest.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
