"""
Migrate BVMT Data - Convert bvmt_data table to stocks + historical_prices
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine
from sqlalchemy import text
from datetime import datetime
from loguru import logger

def migrate_bvmt_data():
    """Migrate data from bvmt_data to stocks and historical_prices"""
    
    logger.info("=" * 80)
    logger.info("🔄 Starting Data Migration")
    logger.info("=" * 80)
    
    with engine.connect() as conn:
       # 1. Get unique stocks from bvmt_data
        logger.info("📊 Step 1: Extracting unique stocks")
        result = conn.execute(text("""
            SELECT DISTINCT 
                "CODE" as code,
                "VALEUR" as ticker,
                "GROUPE" as groupe
            FROM bvmt_data
            ORDER BY "VALEUR"
        """))
        
        stocks_data = result.fetchall()
        logger.info(f"Found {len(stocks_data)} unique stocks")
        
        # 2. Insert into stocks table
        logger.info("📊 Step 2: Populating stocks table")
        inserted_stocks = 0
        
        for stock in stocks_data:
            code, ticker, groupe = stock
            
            # Check if exists
            check = conn.execute(text("""
                SELECT id FROM stocks WHERE ticker = :ticker
            """), {'ticker': ticker})
            
            if not check.fetchone():
                conn.execute(text("""
                    INSERT INTO stocks (ticker, name, sector, groupe, code)
                    VALUES (:ticker, :name, :sector, :groupe, :code)
                    ON CONFLICT (code) DO NOTHING
                """), {
                    'ticker': ticker,
                    'name': ticker,  # We'll update names later
                    'sector': 'Unknown',  # Will be updated based on groupe
                    'groupe': str(groupe) if groupe else None,
                    'code': code
                })
                inserted_stocks += 1
        
        conn.commit()
        logger.info(f"✅ Inserted {inserted_stocks} new stocks")
        
        # 3. Migrate historical prices
        logger.info("📊 Step 3: Migrating historical prices")
        
        result = conn.execute(text("""
            INSERT INTO historical_prices (stock_id, date, open, high, low, close, volume, nb_transactions, capital)
            SELECT 
                s.id,
                TO_DATE(b."SEANCE", 'DD/MM/YYYY'),
                b."OUVERTURE",
                b."PLUS_HAUT",
                b."PLUS_BAS",
                b."CLOTURE",
                b."QUANTITE_NEGOCIEE",
                b."NB_TRANSACTION",
                b."CAPITAUX"
            FROM bvmt_data b
            JOIN stocks s ON s.ticker = b."VALEUR"
            ON CONFLICT DO NOTHING
        """))
        
        conn.commit()
        logger.info(f"✅ Migrated {result.rowcount} price records")
        
        # 4. Verify migration
        logger.info("📊 Step 4: Verifying migration")
        
        result = conn.execute(text("SELECT COUNT(*) FROM stocks"))
        stock_count = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) FROM historical_prices"))
        price_count = result.scalar()
        
        result = conn.execute(text("""
            SELECT MIN(date), MAX(date) FROM historical_prices
        """))
        date_range = result.fetchone()
        
        logger.info(f"✅ Total stocks: {stock_count}")
        logger.info(f"✅ Total price records: {price_count:,}")
        if date_range[0]:
            logger.info(f"✅ Date range: {date_range[0]} to {date_range[1]}")
        
    logger.info("=" * 80)
    logger.info("✅ Migration Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        migrate_bvmt_data()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
