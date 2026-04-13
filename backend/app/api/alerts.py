from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
import datetime

from app.core.db import get_db
from app.models.sensor_event import AnomalyModel, SensorEventModel
from pydantic import BaseModel, ConfigDict

router = APIRouter()

# Schemas for response
class AnomalyResponse(BaseModel):
    id: int
    event_id: str
    timestamp: datetime.datetime
    detected_by: str
    classification: str
    severity: str
    description: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class MetricsResponse(BaseModel):
    total_events: int
    total_anomalies: int
    high_severity: int
    medium_severity: int
    low_severity: int
    anomaly_rate: float

@router.get("/alerts", response_model=List[AnomalyResponse])
async def get_alerts(
    limit: int = 50, 
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(AnomalyModel).order_by(desc(AnomalyModel.timestamp)).limit(limit)
    
    if severity:
        query = query.filter(AnomalyModel.severity == severity.upper())
        
    result = await db.execute(query)
    anomalies = result.scalars().all()
    
    return anomalies

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    # Very basic metrics gathering
    # In production, use materialized views or Redis counters for high speed
    events_count = await db.scalar(select(func.count(SensorEventModel.event_id)))
    anomalies_count = await db.scalar(select(func.count(AnomalyModel.id)))
    
    high = await db.scalar(select(func.count(AnomalyModel.id)).filter(AnomalyModel.severity == 'HIGH'))
    medium = await db.scalar(select(func.count(AnomalyModel.id)).filter(AnomalyModel.severity == 'MEDIUM'))
    low = await db.scalar(select(func.count(AnomalyModel.id)).filter(AnomalyModel.severity == 'LOW'))
    
    events_count = events_count or 0
    anomalies_count = anomalies_count or 0
    rate = (anomalies_count / events_count * 100) if events_count > 0 else 0.0

    return MetricsResponse(
        total_events=events_count,
        total_anomalies=anomalies_count,
        high_severity=high or 0,
        medium_severity=medium or 0,
        low_severity=low or 0,
        anomaly_rate=round(rate, 2)
    )
