import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

# Lire toute la table
df = pd.read_sql("SELECT * FROM bvmt_data", engine)

# Filtrer uniquement l'année 2026
df['SEANCE'] = pd.to_datetime(df['SEANCE'], errors='coerce', dayfirst=True)
df_2026 = df[df['SEANCE'].dt.year == 2026]

# Afficher toutes les lignes de 2026
pd.set_option("display.max_rows", None)
print(df_2026)

# Optionnel : sauvegarder dans un CSV si tu veux
# df_2026.to_csv("../bvmt_data_2026.csv", sep=";", index=False, encoding="utf-8")
