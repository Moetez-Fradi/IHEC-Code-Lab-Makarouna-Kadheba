#!/usr/bin/env python3
"""
Check what tables and data exist in the Neon database.
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
env_path = "backend/services/api_gateway/.env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

print(f"🔌 Connecting to Neon database...")
print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Database Tables Found: {len(tables)}")
        print("=" * 80)
        
        if not tables:
            print("❌ No tables found in database!")
            sys.exit(0)
        
        for table in sorted(tables):
            print(f"\n📋 Table: {table}")
            
            # Get row count
            try:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = result.scalar()
                print(f"   Rows: {count:,}")
                
                # Get column info
                columns = inspector.get_columns(table)
                print(f"   Columns: {len(columns)}")
                for col in columns[:5]:  # Show first 5 columns
                    print(f"     - {col['name']}: {col['type']}")
                if len(columns) > 5:
                    print(f"     ... and {len(columns) - 5} more columns")
                
                # Show sample data if table has rows
                if count > 0:
                    sample = conn.execute(text(f'SELECT * FROM "{table}" LIMIT 3'))
                    rows = sample.fetchall()
                    if rows:
                        print(f"   Sample data (first 3 rows):")
                        for i, row in enumerate(rows, 1):
                            # Show first 3 columns of each row
                            row_dict = dict(row._mapping)
                            sample_cols = list(row_dict.items())[:3]
                            print(f"     {i}. {dict(sample_cols)}")
            
            except Exception as e:
                print(f"   ⚠️  Error reading table: {str(e)[:100]}")
        
        print("\n" + "=" * 80)
        print("✅ Database check complete!\n")
        
        # Summary
        total_rows = 0
        for table in tables:
            try:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                total_rows += result.scalar()
            except:
                pass
        
        print(f"📈 Summary:")
        print(f"   Total tables: {len(tables)}")
        print(f"   Total rows: {total_rows:,}")
        
        # Check specific important tables
        important = ['stocks', 'historical_prices', 'sentiments', 'predictions', 'anomalies']
        existing = [t for t in important if t in tables]
        missing = [t for t in important if t not in tables]
        
        if existing:
            print(f"\n✅ Important tables present: {', '.join(existing)}")
        if missing:
            print(f"\n⚠️  Important tables missing: {', '.join(missing)}")

except Exception as e:
    print(f"\n❌ Error connecting to database:")
    print(f"   {str(e)}")
    sys.exit(1)
