## Overview

Sensor devices track people entering and exiting locations, producing raw event data as CSV files. The goal is to build a pipeline that processes this data into hourly and daily aggregations, stores them in a database, and serves them via a REST API for dashboard visualization.

---

## Architecture and Data Flow

```
CSV Files -> DuckDB (Processing) -> PostgreSQL (Storage) -> FastAPI (API)
```

**Processing Layer (DuckDB)**
Reads CSV files from multiple devices, aggregates raw events into hourly and daily summaries, and calculates derived metrics. Temporary, exists only during pipeline execution.

**Storage Layer (PostgreSQL/Supabase)**
Stores aggregated metrics, and this is where the data comes from for the dashboard.

**API Layer (FastAPI)**
Exposes REST endpoints for metrics. See [README.md](../README.md) for the full list of endpoints and what metrics they return.


### Data Flow

**Ingestion**
DuckDB scans device folders and reads all CSVs and unions results from multiple devices into a single relation.

**Transformation**
Events are aggregated by device and hour, summing people_in and people_out and calculating net_flow. Daily aggregates are then derived from the hourly relation, summing values by day. Both relations stay in DuckDB's internal format throughout, converting to a DataFrame only at the load step for memory efficiency

**Loading**
Both hourly and daily relations are converted to DataFrames and bulk upserted into PostgreSQL.


### Why Separate DuckDB from PostgreSQL

DuckDB and PostgreSQL serve fundamentally different workload types. DuckDB is optimized for full table scans and batch aggregations, which is exactly what the transformation step does. PostgreSQL is concurrent access, indexing mechanism for fast access which is ideal when the data is served for visualization.

---

## Key Design Decisions

### DuckDB for Processing

- Memory efficiency: streams data in chunks rather than loading entire datasets into RAM
- Analytical optimisation: built specifically for aggregations and window functions
- Relation passing between stages: data stays in DuckDB's internal format from ingest through transform to load, converting to a DataFrame only once at the end. This avoids creating multiple in-memory copies at each stage, unlike Pandas where raw and transformed DataFrames exist simultaneously

This matters most at scale, when processing GBs of sensor data from hundreds of devices.

**Trade-offs**
- Even if DuckDB is memory efficient, the fact is its single node, makes it not suitable for horizontal scaling which is discussed further in this write up

### SQLAlchemy for Schema Definition and Loading

SQLAlchemy declarative models define the schema in a type-safe, self-documenting way.

In production I would add Alembic for migration versioning, but that is covered in the Trade-offs section.

### Schema Design

**devices**

| Column | Type | Notes |
|--------|------|-------|
| device_id | VARCHAR (PK) | Unique identifier for each sensor |
| created_at | TIMESTAMP | When the device was first registered |

**hourly_metrics**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | Auto-incrementing |
| device_id | VARCHAR (FK) | References devices |
| hour | TIMESTAMP | Truncated to hour boundary |
| people_in | INTEGER | Total entries during this hour |
| people_out | INTEGER | Total exits during this hour |
| net_flow | INTEGER | people_in - people_out |
| created_at | TIMESTAMP | When record was first inserted |
| updated_at | TIMESTAMP | When record was last modified |

Unique constraint on `(device_id, hour)`. Indexes on `(device_id, hour)` and `hour`.

**daily_aggregates**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | Auto-incrementing |
| device_id | VARCHAR (FK) | References devices |
| date | TIMESTAMP | UTC midnight of the day |
| total_in | INTEGER | Total entries during this day |
| total_out | INTEGER | Total exits during this day |
| net_flow | INTEGER | total_in - total_out |
| created_at | TIMESTAMP | When record was first inserted |
| updated_at | TIMESTAMP | When record was last modified |

Unique constraint on `(device_id, date)`.

### Why Occupancy Is Not Stored

Occupancy is a running total, a cumulative sum of net_flow across all hours. Storing it may create a cascade update problem which means if one hour's net_flow is corrected, every subsequent stored occupancy value for that device becomes incorrect and would need to be recalculated. Instead, occupancy is computed at query time, which always reflects the current state of net_flow automatically.

### Upsert Strategy: Replace Not Add

