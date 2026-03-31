from datetime import date

from database.config import get_engine
from database.models import Device
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_all_devices():
    """Query to retrieve all devices in the system"""
    engine = get_engine()
    with Session(engine) as session:
        devices = session.query(Device).all()
        return devices

def get_hourly_metrics(device_id: str, query_date: date):
    """Query to retrieve hourly metrics for a specific device and date, including running occupancy calculation"""
    engine = get_engine()
    query = text("""
        SELECT
            device_id,
            hour,
            people_in,
            people_out,
            net_flow,
            SUM(net_flow) OVER (PARTITION BY device_id ORDER BY hour) as occupancy
        FROM hourly_metrics
        WHERE device_id = :device_id
        AND DATE_TRUNC('day', hour) = :query_date
        ORDER BY hour
    """)

    with Session(engine) as session:
        result = session.execute(query, {"device_id": device_id, "query_date": query_date})
        return result.mappings().all()

def get_daily_aggregates(device_id: str, start_date: date, end_date: date):
    engine = get_engine()
    query = text("""
        SELECT
            device_id,
            date,
            total_in,
            total_out,
            net_flow
        FROM daily_aggregates
        WHERE device_id = :device_id
        AND date BETWEEN :start_date AND :end_date
        ORDER BY date
    """)

    with Session(engine) as session:
        result = session.execute(query, {
            "device_id": device_id,
            "start_date": start_date,
            "end_date": end_date
        })
        return result.mappings().all()

def get_device_comparison(query_date: date, device_ids: list[str] | None = None):
    engine = get_engine()

    if device_ids:
        where_clause = "AND device_id = ANY(:device_ids)"
        params = {"query_date": query_date, "device_ids": device_ids}
    else:
        where_clause = ""
        params = {"query_date": query_date}

    query = text(f"""
        SELECT
            device_id,
            hour,
            people_in,
            people_out,
            net_flow,
            SUM(net_flow) OVER (PARTITION BY device_id ORDER BY hour) as occupancy
        FROM hourly_metrics
        WHERE DATE_TRUNC('day', hour) = :query_date
        {where_clause}
        ORDER BY device_id, hour
    """)

    with Session(engine) as session:
        result = session.execute(query, params)
        rows = result.mappings().all()

    grouped = {}
    for row in rows:
        device_id = row["device_id"]
        if device_id not in grouped:
            grouped[device_id] = []
        grouped[device_id].append(row)

    return grouped