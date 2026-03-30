import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.getenv('DATA_DIR', './data')


class CSVIngestor:
    """Reads CSV files from device folders using DuckDB"""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or DATA_DIR)
        self.conn = duckdb.connect(':memory:')

    def get_device_folders(self):
        """Scan data directory for device folders"""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        device_folders = [d for d in self.data_dir.iterdir() if d.is_dir()]

        if not device_folders:
            raise ValueError(f"No device folders found in {self.data_dir}")

        return device_folders

    def read_all_devices(self):
        """Read all device data in a single query"""
        device_folders = self.get_device_folders()

        union_queries = []
        for folder in device_folders:
            device_id = folder.name
            csv_pattern = str(folder / "*.csv")

            union_queries.append(f"""
                SELECT
                    '{device_id}' as device_id,
                    timestamp,
                    "in" as people_in,
                    "out" as people_out
                FROM read_csv_auto('{csv_pattern}', header=true)
            """)

        query = " UNION ALL ".join(union_queries) + " ORDER BY timestamp"

        print(f"Reading data from {len(device_folders)} devices...")
        result = self.conn.sql(query)

        row_count = result.count('*').fetchone()[0]
        print(f"Total events loaded: {row_count}")

        return result