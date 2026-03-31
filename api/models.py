from datetime import date, datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class DeviceResponse(BaseModel):
    device_id: str = Field(..., description="Device name retrieved from raw input data")
    created_at: datetime = Field(..., description="Timestamp when the device was first added in the database")

    class Config:
        from_attributes = True
