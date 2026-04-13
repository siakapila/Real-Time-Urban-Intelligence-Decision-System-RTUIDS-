from fastapi import APIRouter, HTTPException, Depends, status
import logging
import json
from app.schemas.events import SensorEvent, EventResponse
from app.core.redis import get_redis
from app.core.config import settings
from redis.asyncio import Redis

router = APIRouter()
logger = logging.getLogger(__name__)

# Basic threshold for backpressure
MAX_QUEUE_LENGTH = 100000 

@router.post("/ingest", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_sensor_data(event: SensorEvent, redis: Redis = Depends(get_redis)):
    try:
        # 1. Backpressure Check
        # To avoid polling XLEN on every single request in extreme scale, 
        # we could use approximate counts, but we will use XLEN here for simplicity.
        queue_length = await redis.xlen(settings.STREAM_NAME)
        if queue_length > MAX_QUEUE_LENGTH:
            logger.warning(f"Backpressure applied: Redis stream queue length {queue_length} > {MAX_QUEUE_LENGTH}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="System overloaded, please retry later with exponential backoff."
            )

        # 2. Idempotency Check
        # We store the event_id as a separate key with a short TTL (e.g. 1 hour) to detect duplicates.
        idempotency_key = f"idemp:event:{event.event_id}"
        is_duplicate = await redis.setnx(idempotency_key, "1")
        if not is_duplicate:
            logger.info(f"Duplicate event detected: {event.event_id}")
            # If it's a duplicate, we return 200/202 to the client as if it succeeded
            return EventResponse(
                status="accepted",
                event_id=event.event_id,
                message="Event accepted (duplicate dismissed)"
            )
        
        # Expire idempotency key to save memory
        await redis.expire(idempotency_key, 3600)

        # 3. Stream Publishing
        # Convert event payload to dict of string for XADD
        payload = event.model_dump()
        payload["timestamp"] = payload["timestamp"].isoformat()
        
        await redis.xadd(settings.STREAM_NAME, payload)
        
        return EventResponse(
            status="accepted",
            event_id=event.event_id,
            message="Event streamed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process event."
        )
