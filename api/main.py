from typing import List

from fastapi import FastAPI, HTTPException

from api.models import DeviceResponse
from api.queries import get_all_devices

app = FastAPI(
    title="Supersight API",
    description="API for accessing occupancy and net people metrics from sensor data",
    version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/devices", response_model=List[DeviceResponse])
def read_devices():
    """Endpoint to retrieve all devices"""
    try:
        devices = get_all_devices()
        return [DeviceResponse.from_orm(device) for device in devices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))