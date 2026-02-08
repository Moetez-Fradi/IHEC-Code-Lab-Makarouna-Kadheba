import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import unicodedata
import re

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

INPUT_FILE = "../histo_cotation_2026.csv"

# Colonnes finales attendues
TARGET_COLUMNS = [
    "SEANCE", "GROUPE", "CODE", "VALEUR", "OUVERTURE", "CLOTURE",
    "PLUS_BAS", "PLUS_HAUT", "QUANTITE_NEGOCIEE", "NB_TRANSACTION", "CAPITAUX"
]

# Mapping colonnes CSV vers colonnes cibles
COL_MAP = {
    "SEANCE": "SEANCE",
    "ISIN.": "CODE",
    "VAL.": "VALEUR",
    "Ouv.": "OUVERTURE",
    "Clô.": "CLOTURE",
    "+ bas": "PLUS_BAS",
    "+ haut": "PLUS_HAUT",
    "Qté": "QUANTITE_NEGOCIEE",
    "Nb. Tr.": "NB_TRANSACTION",
    "Cap.": "CAPITAUX"
}

# Détecter séparateur
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    first_line = f.readline()
    sep = ";" if ";" in first_line else ","

# Lire le CSV
df = pd.read_csv(INPUT_FILE, sep=sep, dtype=str)

# Normaliser les colonnes
def normalize_colname(s):
    s = str(s).strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.upper().strip("_")

df.columns = [normalize_colname(c) for c in df.columns]

# Mapper les colonnes vers la table
df = df.rename(columns={normalize_colname(k): v for k,v in COL_MAP.items()})

# Ajouter colonnes manquantes
for col in TARGET_COLUMNS:
    if col not in df.columns:
        df[col] = pd.NA

# Nettoyer les espaces dans les chaînes
for col in df.select_dtypes(include="object"):
    df[col] = df[col].str.strip()

# Convertir colonnes numériques
num_cols = ["VALEUR","OUVERTURE","CLOTURE","PLUS_BAS","PLUS_HAUT","QUANTITE_NEGOCIEE","CAPITAUX"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col].str.replace(",", ".", regex=False), errors="coerce")

if "NB_TRANSACTION" in df.columns:
    df["NB_TRANSACTION"] = pd.to_numeric(df["NB_TRANSACTION"].str.replace(",", "", regex=False), errors="coerce").fillna(0).astype(int)

# Réordonner colonnes
df = df[TARGET_COLUMNS]

print(df.head)

# Append à la table SQL
# df.to_sql("bvmt_data", engine, if_exists="append", index=False)

print(f"✅ {len(df)} rows from 2026 CSV appended to bvmt_data")
