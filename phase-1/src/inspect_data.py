
from pathlib import Path
import pandas as pd

# Find CSV files anywhere inside this project
all_csv_files = list(Path(".").rglob("*.csv"))

# These are the main files we need for our first task
required_sheets = [
    "fact_payroll",
    "fact_attendance_monthly",
    "dim_employee",
    "dim_department",
    "data_contracts",
    "reconciliation_answer_key",
]

print("CSV files found:", len(all_csv_files))

for sheet in required_sheets:
    matches = [
        file for file in all_csv_files
        if file.name.lower().endswith(f"{sheet}.csv")
    ]

    print("\n" + "=" * 65)
    print("DATASET:", sheet)

    if not matches:
        print("FILE NOT FOUND")
        continue

    file = matches[0]
    print("File path:", file)

    try:
        df = pd.read_csv(file, encoding="utf-8-sig")

        print("Rows:", len(df))
        print("Columns:", len(df.columns))
        print("Column names:")
        print(df.columns.tolist())

        print("\nFirst 2 rows:")
        print(df.head(2).to_string(index=False))

        print("\nMissing values:")
        print(df.isnull().sum().to_dict())

        print("\nDuplicate full rows:", df.duplicated().sum())

    except Exception as error:
        print("ERROR:", error)
