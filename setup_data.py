import zipfile
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_SOURCE = os.getenv('DATA_SOURCE')
DATA_DIR = os.getenv('DATA_DIR', './data')

def setup_data():
    """Extract sensor data zip to data directory"""

    if not Path(DATA_SOURCE).exists():
        print(f"Error: {DATA_SOURCE} not found")
        print(f"Place your sensor_data.zip file and update DATA_SOURCE in .env")
        return

    # Create data directory
    Path(DATA_DIR).mkdir(exist_ok=True)

    # Extract zip
    print(f"Extracting {DATA_SOURCE} to {DATA_DIR}...")
    with zipfile.ZipFile(DATA_SOURCE, 'r') as zip_ref:
        zip_ref.extractall(DATA_DIR)

    # Validate structure
    data_path = Path(DATA_DIR)
    device_folders = [d for d in data_path.iterdir() if d.is_dir()]

    print(f"\nExtracted {len(device_folders)} device folders:")
    for device in device_folders:
        csv_files = list(device.glob('*.csv'))
        print(f"  - {device.name}: {len(csv_files)} CSV files")

    print(f"\n Data setup complete! Files ready in {DATA_DIR}/")

if __name__ == "__main__":
    setup_data()