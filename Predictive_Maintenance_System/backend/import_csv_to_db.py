"""
Utility script to import the AI4I 2020 predictive maintenance dataset
from data/ai4i2020.csv directly into MySQL / database.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from backend.database import engine

CSV_PATH = PROJECT_ROOT / "data" / "ai4i2020.csv"

def import_csv():
    if not CSV_PATH.exists():
        print(f"[Error] File not found: {CSV_PATH}")
        return

    print(f"Reading dataset from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Found {len(df)} rows and {len(df.columns)} columns.")

    clean_cols = {
        "UDI": "udi",
        "Product ID": "product_id",
        "Type": "machine_type",
        "Air temperature [K]": "air_temperature",
        "Process temperature [K]": "process_temperature",
        "Rotational speed [rpm]": "rotational_speed",
        "Torque [Nm]": "torque",
        "Tool wear [min]": "tool_wear",
        "Machine failure": "machine_failure",
        "TWF": "twf",
        "HDF": "hdf",
        "PWF": "pwf",
        "OSF": "osf",
        "RNF": "rnf"
    }
    df = df.rename(columns=clean_cols)

    table_name = "dataset_records"
    print(f"Writing to table '{table_name}' in the database...")
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"✅ Successfully imported {len(df)} rows into table '{table_name}'!")

if __name__ == "__main__":
    import_csv()
