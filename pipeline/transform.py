from datetime import datetime

import duckdb


class MetricsTransformer:
    """Transforms raw event data into aggregated metrics"""

    def __init__(self, conn):
        self.conn = conn

    def aggregate_hourly(self, raw_data_relation):
        """Aggregate events to hourly metrics with net flow"""
        # Register the relation so it can be queried
        self.conn.register("raw_data", raw_data_relation)

        query = """
        SELECT
            device_id,
            DATE_TRUNC('hour', CAST(timestamp AS TIMESTAMP)) as hour,
            SUM(people_in) as people_in,
            SUM(people_out) as people_out,
            SUM(people_in) - SUM(people_out) as net_flow
        FROM raw_data
        GROUP BY device_id, hour
        ORDER BY device_id, hour
        """

        print("Aggregating to hourly metrics...")
        result = self.conn.sql(query)

        row_count = result.count('*').fetchone()[0]
        print(f"Generated {row_count} hourly records")

        return result

    def aggregate_daily(self, hourly_relation):
        """Aggregate hourly metrics to daily totals"""
        self.conn.register("hourly_data", hourly_relation)

        query = """
        SELECT
            device_id,
            DATE_TRUNC('day', hour) as date,
            SUM(people_in) as total_in,
            SUM(people_out) as total_out,
            SUM(net_flow) as net_flow
        FROM hourly_data
        GROUP BY device_id, date
        ORDER BY device_id, date
        """

        print("Aggregating to daily metrics...")
        result = self.conn.sql(query)

        row_count = result.count('*').fetchone()[0]
        print(f"Generated {row_count} daily records")
        return result

    def transform(self, raw_data_relation):
        """Run full transformation pipeline"""
        hourly = self.aggregate_hourly(raw_data_relation)
        daily = self.aggregate_daily(hourly)
        print("Transformation complete")
        return hourly, daily