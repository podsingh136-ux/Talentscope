
print("TalentScope Dataset Checker Started!")

import pandas as pd

file_path = "data/raw/job_market_india.csv"

try:
    df = pd.read_csv(file_path, encoding="utf-8")

    print("\nDataset successfully loaded!")
    print("\nDataset Shape:")
    print(df.shape)

    print("\nColumn Names:")
    print(df.columns.tolist())

    print("\nFirst 5 Records:")
    print(df.head().to_string())

    print("\nMissing Values:")
    print(df.isnull().sum())

except FileNotFoundError:
    print("ERROR: CSV file nahi mili. File location check karo.")

except Exception as e:
    print("ERROR:", e)
