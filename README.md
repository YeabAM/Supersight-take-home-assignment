# People Counting Pipeline

A data engineering pipeline that processes raw sensor event data from people counting devices, aggregates it into hourly and daily metrics, and serves it via a REST API.

For architecture and design decisions write up see [docs/DESIGN.md](docs/DESIGN.md).

---

## Project Structure

### Pipeline

```
pipeline/
├── ingest.py       # Reads CSV files from device folders using DuckDB
├── transform.py    # Aggregates raw events into hourly and daily metrics
├── load.py         # Upserts aggregated data into PostgreSQL via SQLAlchemy
└── run.py          # Orchestrates ingest -> transform -> load
```

### API

```
api/
├── main.py         # FastAPI app and route definitions
├── models.py       # Pydantic response models for Swagger documentation
└── queries.py      # SQL queries against PostgreSQL
```

### Database

```
database/
├── config.py       # SQLAlchemy engine setup
├── models.py       # Table definitions (devices, hourly_metrics, daily_aggregates)
└── create_table.py # Creates tables on first run
```

---

## API Endpoints

Full interactive documentation available at `http://localhost:8000/docs` once the API is running.

### `GET /devices`

Returns all registered sensor devices.

```json
[
  { "device_id": "device_A", "created_at": "2026-03-30T15:33:39.455074" },

  { "device_id": "device_B", "created_at": "2026-03-30T15:33:39.455074" }
]
```

---

### `GET /devices/{device_id}/hourly?date=YYYY-MM-DD`

Returns hourly metrics for a device on a given date. Occupancy is computed on the fly and reflects the running total of people in the space at the end of each hour.

**Returns per hour:** `device_id`, `hour`, `people_in`, `people_out`, `net_flow`, `occupancy`

```json
[
  {
    "device_id": "device_A",
    "hour": "2024-01-01T08:00:00",
    "people_in": 13,
    "people_out": 1,
    "net_flow": 12,
    "occupancy": 12
  },
  {
    "device_id": "device_A",
    "hour": "2024-01-01T09:00:00",
    "people_in": 7,
    "people_out": 5,
    "net_flow": 2,
    "occupancy": 14
  },
  {
    "device_id": "device_A",
    "hour": "2024-01-01T10:00:00",
    "people_in": 0,
    "people_out": 14,
    "net_flow": -14,
    "occupancy": 0
  }
]
```

---

### `GET /devices/{device_id}/daily?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Returns daily aggregated metrics for a device over a date range. Useful for rendering trend charts over longer periods.

**Returns per day:** `device_id`, `date`, `total_in`, `total_out`, `net_flow`

```json
[
  {
    "device_id": "device_A",
    "date": "2024-01-01",
    "total_in": 20,
    "total_out": 20,
    "net_flow": 0
  },
  {
    "device_id": "device_A",
    "date": "2024-01-02",
    "total_in": 16,
    "total_out": 5,
    "net_flow": 11
  }
]
```

---

### `GET /devices/compare?date=YYYY-MM-DD&device_ids=device_A&device_ids=device_B`

Returns hourly metrics with occupancy for multiple devices on the same date in a single query, grouped by device. `device_ids` is optional and defaults to all devices.

**Returns:** `date`, `devices` (dict of device_id → list of hourly metrics with occupancy)

```json
{
  "date": "2024-01-01",
  "devices": {
    "device_A": [
      {
        "device_id": "device_A",
        "hour": "2024-01-01T08:00:00",
        "people_in": 13,
        "people_out": 1,
        "net_flow": 12,
        "occupancy": 12
      },
      {
        "device_id": "device_A",
        "hour": "2024-01-01T09:00:00",
        "people_in": 7,
        "people_out": 5,
        "net_flow": 2,
        "occupancy": 14
      },
      {
        "device_id": "device_A",
        "hour": "2024-01-01T10:00:00",
        "people_in": 0,
        "people_out": 14,
        "net_flow": -14,
        "occupancy": 0
      }
    ],
    "device_B": [
      {
        "device_id": "device_B",
        "hour": "2024-01-01T08:00:00",
        "people_in": 12,
        "people_out": 2,
        "net_flow": 10,
        "occupancy": 10
      },
      {
        "device_id": "device_B",
        "hour": "2024-01-01T09:00:00",
        "people_in": 7,
        "people_out": 5,
        "net_flow": 2,
        "occupancy": 12
      }
    ]
  }
}
```

---

## Running the Service

### Prerequisites

- Docker Desktop running
- `.env` file at the project root with `DATABASE_URL` set to your Supabase connection string. A `.env` file is included with the submission email.

### Run the pipeline

Processes CSV files and loads aggregated metrics into PostgreSQL. For the implementation this is something that runs once and saves data in postgres which is served on Supabase.

```bash
docker compose run pipeline
```

### Start the API

```bash
docker compose up api
```

API is available at `http://0.0.0.0:8000`. Swagger docs at `http://0.0.0.0:8000/docs`.

---

## Deliverables Checklist

- [x] Hourly aggregations (people_in, people_out, net_flow per device per hour)
- [x] Daily aggregations (total_in, total_out, net_flow per device per day)
- [x] Occupancy over time (computed via window function at query time)
- [x] REST API to expose metrics for visualization consumption
- [x] Dockerized services for isolated, reproducible execution
- [x] Write up documentation of design decision
