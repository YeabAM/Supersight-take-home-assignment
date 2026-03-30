import duckdb
from datetime import datetime


class MetricsTransformer:
    """Transforms raw event data into aggregated metrics"""

    def __init__(self, conn):
        self.conn = conn

    def aggregate_hourly(self, raw_data_relation):
        """Aggregate events to hourly metrics with net flow"""
        query = """
        SELECT
            device_id,
            DATE_TRUNC('hour', CAST(timestamp AS TIMESTAMP)) as hour,
            SUM(people_in) as people_in,
            SUM(people_out) as people_out,
            SUM(people_in) - SUM(people_out) as net_flow
        FROM raw_data_relation
        GROUP BY device_id, hour
        ORDER BY device_id, hour
        """

        print("Aggregating to hourly metrics...")
        result = self.conn.execute(query)

        row_count = self.conn.execute(f"SELECT COUNT(*) FROM ({query})").fetchone()[0]
        print(f"Generated {row_count} hourly records")

        return result

    def calculate_occupancy(self, hourly_relation):
        """Calculate running occupancy using window function"""
        query = """
        SELECT
            device_id,
            hour,
            people_in,
            people_out,
            net_flow,
            SUM(net_flow) OVER (
                PARTITION BY device_id
                ORDER BY hour
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) as occupancy
        FROM hourly_relation
        ORDER BY device_id, hour
        """

        print("Calculating occupancy...")
        result = self.conn.execute(query)

        return result

    def transform(self, raw_data_relation):
        """Run full transformation pipeline"""
        hourly = self.aggregate_hourly(raw_data_relation)
        with_occupancy = self.calculate_occupancy(hourly)

        print("Transformation complete")
        return with_occupancy