On conflict, existing values are replaced rather than added to. The assumption is that sensors send absolute hourly counts, not incremental changes. This makes the pipeline idempotent meaning re-running with the same source files produces the same result rather than doubled counts. If the system were to support incremental corrections in the future, the upsert strategy would need revisiting.

### API Layer

- The assignment suggested Django but for a pure data access layer I thought it would be too much. Django brings templates, admin panels, auth, and ORM all tightly coupled together, which would be valuable in a full product. FastAPI fits better because lightweight, async-first, and generates `Swagger` docs automatically from the Pydantic models defined.

- Occupancy is computed at query time

- For device comparison I avoided N+1 queries by fetching all devices in a single query using PostgreSQL's `ANY(:device_ids)`, then doing one linear pass in Python to group flat rows into the nested response. Device IDs are optional and default to all devices.

## Scalability

The current solution handles the assignment dataset well, but here is how each layer would need to evolve at 100x data volume.

**Processing Layer**
DuckDB is single-node, which means scaling it means buying a bigger machine rather than adding more machines. There is a hard ceiling on how much memory and CPU one node can have, and with hundreds of devices running 24/7 that ceiling gets hit. I would move to PySpark here, which distributes the processing workload across a cluster of machines so compute scales horizontally with data volume.

**Raw Data Storage**
Currently CSV files live on the local filesystem, which does not persist across deployments and cannot scale across multiple machines. I would move raw files to cloud object storage like S3 or Azure Blob as the landing zone. This decouples data storage from compute, meaning the processing layer can scale independently and raw data is always available for reprocessing regardless of where the pipeline runs.

**Data Lake and Medallion Architecture**
A flat folder of CSVs breaks down when reprocessing is needed, for example if aggregation logic changes. I would introduce a medallion architecture on top of the object storage: Bronze for raw events exactly as received, Silver for validated and standardized events, Gold for aggregated metrics ready for serving. Reprocessing then triggers from Silver rather than the original source. I would use Delta Lake on top of this, which brings ACID transactions, schema evolution, and time travel. If sensor corrections are something the system supports, time travel makes replaying and correcting historical data clean and auditable.

**Serving Layer**
PostgreSQL scales further than people give it credit for. I would add read replicas to handle dashboard query load, time-based table partitioning so queries for recent data do not scan years of history, and connection pooling for concurrent API requests. The concern at scale is less about replacing PostgreSQL and more about operating it correctly. In a multi-tenant scenario where each customer owns their data, a catalog layer like Unity Catalog adds centralized governance and access control on top.

**Orchestration**
Right now the pipeline is a script with no scheduling, no retry logic, and no visibility into what failed and why. I would replace this with an asset-based orchestrator like Dagster, which Supersight already uses in production. Each medallion layer becomes a data asset with defined dependencies, so when Bronze ingestion fails the system immediately knows which downstream Silver and Gold assets are affected.

---

## Trade-offs and Production Improvements

The focus was on building a correct, idempotent pipeline with sound architectural decisions rather than operational completeness. Here is what I would add in a production version.

**Schema migrations**
Currently the schema is created directly from the SQLAlchemy model definitions on first run. This works for initial setup but cannot modify existing tables or handle schema evolution. I would add Alembic, versioning every schema change as a migration script with upgrade and rollback capability. Straightforward addition, just not worth the setup time for a take-home.

**Data quality validation**
The pipeline has minimal validation right now. I would add data quality checks at the Bronze to Silver boundary, things like non-negative counts, valid timestamps, known device IDs, so bad sensor data gets caught before it propagates into aggregations. Great Expectations is a common framework for this.

**Observability**
No structured logging, alerting, or pipeline monitoring currently exists. I would add structured logs at each pipeline stage, alerts on failures or data anomalies, and visibility into pipeline health over time. Right now if something silently fails it would not surface until someone looked at the data directly.

**Medallion architecture**
The pipeline jumps directly from raw CSVs to aggregated metrics in one step. I would separate this into Bronze, Silver, and Gold layers. If the aggregation logic changes, reprocessing triggers from Silver rather than the original source files, which also makes debugging upstream issues significantly easier.

**Cataloging**
In a multi-tenant deployment, I would add Unity Catalog or equivalent for centralized data discovery, lineage tracking, and access control across all layers. Each customer's data stays isolated and auditable without building custom access control logic into the application.