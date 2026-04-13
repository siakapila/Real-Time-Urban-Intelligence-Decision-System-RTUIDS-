from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import uuid4

class SensorEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for idempotency")
    sensor_id: str = Field(..., description="ID of the sensor making the report")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity percentage")
    traffic_count: int = Field(default=0, description="Number of vehicles passing per minute")
    pollution_level: float = Field(..., description="PM2.5 concentration")

    model_config = ConfigDict(from_attributes=True)

class EventResponse(BaseModel):
    status: str
    event_id: str
    message: str
