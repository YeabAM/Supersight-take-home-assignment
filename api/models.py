from datetime import date as date_type, datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class DeviceResponse(BaseModel):
    device_id: str = Field(..., description="Device name retrieved from raw input data")
    created_at: datetime = Field(..., description="Timestamp when the device was first added in the database")

    # Config class to allow ORM objects to be returned directly from SQLAlchemy queries
    class Config:
        from_attributes = True

class HourlyMetricResponse(BaseModel):

    device_id: str = Field(..., description="Device name retrieved from raw input data")

    hour: datetime = Field(..., description="Start of the hour window (UTC)")

    people_in: int = Field(..., ge=0, description="Number of people who entered during this hour")

    people_out: int = Field(..., ge=0, description="Number of people who exited during this hour")

    net_flow: int = Field(..., description="Net change in occupancy for this hour (in - out)")

    occupancy: int = Field(..., description="Running occupancy at the end of this hour")

    # Config class to allow ORM objects to be returned directly from SQLAlchemy queries
    class Config:
        from_attributes = True


class DailyAggregateResponse(BaseModel):

    device_id: str = Field(..., description="Device name retrieved from raw input data")

    date: date_type = Field(..., description="The date of the aggregation (UTC midnight)")

    total_in: int = Field(..., ge=0, description="Total number of people who entered during this day")

    total_out: int = Field(..., ge=0, description="Total number of people who exited during this day")

    net_flow: int = Field(..., description="Net change in occupancy for this day (total_in - total_out)")


    # Config class to allow ORM objects to be returned directly from SQLAlchemy queries
    class Config:

        from_attributes = True
