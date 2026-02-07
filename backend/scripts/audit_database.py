"""
Database Audit Script - Check what's in Neon PostgreSQL
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import engine
from sqlalchemy import text, inspect
from loguru import logger
from tabulate import tabulate

settings = get_settings()


def audit_database():
    """Comprehensive database audit"""
    print("=" * 80)
    print("🔍 DATABASE AUDIT - Neon PostgreSQL")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # 1. List all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📋 TABLES FOUND: {len(tables)}")
        print("-" * 80)
        for table in sorted(tables):
            print(f"  ✓ {table}")
        print()
        
        # 2. Count rows in each table
        print("📊 ROW COUNTS:")
        print("-" * 80)
        counts = []
        for table in sorted(tables):
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            counts.append([table, f"{count:,}"])
        
        print(tabulate(counts, headers=["Table", "Rows"], tablefmt="grid"))
        print()
        
        # 3. Check stocks table
        if 'stocks' in tables:
            print("🏢 STOCKS TABLE:")
            print("-" * 80)
            result = conn.execute(text("""
                SELECT ticker, name, sector, market_cap 
                FROM stocks 
                ORDER BY ticker 
                LIMIT 10
            """))
            stocks = result.fetchall()
            if stocks:
                stock_data = [[s[0], s[1][:30], s[2], s[3]] for s in stocks]
                print(tabulate(stock_data, headers=["Ticker", "Name", "Sector", "Market Cap"], tablefmt="grid"))
            else:
                print("  ⚠️  No stocks found")
            print()
        
        # 4. Check historical_prices
        if 'historical_prices' in tables:
            print("📈 HISTORICAL PRICES:")
            print("-" * 80)
            result = conn.execute(text("""
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(DISTINCT stock_id) as num_stocks
                FROM historical_prices
            """))
            row = result.fetchone()
            if row and row[0]:
                print(f"  Date Range: {row[0]} to {row[1]}")
                print(f"  Stocks with data: {row[2]}")
                
                # Sample recent data
                result = conn.execute(text("""
                    SELECT hp.date, s.ticker, hp.close, hp.volume
                    FROM historical_prices hp
                    JOIN stocks s ON hp.stock_id = s.id
                    ORDER BY hp.date DESC
                    LIMIT 5
                """))
                recent = result.fetchall()
                if recent:
                    print("\n  Recent data samples:")
                    recent_data = [[r[0], r[1], f"{r[2]:.2f}" if r[2] else "N/A", f"{r[3]:,}" if r[3] else "0"] for r in recent]
                    print(tabulate(recent_data, headers=["Date", "Ticker", "Close", "Volume"], tablefmt="simple"))
            else:
                print("  ⚠️  No historical prices found")
            print()
        
        # 5. Check predictions
        if 'predictions' in tables:
            print("🔮 PREDICTIONS:")
            print("-" * 80)
            result = conn.execute(text("SELECT COUNT(*) FROM predictions"))
            count = result.scalar()
            if count > 0:
                result = conn.execute(text("""
                    SELECT s.ticker, p.prediction_date, p.predicted_price, p.confidence
                    FROM predictions p
                    JOIN stocks s ON p.stock_id = s.id
                    ORDER BY p.prediction_date DESC
                    LIMIT 5
                """))
                preds = result.fetchall()
                pred_data = [[r[0], r[1], f"{r[2]:.2f}", f"{r[3]:.0f}%"] for r in preds]
                print(tabulate(pred_data, headers=["Ticker", "Date", "Predicted Price", "Confidence"], tablefmt="grid"))
            else:
                print("  ℹ️  No predictions yet (waiting for ML model)")
            print()
        
        # 6. Check sentiments
        if 'sentiments' in tables:
            print("💭 SENTIMENTS:")
            print("-" * 80)
            result = conn.execute(text("SELECT COUNT(*) FROM sentiments"))
            count = result.scalar()
            if count > 0:
                result = conn.execute(text("""
                    SELECT s.ticker, sent.date, sent.score, sent.classification
                    FROM sentiments sent
                    JOIN stocks s ON sent.stock_id = s.id
                    ORDER BY sent.date DESC
                    LIMIT 5
                """))
                sents = result.fetchall()
                sent_data = [[r[0], r[1], f"{r[2]:.2f}", r[3]] for r in sents]
                print(tabulate(sent_data, headers=["Ticker", "Date", "Score", "Classification"], tablefmt="grid"))
            else:
                print("  ℹ️  No sentiments yet")
            print()
        
        # 7. Check anomalies
        if 'anomalies' in tables:
            print("⚠️  ANOMALIES:")
            print("-" * 80)
            result = conn.execute(text("SELECT COUNT(*) FROM anomalies"))
            count = result.scalar()
            if count > 0:
                result = conn.execute(text("""
                    SELECT s.ticker, a.detected_at, a.anomaly_type, a.severity
                    FROM anomalies a
                    JOIN stocks s ON a.stock_id = s.id
                    ORDER BY a.detected_at DESC
                    LIMIT 5
                """))
                anoms = result.fetchall()
                anom_data = [[r[0], r[1], r[2], r[3]] for r in anoms]
                print(tabulate(anom_data, headers=["Ticker", "Detected", "Type", "Severity"], tablefmt="grid"))
            else:
                print("  ℹ️  No anomalies detected yet")
            print()
        
        # 8. Check portfolios
        if 'portfolios' in tables:
            print("💼 PORTFOLIOS:")
            print("-" * 80)
            result = conn.execute(text("SELECT COUNT(*) FROM portfolios"))
            count = result.scalar()
            print(f"  Total portfolios: {count}")
            print()
        
        # 9. Database summary
        print("📊 DATABASE SUMMARY:")
        print("-" * 80)
        total_rows = sum(int(c[1].replace(',', '')) for c in counts)
        print(f"  Total tables: {len(tables)}")
        print(f"  Total rows: {total_rows:,}")
        print(f"  Database: neondb")
        print(f"  Status: ✅ Connected")
        print()
        
        print("=" * 80)
        print("✅ Audit Complete!")
        print("=" * 80)


if __name__ == "__main__":
    try:
        audit_database()
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        import traceback
        traceback.print_exc()
