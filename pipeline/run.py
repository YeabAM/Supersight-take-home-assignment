from pipeline.ingest import CSVIngestor
from pipeline.transform import MetricsTransformer
from pipeline.load import DatabaseLoader


def run_pipeline():
    """Execute the full ETL pipeline"""
    print("=" * 50)
    print("Starting Pipeline")
    print("=" * 50)

    try:
        print("\ningesting data...")
        print("-" * 50)
        ingestor = CSVIngestor()
        raw_data = ingestor.read_all_devices()

        print("\ntransforming data...")
        print("-" * 50)
        transformer = MetricsTransformer(ingestor.conn)
        hourly_data, daily_data = transformer.transform(raw_data)

        print("\nloading data...")
        print("-" * 50)
        loader = DatabaseLoader()
        loader.load(hourly_data, daily_data)

        print("\n" + "=" * 50)
        print("Pipeline completed successfully!")
        print("=" * 50)

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"Pipeline failed: {str(e)}")
        print("=" * 50)
        raise


if __name__ == "__main__":
    run_pipeline()