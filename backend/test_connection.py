"""
Quick test script to verify Neon database connection.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Database URL
DATABASE_URL = "postgresql://neondb_owner:npg_bog2kaSA1DNZ@ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require"

print("🔍 Testing Neon PostgreSQL connection...")
print(f"Host: ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech")
print(f"Database: neondb")
print()

try:
    # Create engine
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("✅ Connection successful!")
        print(f"PostgreSQL version: {version[:50]}...")
        print()
        
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = result.fetchall()
        
        if tables:
            print(f"📋 Existing tables ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("📋 No tables found (database is empty)")
        print()
        
        # Check database size
        result = conn.execute(text("SELECT pg_database_size(current_database());"))
        size_bytes = result.fetchone()[0]
        size_mb = size_bytes / (1024 * 1024)
        print(f"💾 Database size: {size_mb:.2f} MB")
        
    print("\n✅ All connection tests passed!")
    print("Ready to initialize database schema.")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)
