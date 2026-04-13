from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class SensorEventModel(Base):
    __tablename__ = "sensor_events"

    event_id = Column(String, primary_key=True, index=True)
    sensor_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    traffic_count = Column(Integer, nullable=False)
    pollution_level = Column(Float, nullable=False)
    
    # We can link it to anomaly if needed, but usually anomaly linking happens via FK from anomaly to event
    anomaly = relationship("AnomalyModel", back_populates="event", uselist=False)

class AnomalyModel(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, ForeignKey("sensor_events.event_id"), unique=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    detected_by = Column(String, nullable=False) # e.g., 'ML_ISOLATION_FOREST' or 'RULE_ENGINE'
    classification = Column(String, nullable=False) # e.g., 'heatwave', 'system_error'
    severity = Column(String, nullable=False) # 'LOW', 'MEDIUM', 'HIGH'
    
    # Store reasoning (could be json or string)
    description = Column(String, nullable=True)
    
    event = relationship("SensorEventModel", back_populates="anomaly")
