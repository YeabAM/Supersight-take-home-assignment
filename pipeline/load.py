from database.config import get_engine
from database.models import Device, HourlyMetric
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


class DatabaseLoader:
    def __init__(self):
        self.engine = get_engine()

    def ensure_devices_exist(self, df):
        device_ids = df['device_id'].unique()

        with Session(self.engine) as session:
            for device_id in device_ids:
                stmt = insert(Device).values(device_id=device_id)
                stmt = stmt.on_conflict_do_nothing(index_elements=['device_id'])
                session.execute(stmt)
            session.commit()

    def upsert_hourly_metrics(self, df):
        print(f"Upserting {len(df)} hourly records...")

        self.ensure_devices_exist(df)

        records = df.to_dict('records')

        stmt = insert(HourlyMetric).values(records)

        stmt = stmt.on_conflict_do_update(
            index_elements=['device_id', 'hour'],
            set_={
                'people_in': stmt.excluded.people_in,
                'people_out': stmt.excluded.people_out,
                'net_flow': stmt.excluded.net_flow,
                'updated_at': func.now()
            }
        )

        with Session(self.engine) as session:
            session.execute(stmt)
            session.commit()

        print(f"Successfully upserted {len(records)} records")

    def load(self, duckdb_relation):
        """Convert DuckDB relation to DataFrame and load to PostgreSQL"""
        
        print("Converting to DataFrame...")
        df = duckdb_relation.df()

        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")

        self.upsert_hourly_metrics(df)

        print("Load complete")
        return df