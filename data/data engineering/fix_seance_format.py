"""
Fix SEANCE column format: DD/MM/YYYY → YYYY-MM-DD
This makes text-based ORDER BY and MAX() work correctly.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # Preview before
    r = conn.execute(text('SELECT "SEANCE" FROM bvmt_data LIMIT 5'))
    print("Before:", [row[0] for row in r.fetchall()])

    # Convert DD/MM/YYYY → YYYY-MM-DD
    result = conn.execute(text("""
        UPDATE bvmt_data
        SET "SEANCE" = SUBSTRING("SEANCE", 7, 4) || '-' ||
                       SUBSTRING("SEANCE", 4, 2) || '-' ||
                       SUBSTRING("SEANCE", 1, 2)
        WHERE "SEANCE" LIKE '__/__/____'
    """))
    print(f"Updated {result.rowcount} rows")

    # Preview after
    r = conn.execute(text('SELECT "SEANCE" FROM bvmt_data LIMIT 5'))
    print("After:", [row[0] for row in r.fetchall()])

    # Verify MAX is now correct
    r = conn.execute(text('SELECT MAX("SEANCE") FROM bvmt_data'))
    print("MAX(SEANCE):", r.fetchone()[0])
