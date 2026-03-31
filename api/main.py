from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

from api.models import DeviceResponse, HourlyMetricResponse, DailyAggregateResponse, DeviceComparisonResponse
from api.queries import get_all_devices, get_device_comparison, get_device_comparison, get_hourly_metrics, get_daily_aggregates
from datetime import date

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

@app.get("/devices/{device_id}/hourly", response_model=List[HourlyMetricResponse])
def get_device_hourly(
    device_id: str,
    date: date = Query(..., description="Date for which to retrieve hourly metrics in YYYY-MM-DD format")
    ):
    metrics = get_hourly_metrics(device_id, date)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No data found for device {device_id} on {date}")
    return metrics

@app.get("/devices/{device_id}/daily", response_model=List[DailyAggregateResponse])
def get_device_daily(
    device_id: str,
    start_date: date = Query(..., description="Start date for the query range (inclusive) in YYYY-MM-DD format"),
    end_date: date = Query(..., description="End date for the query range (inclusive) in YYYY-MM-DD format")
):
    aggregates = get_daily_aggregates(device_id, start_date, end_date)
    if not aggregates:
        raise HTTPException(status_code=404, detail=f"No data found for device {device_id} between {start_date} and {end_date}")
    return aggregates

@app.get("/devices/compare", response_model=DeviceComparisonResponse)
def compare_devices(
    date: date = Query(..., description="Date to compare devices on in YYYY-MM-DD format"),
    device_ids: Optional[List[str]] = Query(None, description="Optional list of device IDs to compare, defaults to all devices")
):
    grouped = get_device_comparison(date, device_ids)
    if not grouped:
        raise HTTPException(status_code=404, detail=f"No data found for the given devices on {date}")
    return DeviceComparisonResponse(date=date, devices=grouped)

