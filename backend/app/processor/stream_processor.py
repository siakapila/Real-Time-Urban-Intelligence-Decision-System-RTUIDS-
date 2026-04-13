import asyncio
import logging
from redis.asyncio import Redis
from app.core.redis import get_redis
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.sensor_event import SensorEventModel, AnomalyModel
from app.engines.decision import decision_engine
from datetime import datetime

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "rtuids_group"
CONSUMER_NAME = "processor_1"

async def setup_consumer_group(redis: Redis):
    try:
        # Create group, MKSTREAM will create the stream if it doesn't exist
        await redis.xgroup_create(settings.STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info(f"Consumer group {CONSUMER_GROUP} created.")
    except Exception as e:
        if "BUSYGROUP Consumer Group name already exists" in str(e):
            logger.info(f"Consumer group {CONSUMER_GROUP} already exists.")
        else:
            logger.error(f"Error creating consumer group: {e}")

async def process_stream():
    """Background task to continuously poll Redis and process batches"""
    redis = await get_redis()
    await setup_consumer_group(redis)
    
    logger.info("Started Async Stream Processor...")
    
    while True:
        try:
            # Block for up to 1000ms waiting for new messages
            # ">" means read all messages delivered to the group that have never been delivered to other consumers
            response = await redis.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={settings.STREAM_NAME: ">"},
                count=settings.MAX_BATCH_SIZE,
                block=1000
            )
            
            if not response:
                # No new messages, sleep slightly to prevent tight loop if block is somehow bypassed
                await asyncio.sleep(0.1)
                continue
            
            # response format: [[stream_name, [(msg_id, payload_dict), ...]]]
            for stream, messages in response:
                message_ids_to_ack = []
                
                async with AsyncSessionLocal() as session:
                    for msg_id, payload in messages:
                        try:
                            # Parse payload
                            event_id = payload.get("event_id")
                            timestamp = datetime.fromisoformat(payload.get("timestamp"))
                            
                            # Log the raw event to db
                            db_event = SensorEventModel(
                                event_id=event_id,
                                sensor_id=payload.get("sensor_id"),
                                timestamp=timestamp,
                                temperature=float(payload.get("temperature", 0.0)),
                                humidity=float(payload.get("humidity", 0.0)),
                                traffic_count=int(payload.get("traffic_count", 0)),
                                pollution_level=float(payload.get("pollution_level", 0.0))
                            )
                            session.add(db_event)
                            
                            # Run Decision Engine (Phase 3 logic - ML + Fallback)
                            is_anomaly, classification, severity, desc, detected_by = decision_engine.evaluate(payload)
                            
                            if is_anomaly:
                                db_anomaly = AnomalyModel(
                                    event_id=event_id,
                                    timestamp=timestamp, 
                                    detected_by=detected_by,
                                    classification=classification,
                                    severity=severity,
                                    description=desc
                                )
                                session.add(db_anomaly)
                            
                            message_ids_to_ack.append(msg_id)
                        except Exception as e:
                            logger.error(f"Error processing single message {msg_id}: {e}")
                    
                    # Commit the batch to DB
                    try:
                        await session.commit()
                        logger.info(f"Processed and committed batch of {len(messages)} events.")
                        
                        # Acknowledge messages in Redis so they aren't delivered again
                        if message_ids_to_ack:
                            await redis.xack(settings.STREAM_NAME, CONSUMER_GROUP, *message_ids_to_ack)
                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Database commit failed, rolling back batch: {e}")
                        # In a real system, you might not ack here or use a DLQ (Dead Letter Queue)

        except asyncio.CancelledError:
            logger.info("Stream processor cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in stream processor loop: {e}")
            await asyncio.sleep(5) # Backoff on major failure
