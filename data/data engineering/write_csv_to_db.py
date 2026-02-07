import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

CSV_FILES = [
    "../histo_cotation_2023.csv",
    "../histo_cotation_2024.csv",
    "../histo_cotation_2025.csv",
]

engine = create_engine(DATABASE_URL)

FILTER_COLUMN = "GROUPE"
FILTER_VALUES = [21, 32]

for file in CSV_FILES:
    df = pd.read_csv(file, sep=";")
    print(f"{file} original length: {len(df)}")

    df = pd.read_csv(file, sep=';')

    df.columns = df.columns.str.strip()

    # Trim string/object columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    df_clean = df[~df[FILTER_COLUMN].isin(FILTER_VALUES)]

    table_name = "bvmt_data"
    df_clean.to_sql(table_name, engine, if_exists="append", index=False)

    print(f"✅ {file} inserted, {len(df_clean)} rows after filter.")

print("All CSVs processed and pushed to Postgres.")
